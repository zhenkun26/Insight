from __future__ import annotations

import time
from threading import Event

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.ingestion.ocr import OCRUnavailableError
from app.main import build_services, create_app
from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.services.catalog import DocumentCatalog
from app.services.ingestion import IngestionService
from app.services.jobs import IndexJobService
from app.services.qa import REFUSAL_ANSWER, QuestionAnsweringService
from app.services.rerank import OllamaReranker, SimpleKeywordReranker
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


def test_reranker_factory_respects_model_configuration(tmp_path):
    def make_config(**overrides):
        return Settings(
            database_path=str(tmp_path / f"{overrides.get('name', 'default')}.db"),
            bm25_index_path=str(tmp_path / f"{overrides.get('name', 'default')}.json"),
            upload_dir=str(tmp_path / f"{overrides.get('name', 'default')}-uploads"),
            milvus_uri="",
            enable_rerank=overrides.get("enable_rerank", False),
            reranker_model=overrides.get("reranker_model", ""),
        )

    cases = [
        (make_config(name="disabled"), None),
        (make_config(name="keyword", enable_rerank=True), SimpleKeywordReranker),
        (make_config(name="model", enable_rerank=True, reranker_model="rerank"), OllamaReranker),
    ]
    services = []
    try:
        for config, expected in cases:
            built = build_services(config)
            services.append(built)
            assert (
                isinstance(built.retriever.reranker, expected)
                if expected
                else built.retriever.reranker is None
            )
    finally:
        for built in services:
            built.job_service.close()


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


def test_index_job_exposes_ocr_error_code(tmp_path):
    config = Settings(
        database_path=str(tmp_path / "catalog.db"),
        bm25_index_path=str(tmp_path / "bm25.json"),
        upload_dir=str(tmp_path / "uploads"),
        job_workers=1,
    )
    catalog = DocumentCatalog(config.database_path)

    class BrokenIngestion:
        @staticmethod
        def hash_bytes(_data):
            return "hash"

        def ingest(self, *_args):
            raise OCRUnavailableError("install OCR tools")

    jobs = IndexJobService(catalog, BrokenIngestion(), lambda _chunks: None, config)
    try:
        job = jobs.submit_upload("scan.pdf", b"pdf")
        for _ in range(40):
            current = catalog.get_job(job["job_id"])
            if current["status"] == "failed":
                break
            time.sleep(0.01)
        assert current["status"] == "failed"
        assert current["error"].startswith("ocr_unavailable:")
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


def test_queued_job_can_be_cancelled_without_index_callback(tmp_path):
    config = Settings(
        database_path=str(tmp_path / "db.sqlite"),
        bm25_index_path=str(tmp_path / "bm25.json"),
        upload_dir=str(tmp_path / "uploads"),
        job_workers=1,
    )
    catalog = DocumentCatalog(config.database_path)
    ingestion = IngestionService(catalog, config)
    started = Event()
    release = Event()
    callback_count = 0

    def callback(_chunks):
        nonlocal callback_count
        callback_count += 1
        started.set()
        release.wait(timeout=1)

    jobs = IndexJobService(catalog, ingestion, callback, config)
    try:
        first = jobs.submit_upload("first.txt", b"first weather document")
        assert started.wait(timeout=1)
        second = jobs.submit_upload("second.txt", b"second weather document")
        cancelled = jobs.cancel(second["job_id"], "trace-cancel")
        assert cancelled["status"] == "cancelled"
        assert jobs.cancel(second["job_id"])["status"] == "cancelled"
        release.set()
        for _ in range(40):
            if catalog.get_job(first["job_id"])["status"] == "succeeded":
                break
            time.sleep(0.01)
        assert callback_count == 1
        assert catalog.get_job(second["job_id"])["status"] == "cancelled"
    finally:
        release.set()
        jobs.close()


def test_native_stream_emits_multiple_grounded_fragments():
    chunk = Chunk("chunk-1", "doc-1", "guide.txt", "台风预警分为四级")

    class Retriever:
        last_status = {"keyword": "ok", "vector": "disabled"}

        def search(self, _query):
            from app.models.domain import RetrievalResult

            return [RetrievalResult(chunk, 0.2)]

    class StreamModel:
        def generate(self, *_args):
            raise AssertionError("native stream should not use non-stream generate")

        def stream_generate(self, *_args):
            yield "第一片段"
            yield "第二片段"

    events = list(QuestionAnsweringService(Retriever(), StreamModel()).stream_answer("台风预警"))
    assert [event["event"] for event in events] == [
        "start",
        "retrieval",
        "source",
        "token",
        "token",
        "complete",
    ]
    assert [event["data"]["text"] for event in events if event["event"] == "token"] == [
        "第一片段",
        "第二片段",
    ]
    assert events[-1]["data"]["stream_mode"] == "native"


def test_broken_native_stream_uses_safe_single_event_fallback():
    chunk = Chunk("chunk-1", "doc-1", "guide.txt", "台风预警分为四级")

    class Retriever:
        last_status = {"keyword": "ok", "vector": "disabled"}

        def search(self, _query):
            from app.models.domain import RetrievalResult

            return [RetrievalResult(chunk, 0.2)]

    class BrokenStreamModel:
        def generate(self, *_args):
            return "安全 fallback [1]"

        def stream_generate(self, *_args):
            raise RuntimeError("connection reset")

    events = list(
        QuestionAnsweringService(Retriever(), BrokenStreamModel()).stream_answer("台风预警")
    )
    tokens = [event["data"]["text"] for event in events if event["event"] == "token"]
    assert tokens == ["安全 fallback [1]"]
    assert events[-1]["data"]["status"] == "stream_fallback"
    assert events[-1]["data"]["stream_mode"] == "fallback"
