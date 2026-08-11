## 1. FastAPI static entry

- [x] 1.1 Add same-origin root and `/assets/` static serving to the FastAPI app factory without intercepting existing API routes.
- [x] 1.2 Add endpoint tests for the HTML entry point, CSS/JavaScript assets, and an existing JSON API route.

## 2. Browser console

- [x] 2.1 Create the dependency-free HTML shell and responsive visual layout for document, search, and chat workspaces.
- [x] 2.2 Implement document upload, job polling, document listing, and readable error/empty states.
- [x] 2.3 Implement search submission and rendering of scores, snippets, sources, and latency.
- [x] 2.4 Implement POST SSE stream parsing for chat, incremental answer rendering, sources/stages display, fallback handling, and AbortController cancellation.

## 3. Documentation and verification

- [x] 3.1 Document local console startup, usage, and limitations in the README.
- [x] 3.2 Run formatting, lint, unit/API tests, strict OpenSpec validation, Docker Compose validation, and a manual browser/static smoke check.
- [x] 3.3 Sync accepted requirements to main specs and archive the completed OpenSpec change.
