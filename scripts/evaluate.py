from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunker import chunk_pages, stable_chunk_id, stable_document_id
from app.ingestion.parsers import parse_document
from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import InMemoryVectorStore, MilvusVectorStore
from app.services.ollama import OllamaClient
from app.services.rerank import OllamaReranker, SimpleKeywordReranker

RETRIEVAL_MODES = {"bm25", "vector", "hybrid"}
VECTOR_BACKENDS = {"memory", "milvus"}
RERANKER_MODES = {"disabled", "keyword", "ollama"}
TIMING_KEYS = ("keyword_ms", "vector_ms", "fusion_ms", "rerank_ms", "total_ms")
DEFAULT_VECTOR_SCORE_THRESHOLD = 0.7


def _effective_vector_score_threshold(
    retrieval_mode: str, configured: float | None
) -> float | None:
    if retrieval_mode == "bm25":
        return None
    value = (
        configured
        if configured is not None
        else float(os.getenv("VECTOR_SCORE_THRESHOLD", str(DEFAULT_VECTOR_SCORE_THRESHOLD)))
    )
    if not 0 <= value <= 1:
        raise ValueError("vector score threshold must be between zero and one")
    return value


def build_retriever(
    sample_dir: Path,
    *,
    top_k: int = 5,
    retrieval_mode: str = "bm25",
    vector_backend: str = "memory",
    embedding_model: str = "",
    milvus_uri: str = "",
    milvus_collection: str = "insight_eval_chunks",
    reranker_mode: str = "disabled",
    reranker_model: str = "",
    ollama_base_url: str = "http://localhost:11434",
    request_timeout_seconds: float = 60,
    vector_score_threshold: float | None = None,
) -> HybridRetriever:
    if retrieval_mode not in RETRIEVAL_MODES:
        raise ValueError(f"retrieval mode must be one of: {', '.join(sorted(RETRIEVAL_MODES))}")
    if vector_backend not in VECTOR_BACKENDS:
        raise ValueError(f"vector backend must be one of: {', '.join(sorted(VECTOR_BACKENDS))}")
    if reranker_mode not in RERANKER_MODES:
        raise ValueError(f"reranker mode must be one of: {', '.join(sorted(RERANKER_MODES))}")
    if top_k < 1:
        raise ValueError("top_k must be greater than zero")
    if request_timeout_seconds <= 0:
        raise ValueError("request timeout must be greater than zero")
    if vector_score_threshold is not None and not 0 <= vector_score_threshold <= 1:
        raise ValueError("vector score threshold must be between zero and one")

    chunks: list[Chunk] = []
    for path in sorted(sample_dir.iterdir()):
        if path.suffix.lower() not in {".md", ".markdown", ".txt", ".pdf"}:
            continue
        data = path.read_bytes()
        document_id = stable_document_id(data)
        for draft in chunk_pages(parse_document(path.name, data), max_chars=900, overlap=100):
            chunks.append(
                Chunk(
                    stable_chunk_id(document_id, draft.position, draft.text),
                    document_id,
                    path.name,
                    draft.text,
                    draft.page,
                    draft.section,
                    draft.position,
                )
            )
    index = BM25Index()
    index.build(chunks)
    needs_vector = retrieval_mode != "bm25"
    effective_vector_score_threshold = _effective_vector_score_threshold(
        retrieval_mode, vector_score_threshold
    )
    if needs_vector:
        embedding_model = embedding_model.strip() or os.getenv("EMBEDDING_MODEL", "").strip()
        if not embedding_model:
            raise ValueError("vector or hybrid mode requires --embedding-model or EMBEDDING_MODEL")
        if vector_backend == "milvus" and not milvus_uri.strip():
            raise ValueError("milvus vector backend requires --milvus-uri or MILVUS_URI")

    needs_ollama = needs_vector or reranker_mode == "ollama"
    ollama = None
    vector_store = None
    if needs_ollama:
        ollama = OllamaClient(
            ollama_base_url,
            os.getenv("LLM_MODEL", "llama3.2:3b"),
            embedding_model or os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            request_timeout_seconds,
        )
    if needs_vector:
        vector_store = (
            InMemoryVectorStore()
            if vector_backend == "memory"
            else MilvusVectorStore(milvus_uri, milvus_collection)
        )
        vectors = [ollama.embed(chunk.text) for chunk in chunks]
        vector_store.upsert(chunks, vectors)

    reranker = None
    if reranker_mode == "keyword":
        reranker = SimpleKeywordReranker()
    elif reranker_mode == "ollama":
        if not reranker_model.strip():
            raise ValueError("ollama reranker mode requires --reranker-model or RERANKER_MODEL")
        reranker = OllamaReranker(ollama, reranker_model)
    return HybridRetriever(
        index,
        ollama if needs_vector else None,
        vector_store,
        top_k=top_k,
        candidate_k=max(20, top_k),
        score_threshold=0.001,
        reranker=reranker,
        keyword_enabled=retrieval_mode != "vector",
        vector_score_threshold=effective_vector_score_threshold if needs_vector else None,
    )


def _stage_averages(rows: list[dict]) -> dict[str, float | None]:
    averages: dict[str, float | None] = {}
    for key in TIMING_KEYS:
        values = [row["stage_timings_ms"].get(key) for row in rows]
        measured = [float(value) for value in values if value is not None]
        averages[key] = round(sum(measured) / len(measured), 3) if measured else None
    return averages


def evaluate(
    sample_dir: Path,
    question_file: Path,
    top_k: int = 5,
    *,
    retrieval_mode: str = "bm25",
    vector_backend: str = "memory",
    embedding_model: str = "",
    milvus_uri: str = "",
    milvus_collection: str = "insight_eval_chunks",
    reranker_mode: str = "disabled",
    reranker_model: str = "",
    ollama_base_url: str = "http://localhost:11434",
    request_timeout_seconds: float = 60,
    vector_score_threshold: float | None = None,
) -> dict:
    effective_embedding_model = (embedding_model.strip() if retrieval_mode != "bm25" else "") or (
        os.getenv("EMBEDDING_MODEL", "").strip() if retrieval_mode != "bm25" else ""
    )
    effective_vector_threshold = _effective_vector_score_threshold(
        retrieval_mode, vector_score_threshold
    )
    retriever = build_retriever(
        sample_dir,
        top_k=top_k,
        retrieval_mode=retrieval_mode,
        vector_backend=vector_backend,
        embedding_model=effective_embedding_model,
        milvus_uri=milvus_uri,
        milvus_collection=milvus_collection,
        reranker_mode=reranker_mode,
        reranker_model=reranker_model,
        ollama_base_url=ollama_base_url,
        request_timeout_seconds=request_timeout_seconds,
        vector_score_threshold=vector_score_threshold,
    )
    questions = json.loads(question_file.read_text(encoding="utf-8"))
    hits = 0
    refusal_hits = 0
    refusal_count = 0
    refusal_false_positives = 0
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    rows = []
    for item in questions:
        results = retriever.search(item["question"], top_k)
        latency = float(retriever.last_timings["total_ms"] or 0)
        latencies.append(latency)
        expected = [value.lower() for value in item["expected"]]
        should_refuse = bool(item.get("should_refuse"))
        if should_refuse:
            refusal_count += 1
            if not results:
                refusal_hits += 1
            else:
                refusal_false_positives += 1
        matched_rank = None
        if not should_refuse and expected:
            for rank, result in enumerate(results, 1):
                haystack = f"{result.chunk.filename} {result.chunk.text}".lower()
                if all(term in haystack for term in expected):
                    matched_rank = rank
                    break
        if matched_rank:
            hits += 1
            reciprocal_ranks.append(1 / matched_rank)
        else:
            reciprocal_ranks.append(0.0)
        rows.append(
            {
                "question": item["question"],
                "matched_rank": matched_rank,
                "latency_ms": round(latency, 3),
                "stage_status": dict(retriever.last_status),
                "stage_timings_ms": {
                    key: round(value, 3) if value is not None else None
                    for key, value in retriever.last_timings.items()
                },
                "should_refuse": should_refuse,
                "refused": not results,
                "result_count": len(results),
            }
        )
    count = len(questions) or 1
    return {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "profile": reranker_mode,
        "retrieval_mode": retrieval_mode,
        "models": {
            "llm": os.getenv("LLM_MODEL", "not_used"),
            "embedding": effective_embedding_model if retrieval_mode != "bm25" else "not_used",
            "reranker": reranker_model or "not_used",
        },
        "parameters": {
            "top_k": top_k,
            "retrieval_mode": retrieval_mode,
            "vector_backend": vector_backend if retrieval_mode != "bm25" else None,
            "embedding_model": effective_embedding_model if retrieval_mode != "bm25" else None,
            "milvus_uri": milvus_uri
            if retrieval_mode != "bm25" and vector_backend == "milvus"
            else None,
            "milvus_collection": milvus_collection if retrieval_mode != "bm25" else None,
            "reranker_mode": reranker_mode,
            "reranker_model": reranker_model or None,
            "ollama_base_url": ollama_base_url
            if retrieval_mode != "bm25" or reranker_mode == "ollama"
            else None,
            "request_timeout_seconds": request_timeout_seconds,
            "vector_score_threshold": (effective_vector_threshold),
            "retriever": (
                "bm25-only local baseline"
                if retrieval_mode == "bm25" and reranker_mode == "disabled"
                else f"{retrieval_mode}+{reranker_mode}"
            ),
        },
        "dataset": str(question_file),
        "count": len(questions),
        "hit_rate": round(hits / count, 4),
        "mrr": round(sum(reciprocal_ranks) / count, 4),
        "refusal_accuracy": round(refusal_hits / refusal_count, 4) if refusal_count else None,
        "refusal_calibration": {
            "threshold": (effective_vector_threshold),
            "refusal_count": refusal_count,
            "false_positive_answers": refusal_false_positives,
            "false_positive_rate": (
                round(refusal_false_positives / refusal_count, 4) if refusal_count else None
            ),
        },
        "average_latency_ms": round(sum(latencies) / count, 3),
        "average_stage_latency_ms": _stage_averages(rows),
        "rows": rows,
    }


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _score_threshold(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between zero and one")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Insight retrieval on the bundled demo corpus"
    )
    parser.add_argument("--samples", type=Path, default=Path("data/sample_docs"))
    parser.add_argument("--questions", type=Path, default=Path("data/eval_questions.json"))
    parser.add_argument("--top-k", type=_positive_int, default=5)
    parser.add_argument("--retrieval-mode", choices=sorted(RETRIEVAL_MODES), default="bm25")
    parser.add_argument(
        "--vector-backend",
        choices=sorted(VECTOR_BACKENDS),
        default=os.getenv("VECTOR_BACKEND", "memory"),
    )
    parser.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", ""))
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", ""))
    parser.add_argument(
        "--milvus-collection",
        default=os.getenv("MILVUS_COLLECTION", "insight_eval_chunks"),
    )
    parser.add_argument("--reranker-mode", choices=sorted(RERANKER_MODES), default="disabled")
    parser.add_argument("--reranker-model", default=os.getenv("RERANKER_MODEL", ""))
    parser.add_argument(
        "--ollama-base-url", default=os.getenv("LLM_BASE_URL", "http://localhost:11434")
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=_positive_float,
        default=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")),
    )
    parser.add_argument(
        "--vector-score-threshold",
        type=_score_threshold,
        default=float(os.getenv("VECTOR_SCORE_THRESHOLD", str(DEFAULT_VECTOR_SCORE_THRESHOLD))),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(
            args.samples,
            args.questions,
            args.top_k,
            retrieval_mode=args.retrieval_mode,
            vector_backend=args.vector_backend,
            embedding_model=args.embedding_model,
            milvus_uri=args.milvus_uri,
            milvus_collection=args.milvus_collection,
            reranker_mode=args.reranker_mode,
            reranker_model=args.reranker_model,
            ollama_base_url=args.ollama_base_url,
            request_timeout_seconds=args.request_timeout_seconds,
            vector_score_threshold=args.vector_score_threshold,
        )
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
