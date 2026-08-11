from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from app.models.domain import RetrievalResult, Source
from app.workflows.state import WorkflowState

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
    trace_id: str | None = None
    stages: list[dict] = field(default_factory=list)
    retrieval_status: dict[str, str] = field(default_factory=dict)


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

    def answer(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
        trace_id: str | None = None,
    ) -> ChatResult:
        started = time.perf_counter()
        state = WorkflowState(query, trace_id or WorkflowState(query).trace_id, history or [])
        with state.stage("query_analysis"):
            normalized_query = " ".join(query.split())[:2000]
        with state.stage("retrieval"):
            results = self.retriever.search(normalized_query)
            state.retrieval_status = dict(getattr(self.retriever, "last_status", {}))
        with state.stage("rerank"):
            pass
        with state.stage("relevance_check"):
            reliable = [result for result in results if result.score >= self.score_threshold]
        if not reliable:
            with state.stage("fallback"):
                pass
            return ChatResult(
                query,
                REFUSAL_ANSWER,
                [],
                results,
                (time.perf_counter() - started) * 1000,
                "refused",
                state.trace_id,
                [event.as_dict() for event in state.events],
                state.retrieval_status,
            )
        system = "你是洞察者 Insight 的本地知识库助手。只能根据 CONTEXT 回答。若 CONTEXT 没有依据，必须回答当前知识库中没有足够信息。回答末尾必须列出使用的来源编号。不要补充常识或猜测。"
        history_text = "\n".join(
            f"{message['role']}: {message['content']}" for message in (history or [])
        )
        prompt = f"HISTORY (not evidence):\n{history_text}\n\nCONTEXT:\n{build_context(reliable)}\n\nQUESTION:\n{normalized_query}\n\n请用中文简洁回答，并使用 [1] 这样的来源编号。"
        try:
            with state.stage("generation"):
                answer = self.llm.generate(prompt, system)
        except Exception as exc:
            return ChatResult(
                query,
                "本地模型服务暂时不可用，无法生成回答。",
                [],
                reliable,
                (time.perf_counter() - started) * 1000,
                f"llm_error:{exc.__class__.__name__}",
                state.trace_id,
                [event.as_dict() for event in state.events],
                state.retrieval_status,
            )
        sources = [result.chunk.source for result in reliable]
        return ChatResult(
            query,
            answer,
            sources,
            reliable,
            (time.perf_counter() - started) * 1000,
            "ok",
            state.trace_id,
            [event.as_dict() for event in state.events],
            state.retrieval_status,
        )
