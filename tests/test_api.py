from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.api.routes import AppServices
from app.core.config import Settings
from app.main import create_app
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.services.catalog import DocumentCatalog
from app.services.ingestion import IngestionService
from app.services.qa import QuestionAnsweringService


class FakeOllama:
    def health(self):
        return "ok"

    def embed(self, _text):
        return [1.0, 0.0]

    def generate(self, _prompt, _system):
        return "依据 [1]，这是测试回答。"


def make_client(tmp_path):
    config = Settings(
        database_path=str(tmp_path / "db.sqlite"),
        bm25_index_path=str(tmp_path / "bm25.json"),
        upload_dir=str(tmp_path / "uploads"),
        milvus_uri="memory://",
    )
    catalog = DocumentCatalog(config.database_path)
    index = BM25Index(config.bm25_index_path)
    retriever = HybridRetriever(index, top_k=5, score_threshold=0.001)
    ollama = FakeOllama()
    ingestion = IngestionService(catalog, config)
    services = AppServices(
        catalog,
        ingestion,
        retriever,
        QuestionAnsweringService(retriever, ollama, 0.001),
        ollama,
        config,
    )
    services._index_chunks = lambda chunks: (index.build(catalog.get_chunks()), index.save())
    return TestClient(create_app(config, services))


def test_health_and_upload(tmp_path):
    client = make_client(tmp_path)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["dependencies"]["ocr"]["enabled"] is False
    response = client.post(
        "/documents/upload",
        files={"file": ("guide.txt", b"# 4. Testing\nThe document is a demo.", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["chunk_count"] == 1
    assert client.get("/documents").json()[0]["filename"] == "guide.txt"


def test_web_console_assets_and_api_routes(tmp_path):
    client = make_client(tmp_path)
    page = client.get("/")
    assert page.status_code == 200
    assert "洞察者" in page.text
    assert client.get("/assets/app.js").headers["content-type"].startswith("text/javascript")
    assert client.get("/assets/styles.css").headers["content-type"].startswith("text/css")
    assert client.get("/health").json()["status"] == "ok"


def test_chat_mock_and_refusal(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/documents/upload",
        files={"file": ("guide.txt", "台风预警信号说明".encode(), "text/plain")},
    )
    response = client.post("/chat", json={"query": "台风预警"})
    assert response.status_code == 200
    assert "answer" in response.json()


def test_metadata_filter_and_sse_response(tmp_path):
    client = make_client(tmp_path)
    upload = client.post(
        "/documents/upload",
        files={"file": ("guide.txt", "台风预警信号说明".encode(), "text/plain")},
    )
    document_id = upload.json()["document_id"]
    updated = client.patch(
        f"/documents/{document_id}/metadata",
        json={"source": "demo", "tags": ["typhoon"], "description": "test"},
    )
    assert updated.status_code == 200
    search = client.post("/search", json={"query": "台风", "tag": "typhoon"})
    assert search.status_code == 200
    assert search.json()["retrieval_results"]
    stream = client.post("/chat/stream", json={"query": "台风预警"})
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: complete" in stream.text
