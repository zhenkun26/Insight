from __future__ import annotations

import math
from collections.abc import Sequence

from app.models.domain import Chunk, RetrievalResult


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return dot / norm if norm else 0.0


class InMemoryVectorStore:
    def __init__(self):
        self._items: dict[str, tuple[Chunk, list[float]]] = {}

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[list[float]]) -> None:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._items[chunk.chunk_id] = (chunk, vector)

    def search(
        self,
        vector: list[float],
        limit: int,
        allowed_chunk_ids: set[str] | None = None,
    ) -> list[RetrievalResult]:
        results = [
            RetrievalResult(
                chunk,
                cosine_similarity(vector, item_vector),
                vector_score=cosine_similarity(vector, item_vector),
            )
            for chunk, item_vector in self._items.values()
            if allowed_chunk_ids is None or chunk.chunk_id in allowed_chunk_ids
        ]
        return sorted(results, key=lambda item: (-item.score, item.chunk.position))[:limit]

    def delete_document(self, document_id: str) -> None:
        self._items = {
            key: value for key, value in self._items.items() if value[0].document_id != document_id
        }


class MilvusVectorStore:
    """MilvusClient adapter for Milvus Lite files and remote Milvus URIs."""

    def __init__(self, uri: str, collection_name: str = "insight_chunks"):
        import os

        configured_uri = os.environ.pop("MILVUS_URI", None)
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise RuntimeError("Milvus vector storage requires pymilvus[milvus_lite]") from exc
        finally:
            if configured_uri is not None:
                os.environ["MILVUS_URI"] = configured_uri

        self._client = MilvusClient(uri)
        self._collection_name = collection_name

    def _ensure_collection(self, dimension: int) -> None:
        if not self._client.has_collection(self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                dimension=dimension,
                primary_field_name="chunk_id",
                id_type="string",
                vector_field_name="vector",
                metric_type="COSINE",
                auto_id=False,
            )

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[list[float]]) -> None:
        if not chunks:
            return
        if not vectors or not vectors[0]:
            raise ValueError("embedding vectors cannot be empty")
        self._ensure_collection(len(vectors[0]))
        self._client.upsert(
            collection_name=self._collection_name,
            data=[
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "text": chunk.text,
                    "vector": vector,
                }
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
        )

    def search(
        self,
        vector: list[float],
        limit: int,
        allowed_chunk_ids: set[str] | None = None,
    ) -> list[RetrievalResult]:
        if not self._client.has_collection(self._collection_name):
            return []
        self._client.load_collection(collection_name=self._collection_name)
        rows = self._client.search(
            collection_name=self._collection_name,
            data=[vector],
            limit=max(limit * 3, limit) if allowed_chunk_ids is not None else limit,
            output_fields=["document_id", "filename", "text"],
        )[0]
        results = [
            RetrievalResult(
                Chunk(
                    str(row["entity"].get("chunk_id", row.get("id", ""))),
                    row["entity"].get("document_id", ""),
                    row["entity"].get("filename", ""),
                    row["entity"].get("text", ""),
                ),
                float(row["distance"]),
                vector_score=float(row["distance"]),
            )
            for row in rows
        ]
        if allowed_chunk_ids is not None:
            results = [item for item in results if item.chunk.chunk_id in allowed_chunk_ids]
        return results[:limit]

    def delete_document(self, document_id: str) -> None:
        if self._client.has_collection(self._collection_name):
            self._client.delete(
                collection_name=self._collection_name,
                filter=f'document_id == "{document_id}"',
            )
