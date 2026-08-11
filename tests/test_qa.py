from __future__ import annotations

from app.models.domain import Chunk, RetrievalResult
from app.services.qa import REFUSAL_ANSWER, QuestionAnsweringService


class FakeRetriever:
    def __init__(self, results):
        self.results = results

    def search(self, _query):
        return self.results


class FakeLLM:
    def __init__(self, answer="依据 [1]，台风预警分为四级。"):
        self.answer = answer
        self.called = False

    def generate(self, _prompt, _system):
        self.called = True
        return self.answer


def test_grounded_answer_contains_source():
    chunk = Chunk("chunk-1", "doc-1", "warning.md", "台风预警分为四级。", page=3, section="预警")
    llm = FakeLLM()
    result = QuestionAnsweringService(FakeRetriever([RetrievalResult(chunk, 0.2)]), llm).answer(
        "台风预警分几级？"
    )
    assert result.status == "ok"
    assert result.sources[0].filename == "warning.md"
    assert result.sources[0].page == 3
    assert llm.called


def test_no_context_refuses_without_calling_llm():
    llm = FakeLLM()
    result = QuestionAnsweringService(FakeRetriever([]), llm).answer("不存在的问题")
    assert result.answer == REFUSAL_ANSWER
    assert result.status == "refused"
    assert not llm.called
