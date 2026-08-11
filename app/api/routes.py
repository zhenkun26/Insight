from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.models.domain import RetrievalResult
from app.schemas.api import (
    ChatResponse,
    QueryRequest,
    RetrievalResponse,
    SearchResponse,
    SourceResponse,
)
from app.services.qa import QuestionAnsweringService


@dataclass
class AppServices:
    catalog: object
    ingestion: object
    retriever: object
    qa: QuestionAnsweringService
    ollama: object
    settings: object


def _retrieval_response(result: RetrievalResult) -> RetrievalResponse:
    return RetrievalResponse(**result.as_dict())


def _source_response(source) -> SourceResponse:
    return SourceResponse(**source.as_dict())


def create_router(services: AppServices) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        ollama_status = services.ollama.health() if services.ollama else "not_configured"
        return {
            "status": "ok",
            "service": services.settings.app_name,
            "version": services.settings.app_version,
            "dependencies": {
                "ollama": ollama_status,
                "vector_store": "configured" if services.retriever.vector_store else "keyword_only",
            },
            "retrieval": services.retriever.last_status,
        }

    @router.post("/documents/upload")
    async def upload_document(file: UploadFile = File(...)) -> dict:
        if not file.filename:
            raise HTTPException(status_code=400, detail="filename is required")
        try:
            data = await file.read()
            return services.ingestion.ingest(
                file.filename,
                data,
                services._index_chunks if hasattr(services, "_index_chunks") else None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"document indexing failed: {exc.__class__.__name__}"
            ) from exc

    @router.get("/documents")
    def list_documents() -> list[dict]:
        return services.catalog.list_documents()

    @router.delete("/documents/{document_id}")
    def delete_document(document_id: str) -> dict:
        if not services.catalog.get_document(document_id):
            raise HTTPException(status_code=404, detail="document not found")
        services.ingestion.delete(
            document_id,
            services.retriever.vector_store.delete_document
            if services.retriever.vector_store
            else None,
        )
        return {"document_id": document_id, "deleted": True}

    @router.post("/documents/reindex")
    def reindex() -> dict:
        try:
            return services.ingestion.reindex(
                services._index_chunks if hasattr(services, "_index_chunks") else None
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"reindex failed: {exc.__class__.__name__}"
            ) from exc

    @router.post("/search", response_model=SearchResponse)
    def search(payload: QueryRequest) -> SearchResponse:
        started = time.perf_counter()
        results = services.retriever.search(payload.query, payload.top_k)
        return SearchResponse(
            query=payload.query,
            retrieval_results=[_retrieval_response(result) for result in results],
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    @router.post("/chat", response_model=ChatResponse)
    def chat(payload: QueryRequest, request: Request) -> ChatResponse:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        result = services.qa.answer(payload.query)
        return ChatResponse(
            query=result.query,
            answer=result.answer,
            sources=[_source_response(source) for source in result.sources],
            retrieval_results=[_retrieval_response(item) for item in result.retrieval_results],
            latency_ms=result.latency_ms,
            status=result.status,
        )

    @router.post("/chat/stream")
    def chat_stream(payload: QueryRequest):
        result = services.qa.answer(payload.query)

        def body():
            yield result.answer

        return StreamingResponse(
            body(), media_type="text/plain", headers={"x-insight-status": result.status}
        )

    return router
