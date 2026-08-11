from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import build_services, create_app
from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.services.catalog import DocumentCatalog
from app.services.ingestion import IngestionService
from app.services.jobs import IndexJobService
from app.services.qa import REFUSAL_ANSWER, QuestionAnsweringService
from app.services.session import SessionService


def test_catalog_metadata_and_session_cleanup(tmp_path):
    catalog = DocumentCatalog(str(tmp_path / "catalog.db"))
    catalog.upsert_document(
        "doc-1", "guide.txt", "hash-1", 10, "indexed", source="public", tags=["warning"]
    )
    catalog.update_document_metadata(
        "doc-1", source="official", tags=["typhoon"], description="demo"
    )
    assert catalog.list_documents(source="official", tag="typhoon")[0]["document_id"] == "doc-1"

    session = SessionService(catalog, Settings(session_max_turns=1, session_max_chars=20))
    session.append("session-1", "user", "这是一条较长的问题内容")
    session.append("session-1", "assistant", "回答")
    assert len(session.history("session-1")) == 2
    assert session.delete("session-1")
    assert session.history("session-1") == []


def test_hybrid_filters_and_offset():
    chunks = [
        Chunk("a", "doc-a", "warning.md", "台风预警信号", position=0),
        Chunk("b", "doc-b", "rain.txt", "暴雨预警信号", position=1),
    ]
    index = BM25Index()
    index.build(chunks)
    retriever = HybridRetriever(index, top_k=1, score_threshold=0.001)
    allowed = {"b"}
    results = retriever.search("预警", allowed_chunk_ids=allowed, offset=0)
    assert [item.chunk.chunk_id for item in results] == ["b"]


def test_index_job_upload_reaches_terminal_state(tmp_path):
    config = Settings(
        database_path=str(tmp_path / "db.sqlite"),
        bm25_index_path=str(tmp_path / "bm25.json"),
        upload_dir=str(tmp_path / "uploads"),
        job_workers=1,
    )
    catalog = DocumentCatalog(config.database_path)
    ingestion = IngestionService(catalog, config)
    index = BM25Index(config.bm25_index_path)

    def callback(chunks):
        index.build(catalog.get_chunks())
        index.save()
        assert chunks

    jobs = IndexJobService(catalog, ingestion, callback, config)
    try:
        job = jobs.submit_upload("guide.txt", "台风预警信号分为四级".encode())
        for _ in range(40):
            current = catalog.get_job(job["job_id"])
            if current["status"] in {"succeeded", "failed"}:
                break
            time.sleep(0.01)
        assert current["status"] == "succeeded"
        assert catalog.get_document(current["document_id"])["status"] == "indexed"
    finally:
        jobs.close()


def test_history_never_replaces_retrieval_evidence():
    class EmptyRetriever:
        last_status = {"keyword": "ok", "vector": "disabled"}

        def search(self, _query):
            return []

    class NeverCalled:
        def generate(self, *_args):
            raise AssertionError("LLM must not be called")

    result = QuestionAnsweringService(EmptyRetriever(), NeverCalled()).answer(
        "刚才的预警是什么？",
        history=[{"role": "assistant", "content": "台风分为四级"}],
    )
    assert result.answer == REFUSAL_ANSWER
    assert "fallback" in [stage["name"] for stage in result.stages]


def test_production_app_upload_returns_pollable_job(tmp_path):
    config = Settings(
        database_path=str(tmp_path / "db.sqlite"),
        bm25_index_path=str(tmp_path / "bm25.json"),
        upload_dir=str(tmp_path / "uploads"),
        milvus_uri="",
        job_workers=1,
    )
    services = build_services(config)
    client = TestClient(create_app(config, services))
    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("guide.txt", "台风预警信号分为四级".encode(), "text/plain")},
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        for _ in range(40):
            job = client.get(f"/jobs/{job_id}").json()
            if job["status"] in {"succeeded", "failed"}:
                break
            time.sleep(0.01)
        assert job["status"] == "succeeded"
        assert client.get("/documents").json()[0]["status"] == "indexed"
    finally:
        services.job_service.close()
