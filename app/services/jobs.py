from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from app.ingestion.chunker import stable_document_id

logger = logging.getLogger("insight.jobs")


class IndexJobService:
    """Small local job runner with SQLite-backed status and bounded workers."""

    def __init__(self, catalog, ingestion, index_callback, settings):
        self.catalog = catalog
        self.ingestion = ingestion
        self.index_callback = index_callback
        self.settings = settings
        self.executor = ThreadPoolExecutor(max_workers=max(1, settings.job_workers))
        self._lock = threading.Lock()
        self.catalog.recover_running_jobs()

    def submit_upload(self, filename: str, data: bytes, trace_id: str | None = None) -> dict:
        document_id = stable_document_id(data)
        existing = self.catalog.find_by_hash(self.ingestion.hash_bytes(data))
        job = self.catalog.create_job(
            "upload",
            document_id if self.catalog.get_document(document_id) else None,
            trace_id=trace_id,
        )
        if existing:
            self.catalog.update_job(
                job["job_id"],
                status="succeeded",
                processed_chunks=len(self.catalog.get_chunks(existing["document_id"])),
                total_chunks=len(self.catalog.get_chunks(existing["document_id"])),
                finished_at=self._now(),
            )
            return self.catalog.get_job(job["job_id"]) or job
        self.executor.submit(self._run_upload, job["job_id"], filename, data)
        return job

    def _run_upload(self, job_id: str, filename: str, data: bytes) -> None:
        self.catalog.update_job(job_id, status="running", started_at=self._now())
        document_id = stable_document_id(data)
        try:
            result = self.ingestion.ingest(filename, data, self._callback(job_id))
            self.catalog.update_job(
                job_id,
                status="succeeded",
                document_id=result.get("document_id", document_id),
                processed_chunks=result.get("chunk_count", 0),
                total_chunks=result.get("chunk_count", 0),
                finished_at=self._now(),
            )
        except Exception as exc:
            logger.exception("index job failed", extra={"job_id": job_id})
            self.catalog.update_job(
                job_id,
                status="failed",
                error=exc.__class__.__name__,
                retryable=True,
                finished_at=self._now(),
            )

    def submit_reindex(self, trace_id: str | None = None) -> dict:
        job = self.catalog.create_job("reindex", trace_id=trace_id)
        self.executor.submit(self._run_reindex, job["job_id"])
        return job

    def _run_reindex(self, job_id: str) -> None:
        self.catalog.update_job(job_id, status="running", started_at=self._now())
        try:
            result = self.ingestion.reindex(self._callback(job_id))
            self.catalog.update_job(
                job_id,
                status="succeeded",
                processed_chunks=result.get("chunks", 0),
                total_chunks=result.get("chunks", 0),
                finished_at=self._now(),
            )
        except Exception as exc:
            logger.exception("reindex job failed", extra={"job_id": job_id})
            self.catalog.update_job(
                job_id,
                status="failed",
                error=exc.__class__.__name__,
                retryable=True,
                finished_at=self._now(),
            )

    def _callback(self, job_id: str) -> Callable:
        def callback(chunks):
            self.index_callback(chunks)
            self.catalog.update_job(
                job_id,
                processed_chunks=len(chunks),
                total_chunks=len(chunks),
            )

        return callback

    def retry(self, job_id: str, trace_id: str | None = None) -> dict | None:
        original = self.catalog.get_job(job_id)
        if not original or not original["retryable"]:
            return None
        if original["operation"] == "reindex":
            return self.submit_reindex(trace_id)
        document = self.catalog.get_document(original.get("document_id", ""))
        if not document:
            return None
        path = Path(
            self.settings.upload_dir,
            f"{document['document_id']}{Path(document['filename']).suffix.lower()}",
        )
        if not path.exists():
            return None
        return self.submit_upload(document["filename"], path.read_bytes(), trace_id)

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
