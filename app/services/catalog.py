from __future__ import annotations

import json
import sqlite3
import uuid
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
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
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
                    source TEXT,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    description TEXT,
                    parser_version TEXT NOT NULL DEFAULT '1',
                    index_version TEXT NOT NULL DEFAULT '1',
                    embedding_model TEXT,
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
                    position INTEGER NOT NULL,
                    index_version TEXT NOT NULL DEFAULT '1'
                );
                CREATE TABLE IF NOT EXISTS index_jobs (
                    job_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    processed_chunks INTEGER NOT NULL DEFAULT 0,
                    total_chunks INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    retryable INTEGER NOT NULL DEFAULT 0,
                    parent_job_id TEXT,
                    trace_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS session_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            self._ensure_column(connection, "documents", "source", "TEXT")
            self._ensure_column(connection, "documents", "tags_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "documents", "description", "TEXT")
            self._ensure_column(
                connection, "documents", "parser_version", "TEXT NOT NULL DEFAULT '1'"
            )
            self._ensure_column(
                connection, "documents", "index_version", "TEXT NOT NULL DEFAULT '1'"
            )
            self._ensure_column(connection, "documents", "embedding_model", "TEXT")
            self._ensure_column(connection, "chunks", "index_version", "TEXT NOT NULL DEFAULT '1'")
            connection.commit()

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection, table: str, name: str, definition: str
    ) -> None:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if name not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def find_by_hash(self, content_hash: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE content_hash = ?", (content_hash,)
            ).fetchone()
        return self._document_dict(row) if row else None

    def upsert_document(
        self,
        document_id: str,
        filename: str,
        content_hash: str,
        size_bytes: int,
        status: str,
        *,
        source: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
        parser_version: str = "1",
        index_version: str = "1",
        embedding_model: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO documents(document_id, filename, content_hash, size_bytes, status,
                   source, tags_json, description, parser_version, index_version, embedding_model,
                   created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(document_id) DO UPDATE SET filename=excluded.filename,
                   status=excluded.status, source=COALESCE(excluded.source, documents.source),
                   tags_json=excluded.tags_json, description=COALESCE(excluded.description, documents.description),
                   parser_version=excluded.parser_version, index_version=excluded.index_version,
                   embedding_model=excluded.embedding_model, updated_at=excluded.updated_at""",
                (
                    document_id,
                    filename,
                    content_hash,
                    size_bytes,
                    status,
                    source,
                    json.dumps(tags or [], ensure_ascii=False),
                    description,
                    parser_version,
                    index_version,
                    embedding_model,
                    now,
                    now,
                ),
            )
            connection.commit()

    def replace_chunks(self, document_id: str, chunks: Iterable[Chunk]) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                "INSERT INTO chunks(chunk_id, document_id, filename, text, page, section, position, index_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        c.chunk_id,
                        c.document_id,
                        c.filename,
                        c.text,
                        c.page,
                        c.section,
                        c.position,
                        self._document_index_version(connection, document_id),
                    )
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

    def set_index_metadata(
        self, document_id: str, index_version: str, embedding_model: str
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """UPDATE documents SET index_version = ?, embedding_model = ?,
                   status = 'indexed', updated_at = ? WHERE document_id = ?""",
                (index_version, embedding_model, datetime.now(UTC).isoformat(), document_id),
            )
            connection.commit()

    def list_documents(
        self,
        *,
        source: str | None = None,
        tag: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        args: list[str] = []
        if source:
            clauses.append("source = ?")
            args.append(source)
        if status:
            clauses.append("status = ?")
            args.append(status)
        if tag:
            clauses.append("EXISTS (SELECT 1 FROM json_each(tags_json) WHERE value = ?)")
            args.append(tag)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM documents{where} ORDER BY created_at DESC", args
            ).fetchall()
        return [self._document_dict(row) for row in rows]

    def get_document(self, document_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
        return self._document_dict(row) if row else None

    @staticmethod
    def _document_dict(row: sqlite3.Row) -> dict:
        item = dict(row)
        try:
            item["tags"] = json.loads(item.pop("tags_json", "[]"))
        except json.JSONDecodeError:
            item["tags"] = []
        return item

    @staticmethod
    def _document_index_version(connection: sqlite3.Connection, document_id: str) -> str:
        row = connection.execute(
            "SELECT index_version FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
        return row[0] if row else "1"

    def get_chunks(self, document_id: str | None = None) -> list[Chunk]:
        query = """SELECT c.*, d.source AS document_source, d.tags_json
                   FROM chunks c JOIN documents d ON d.document_id = c.document_id"""
        args: tuple = ()
        if document_id:
            query += " WHERE c.document_id = ?"
            args = (document_id,)
        query += " ORDER BY c.document_id, c.position"
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
                row["document_source"],
                self._parse_tags(row["tags_json"]),
            )
            for row in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        with closing(self._connect()) as connection:
            result = connection.execute(
                "DELETE FROM documents WHERE document_id = ?", (document_id,)
            )
            connection.commit()
        return result.rowcount > 0

    @staticmethod
    def _parse_tags(value: str | None) -> list[str]:
        try:
            parsed = json.loads(value or "[]")
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []

    def update_document_metadata(
        self,
        document_id: str,
        *,
        source: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> dict | None:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """UPDATE documents SET source = ?, tags_json = ?, description = ?, updated_at = ?
                   WHERE document_id = ?""",
                (source, json.dumps(tags or [], ensure_ascii=False), description, now, document_id),
            )
            connection.commit()
        return self.get_document(document_id)

    def allowed_chunk_ids(
        self,
        *,
        document_ids: list[str] | None = None,
        source: str | None = None,
        tag: str | None = None,
        only_indexed: bool = False,
    ) -> set[str] | None:
        clauses: list[str] = []
        args: list[str] = []
        if document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            clauses.append(f"c.document_id IN ({placeholders})")
            args.extend(document_ids)
        if source:
            clauses.append("d.source = ?")
            args.append(source)
        if tag:
            clauses.append("EXISTS (SELECT 1 FROM json_each(d.tags_json) WHERE value = ?)")
            args.append(tag)
        if only_indexed:
            clauses.append("d.status = 'indexed'")
        if not clauses:
            return None
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT c.chunk_id FROM chunks c JOIN documents d ON d.document_id = c.document_id WHERE {' AND '.join(clauses)}",
                args,
            ).fetchall()
        return {row[0] for row in rows}

    def mark_reindex_required(self, index_version: str, embedding_model: str) -> int:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            result = connection.execute(
                """UPDATE documents SET status = 'reindex_required', updated_at = ?
                   WHERE status = 'indexed' AND (index_version != ? OR COALESCE(embedding_model, '') != ?)""",
                (now, index_version, embedding_model),
            )
            connection.commit()
        return result.rowcount

    def create_job(
        self,
        operation: str,
        document_id: str | None = None,
        *,
        total_chunks: int = 0,
        trace_id: str | None = None,
        parent_job_id: str | None = None,
    ) -> dict:
        job_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO index_jobs(job_id, document_id, operation, status, total_chunks,
                   parent_job_id, trace_id, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?)""",
                (job_id, document_id, operation, total_chunks, parent_job_id, trace_id, now, now),
            )
            connection.commit()
        return self.get_job(job_id) or {}

    def update_job(self, job_id: str, **fields) -> dict | None:
        allowed = {
            "document_id",
            "status",
            "processed_chunks",
            "total_chunks",
            "error",
            "retryable",
            "started_at",
            "finished_at",
            "trace_id",
            "parent_job_id",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return self.get_job(job_id)
        updates["updated_at"] = datetime.now(UTC).isoformat()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = [int(value) if isinstance(value, bool) else value for value in updates.values()]
        values.append(job_id)
        with closing(self._connect()) as connection:
            connection.execute(f"UPDATE index_jobs SET {assignments} WHERE job_id = ?", values)
            connection.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM index_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["retryable"] = bool(item["retryable"])
        return item

    def recover_running_jobs(self) -> int:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            result = connection.execute(
                """UPDATE index_jobs SET status = 'failed', error = 'process_restarted',
                   retryable = 1, updated_at = ?, finished_at = ? WHERE status = 'running'""",
                (now, now),
            )
            connection.commit()
        return result.rowcount

    def ensure_session(self, session_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions(session_id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id)
            )
            connection.commit()

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.ensure_session(session_id)
        with closing(self._connect()) as connection:
            connection.execute(
                "INSERT INTO session_messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.now(UTC).isoformat()),
            )
            connection.commit()

    def list_messages(self, session_id: str) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT role, content, created_at FROM session_messages WHERE session_id = ? ORDER BY message_id",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        with closing(self._connect()) as connection:
            result = connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            connection.commit()
        return result.rowcount > 0
