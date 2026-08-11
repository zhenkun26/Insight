from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.models.domain import RetrievalResult
from app.schemas.api import (
    ChatResponse,
    DocumentMetadataUpdate,
    JobResponse,
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
    job_service: object | None = None
    session_service: object | None = None


def _retrieval_response(result: RetrievalResult, catalog=None) -> RetrievalResponse:
    data = result.as_dict()
    if catalog:
        document = catalog.get_document(result.chunk.document_id)
        if document:
            data["source"].update(source=document.get("source"), tags=document.get("tags", []))
    return RetrievalResponse(**data)


def _source_response(source, catalog=None) -> SourceResponse:
    data = source.as_dict()
    if catalog:
        document = catalog.get_document(source.document_id)
        if document:
            data.update(source=document.get("source"), tags=document.get("tags", []))
    return SourceResponse(**data)


def _api_error(
    status_code: int, error_code: str, detail: str, trace_id: str | None = None
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error_code": error_code, "detail": detail, "trace_id": trace_id},
    )


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
                "index_jobs": "configured" if services.job_service else "synchronous",
            },
            "retrieval": services.retriever.last_status,
        }

    @router.post("/documents/upload")
    async def upload_document(request: Request, file: UploadFile = File(...)) -> dict:
        if not file.filename:
            raise _api_error(400, "filename_required", "filename is required")
        try:
            data = await file.read()
            if services.job_service:
                trace_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
                return services.job_service.submit_upload(file.filename, data, trace_id)
            return services.ingestion.ingest(
                file.filename,
                data,
                services._index_chunks if hasattr(services, "_index_chunks") else None,
            )
        except ValueError as exc:
            raise _api_error(415, "unsupported_document", str(exc)) from exc
        except Exception as exc:
            raise _api_error(500, "document_indexing_failed", exc.__class__.__name__) from exc

    @router.get("/documents")
    def list_documents(
        source: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[dict]:
        return services.catalog.list_documents(source=source, tag=tag, status=status)[
            offset : offset + limit
        ]

    @router.patch("/documents/{document_id}/metadata")
    def update_document_metadata(document_id: str, payload: DocumentMetadataUpdate) -> dict:
        if not services.catalog.get_document(document_id):
            raise _api_error(404, "document_not_found", "document not found")
        return (
            services.catalog.update_document_metadata(
                document_id,
                source=payload.source,
                tags=payload.tags,
                description=payload.description,
            )
            or {}
        )

    @router.delete("/documents/{document_id}")
    def delete_document(document_id: str) -> dict:
        if not services.catalog.get_document(document_id):
            raise _api_error(404, "document_not_found", "document not found")
        services.ingestion.delete(
            document_id,
            services.retriever.vector_store.delete_document
            if services.retriever.vector_store
            else None,
        )
        return {"document_id": document_id, "deleted": True}

    @router.post("/documents/reindex")
    def reindex(request: Request) -> dict:
        try:
            if services.job_service:
                return services.job_service.submit_reindex(
                    getattr(request.state, "request_id", None)
                )
            return services.ingestion.reindex(
                services._index_chunks if hasattr(services, "_index_chunks") else None
            )
        except Exception as exc:
            raise _api_error(500, "reindex_failed", exc.__class__.__name__) from exc

    @router.get("/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str) -> JobResponse:
        job = services.catalog.get_job(job_id)
        if not job:
            raise _api_error(404, "job_not_found", "job not found")
        return JobResponse(**job)

    @router.post("/jobs/{job_id}/retry", response_model=JobResponse)
    def retry_job(job_id: str, request: Request) -> JobResponse:
        if not services.job_service:
            raise _api_error(409, "jobs_not_configured", "async jobs are not configured")
        job = services.job_service.retry(job_id, getattr(request.state, "request_id", None))
        if not job:
            raise _api_error(409, "job_not_retryable", "job is not retryable")
        return JobResponse(**job)

    @router.post("/search", response_model=SearchResponse)
    def search(payload: QueryRequest, request: Request) -> SearchResponse:
        started = time.perf_counter()
        trace_id = (
            payload.trace_id or getattr(request.state, "request_id", None) or str(uuid.uuid4())
        )
        allowed_chunk_ids = services.catalog.allowed_chunk_ids(
            document_ids=payload.document_ids,
            source=payload.source,
            tag=payload.tag,
            only_indexed=True,
        )
        results = services.retriever.search(
            payload.query,
            payload.top_k,
            offset=payload.offset,
            allowed_chunk_ids=allowed_chunk_ids,
        )
        return SearchResponse(
            query=payload.query,
            retrieval_results=[_retrieval_response(result, services.catalog) for result in results],
            latency_ms=(time.perf_counter() - started) * 1000,
            trace_id=trace_id,
            stages=[{"name": "retrieval", "status": "ok", "latency_ms": 0}],
            retrieval_status=dict(getattr(services.retriever, "last_status", {})),
        )

    @router.post("/chat", response_model=ChatResponse)
    def chat(payload: QueryRequest, request: Request) -> ChatResponse:
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        session_id = payload.session_id
        history = services.session_service.history(session_id) if services.session_service else []
        result = services.qa.answer(payload.query, history=history, trace_id=request_id)
        if services.session_service and session_id:
            services.session_service.append(session_id, "user", payload.query)
            services.session_service.append(session_id, "assistant", result.answer)
        return ChatResponse(
            query=result.query,
            answer=result.answer,
            sources=[_source_response(source, services.catalog) for source in result.sources],
            retrieval_results=[
                _retrieval_response(item, services.catalog) for item in result.retrieval_results
            ],
            latency_ms=result.latency_ms,
            status=result.status,
            trace_id=result.trace_id,
            stages=result.stages,
            retrieval_status=result.retrieval_status,
        )

    @router.post("/chat/stream")
    def chat_stream(payload: QueryRequest, request: Request):
        trace_id = (
            payload.trace_id or getattr(request.state, "request_id", None) or str(uuid.uuid4())
        )
        history = (
            services.session_service.history(payload.session_id) if services.session_service else []
        )
        result = services.qa.answer(payload.query, history=history, trace_id=trace_id)
        if services.session_service and payload.session_id:
            services.session_service.append(payload.session_id, "user", payload.query)
            services.session_service.append(payload.session_id, "assistant", result.answer)

        def body():
            yield f"event: start\ndata: {json.dumps({'trace_id': result.trace_id})}\n\n"
            yield f"event: retrieval\ndata: {json.dumps({'status': result.retrieval_status, 'stages': result.stages}, ensure_ascii=False)}\n\n"
            for source in result.sources:
                yield f"event: source\ndata: {json.dumps(_source_response(source, services.catalog).model_dump(), ensure_ascii=False)}\n\n"
            yield f"event: token\ndata: {json.dumps({'text': result.answer}, ensure_ascii=False)}\n\n"
            yield f"event: complete\ndata: {json.dumps({'status': result.status})}\n\n"

        return StreamingResponse(
            body(), media_type="text/event-stream", headers={"x-insight-status": result.status}
        )

    @router.delete("/sessions/{session_id}")
    def delete_session(session_id: str) -> dict:
        if not services.session_service:
            raise _api_error(409, "sessions_not_configured", "sessions are not configured")
        deleted = services.session_service.delete(session_id)
        return {"session_id": session_id, "deleted": deleted}

    return router
