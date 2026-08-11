from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.models.domain import RetrievalResult, Source

REFUSAL_ANSWER = "当前知识库中没有足够信息，无法可靠回答该问题。"


class LanguageModel(Protocol):
    def generate(self, prompt: str, system: str) -> str: ...


@dataclass
class ChatResult:
    query: str
    answer: str
    sources: list[Source]
    retrieval_results: list[RetrievalResult]
    latency_ms: float
    status: str = "ok"


def build_context(results: Sequence[RetrievalResult]) -> str:
    return "\n\n".join(
        f"[{index}] {result.chunk.filename} | chunk={result.chunk.chunk_id} | page={result.chunk.page or '-'} | section={result.chunk.section or '-'}\n{result.chunk.text}"
        for index, result in enumerate(results, 1)
    )


class QuestionAnsweringService:
    def __init__(self, retriever, llm: LanguageModel, score_threshold: float = 0.01):
        self.retriever = retriever
        self.llm = llm
        self.score_threshold = score_threshold

    def answer(self, query: str) -> ChatResult:
        started = time.perf_counter()
        normalized_query = " ".join(query.split())[:2000]
        results = self.retriever.search(normalized_query)
        reliable = [result for result in results if result.score >= self.score_threshold]
        if not reliable:
            return ChatResult(
                query,
                REFUSAL_ANSWER,
                [],
                results,
                (time.perf_counter() - started) * 1000,
                "refused",
            )
        system = "你是洞察者 Insight 的本地知识库助手。只能根据 CONTEXT 回答。若 CONTEXT 没有依据，必须回答当前知识库中没有足够信息。回答末尾必须列出使用的来源编号。不要补充常识或猜测。"
        prompt = f"CONTEXT:\n{build_context(reliable)}\n\nQUESTION:\n{normalized_query}\n\n请用中文简洁回答，并使用 [1] 这样的来源编号。"
        try:
            answer = self.llm.generate(prompt, system)
        except Exception as exc:
            return ChatResult(
                query,
                "本地模型服务暂时不可用，无法生成回答。",
                [],
                reliable,
                (time.perf_counter() - started) * 1000,
                f"llm_error:{exc.__class__.__name__}",
            )
        sources = [result.chunk.source for result in reliable]
        return ChatResult(query, answer, sources, reliable, (time.perf_counter() - started) * 1000)
