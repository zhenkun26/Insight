from __future__ import annotations

from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import InMemoryVectorStore


class FakeEmbedding:
    def embed(self, text: str) -> list[float]:
        return [float(text.lower().count("台风")), float(text.lower().count("暴雨")), 1.0]


def chunks():
    return [
        Chunk(
            "a",
            "doc-a",
            "warning.md",
            "台风预警信号分为蓝色、黄色、橙色和红色。",
            section="预警",
            position=0,
        ),
        Chunk(
            "b", "doc-b", "rain.txt", "暴雨预警关注降水量和影响范围。", section="降水", position=1
        ),
    ]


def test_bm25_returns_keyword_match():
    index = BM25Index()
    index.build(chunks())
    results = index.search("台风预警")
    assert results[0].chunk.chunk_id == "a"
    assert results[0].keyword_score > 0


def test_hybrid_fuses_and_deduplicates():
    index = BM25Index()
    index.build(chunks())
    vectors = InMemoryVectorStore()
    embeddings = FakeEmbedding()
    vectors.upsert(chunks(), [embeddings.embed(item.text) for item in chunks()])
    retriever = HybridRetriever(index, embeddings, vectors, top_k=2, score_threshold=0.001)
    results = retriever.search("台风")
    assert results[0].chunk.chunk_id == "a"
    assert len({item.chunk.chunk_id for item in results}) == len(results)
    assert retriever.last_status["vector"] == "ok"


def test_hybrid_falls_back_when_vector_fails():
    class BrokenVector:
        def search(self, *_args):
            raise RuntimeError("offline")

    index = BM25Index()
    index.build(chunks())
    retriever = HybridRetriever(index, FakeEmbedding(), BrokenVector(), score_threshold=0.001)
    assert retriever.search("台风")
    assert retriever.last_status["vector"].startswith("fallback:")
