from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str, llm_model: str, embedding_model: str, timeout: float = 60):
        self.base_url = base_url.rstrip("/")
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.timeout = timeout

    def embed(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        vector = payload.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise ValueError("Ollama returned an invalid embedding")
        return [float(value) for value in vector]

    def generate(self, prompt: str, system: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.llm_model, "system": system, "prompt": prompt, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        answer = payload.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Ollama returned an empty answer")
        return answer.strip()

    def stream_generate(self, prompt: str, system: str) -> Iterator[str]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json={"model": self.llm_model, "system": system, "prompt": prompt, "stream": True},
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    payload: dict[str, Any] = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError("Ollama returned an invalid stream event") from exc
                fragment = payload.get("response")
                if fragment is not None and not isinstance(fragment, str):
                    raise ValueError("Ollama returned an invalid stream fragment")
                if fragment:
                    yield fragment
                if payload.get("done") is True:
                    break

    def health(self) -> str:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            response.raise_for_status()
            return "ok"
        except Exception as exc:
            return f"unavailable:{exc.__class__.__name__}"
