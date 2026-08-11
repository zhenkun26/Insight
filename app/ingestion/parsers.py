from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}


@dataclass
class ParsedPage:
    text: str
    page: int | None = None


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _parse_pdf(data: bytes) -> list[ParsedPage]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF parsing requires the optional pypdf dependency") from exc
    import io

    reader = PdfReader(io.BytesIO(data))
    return [
        ParsedPage(clean_text(page.extract_text() or ""), index + 1)
        for index, page in enumerate(reader.pages)
    ]


def parse_document(filename: str, data: bytes) -> list[ParsedPage]:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {extension or 'unknown'}")
    if extension == ".pdf":
        return _parse_pdf(data)
    return [ParsedPage(clean_text(data.decode("utf-8-sig")), None)]
