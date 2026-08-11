from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.ingestion.parsers import ParsedPage


@dataclass
class ChunkDraft:
    text: str
    page: int | None
    section: str | None
    position: int


def _sections(text: str) -> list[tuple[str | None, str]]:
    current: str | None = None
    buffer: list[str] = []
    output: list[tuple[str | None, str]] = []
    heading = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
    for line in text.splitlines():
        match = heading.match(line)
        if match:
            if buffer:
                output.append((current, "\n".join(buffer).strip()))
                buffer = []
            current = match.group(2).strip()
        elif line.strip():
            buffer.append(line.strip())
    if buffer:
        output.append((current, "\n".join(buffer).strip()))
    return output


def chunk_pages(
    pages: list[ParsedPage], max_chars: int = 900, overlap: int = 120
) -> list[ChunkDraft]:
    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("max_chars must be positive and overlap must be smaller than max_chars")
    output: list[ChunkDraft] = []
    position = 0
    for page in pages:
        for section, text in _sections(page.text):
            start = 0
            while start < len(text):
                end = min(start + max_chars, len(text))
                if end < len(text):
                    boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
                    if boundary > start + max_chars // 2:
                        end = boundary
                value = text[start:end].strip()
                if value:
                    output.append(ChunkDraft(value, page.page, section, position))
                    position += 1
                if end >= len(text):
                    break
                start = max(0, end - overlap)
    return output


def stable_document_id(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:20]


def stable_chunk_id(document_id: str, position: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{position}:{text}".encode()).hexdigest()[:16]
    return f"{document_id}-{digest}"
