## Why

Insight already exposes the complete local RAG workflow through HTTP APIs, but a public demo currently requires manually composing upload, job polling, search, and SSE requests. A small same-origin browser console will make the project directly demonstrable to GitHub visitors while preserving the local-first deployment model and avoiding a separate frontend toolchain.

## What Changes

- Add a browser console served by the FastAPI application at `/`.
- Provide document upload, indexing-job progress, document listing, search, and grounded chat interactions.
- Consume the existing native SSE chat stream and display answer text, sources, retrieval metadata, and workflow stages.
- Add a responsive, dependency-free HTML/CSS/JavaScript UI that works without Node.js, a frontend build step, or external web services.
- Add static console serving behavior and endpoint coverage tests.
- Document the console startup and usage flow in the README.

## Capabilities

### New Capabilities

- `web-console`: Provide a local browser interface for managing documents, searching the knowledge base, and asking grounded questions.

### Modified Capabilities

- `http-api`: Serve the web console from the same FastAPI application while keeping existing API routes and local deployment behavior intact.

## Impact

- Affected code: FastAPI app factory, new `app/web/` static assets, API integration tests, and README.
- Affected runtime: no new service or Python dependency; Docker already copies the application package and will include the static assets.
- The console uses same-origin requests and inherits the existing API configuration, model availability, and local CORS/deployment constraints.
