from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.ocr import ocr_pdf_pages

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


def _extract_pdf_pages(data: bytes) -> list[ParsedPage]:
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


def _parse_pdf(
    data: bytes,
    *,
    ocr_enabled: bool = False,
    ocr_language: str = "eng",
    ocr_timeout_seconds: float = 30,
    ocr_temp_dir: str | None = None,
) -> list[ParsedPage]:
    pages = _extract_pdf_pages(data)
    if not ocr_enabled:
        return pages
    empty_pages = [page.page for page in pages if page.page is not None and not page.text]
    ocr_text = ocr_pdf_pages(
        data,
        empty_pages,
        language=ocr_language,
        timeout_seconds=ocr_timeout_seconds,
        temp_dir=ocr_temp_dir,
    )
    parsed_pages = []
    for page in pages:
        replacement = ocr_text.get(page.page) if page.page is not None else None
        parsed_pages.append(ParsedPage(replacement or page.text, page.page))
    return parsed_pages


def parse_document(
    filename: str,
    data: bytes,
    *,
    ocr_enabled: bool = False,
    ocr_language: str = "eng",
    ocr_timeout_seconds: float = 30,
    ocr_temp_dir: str | None = None,
) -> list[ParsedPage]:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {extension or 'unknown'}")
    if extension == ".pdf":
        return _parse_pdf(
            data,
            ocr_enabled=ocr_enabled,
            ocr_language=ocr_language,
            ocr_timeout_seconds=ocr_timeout_seconds,
            ocr_temp_dir=ocr_temp_dir,
        )
    return [ParsedPage(clean_text(data.decode("utf-8-sig")), None)]
