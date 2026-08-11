## 1. Retrieval timing

- [x] 1.1 Add per-search keyword, vector, fusion, rerank, and total timing/status state to `HybridRetriever` without changing ranking behavior.
- [x] 1.2 Add regression coverage proving disabled stages are explicit and enabled rerank timings are captured.

## 2. Evaluation profiles

- [x] 2.1 Add `disabled`, `keyword`, and `ollama` reranker profile selection to `scripts/evaluate.py` with explicit validation and model/address options.
- [x] 2.2 Extend evaluation JSON with profile, stage averages, per-question stage timing, and backward-compatible configuration metadata.
- [x] 2.3 Add offline evaluation script tests for default and keyword profiles, plus invalid Ollama configuration.
- [x] 2.4 Document profile commands, output interpretation, and external-model caveats in README.

## 3. Verification and delivery

- [x] 3.1 Run full tests, lint, lock/spec/Docker checks, default evaluation, and inspect generated JSON metrics.
- [x] 3.2 If local Ollama is available, run one explicit Ollama profile smoke evaluation; otherwise record the external check as BLOCKED with offline evidence.
- [x] 3.3 Sync the accepted evaluation requirement, archive the change, commit, push, and verify GitHub Actions.
