## 1. Search API observability

- [x] 1.1 Map `HybridRetriever.last_status` and `last_timings` into `/search` stage entries without changing retrieval ranking or existing response fields.
- [x] 1.2 Add API tests for disabled stages, enabled stages, and vector fallback status/timing serialization.

## 2. Web Console diagnostics

- [x] 2.1 Render search stage chips with status, measured milliseconds, and disabled/null handling in the dependency-free console.
- [x] 2.2 Add or update static console tests and README response documentation.

## 3. Verification and delivery

- [x] 3.1 Run full tests, lint, format, lock, OpenSpec, import, Docker Compose, and diff checks.
- [x] 3.2 Sync the accepted requirements, archive the change, commit, push, and verify GitHub Actions.
