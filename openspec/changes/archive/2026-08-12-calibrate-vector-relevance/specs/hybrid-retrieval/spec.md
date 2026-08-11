## ADDED Requirements

### Requirement: Calibrated vector relevance filtering
向量召回结果 SHALL expose a normalized relevance score in the inclusive `[0, 1]` range. Vector and hybrid retrieval SHALL support an independently configurable vector score threshold; when configured, candidates below that threshold MUST be removed before rank fusion. BM25-only retrieval MUST remain unaffected by this threshold.

#### Scenario: Normalize vector scores
- **WHEN** a vector backend returns a score below `0` or above `1`
- **THEN** the response clamps the exposed vector score into `[0, 1]`

#### Scenario: Filter weak vector candidates before fusion
- **WHEN** vector or hybrid retrieval is configured with `VECTOR_SCORE_THRESHOLD` and a candidate score is lower than the threshold
- **THEN** that candidate does not contribute to fused results or final context

#### Scenario: Preserve BM25 behavior
- **WHEN** the retrieval mode is `bm25`
- **THEN** no vector threshold is applied and the existing keyword-only result behavior is preserved

#### Scenario: Disable vector threshold explicitly
- **WHEN** vector retrieval has no vector score threshold configured
- **THEN** vector candidates are not removed solely because of this new calibration feature
