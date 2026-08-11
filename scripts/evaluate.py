from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunker import chunk_pages, stable_chunk_id, stable_document_id
from app.ingestion.parsers import parse_document
from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever


def build_retriever(sample_dir: Path) -> HybridRetriever:
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
    return HybridRetriever(index, top_k=5, score_threshold=0.001)


def evaluate(sample_dir: Path, question_file: Path, top_k: int = 5) -> dict:
    retriever = build_retriever(sample_dir)
    questions = json.loads(question_file.read_text(encoding="utf-8"))
    hits = 0
    refusal_hits = 0
    refusal_count = 0
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    rows = []
    for item in questions:
        started = time.perf_counter()
        results = retriever.search(item["question"], top_k)
        latency = (time.perf_counter() - started) * 1000
        latencies.append(latency)
        expected = [value.lower() for value in item["expected"]]
        should_refuse = bool(item.get("should_refuse"))
        if should_refuse:
            refusal_count += 1
            if not results:
                refusal_hits += 1
        matched_rank = None
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
                "should_refuse": should_refuse,
                "result_count": len(results),
            }
        )
    count = len(questions) or 1
    return {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "models": {
            "llm": os.getenv("LLM_MODEL", "not_used"),
            "embedding": os.getenv("EMBEDDING_MODEL", "not_used"),
        },
        "parameters": {"top_k": top_k, "retriever": "bm25-only local baseline"},
        "dataset": str(question_file),
        "count": len(questions),
        "hit_rate": round(hits / count, 4),
        "mrr": round(sum(reciprocal_ranks) / count, 4),
        "refusal_accuracy": round(refusal_hits / refusal_count, 4) if refusal_count else None,
        "average_latency_ms": round(sum(latencies) / count, 3),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Insight retrieval on the bundled demo corpus"
    )
    parser.add_argument("--samples", type=Path, default=Path("data/sample_docs"))
    parser.add_argument("--questions", type=Path, default=Path("data/eval_questions.json"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.samples, args.questions, args.top_k)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
