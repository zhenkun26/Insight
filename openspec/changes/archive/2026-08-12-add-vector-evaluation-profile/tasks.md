## 1. Retrieval modes

- [x] 1.1 Add a backward-compatible keyword-enabled switch to `HybridRetriever` and expose accurate disabled status/timing for vector-only mode.
- [x] 1.2 Add regression tests proving BM25 mode does not call vector dependencies, vector mode does not call BM25, and hybrid mode preserves fusion behavior.

## 2. Vector evaluation profiles

- [x] 2.1 Extend `scripts/evaluate.py` with `bm25`, `vector`, and `hybrid` modes, memory/Milvus backends, Ollama Embedding configuration, and fail-fast validation.
- [x] 2.2 Extend evaluation JSON and tests with retrieval mode, vector backend, Embedding/Milvus metadata, and vector stage timing.
- [x] 2.3 Add Milvus adapter contract coverage with a fake client and document real integration boundaries.
- [x] 2.4 Document offline, memory, and explicit Milvus Lite evaluation commands without claiming fixed metrics.

## 3. Verification and delivery

- [x] 3.1 Run full offline tests, lint, format, lock, OpenSpec, import, Docker Compose, and diff checks.
- [x] 3.2 Run one explicit Ollama Embedding + Milvus Lite hybrid smoke when local models/services are available; otherwise record the integration check as BLOCKED with offline evidence.
- [x] 3.3 Sync accepted requirements, archive, commit, push, and verify GitHub Actions.
