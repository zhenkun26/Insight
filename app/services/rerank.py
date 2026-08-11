from __future__ import annotations

from collections.abc import Sequence

from app.models.domain import RetrievalResult


class SimpleKeywordReranker:
    """Small deterministic reranker useful for local demos and tests."""

    def rerank(self, query: str, results: Sequence[RetrievalResult]) -> list[RetrievalResult]:
        terms = set(query.lower().split())
        ranked = []
        for result in results:
            overlap = sum(term in result.chunk.text.lower() for term in terms)
            result.rerank_score = overlap / max(len(terms), 1)
            result.score = result.rerank_score
            ranked.append(result)
        return sorted(ranked, key=lambda item: (-item.score, item.chunk.position))
