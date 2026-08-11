from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Insight")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "local")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    database_path: str = os.getenv("DATABASE_PATH", "data/insight.db")
    bm25_index_path: str = os.getenv("BM25_INDEX_PATH", "data/bm25.json")
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    # Empty by default keeps imports and CI independent from a vector service.
    # Set MILVUS_URI=data/milvus.db for Milvus Lite or use the Compose URI.
    milvus_uri: str = os.getenv("MILVUS_URI", "")
    milvus_collection: str = os.getenv("MILVUS_COLLECTION", "insight_chunks")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.2:3b")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    reranker_model: str = os.getenv("RERANKER_MODEL", "")
    top_k: int = int(os.getenv("TOP_K", "5"))
    candidate_k: int = int(os.getenv("CANDIDATE_K", "20"))
    score_threshold: float = float(os.getenv("SCORE_THRESHOLD", "0.01"))
    vector_score_threshold: float = float(os.getenv("VECTOR_SCORE_THRESHOLD", "0.7"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
    enable_rerank: bool = _env_bool("ENABLE_RERANK", False)
    job_workers: int = int(os.getenv("JOB_WORKERS", "2"))
    index_version: str = os.getenv("INDEX_VERSION", "1")
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    session_max_turns: int = int(os.getenv("SESSION_MAX_TURNS", "6"))
    session_max_chars: int = int(os.getenv("SESSION_MAX_CHARS", "6000"))
    session_message_max_chars: int = int(os.getenv("SESSION_MESSAGE_MAX_CHARS", "2000"))
    log_query_content: bool = _env_bool("LOG_QUERY_CONTENT", False)
    ocr_enabled: bool = _env_bool("OCR_ENABLED", False)
    ocr_language: str = os.getenv("OCR_LANGUAGE", "eng")
    ocr_timeout_seconds: float = float(os.getenv("OCR_TIMEOUT_SECONDS", "30"))
    ocr_temp_dir: str | None = os.getenv("OCR_TEMP_DIR") or None

    def __post_init__(self) -> None:
        if not 0 <= self.vector_score_threshold <= 1:
            raise ValueError("VECTOR_SCORE_THRESHOLD must be between zero and one")
        if self.ocr_enabled and self.ocr_timeout_seconds <= 0:
            raise ValueError("OCR_TIMEOUT_SECONDS must be greater than zero when OCR is enabled")
        if self.ocr_enabled and not self.ocr_language.strip():
            raise ValueError("OCR_LANGUAGE must not be empty when OCR is enabled")

    def ensure_directories(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.bm25_index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        if self.ocr_temp_dir:
            Path(self.ocr_temp_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
