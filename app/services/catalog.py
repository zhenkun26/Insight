from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.models.domain import Chunk


class DocumentCatalog:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_hash TEXT UNIQUE NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    text TEXT NOT NULL,
                    page INTEGER,
                    section TEXT,
                    position INTEGER NOT NULL
                );
            """)
            connection.commit()

    def find_by_hash(self, content_hash: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE content_hash = ?", (content_hash,)
            ).fetchone()
        return dict(row) if row else None

    def upsert_document(
        self, document_id: str, filename: str, content_hash: str, size_bytes: int, status: str
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO documents(document_id, filename, content_hash, size_bytes, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(document_id) DO UPDATE SET filename=excluded.filename, status=excluded.status, updated_at=excluded.updated_at""",
                (document_id, filename, content_hash, size_bytes, status, now, now),
            )
            connection.commit()

    def replace_chunks(self, document_id: str, chunks: Iterable[Chunk]) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                "INSERT INTO chunks(chunk_id, document_id, filename, text, page, section, position) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (c.chunk_id, c.document_id, c.filename, c.text, c.page, c.section, c.position)
                    for c in chunks
                ],
            )
            connection.commit()

    def set_status(self, document_id: str, status: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE document_id = ?",
                (status, datetime.now(UTC).isoformat(), document_id),
            )
            connection.commit()

    def list_documents(self) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_chunks(self, document_id: str | None = None) -> list[Chunk]:
        query = "SELECT * FROM chunks"
        args: tuple = ()
        if document_id:
            query += " WHERE document_id = ?"
            args = (document_id,)
        query += " ORDER BY document_id, position"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, args).fetchall()
        return [
            Chunk(
                row["chunk_id"],
                row["document_id"],
                row["filename"],
                row["text"],
                row["page"],
                row["section"],
                row["position"],
            )
            for row in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            result = connection.execute(
                "DELETE FROM documents WHERE document_id = ?", (document_id,)
            )
            connection.commit()
        return result.rowcount > 0
