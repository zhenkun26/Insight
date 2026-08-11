from __future__ import annotations

import json

import pytest

import scripts.evaluate as evaluation
from scripts.evaluate import evaluate


def make_eval_files(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "warning.txt").write_text("台风预警信号分为四级，包含蓝色和红色。", encoding="utf-8")
    questions = tmp_path / "questions.json"
    questions.write_text(
        json.dumps(
            [
                {"question": "台风预警分为几级？", "expected": ["warning.txt", "四级"]},
                {"question": "航空发动机维修周期？", "expected": [], "should_refuse": True},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return samples, questions


def test_default_evaluation_reports_disabled_stages(tmp_path):
    samples, questions = make_eval_files(tmp_path)
    result = evaluate(samples, questions)
    assert result["profile"] == "disabled"
    assert result["count"] == 2
    assert result["rows"][1]["matched_rank"] is None
    assert result["average_stage_latency_ms"]["keyword_ms"] is not None
    assert result["average_stage_latency_ms"]["vector_ms"] is None
    assert result["rows"][0]["stage_status"]["rerank"] == "disabled"
    assert result["parameters"]["vector_score_threshold"] is None
    assert result["refusal_calibration"] == {
        "threshold": None,
        "refusal_count": 1,
        "false_positive_answers": 0,
        "false_positive_rate": 0.0,
    }


def test_keyword_profile_reports_rerank_stage(tmp_path):
    samples, questions = make_eval_files(tmp_path)
    result = evaluate(samples, questions, reranker_mode="keyword")
    assert result["profile"] == "keyword"
    assert result["parameters"]["retriever"] == "bm25+keyword"
    assert result["average_stage_latency_ms"]["rerank_ms"] is not None
    assert result["rows"][0]["stage_status"]["rerank"] == "ok"


def test_ollama_profile_requires_a_model(tmp_path):
    samples, questions = make_eval_files(tmp_path)
    with pytest.raises(ValueError, match="requires"):
        evaluate(samples, questions, reranker_mode="ollama")


def test_vector_profile_uses_memory_backend_and_reports_timings(tmp_path, monkeypatch):
    samples, questions = make_eval_files(tmp_path)

    class FakeOllama:
        def __init__(self, *_args):
            pass

        def embed(self, text):
            return [float(text.count("台风")), float(text.count("暴雨")), 1.0]

    monkeypatch.setattr(evaluation, "OllamaClient", FakeOllama)
    result = evaluate(
        samples,
        questions,
        retrieval_mode="vector",
        vector_backend="memory",
        embedding_model="fake-embedding",
    )
    assert result["retrieval_mode"] == "vector"
    assert result["parameters"]["vector_backend"] == "memory"
    assert result["models"]["embedding"] == "fake-embedding"
    assert result["average_stage_latency_ms"]["keyword_ms"] is None
    assert result["average_stage_latency_ms"]["vector_ms"] is not None
    assert result["rows"][0]["stage_status"]["keyword"] == "disabled"
    assert result["parameters"]["vector_score_threshold"] == 0.7
    assert result["refusal_calibration"]["threshold"] == 0.7
    assert result["refusal_calibration"]["false_positive_answers"] == 1
    assert result["rows"][1]["refused"] is False


def test_vector_threshold_can_be_calibrated_and_validated(tmp_path, monkeypatch):
    samples, questions = make_eval_files(tmp_path)

    class FakeOllama:
        def __init__(self, *_args):
            pass

        def embed(self, text):
            return [float(text.count("台风")), float(text.count("暴雨")), 1.0]

    monkeypatch.setattr(evaluation, "OllamaClient", FakeOllama)
    result = evaluate(
        samples,
        questions,
        retrieval_mode="vector",
        embedding_model="fake-embedding",
        vector_score_threshold=0.8,
    )
    assert result["refusal_calibration"]["threshold"] == 0.8
    assert result["refusal_calibration"]["false_positive_answers"] == 0
    assert result["refusal_calibration"]["false_positive_rate"] == 0.0
    with pytest.raises(ValueError, match="between zero and one"):
        evaluate(
            samples,
            questions,
            retrieval_mode="vector",
            embedding_model="fake-embedding",
            vector_score_threshold=1.1,
        )


def test_vector_profile_requires_embedding_model(tmp_path):
    samples, questions = make_eval_files(tmp_path)
    with pytest.raises(ValueError, match="embedding"):
        evaluate(samples, questions, retrieval_mode="vector", vector_backend="memory")


def test_milvus_profile_requires_uri(tmp_path):
    samples, questions = make_eval_files(tmp_path)
    with pytest.raises(ValueError, match="milvus"):
        evaluate(
            samples,
            questions,
            retrieval_mode="hybrid",
            vector_backend="milvus",
            embedding_model="fake-embedding",
        )
