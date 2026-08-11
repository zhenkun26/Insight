## 1. Project foundation

- [x] 1.1 Create the Python package structure for configuration, schemas, services, ingestion, retrieval, API, and workflows.
- [x] 1.2 Add `pyproject.toml`, runtime dependencies, development dependencies, lint/format configuration, and Python 3.11+ metadata.
- [x] 1.3 Implement environment-based settings for model endpoints, model names, Milvus URI, storage paths, Top-K, thresholds, timeouts, and rerank enablement.
- [x] 1.4 Add `.env.example`, `.gitignore`, package entrypoint, and a minimal `GET /health` endpoint with dependency status fields.

## 2. Document ingestion and catalog

- [x] 2.1 Implement PDF, Markdown, and TXT parsers with normalized text output and best-effort page/heading metadata.
- [x] 2.2 Implement text cleaning and heading/paragraph-aware chunking with configurable maximum size and overlap.
- [x] 2.3 Define document, chunk, source, and index-status schemas with stable document and chunk identifiers.
- [x] 2.4 Implement the SQLite document catalog for metadata, content fingerprints, chunks, and index lifecycle state.
- [x] 2.5 Implement duplicate detection, document listing, document deletion, and reindex planning.
- [x] 2.6 Add ingestion tests for supported formats, unsupported formats, chunk limits, metadata preservation, duplicates, and deletion state.

## 3. Indexing and retrieval

- [x] 3.1 Define vector store and embedding provider protocols plus fake implementations for tests.
- [x] 3.2 Implement Ollama Embedding HTTP adapter using environment configuration and explicit timeout/error handling.
- [x] 3.3 Implement Milvus/Milvus Lite vector store adapter with upsert, search, delete-by-document, and rebuild operations.
- [x] 3.4 Implement BM25 index construction, persistence, loading, keyword search, and synchronization with the document catalog.
- [x] 3.5 Implement hybrid retrieval with per-source scores, stable deduplication, configurable RRF fusion, Top-K, and threshold filtering.
- [x] 3.6 Implement optional reranker protocol, configured reranker adapter, and fallback behavior when disabled or unavailable.
- [x] 3.7 Add retrieval tests for BM25, vector adapter calls, RRF ordering, deduplication, thresholds, and rerank fallback.

## 4. Grounded question answering

- [x] 4.1 Define query, retrieval result, source citation, chat response, and error schemas including `latency_ms`.
- [x] 4.2 Implement Ollama LLM HTTP adapter with environment-based model selection, timeout handling, and response validation.
- [x] 4.3 Implement the explicit question-answering workflow: query analysis, retrieval, rerank, relevance check, answer, and fallback.
- [x] 4.4 Implement context formatting and a strict grounded-answer prompt requiring source identifiers and refusal when evidence is insufficient.
- [x] 4.5 Add mock-based tests for evidence-grounded answers, no-result refusal, source citation format, and LLM failure handling.

## 5. FastAPI interfaces

- [x] 5.1 Implement `POST /documents/upload` with multipart validation, ingestion, indexing, and structured response data.
- [x] 5.2 Implement `GET /documents`, `DELETE /documents/{document_id}`, and `POST /documents/reindex`.
- [x] 5.3 Implement `POST /search` with configurable retrieval parameters and inspectable result metadata.
- [x] 5.4 Implement `POST /chat` and a non-blocking `POST /chat/stream` response path with consistent schemas.
- [x] 5.5 Add API error handlers, request correlation/logging fields, sensitive-content safeguards, and health-check dependency reporting.
- [x] 5.6 Add FastAPI TestClient coverage for health, upload, document lifecycle, search, chat, and mocked model behavior.

## 6. Demo data, evaluation, and documentation

- [x] 6.1 Add clearly labeled synthetic sample meteorological documents without presenting them as official business data.
- [x] 6.2 Add 10–20 evaluation questions with expected document/chunk or key-content matches.
- [x] 6.3 Implement an evaluation script that calculates real Recall@K, MRR or hit rate, average latency, run date, model names, and parameters.
- [x] 6.4 Add `Dockerfile` and `docker-compose.yml` for the API and Milvus local deployment, with documented Ollama connectivity options.
- [x] 6.5 Write README sections for architecture, setup, Ollama models, Milvus, ingestion, API examples, testing, evaluation, limitations, and roadmap.

## 7. Quality gates and delivery

- [x] 7.1 Add GitHub Actions CI for dependency installation, formatting/lint checks, import checks, and pytest without external services.
- [x] 7.2 Run the project test suite and fix failures without weakening assertions or hiding unavailable-service states.
- [x] 7.3 Run the evaluation script in the available environment, record only measured results, and document blocked model-dependent checks when applicable.
- [x] 7.4 Run OpenSpec validation and reconcile this task checklist with the implemented and verified behavior.
