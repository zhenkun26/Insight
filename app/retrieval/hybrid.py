from __future__ import annotations

from app.models.domain import RetrievalResult
from app.retrieval.bm25 import BM25Index
from app.retrieval.protocols import EmbeddingProvider, Reranker, VectorStore


class HybridRetriever:
    def __init__(
        self,
        bm25: BM25Index,
        embeddings: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        top_k: int = 5,
        candidate_k: int = 20,
        score_threshold: float = 0.01,
        rrf_k: int = 60,
        reranker: Reranker | None = None,
    ):
        self.bm25 = bm25
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.top_k = top_k
        self.candidate_k = candidate_k
        self.score_threshold = score_threshold
        self.rrf_k = rrf_k
        self.reranker = reranker
        self.last_status: dict[str, str] = {}

    def search(self, query: str, top_k: int | None = None) -> list[RetrievalResult]:
        if not query.strip():
            return []
        limit = top_k or self.top_k
        keyword_results = self.bm25.search(query, self.candidate_k)
        vector_results: list[RetrievalResult] = []
        self.last_status = {
            "keyword": "ok",
            "vector": "disabled" if not (self.embeddings and self.vector_store) else "ok",
        }
        if self.embeddings and self.vector_store:
            try:
                vector_results = self.vector_store.search(
                    self.embeddings.embed(query), self.candidate_k
                )
            except Exception as exc:
                self.last_status["vector"] = f"fallback:{exc.__class__.__name__}"
        merged: dict[str, RetrievalResult] = {}
        for rank, result in enumerate(keyword_results, 1):
            merged[result.chunk.chunk_id] = RetrievalResult(
                result.chunk,
                1 / (self.rrf_k + rank),
                keyword_score=result.keyword_score,
                details={"keyword_rank": rank},
            )
        for rank, result in enumerate(vector_results, 1):
            current = merged.get(result.chunk.chunk_id)
            if current:
                current.score += 1 / (self.rrf_k + rank)
                current.vector_score = result.vector_score
                current.details["vector_rank"] = rank
            else:
                merged[result.chunk.chunk_id] = RetrievalResult(
                    result.chunk,
                    1 / (self.rrf_k + rank),
                    vector_score=result.vector_score,
                    details={"vector_rank": rank},
                )
        results = sorted(merged.values(), key=lambda item: (-item.score, item.chunk.position))
        if self.reranker:
            try:
                results = self.reranker.rerank(query, results)
                self.last_status["rerank"] = "ok"
            except Exception as exc:
                self.last_status["rerank"] = f"fallback:{exc.__class__.__name__}"
        else:
            self.last_status["rerank"] = "disabled"
        threshold = self.score_threshold
        return [result for result in results if result.score >= threshold][:limit]
