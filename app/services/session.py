from __future__ import annotations

import uuid


class SessionService:
    def __init__(self, catalog, settings):
        self.catalog = catalog
        self.max_turns = max(1, settings.session_max_turns)
        self.max_chars = max(100, settings.session_max_chars)
        self.max_message_chars = max(100, settings.session_message_max_chars)

    def create_id(self) -> str:
        return str(uuid.uuid4())

    def history(self, session_id: str | None) -> list[dict]:
        if not session_id:
            return []
        messages = self.catalog.list_messages(session_id)
        messages = messages[-self.max_turns * 2 :]
        kept: list[dict] = []
        total = 0
        for message in reversed(messages):
            content = message["content"][: self.max_message_chars]
            if total + len(content) > self.max_chars:
                break
            kept.append({"role": message["role"], "content": content})
            total += len(content)
        return list(reversed(kept))

    def append(self, session_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("unsupported session role")
        self.catalog.append_message(
            session_id,
            role,
            content[: self.max_message_chars],
        )

    def delete(self, session_id: str) -> bool:
        return self.catalog.delete_session(session_id)
