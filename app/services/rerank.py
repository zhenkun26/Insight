from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol

from app.models.domain import RetrievalResult
from app.retrieval.bm25 import tokenize


class ModelGenerator(Protocol):
    def generate(self, prompt: str, system: str, model: str | None = None) -> str: ...


_SCORE_PATTERN = re.compile(r"(?:0|1)(?:\.\d+)?")


def parse_rerank_score(response: str) -> float:
    value = response.strip()
    if not _SCORE_PATTERN.fullmatch(value):
        raise ValueError("reranker response must be a single number between 0 and 1")
    score = float(value)
    if not 0 <= score <= 1:
        raise ValueError("reranker score must be between 0 and 1")
    return score


class SimpleKeywordReranker:
    """Small deterministic reranker useful for local demos and tests."""

    def rerank(self, query: str, results: Sequence[RetrievalResult]) -> list[RetrievalResult]:
        terms = set(tokenize(query))
        ranked = []
        for result in results:
            text_terms = set(tokenize(result.chunk.text))
            overlap = sum(term in text_terms for term in terms)
            result.rerank_score = overlap / max(len(terms), 1)
            result.score = result.rerank_score
            ranked.append(result)
        return sorted(ranked, key=lambda item: (-item.score, item.chunk.position))


class OllamaReranker:
    """Score candidates with a local Ollama model, applying results atomically."""

    def __init__(self, generator: ModelGenerator, model: str):
        if not model.strip():
            raise ValueError("reranker model must not be empty")
        self.generator = generator
        self.model = model

    def rerank(self, query: str, results: Sequence[RetrievalResult]) -> list[RetrievalResult]:
        system = (
            "You are a retrieval relevance scorer. Return only one decimal number between 0 and 1. "
            "Do not return words, JSON, markdown, or explanations."
        )
        scored: list[tuple[RetrievalResult, float]] = []
        for result in results:
            prompt = (
                "QUERY:\n"
                f"{query}\n\nPASSAGE:\n"
                f"{result.chunk.text}\n\n"
                "Return only the relevance score."
            )
            raw_score = self.generator.generate(prompt, system, model=self.model)
            scored.append((result, parse_rerank_score(raw_score)))
        for result, score in scored:
            result.rerank_score = score
            result.score = score
        return [
            result
            for result, _score in sorted(
                scored, key=lambda item: (-item[1], item[0].chunk.position)
            )
        ]
