from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion import ocr, parsers
from app.ingestion.chunker import chunk_pages, stable_chunk_id, stable_document_id
from app.ingestion.parsers import ParsedPage, parse_document
from app.models.domain import Chunk
from app.services.catalog import DocumentCatalog


def test_parse_text_and_clean_whitespace():
    pages = parse_document("guide.txt", "  第一行  \n\n\n 第二行\t".encode())
    assert pages[0].text == "第一行\n\n第二行"


def test_pdf_ocr_is_opt_in_and_preserves_native_pages(monkeypatch):
    monkeypatch.setattr(
        parsers,
        "_extract_pdf_pages",
        lambda _data: [ParsedPage("", page=1), ParsedPage("原生文本", page=2)],
    )
    calls = []

    def fake_ocr(data, page_numbers, **kwargs):
        calls.append((data, page_numbers, kwargs))
        return {1: "扫描文本"}

    monkeypatch.setattr(parsers, "ocr_pdf_pages", fake_ocr)
    default_pages = parse_document("scan.pdf", b"pdf")
    assert [page.text for page in default_pages] == ["", "原生文本"]
    assert calls == []
    pages = parse_document(
        "scan.pdf",
        b"pdf",
        ocr_enabled=True,
        ocr_language="chi_sim+eng",
        ocr_timeout_seconds=9,
    )
    assert [page.text for page in pages] == ["扫描文本", "原生文本"]
    assert calls[0][1] == [1]
    assert calls[0][2]["language"] == "chi_sim+eng"


def test_ocr_missing_tools_has_explicit_error(monkeypatch, tmp_path):
    monkeypatch.setattr(ocr.shutil, "which", lambda _name: None)
    with pytest.raises(ocr.OCRUnavailableError, match="OCR_ENABLED=false"):
        ocr.ocr_pdf_pages(b"pdf", [1], language="eng", timeout_seconds=1, temp_dir=str(tmp_path))


def test_ocr_adapter_returns_text_and_cleans_images(monkeypatch, tmp_path):
    monkeypatch.setattr(ocr.shutil, "which", lambda name: f"/usr/bin/{name}")
    commands = []

    def fake_run(command, **_kwargs):
        commands.append(command)
        if "-png" in command:
            Path(command[-1] + "-1.png").write_bytes(b"image")
            return ocr.subprocess.CompletedProcess(command, 0, "", "")
        return ocr.subprocess.CompletedProcess(command, 0, "识别文本\n", "")

    monkeypatch.setattr(ocr.subprocess, "run", fake_run)
    assert ocr.ocr_pdf_pages(
        b"pdf", [1], language="chi_sim+eng", timeout_seconds=1, temp_dir=str(tmp_path)
    ) == {1: "识别文本"}
    assert commands[1][-2:] == ["-l", "chi_sim+eng"]
    assert list(tmp_path.iterdir()) == []


def test_ocr_timeout_cleans_temporary_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(ocr.shutil, "which", lambda name: name)

    def timeout(*_args, **_kwargs):
        raise ocr.subprocess.TimeoutExpired("tesseract", 1)

    monkeypatch.setattr(ocr.subprocess, "run", timeout)
    with pytest.raises(ocr.OCRTimeoutError):
        ocr.ocr_pdf_pages(b"pdf", [1], language="eng", timeout_seconds=1, temp_dir=str(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_ocr_settings_reject_non_positive_timeout():
    from app.core.config import Settings

    with pytest.raises(ValueError, match="OCR_TIMEOUT_SECONDS"):
        Settings(ocr_enabled=True, ocr_timeout_seconds=0)


def test_chunk_preserves_heading_and_page():
    pages = [ParsedPage("# 预警信号\n\n红色预警需要及时转移。" * 10, page=2)]
    chunks = chunk_pages(pages, max_chars=40, overlap=5)
    assert chunks
    assert all(len(item.text) <= 40 for item in chunks)
    assert all(item.page == 2 for item in chunks)
    assert chunks[0].section == "预警信号"


def test_stable_ids_and_catalog_lifecycle(tmp_path):
    data = b"weather document"
    document_id = stable_document_id(data)
    chunk_id = stable_chunk_id(document_id, 0, "text")
    catalog = DocumentCatalog(str(tmp_path / "catalog.db"))
    catalog.upsert_document(document_id, "guide.txt", document_id, len(data), "indexed")
    catalog.replace_chunks(
        document_id, [Chunk(chunk_id, document_id, "guide.txt", "text", 1, "intro", 0)]
    )
    assert catalog.find_by_hash(document_id)["document_id"] == document_id
    assert catalog.get_chunks(document_id)[0].source.page == 1
    assert catalog.delete_document(document_id)
    assert catalog.get_document(document_id) is None
