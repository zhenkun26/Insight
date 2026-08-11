from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from pathlib import Path

from app.models.domain import Chunk, RetrievalResult


def tokenize(text: str) -> list[str]:
    # Keep Latin words intact and split CJK into searchable characters. This
    # avoids requiring a language-specific tokenizer for short local corpora.
    return re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower())


class BM25Index:
    def __init__(self, path: str | None = None):
        self.path = path
        self.chunks: list[Chunk] = []
        self._tokens: list[list[str]] = []
        self._idf: dict[str, float] = {}
        self._avgdl = 0.0

    def build(self, chunks: Sequence[Chunk]) -> None:
        self.chunks = list(chunks)
        self._tokens = [tokenize(chunk.text) for chunk in self.chunks]
        document_frequency: dict[str, int] = {}
        for tokens in self._tokens:
            for token in set(tokens):
                document_frequency[token] = document_frequency.get(token, 0) + 1
        count = len(self.chunks)
        self._idf = {
            token: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }
        self._avgdl = sum(map(len, self._tokens)) / count if count else 0.0

    def search(self, query: str, limit: int = 20) -> list[RetrievalResult]:
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return []
        scored: list[RetrievalResult] = []
        for chunk, tokens in zip(self.chunks, self._tokens, strict=True):
            frequencies = {token: tokens.count(token) for token in set(query_tokens)}
            score = 0.0
            for token, frequency in frequencies.items():
                if not frequency:
                    continue
                idf = self._idf.get(token, 0.0)
                denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / (self._avgdl or 1))
                score += idf * frequency * 2.5 / denominator
            if score > 0:
                scored.append(RetrievalResult(chunk, score, keyword_score=score))
        return sorted(scored, key=lambda item: (-item.score, item.chunk.position))[:limit]

    def save(self) -> None:
        if not self.path:
            return
        target = Path(self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "chunks": [
                        {
                            "chunk_id": c.chunk_id,
                            "document_id": c.document_id,
                            "filename": c.filename,
                            "text": c.text,
                            "page": c.page,
                            "section": c.section,
                            "position": c.position,
                        }
                        for c in self.chunks
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> None:
        if not self.path or not Path(self.path).exists():
            return
        raw = json.loads(Path(self.path).read_text(encoding="utf-8"))
        self.build([Chunk(**item) for item in raw.get("chunks", [])])
