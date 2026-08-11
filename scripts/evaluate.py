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
from app.services.ollama import OllamaClient
from app.services.rerank import OllamaReranker, SimpleKeywordReranker

RERANKER_MODES = {"disabled", "keyword", "ollama"}
TIMING_KEYS = ("keyword_ms", "vector_ms", "fusion_ms", "rerank_ms", "total_ms")


def build_retriever(
    sample_dir: Path,
    *,
    top_k: int = 5,
    reranker_mode: str = "disabled",
    reranker_model: str = "",
    ollama_base_url: str = "http://localhost:11434",
    request_timeout_seconds: float = 60,
) -> HybridRetriever:
    if reranker_mode not in RERANKER_MODES:
        raise ValueError(f"reranker mode must be one of: {', '.join(sorted(RERANKER_MODES))}")
    if top_k < 1:
        raise ValueError("top_k must be greater than zero")
    if request_timeout_seconds <= 0:
        raise ValueError("request timeout must be greater than zero")

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
    reranker = None
    if reranker_mode == "keyword":
        reranker = SimpleKeywordReranker()
    elif reranker_mode == "ollama":
        if not reranker_model.strip():
            raise ValueError("ollama reranker mode requires --reranker-model or RERANKER_MODEL")
        client = OllamaClient(
            ollama_base_url,
            os.getenv("LLM_MODEL", "llama3.2:3b"),
            os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            request_timeout_seconds,
        )
        reranker = OllamaReranker(client, reranker_model)
    return HybridRetriever(
        index,
        top_k=top_k,
        candidate_k=max(20, top_k),
        score_threshold=0.001,
        reranker=reranker,
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
    reranker_mode: str = "disabled",
    reranker_model: str = "",
    ollama_base_url: str = "http://localhost:11434",
    request_timeout_seconds: float = 60,
) -> dict:
    retriever = build_retriever(
        sample_dir,
        top_k=top_k,
        reranker_mode=reranker_mode,
        reranker_model=reranker_model,
        ollama_base_url=ollama_base_url,
        request_timeout_seconds=request_timeout_seconds,
    )
    questions = json.loads(question_file.read_text(encoding="utf-8"))
    hits = 0
    refusal_hits = 0
    refusal_count = 0
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
                "result_count": len(results),
            }
        )
    count = len(questions) or 1
    return {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "profile": reranker_mode,
        "models": {
            "llm": os.getenv("LLM_MODEL", "not_used"),
            "embedding": os.getenv("EMBEDDING_MODEL", "not_used"),
            "reranker": reranker_model or "not_used",
        },
        "parameters": {
            "top_k": top_k,
            "reranker_mode": reranker_mode,
            "reranker_model": reranker_model or None,
            "ollama_base_url": ollama_base_url if reranker_mode == "ollama" else None,
            "request_timeout_seconds": request_timeout_seconds,
            "retriever": (
                "bm25-only local baseline"
                if reranker_mode == "disabled"
                else f"bm25+{reranker_mode}"
            ),
        },
        "dataset": str(question_file),
        "count": len(questions),
        "hit_rate": round(hits / count, 4),
        "mrr": round(sum(reciprocal_ranks) / count, 4),
        "refusal_accuracy": round(refusal_hits / refusal_count, 4) if refusal_count else None,
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Insight retrieval on the bundled demo corpus"
    )
    parser.add_argument("--samples", type=Path, default=Path("data/sample_docs"))
    parser.add_argument("--questions", type=Path, default=Path("data/eval_questions.json"))
    parser.add_argument("--top-k", type=_positive_int, default=5)
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(
            args.samples,
            args.questions,
            args.top_k,
            reranker_mode=args.reranker_mode,
            reranker_model=args.reranker_model,
            ollama_base_url=args.ollama_base_url,
            request_timeout_seconds=args.request_timeout_seconds,
        )
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
