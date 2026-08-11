## 1. Model reranker

- [x] 1.1 Extend the Ollama generation client with an optional model override while preserving the default QA model.
- [x] 1.2 Implement strict numeric score parsing and atomic Ollama candidate reranking with bounded failure behavior.
- [x] 1.3 Update service construction to select disabled, deterministic keyword, or Ollama reranking according to configuration.

## 2. Contract and documentation

- [x] 2.1 Add retrieval tests for valid scores, invalid output, request failure, original-order fallback, and no partial mutation.
- [x] 2.2 Update environment examples, README configuration guidance, and retrieval observability notes.

## 3. Verification and delivery

- [x] 3.1 Run L0/L1/L2 checks, full tests, lint, lock/spec/Docker validation, and evaluation baseline.
- [x] 3.2 Run Ollama request contract tests and a local Ollama availability probe, clearly labeling unavailable external integration.
- [x] 3.3 Sync the accepted hybrid-retrieval requirement, archive the change, commit, push, and verify GitHub Actions.
