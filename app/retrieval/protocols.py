from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.models.domain import Chunk, RetrievalResult


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[list[float]]) -> None: ...
    def search(self, vector: list[float], limit: int) -> list[RetrievalResult]: ...
    def delete_document(self, document_id: str) -> None: ...


class Reranker(Protocol):
    def rerank(self, query: str, results: Sequence[RetrievalResult]) -> list[RetrievalResult]: ...
