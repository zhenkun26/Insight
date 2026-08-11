from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import Settings
from app.ingestion.chunker import chunk_pages, stable_chunk_id, stable_document_id
from app.ingestion.parsers import parse_document
from app.models.domain import Chunk
from app.services.catalog import DocumentCatalog


class IngestionService:
    def __init__(self, catalog: DocumentCatalog, settings: Settings):
        self.catalog = catalog
        self.settings = settings
        self.settings.ensure_directories()

    def ingest(self, filename: str, data: bytes, index_callback=None) -> dict:
        content_hash = self.hash_bytes(data)
        existing = self.catalog.find_by_hash(content_hash)
        if existing:
            return {
                **existing,
                "duplicate": True,
                "chunk_count": len(self.catalog.get_chunks(existing["document_id"])),
            }
        document_id = stable_document_id(data)
        pages = parse_document(filename, data)
        drafts = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
        chunks = [
            Chunk(
                stable_chunk_id(document_id, draft.position, draft.text),
                document_id,
                filename,
                draft.text,
                draft.page,
                draft.section,
                draft.position,
            )
            for draft in drafts
        ]
        self.catalog.upsert_document(
            document_id,
            filename,
            content_hash,
            len(data),
            "processing",
            index_version=self.settings.index_version,
            embedding_model=self.settings.embedding_model,
        )
        self.catalog.replace_chunks(document_id, chunks)
        Path(self.settings.upload_dir, f"{document_id}{Path(filename).suffix.lower()}").write_bytes(
            data
        )
        try:
            if index_callback:
                index_callback(chunks)
            self.catalog.set_status(document_id, "indexed")
        except Exception:
            self.catalog.set_status(document_id, "index_failed")
            raise
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "indexed",
            "chunk_count": len(chunks),
            "duplicate": False,
        }

    def delete(self, document_id: str, delete_callback=None) -> bool:
        if delete_callback:
            delete_callback(document_id)
        return self.catalog.delete_document(document_id)

    def reindex(self, index_callback=None) -> dict:
        chunks = self.catalog.get_chunks()
        if index_callback:
            index_callback(chunks)
        for document in self.catalog.list_documents():
            self.catalog.set_index_metadata(
                document["document_id"],
                self.settings.index_version,
                self.settings.embedding_model,
            )
        return {
            "documents": len(self.catalog.list_documents()),
            "chunks": len(chunks),
            "status": "indexed",
        }

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
