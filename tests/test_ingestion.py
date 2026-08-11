from __future__ import annotations

from app.ingestion.chunker import chunk_pages, stable_chunk_id, stable_document_id
from app.ingestion.parsers import ParsedPage, parse_document
from app.models.domain import Chunk
from app.services.catalog import DocumentCatalog


def test_parse_text_and_clean_whitespace():
    pages = parse_document("guide.txt", "  第一行  \n\n\n 第二行\t".encode())
    assert pages[0].text == "第一行\n\n第二行"


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
