from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=10000)
    source: str | None = Field(default=None, max_length=500)
    tag: str | None = Field(default=None, max_length=100)
    document_ids: list[str] | None = Field(default=None, max_length=50)
    session_id: str | None = Field(default=None, max_length=100)
    trace_id: str | None = Field(default=None, max_length=100)


class SourceResponse(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page: int | None = None
    section: str | None = None
    source: str | None = None
    tags: list[str] = Field(default_factory=list)


class RetrievalResponse(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    keyword_score: float | None = None
    vector_score: float | None = None
    rerank_score: float | None = None
    status: str | None = None
    source: SourceResponse


class SearchResponse(BaseModel):
    query: str
    retrieval_results: list[RetrievalResponse]
    latency_ms: float
    trace_id: str | None = None
    stages: list[dict] = Field(default_factory=list)
    retrieval_status: dict[str, str] = Field(default_factory=dict)


class ChatResponse(SearchResponse):
    answer: str
    sources: list[SourceResponse]
    status: str = "ok"


class JobResponse(BaseModel):
    job_id: str
    document_id: str | None = None
    operation: str
    status: str
    processed_chunks: int = 0
    total_chunks: int = 0
    error: str | None = None
    retryable: bool = False
    parent_job_id: str | None = None
    trace_id: str | None = None
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None


class DocumentMetadataUpdate(BaseModel):
    source: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    description: str | None = Field(default=None, max_length=2000)


class ErrorResponse(BaseModel):
    error_code: str
    detail: str
    trace_id: str | None = None
