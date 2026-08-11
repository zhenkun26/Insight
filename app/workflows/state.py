from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StageEvent:
    name: str
    status: str
    latency_ms: float
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 3),
            "detail": self.detail,
        }


@dataclass
class WorkflowState:
    query: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: list[dict[str, str]] = field(default_factory=list)
    events: list[StageEvent] = field(default_factory=list)
    retrieval_status: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def stage(self, name: str):
        started = time.perf_counter()

        class Stage:
            def __enter__(_self):
                return _self

            def __exit__(_self, exc_type, _value, _traceback):
                status = "ok" if exc_type is None else "error"
                self.events.append(StageEvent(name, status, (time.perf_counter() - started) * 1000))
                return False

        return Stage()
