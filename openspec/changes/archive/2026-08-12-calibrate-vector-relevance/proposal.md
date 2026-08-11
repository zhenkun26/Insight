## Why

The first real local vector/hybrid evaluation showed that raw vector scores and the existing RRF threshold are not sufficient for refusal decisions: unrelated questions could still produce candidates. The project needs an explicit, bounded vector relevance signal and a measurable way to calibrate refusal behavior without changing the default BM25 workflow.

## What Changes

- Normalize vector retrieval scores to a stable `[0, 1]` range before exposing or filtering them.
- Add an environment-configurable `VECTOR_SCORE_THRESHOLD` for vector and hybrid retrieval, independent of the RRF/final result threshold.
- Filter vector candidates by the dedicated threshold before fusion while preserving vector fallback behavior.
- Expose the effective vector threshold in evaluation parameters and add refusal false-positive calibration metrics.
- Extend tests and README guidance so threshold sweeps can be run against the same evaluation set without relying on external services in CI.

## Capabilities

### New Capabilities

<!-- No new standalone capability; this change tightens existing retrieval and evaluation contracts. -->

### Modified Capabilities

- `hybrid-retrieval`: vector and hybrid retrieval must use normalized vector relevance scores and an independently configurable vector-candidate threshold.
- `evaluation-and-delivery`: evaluation reports must expose refusal calibration outcomes, including false-positive counts/rates and the effective vector threshold.

## Impact

- Affected code: vector stores, hybrid retriever, application settings/factory, evaluation CLI, tests, `.env.example`, and README.
- No new runtime dependency or external service is introduced.
- BM25-only retrieval remains behaviorally compatible; vector/hybrid deployments gain a default threshold that can be overridden through configuration.
