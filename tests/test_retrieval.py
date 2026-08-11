from __future__ import annotations

from app.models.domain import Chunk, RetrievalResult
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import InMemoryVectorStore
from app.services.rerank import OllamaReranker, parse_rerank_score


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


def test_ollama_reranker_scores_and_orders_candidates():
    class Scorer:
        def __init__(self):
            self.models = []

        def generate(self, prompt, _system, model=None):
            self.models.append(model)
            return "0.9" if "台风" in prompt else "0.1"

    scorer = Scorer()
    results = [RetrievalResult(chunks()[1], 0.8), RetrievalResult(chunks()[0], 0.7)]
    ranked = OllamaReranker(scorer, "rerank-model").rerank("台风", results)
    assert ranked[0].chunk.chunk_id == "a"
    assert ranked[0].rerank_score == 0.9
    assert scorer.models == ["rerank-model", "rerank-model"]


def test_ollama_reranker_failure_does_not_partially_mutate_results():
    class BrokenScorer:
        calls = 0

        def generate(self, _prompt, _system, model=None):
            self.calls += 1
            return "0.8" if self.calls == 1 else "not-a-score"

    results = [RetrievalResult(chunks()[0], 0.4), RetrievalResult(chunks()[1], 0.3)]
    scorer = BrokenScorer()
    try:
        OllamaReranker(scorer, "rerank-model").rerank("台风", results)
    except ValueError as exc:
        assert "single number" in str(exc)
    else:
        raise AssertionError("invalid model score must fail")
    assert [item.score for item in results] == [0.4, 0.3]
    assert [item.rerank_score for item in results] == [None, None]


def test_hybrid_rerank_failure_keeps_fused_order_and_status():
    class InvalidScorer:
        def generate(self, *_args, **_kwargs):
            return "explanation: irrelevant"

    index = BM25Index()
    index.build(chunks())
    retriever = HybridRetriever(
        index,
        top_k=2,
        score_threshold=0.001,
        reranker=OllamaReranker(InvalidScorer(), "rerank-model"),
    )
    results = retriever.search("台风")
    assert results
    assert retriever.last_status["rerank"].startswith("fallback:")
    assert all(item.rerank_score is None for item in results)


def test_rerank_score_parser_rejects_non_numeric_output():
    assert parse_rerank_score("0") == 0.0
    assert parse_rerank_score("1.0") == 1.0
    for invalid in ("0.5 explanation", "-0.1", "1.1", "json: 0.5"):
        try:
            parse_rerank_score(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid score accepted: {invalid}")
