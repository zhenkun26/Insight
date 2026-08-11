## 1. OCR runtime and parser

- [x] 1.1 Add opt-in OCR settings with validation for enabled state, language, timeout, and temporary work behavior.
- [x] 1.2 Implement a bounded local OCR adapter that probes required tools, renders PDF pages, OCRs only requested pages, and cleans temporary files.
- [x] 1.3 Integrate OCR into PDF parsing without changing text-layer pages or non-PDF parsing.

## 2. API and observability

- [x] 2.1 Map OCR unavailable, timeout, and command failures to explicit document parsing errors and expose OCR configuration status in health output.
- [x] 2.2 Document platform prerequisites, environment variables, failure behavior, and reindex guidance in README and `.env.example`.

## 3. Verification and delivery

- [x] 3.1 Add parser and adapter tests for default behavior, blank-page OCR, mixed pages, invalid timeout, missing tools, timeout, and cleanup.
- [x] 3.2 Run L0/L1/L2 checks, full pytest/Ruff/OpenSpec/Docker/evaluation verification, and a local runtime tool probe.
- [x] 3.3 Sync the accepted specification, archive the completed change, commit, push, and verify GitHub Actions.
