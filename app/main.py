from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import AppServices, create_router
from app.core.config import Settings, settings
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import MilvusVectorStore
from app.services.catalog import DocumentCatalog
from app.services.ingestion import IngestionService
from app.services.jobs import IndexJobService
from app.services.ollama import OllamaClient
from app.services.qa import QuestionAnsweringService
from app.services.rerank import OllamaReranker, SimpleKeywordReranker
from app.services.session import SessionService

WEB_DIR = Path(__file__).resolve().parent / "web"


def build_services(config: Settings = settings) -> AppServices:
    config.ensure_directories()
    catalog = DocumentCatalog(config.database_path)
    catalog.mark_reindex_required(config.index_version, config.embedding_model)
    bm25 = BM25Index(config.bm25_index_path)
    if not any(item["status"] == "reindex_required" for item in catalog.list_documents()):
        bm25.load()
    ollama = OllamaClient(
        config.llm_base_url,
        config.llm_model,
        config.embedding_model,
        config.request_timeout_seconds,
    )
    vector_store = None
    if config.milvus_uri:
        try:
            vector_store = MilvusVectorStore(config.milvus_uri, config.milvus_collection)
        except Exception:
            vector_store = None
    if not config.enable_rerank:
        reranker = None
    elif config.reranker_model:
        reranker = OllamaReranker(ollama, config.reranker_model)
    else:
        reranker = SimpleKeywordReranker()
    retriever = HybridRetriever(
        bm25,
        ollama if vector_store else None,
        vector_store,
        config.top_k,
        config.candidate_k,
        config.score_threshold,
        config.rrf_k,
        reranker,
        keyword_enabled=True,
        vector_score_threshold=config.vector_score_threshold,
    )
    ingestion = IngestionService(catalog, config)

    def index_chunks(chunks):
        all_chunks = catalog.get_chunks()
        bm25.build(all_chunks)
        bm25.save()
        if vector_store:
            vectors = [ollama.embed(chunk.text) for chunk in chunks]
            vector_store.upsert(chunks, vectors)

    services = AppServices(
        catalog,
        ingestion,
        retriever,
        QuestionAnsweringService(retriever, ollama, config.score_threshold),
        ollama,
        config,
    )
    services._index_chunks = index_chunks
    services.session_service = SessionService(catalog, config)
    services.job_service = IndexJobService(catalog, ingestion, index_chunks, config)
    return services


def create_app(config: Settings = settings, services: AppServices | None = None) -> FastAPI:
    app = FastAPI(title=config.app_name, version=config.app_version or __version__)

    @app.middleware("http")
    async def request_logging(request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logging.getLogger("insight.request").info(
            "request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    app.include_router(create_router(services or build_services(config)))

    @app.get("/", include_in_schema=False)
    def web_console() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html", media_type="text/html")

    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="web-assets")
    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
