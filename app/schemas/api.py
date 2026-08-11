from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)


class SourceResponse(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page: int | None = None
    section: str | None = None


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


class ChatResponse(SearchResponse):
    answer: str
    sources: list[SourceResponse]
    status: str = "ok"


class ErrorResponse(BaseModel):
    error: str
    request_id: str | None = None
