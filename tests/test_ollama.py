from __future__ import annotations

import httpx

from app.services.ollama import OllamaClient


def test_ollama_generate_uses_override_model_without_changing_default(monkeypatch):
    calls = []

    def fake_post(url, *, json, timeout):
        calls.append((url, json, timeout))
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"response": "0.8"},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OllamaClient("http://ollama:11434", "answer-model", "embed-model", 12)
    assert client.generate("prompt", "system") == "0.8"
    assert client.generate("prompt", "system", model="rerank-model") == "0.8"
    assert calls[0][1]["model"] == "answer-model"
    assert calls[1][1]["model"] == "rerank-model"
    assert all(call[2] == 12 for call in calls)
