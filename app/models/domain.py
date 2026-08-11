from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Source:
    document_id: str
    filename: str
    chunk_id: str
    page: int | None = None
    section: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "chunk_id": self.chunk_id,
            "page": self.page,
            "section": self.section,
        }


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    page: int | None = None
    section: str | None = None
    position: int = 0

    @property
    def source(self) -> Source:
        return Source(self.document_id, self.filename, self.chunk_id, self.page, self.section)


@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float
    keyword_score: float | None = None
    vector_score: float | None = None
    rerank_score: float | None = None
    status: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "document_id": self.chunk.document_id,
            "text": self.chunk.text,
            "score": self.score,
            "keyword_score": self.keyword_score,
            "vector_score": self.vector_score,
            "rerank_score": self.rerank_score,
            "status": self.status,
            "source": self.chunk.source.as_dict(),
        }
