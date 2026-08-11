## 1. Vector score calibration

- [x] 1.1 Add a shared vector score normalization helper and apply it in memory and Milvus retrieval results.
- [x] 1.2 Add `VECTOR_SCORE_THRESHOLD` configuration, validate its range, and pass it to vector-capable application retrieval.
- [x] 1.3 Filter below-threshold vector candidates before hybrid fusion while preserving BM25-only and fallback behavior.

## 2. Evaluation and documentation

- [x] 2.1 Add vector threshold CLI/config plumbing and record the effective value in evaluation output.
- [x] 2.2 Add refusal calibration counts/rates and per-question refusal state to evaluation reports.
- [x] 2.3 Update environment and README instructions with threshold calibration examples and limitations.

## 3. Verification

- [x] 3.1 Add unit and integration-style tests for normalization, threshold filtering, configuration validation, and refusal metrics.
- [x] 3.2 Run formatting, tests, OpenSpec validation, default evaluation, and vector/hybrid smoke checks; archive and deliver the change.
