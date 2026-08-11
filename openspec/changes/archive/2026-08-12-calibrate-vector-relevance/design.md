## Context

The current vector stores return backend-dependent values: the in-memory implementation emits cosine similarity while Milvus emits its configured distance value. The hybrid retriever currently applies only the RRF/final threshold, so a vector candidate can enter the pipeline even when it is not useful for grounding. See `proposal.md` and the added requirements in the delta specs for the externally visible contract.

## Goals / Non-Goals

**Goals:**

- Make vector scores comparable and safe to expose across the in-memory and Milvus adapters.
- Apply a separately configurable vector-candidate gate before RRF fusion.
- Preserve the offline BM25 default and existing fallback behavior.
- Make refusal false positives measurable and comparable across threshold runs.

**Non-Goals:**

- Changing the embedding model, distance metric, Milvus schema, or RRF formula.
- Adding a learned calibration model or automatic threshold optimizer.
- Making refusal decisions depend on an LLM call.

## Decisions

1. **Clamp scores to `[0, 1]` rather than remap cosine values.** The current in-memory cosine score is already a useful similarity signal, while mapping `[-1, 1]` to `[0, 1]` would turn an unrelated zero-similarity result into `0.5`. Clamping preserves strong positive scores and makes invalid backend overshoots safe. Both adapters will normalize before constructing `RetrievalResult`.

2. **Use an independent `VECTOR_SCORE_THRESHOLD`.** `SCORE_THRESHOLD` applies to fused RRF scores and has a different scale, so reusing it cannot calibrate vector relevance. The application default is `0.7`, configurable through the environment and CLI; a `None` value remains available to library callers that need the legacy unfiltered behavior.

3. **Filter before fusion.** Removing weak vector candidates before RRF avoids letting them affect rank order and keeps the result list explainable. Keyword fallback remains available in hybrid mode when vector calls fail; an empty filtered vector list is treated as a successful vector stage with no candidates.

4. **Report false positives, not only refusal accuracy.** For each refusal question, a non-empty retrieved result is a false-positive answer opportunity. The report will retain the existing refusal accuracy and add count/rate fields plus the effective threshold, enabling manual threshold sweeps without pretending to optimize automatically.

## Risks / Trade-offs

- [Risk] A default threshold of `0.7` may remove useful candidates for some embedding models. → Mitigation: expose the value through `VECTOR_SCORE_THRESHOLD`, record it in evaluation output, and document threshold sweeps.
- [Risk] Clamping does not correct a backend configured with a fundamentally different distance interpretation. → Mitigation: keep the adapter contract explicit, use the known Milvus cosine configuration, and report the backend and model in every vector evaluation.
- [Risk] Threshold filtering can increase refusal rates while lowering recall. → Mitigation: evaluate hit rate/MRR and refusal false-positive rate together rather than treating refusal alone as success.

## Migration Plan

Add the environment setting and CLI option with the documented default. Existing BM25 users need no migration. Existing vector/hybrid users should rerun evaluation and tune the threshold for their embedding model; rollback consists of setting `VECTOR_SCORE_THRESHOLD` to an intentionally permissive value or leaving the library-level option unset.
