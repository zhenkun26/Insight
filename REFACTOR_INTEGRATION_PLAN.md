# Insight Refactoring and Atmos-RAG Integration Plan

Date: 2026-10-02, America/New_York\
Plan revision: 1\
Product standard: a maintainable, single-user, local-first application\
Delivery method: one bounded, verifiable increment at a time

This plan makes Insight the application and engineering home. Atmos-RAG contributes its source organization, meteorological evidence requirements, and experimental method. Refactoring existing behavior takes priority over adding features or replacing the stack.

The current request authorizes this planning package. It does not start the implementation increments below. Current authorization, progress, blockers, and the resume point belong to [REFACTOR_STATUS.md](docs/REFACTOR_STATUS.md). The planning consistency review is [recorded separately](docs/reviews/2026-10-02-refactor-plan-consistency.md).

## 1. Intended outcome and engineering standard

The application should let its owner import selected local material, search within an explicit scope, inspect original evidence, and obtain an answer whose citations can be checked. It must explain missing evidence and unavailable dependencies without reporting them as successful answers.

Success means:

- The owner can understand the important modules, run the application from documented steps, and diagnose failures.
- Keyword search remains usable without a vector service or a generating model. Answer generation reports its actual readiness separately.
- Search, chat, and streaming chat honor the same eligible-document rules and requested scope.
- Document changes, failed indexing, retries, restart recovery, and logical removal keep the visible evidence set consistent.
- A citation resolves to a specific source revision and location; a candidate score is not presented as answer correctness.
- Application data and source material remain recoverable. Migration and rollback procedures are verified on isolated copies before actual migration.
- Tests explain behavior and failure recovery. A small demonstration dataset is not advertised as professional validation.
- A later session can resume from repository records without depending on chat history.

Maintainability does not mean introducing microservices, a framework for every operation, or arbitrary coverage and file-count targets. Use consequences, observed failures, module responsibilities, and recovery needs to determine scope.

## 2. Scope and explicit exclusions

| Area | Planned baseline | Outside the current plan's default implementation |
| --- | --- | --- |
| Application home | Existing Insight repository and Python application | A second maintained backend in Atmos-RAG; repository renaming |
| User and platform | One local user; macOS is the first acceptance environment | Public hosting, multi-user tenancy, enterprise RBAC, universal platform support |
| Input | Selected PDF, Markdown, and TXT files; explicit local source roots | Scanning the entire home directory or Obsidian vault |
| Retrieval | Searchable original material, lexical/BM25 baseline, optional existing vector path | Mandatory hybrid retrieval or mandatory reranking |
| Evidence | Source revisions, locations, relevant sections, validated citation identifiers | A promise of automatic scientific truth verification |
| Integration | One-way reading of selected Atmos-RAG/Obsidian material | Bidirectional synchronization or automatic edits to source notes |
| Runtime | Local model adapter and local storage; explicit degraded capabilities | Unapproved cloud calls, model training, Kubernetes, managed services |
| Later experiments | Only extensions supported by labeled failure cases | GraphRAG, autonomous agent loops, visual retrieval, fine-tuning, scientific array computation by default |

The current Atmos-RAG archive and Obsidian originals remain preserved. Integration does not require moving their master files into Git, copying every PDF, or deleting old folders. A missing source becomes unavailable in the application's catalog; filesystem cleanup remains a user action under the current no-deletion instruction.

## 3. Baseline and evidence limits

Baseline application commit: `abb59d7515119e9dcc4ee13bc307cbdc4bed8841`.

The 2026-10-02 investigation found:

- Insight contains the application, tests, evaluation script, browser console, and eleven main OpenSpec capability directories.
- Atmos-RAG has no local Git repository or application implementation. Its archive registers a separate Obsidian knowledge directory.
- The Obsidian materials include thirteen Markdown notes, seven RAG-methodology PDFs, and twelve unannotated question seeds. The meteorology directory contains its usage note, not an established domain corpus.
- Insight's evaluation uses three sample documents and twelve questions, including two refusal questions. These are smoke-test assets.
- Existing tracked Insight contents match the baseline; 144 file-mode differences existed before this task and must remain outside its commits.
- Baseline GitHub CI succeeded. Prior controlled checks passed syntax/lint and fifteen existing pure-memory test functions, but did not constitute a full local pytest run or real Ollama/Milvus qualification.
- Current OpenSpec CLI and the ordinary local Python dependency environment are unavailable. Recheck them in R01; do not invent an installation or validation success.

These are dated observations, not future acceptance receipts. Prior conversation probes identify work; each implementation increment must reproduce relevant failures and verify its final content. The actual result of this planning package is recorded in the review and status files.

Baseline references:

- [Application composition](app/main.py), [configuration](app/core/config.py), [API](app/api/routes.py), and [API models](app/schemas/api.py).
- [Ingestion](app/services/ingestion.py), [tasks](app/services/jobs.py), and [catalog](app/services/catalog.py).
- [Hybrid retrieval](app/retrieval/hybrid.py), [vector adapter](app/retrieval/vector.py), [BM25](app/retrieval/bm25.py), and [provider protocols](app/retrieval/protocols.py).
- [Parsing](app/ingestion/parsers.py), [chunking](app/ingestion/chunker.py), [QA](app/services/qa.py), and [browser console](app/web/app.js).
- [Evaluation](scripts/evaluate.py), [tests](tests), [dependencies](pyproject.toml), [lockfile](uv.lock), [CI](.github/workflows/ci.yml), and [deployment](docker-compose.yml).

Machine-specific source roots belong to local configuration, using names such as `INSIGHT_ROOT`, `ATMOS_ARCHIVE_ROOT`, and `ATMOS_KNOWLEDGE_ROOT`. Do not publish private paths, notes, credentials, or raw runtime records in planning documents.

## 4. Decision ownership and document responsibilities

| Record | Owns | Does not own |
| --- | --- | --- |
| This plan | Product boundary, proposed architecture, increment sequence, workflow and acceptance rules | Live completion state, implementation authorization, test results |
| [Status](docs/REFACTOR_STATUS.md) | Current scope, active increment, authorization reference, blockers, next action, links to decisions and receipts | Independent grants of permission or copied specifications |
| [Main OpenSpec specifications](openspec/specs) | Current documented behavior contracts | Proof that implementation meets the contracts |
| An implementation change's OpenSpec artifacts | Its proposal, design, delta requirements, and tasks | Authority to push, merge, migrate private sources, or advance another increment |
| Git | Actual file content, branches and commit history | Professional acceptance or user permission |
| Increment verification receipt | Commands, artifact/version identity, outcomes, limitations, acceptance evidence | Permission or a replacement task list |
| User messages | Task-specific authorization and acceptance | Automatic permission inferred from generated documents |

Read live code and Git to verify state. If the plan, status, specifications, and implementation disagree, record the discrepancy and reconcile the affected scope before claiming completion. Do not silently choose whichever record is most convenient.

Planning constraints already established by the user:

- Insight is the application home; prioritize refactoring and personal use.
- Work one increment at a time; retain existing source material and unrelated changes.
- Follow the no-filesystem-deletion rule, including test cleanup and temporary artifacts.
- New dependencies require permission. Installing already-declared dependencies can be routine within an authorized increment, after reviewing installation side effects.
- Commit completed task changes after appropriate verification; push requires explicit authorization for the current branch and destination. Merge and release are separate.

Proposed engineering choices, to be resolved in the affected increment's design:

- Preserve a modular monolith, SQLite, and a lexical baseline.
- Keep original sources external and read them one way.
- Publish validated index generations rather than mutating the active evidence set during construction.
- Separate stable document identity, content revision, evidence location, and encoding/index configuration.
- Return per-request retrieval reports and use catalog-backed evidence hydration.

Creating this plan does not make every proposed design decision accepted. Record later accepted or superseded decisions in the decision section of the current change's design, with their reason and user reference where authorization matters. Status stores a pointer, not another copy.

## 5. Target responsibilities and contracts

Keep existing directories unless responsibilities justify a move. The table describes responsibilities, not a mandate to create every named class or a large new directory tree.

| Responsibility | Existing home | Target contract |
| --- | --- | --- |
| Composition and configuration | `app/main.py`, `app/core` | Explicit startup/shutdown; validated configuration loaded at construction; no hidden resource creation in library imports |
| Source intake | `app/services/ingestion.py`, future source adapter | Upload or allowed-root read; input receipt; source provenance; no modification of master material |
| Parsing and evidence structure | `app/ingestion` | Original-to-derived location mapping, title hierarchy, paragraph/section relationships, explicit unsupported or partial content |
| Catalog and tasks | `app/services/catalog.py`, `jobs.py` | Stable identities, revisions, states, job lineage, reproducible build configuration, recoverable publication |
| Retrieval | `app/retrieval` | One scope contract; per-request results, status, timings and score meaning; backend-independent evidence identifiers |
| Evidence reading | Initially a focused service alongside QA | Hydrate identifiers from the catalog; recover relevant parent sections under a context budget |
| QA and sessions | `qa.py`, `session.py` | Separate conversation aid from evidence; citation validation; explicit success/refusal/partial/failure states |
| Provider adapters | `ollama.py`, `rerank.py`, `vector.py` | Query/document encoding semantics, batch support, versions, timeouts, readiness and failure categories |
| API and browser | `app/api`, `schemas`, `web` | Compatible public behavior, explicit scope, inspectable source location, accurate progress and terminal states |
| Evaluation | `scripts/evaluate.py`, `tests` | Shared production configuration, annotated evidence, meaningful denominators, isolated deterministic and live checks |

### 5.1 Scope and retrieval report

Scope includes source/document selection, domain, revision eligibility, and logical removal/index status. Existing filters should map to it without silently broadening a request. An explicitly empty allowed set means no evidence, not unrestricted retrieval.

Eligibility refers to a validated active revision and the capability requested. A failed staged replacement or optional vector build does not invalidate a still-usable lexical generation. Retained active content can remain readable while its replacement is pending, with that condition visible; superseded, logically removed or unavailable content cannot silently re-enter current results. Define any explicit snapshot-reading policy separately from current-source search.

The retrieval operation returns its own results and execution report. Eliminate consumers' dependence on mutable `last_status`/`last_timings`. Keep raw lexical, vector, fusion, and rerank scores distinct; record their meaning. A ranking score is not a calibrated answer probability.

Backends should filter before candidate truncation where supported. Where a backend cannot honor a scope correctly, report the limitation or use a correct scoped fallback; do not treat fixed global overfetch as complete scoped retrieval.

### 5.2 Source identity and index lifecycle

Use distinct concepts for stable document identity, immutable content revision/hash, source locator, derived evidence unit, and build configuration. Preserve legacy IDs through an explicit mapping when migrating. Only add persisted fields that have a demonstrated consumer or integrity requirement.

The publication protocol must define ordering across catalog, lexical index and optional vectors. SQLite and vector storage do not share a transaction. Construct and validate a new generation, then switch the active catalog reference only when required outputs are ready. Retain the prior usable generation and define restart behavior for every interrupted step.

Keyword-only operation must remain a legitimate configuration. If vectors are optional and their build fails, record separate capability readiness; do not misreport the vector build as successful or expose an ambiguous partially published state.

A new file revision remains staged until ready. Source edits, logical removal, failed builds and model changes must have deterministic consequences for current retrieval and old citations. Old citations remain tied to their revision; if retained source content is unavailable, show that limitation instead of redirecting to a newer revision.

### 5.3 Evidence and answers

Retrieval units may be smaller than the evidence supplied to generation. Hydrate the relevant section, variable definition and conditions where available. Apply a recorded context budget; label omissions instead of implying complete reading.

Citation identifiers must exist in the supplied evidence set. Display retrieved candidates separately from actually cited sources. Deterministic citation validation is necessary but does not prove that a scientific claim is entailed. Domain usefulness remains a human acceptance item.

Keep streaming and non-streaming semantics aligned. Confirm successful stream termination, preserve partial output on failure, and make the browser distinguish refusal, model failure, partial output, fallback and owner cancellation. Verify cancellation propagation with a real provider before claiming it stops model computation.

## 6. Traceability from findings to increments

The IDs below identify work, not independently verified defects in every environment. R01 refreshes evidence classifications; later receipts close them with final-state checks.

| Finding | Refactoring concern | Owner | Required behavior evidence |
| --- | --- | --- | --- |
| F01 | Search/chat scope mismatch and invalid-source eligibility | R02 | Search, chat and stream exclude the same out-of-scope, unready, inactive, unavailable and logically removed revisions under the requested capability |
| F02 | Shared retrieval report races | R02 | Overlapping successful/failed requests retain their own results, errors and timings |
| F03 | Vector post-filter truncation misses scoped evidence | R02 | A valid scoped hit outside the global candidate window is still retrievable |
| F04 | Offset pagination limited by fixed candidate count | R02 | Paging policy is explicit and stable beyond the first candidate window |
| F05 | Failed duplicates reported as successful | R03 | Same-content failed/stale builds execute recovery; successful equivalent builds remain idempotent |
| F06 | Retry input/lineage and queued restart recovery gaps | R03 | Retry has durable input and parent linkage; restart accounts for queued/running work |
| F07 | Stale lexical contents and inconsistent publication | R03 | Failure/logical removal cannot leak invalid evidence; interrupted publication retains a usable state |
| F08 | Configuration/import/lifecycle and resource limits | R01, R03 | Documented config works; imports are inert; upload/queue/index resources have tested bounds |
| F09 | Source metadata loss and weak version tracking | R04 | Every retrieval path resolves the same revision, page/section and original source |
| F10 | Obsidian exclusions/frontmatter not enforced | R06 | Denied directories, `rag_index: false`, drafts and evaluation content remain excluded |
| F11 | Title hierarchy and evidence context loss | R05 | Title-only terminology is searchable; formulas and conditions can be read together |
| F12 | Invalid/unused citations accepted | R05 | Invalid citation IDs cannot be reported as a validated answer; used sources are distinguishable |
| F13 | Ranking used as evidence sufficiency | R05 | Lexical topic overlap without answer evidence is handled explicitly; score meanings remain distinct |
| F14 | Stream, UI readiness and session behavior mismatch | R05 | Honest terminal states, bounded history-assisted queries, and partial/error display |
| F15 | Evaluation denominator/configuration/support limitations | R01, R08 | Answerable/unanswerable results are separate; shared configuration and evidence annotations are explicit |
| F16 | Legacy embedding API and serial/model-specific adapter gaps | R07 | Batch/query/document encoding, model identity, timeout and fallback contracts work |
| F17 | Stack compatibility and reproducibility gaps | R01, R07 | One reproducible baseline; actual client/server/provider compatibility is exercised |
| F18 | No real annotated meteorology corpus | R06, R08 | Owner-selected material and reviewed questions support professional acceptance |

## 7. Implementation increments

Order is R01 -> R02 -> R03 -> R04 -> R05 -> R06 -> R07 -> R08. R07's experiment track is conditional and can be explicitly deferred; its adapter/compatibility work is considered separately. Split an increment only when its recovery or verification boundary requires it, and record the resulting scope rather than proceeding to multiple increments implicitly.

### R01 — Establish the runnable, recoverable baseline

**Entry:** owner authorizes R01; refresh live Git and environment.\
**Purpose:** make future changes measurable without destroying existing state.

- Inventory settings, commands, dependency declarations, lockfile use, runtime paths, task lifecycle and API consumers.
- Resolve `.env` loading, configuration construction/validation and inert imports with explicit lifecycle management where required to establish the baseline.
- Define a loopback-only personal-use startup profile; external network exposure is a separate scope decision.
- Establish a side-effect-reviewed verification path that retains temporary artifacts and never invokes forbidden filesystem cleanup, including pytest/plugin defaults, OCR helpers and build tools.
- Reproduce the relevant investigation probes and save their inputs/outcomes as qualified baseline evidence. Do not label expected baseline defects as fixed.
- Define the production/evaluation configuration contract and metric denominators before comparisons; preserve legacy metric output or specify its compatibility transition.
- Determine which currently declared dependencies and services are actually needed for keyword-only operation. New packages require owner approval.
- Resolve OpenSpec tooling availability through an authorized setup choice; do not hand-author a falsely CLI-validated change.

**Exit:** documented local startup and configuration; repeatable safe deterministic checks; known defects classified; runtime/data snapshot and recovery method identified. Real-service readiness may be BLOCKED with an explicit scope limit.\
**Recovery:** restore configuration/startup behavior using focused corrective commits; retain all user data and prior receipts.\
**Primary files:** configuration, composition, dependency/CI definitions, test setup and evaluator as justified by the baseline findings.

### R02 — Make retrieval boundaries and reports consistent

**Entry:** R01's applicable baseline and verification path are complete.\
**Purpose:** one retrieval contract for all public entry points.

- Introduce the minimal common scope and per-request report structures.
- Apply catalog eligibility and scope to search, chat and stream, including the keyword fallback.
- Replace shared request status with returned reports; align provider protocol signatures and consumers.
- Correct backend filtering and stable pagination without changing QA context selection silently.
- Preserve public response compatibility where possible; document intentional corrections and add negative boundary tests.

**Exit:** F01-F04 behavior evidence passes; overlapping requests, empty scope, invalid sources and scoped fallback are covered.\
**Recovery:** retain compatible endpoints and schemas; revert only this increment's behavior through corrective commits if needed.\
**Primary files:** retrieval/protocols, API schemas/routes, QA consumers and corresponding tests.

### R03 — Repair indexing, tasks and publication

**Entry:** R02's eligibility contract exists.\
**Purpose:** task success means an actually usable, coherent index state.

- Persist an input receipt and task/source association before processing; associate retries with their parent and record their actual recoverability.
- Distinguish equivalent successful work from failed/stale work during duplicate detection.
- Recover queued and running tasks after restart, using one local ownership strategy; enforce the chosen single-process job model instead of accidentally supporting multiple competing runners.
- Implement staged publication and explicit lexical/vector capability readiness; define failure recovery across storage boundaries.
- Make logical removal/update invalidate every retrieval entry point consistently without deleting master files.
- Bound upload size, queued input, concurrent index work and retained future/report state based on resource behavior; serialize or isolate index construction as needed.
- Add failures before/after each publication boundary, retry checks and restart checks. Test on isolated retained artifacts.

**Exit:** F05-F08 behavior evidence passes; no unexecuted recovery is reported successful; previous usable evidence survives failed publication.\
**Recovery:** retain previous active generation and input receipts; restore its catalog reference through the documented procedure.\
**Primary files:** ingestion, catalog, task service, index composition, API task behavior and tests.

### R04 — Unify revisions, evidence locations and migrations

**Entry:** R03's publication and recovery contract exists.\
**Purpose:** a source remains identifiable through edits, backend changes and citations.

- Design a minimal stable-document/revision/evidence schema and a legacy-ID mapping.
- Preserve source provenance, page sequence versus printed page labels where available, heading path and evidence relationships.
- Hydrate retrieved identifiers from the catalog rather than reconstructing partial source records in each backend.
- Record the actual parser/chunker/encoding configuration and validate vector-space dimension/model compatibility before activation.
- Separate reparse, rechunk and re-embed operations; a reindex command must state which operation it performs.
- Write a repeatable migration with preconditions and postconditions. Verify it on a copy with references, interrupted migration, repeated invocation and restoration to the prior state.
- Actual migration of existing user data needs an explicit authorized input scope and reviewed recovery receipt; development fixtures do not authorize touching the live catalog.

**Exit:** F09 behavior evidence passes; legacy sources resolve; old and new revisions cannot silently alias; migration/recovery works on retained copies.\
**Recovery:** retained schema/data snapshot and source-ID mapping; no dropping files or destructive resets.\
**Primary files:** catalog/domain models, ingestion/parsing, vector hydration, schemas and migration tests.

### R05 — Refactor evidence reading, answers and the personal interface

**Entry:** R02 scope and R04 source identity are stable.\
**Purpose:** give the owner an inspectable evidence workflow.

- Index meaningful titles/aliases while preserving original text and heading hierarchy.
- Add focused section/neighbor reading under a recorded context budget; retain definitions, formula conditions and source locations where present.
- Separate ordering from evidence sufficiency; create hard negatives with overlapping terms but absent answer evidence. Avoid promising perfect automatic refusal.
- Validate citation membership and report used citations separately from candidates. Scientific support still requires domain acceptance.
- Align streaming/non-streaming generation, partial/failure states, readiness display and safe source opening within permitted roots. Treat source text, filenames and model output as untrusted display content; verify path and browser-rendering boundaries.
- Use bounded conversation history to resolve follow-up references without treating historical answers as source evidence.
- Add source reading/opening, scope selection and failure feedback to the existing browser console. Introduce a frontend framework only if concrete interface needs justify it and dependency approval exists.

**Exit:** F11-F14 checks pass; the owner can inspect a citation's source revision; deterministic checks do not masquerade as scientific correctness.\
**Recovery:** compatible existing routes and a retained UI behavior baseline; fall back to source search/read if generation is unavailable.\
**Primary files:** parsing/chunking, evidence/QA/session services, API schemas/routes, web console and tests.

### R06 — Integrate selected Atmos-RAG material one way

**Entry:** R03-R05 source and evidence lifecycle works; owner identifies permitted source roots.\
**Purpose:** turn the archive's conventions into implemented intake behavior.

- Implement an explicit allowed-root source adapter with path/symlink escape checks and no master-file writes.
- Parse the needed frontmatter fields; define missing/invalid metadata behavior and report exclusions.
- Enforce directory exclusions, `rag_index: false`, domain separation, draft/review policy and evaluation/training-output isolation before indexing.
- Detect content changes, source disappearance and renames; retain original-revision provenance and publish updates through R03/R04.
- Keep methodology PDFs in a separate scope. Teaching notes and templates are not automatically meteorology evidence.
- Use synthetic fixtures first. Integrate only the owner's named real corpus; no hidden scan of the entire vault.
- Turn applicable question seeds into concrete questions with reviewed source locations. Retain unreviewed seeds separately and label unavailable material honestly.

**Exit:** F10 checks pass; controlled import/update/unavailable-source scenarios work; source masters are unchanged. F18 domain readiness remains BLOCKED until real material and annotation exist.\
**Recovery:** disable the adapter or restore the previous active catalog generation; originals are untouched.\
**Primary files:** a focused source adapter, metadata intake, local config, catalog integration and tests. Atmos-RAG originals are read-only unless separately authorized.

### R07 — Modernize adapters and evaluate optional components

**Entry:** R01-R06 applicable contracts pass; verify current official compatibility information again.\
**Purpose:** update necessary interfaces, then retain only justified complexity.

**Contract track:**

- Migrate Ollama embedding to the current batch-capable interface, with explicit query/document semantics for the configured model.
- Reuse clients where useful; validate batch output shape, finite values, dimensions, model identity, timeout and readiness behavior.
- Separate optional vector/OCR/model dependencies and document a reproducible lexical installation path; preserve declared contracts and ask before new packages.
- Align a chosen Milvus client/server/Lite profile and Docker model connectivity. A container's loopback address is not the host's model endpoint.
- Retain explicit degraded capabilities and run real adapter checks on authorized local services before declaring them qualified.

**Conditional experiment track:**

- Compare terminology expansion, multilingual embedding, reranking and generation models on the same annotated corpus and question split.
- Record source/model revisions, candidate and context budgets, quality, latency, memory and calls. Do not choose defaults from advertised leaderboards.
- Keep the existing backend until replacement has a concrete operational benefit. A new vector store or framework is a separate scope/dependency decision.
- If annotated domain evidence is absent, defer the experiments explicitly. Do not block contract repairs on a fake performance comparison.

**Exit:** F16-F17 evidence passes for the selected supported profiles; optional defaults have evidence or remain unchanged/deferred. Required real-service checks that remain BLOCKED keep the corresponding qualification and increment exit pending; deterministic adapter tests do not close them.\
**Recovery:** retained adapter/configuration path and prior index generation; model changes activate a distinct encoding space.\
**Primary files:** provider/vector/rerank adapters, dependency/lock definitions, deployment and evaluation profiles.

### R08 — Verify integrated personal use and close the refactoring program

**Entry:** required prior increments are verified; conditional experiments have an explicit disposition.\
**Purpose:** independently judge engineering readiness and actual personal usefulness.

- Exercise startup, keyword-only mode, dependency failure, selected import, revision update, retry, restart, logical removal, search/chat/stream scope, source opening and partial/error display on the final content.
- Verify the final environment/installation instructions and recovery steps on retained copies. Record the actual OS/runtime; do not imply untested Windows/Linux support.
- Evaluate labeled real questions separately for retrieval, complete-evidence coverage, answer support, refusal and scientific conditions.
- Have the owner perform source-based manual acceptance on real learning/research tasks. Record acceptance, requested corrections and missing inputs without fabricating approval.
- Run the workflow consistency audit in section 11 and reconcile status, current changes, main specifications, documentation and verification receipts.
- Archive only actually completed OpenSpec changes using the applicable workflow. Archive means preserving history, not deleting files or branches.

**Exit:** engineering acceptance and domain/manual acceptance are reported separately. If domain inputs are missing, report the engineering increment's actual completion and leave product/domain acceptance BLOCKED; do not mark the whole program complete.\
**Recovery:** retain prior releases/configuration/data snapshots and use verified restoration or corrective commits.\
**Primary files:** evaluation/tests, usage/recovery documentation, status and completed change records.

## 8. Per-increment workflow

1. **Resume and inspect:** read applicable instructions, status, the plan's relevant increment, its OpenSpec artifacts, then live Git/code and receipts. Reconfirm the actual active scope; do not infer it from the last conversation summary.
2. **Scope the authorized increment:** record the user's reference, objective, inputs, affected responsibilities, exclusions, compatibility changes, verification, recovery and completion conditions. Routine implementation choices inside this scope do not require repeated permission.
3. **Prepare the change:** use the existing OpenSpec workflow where applicable. Check current CLI/schema behavior and read its generated instructions. No active change is created by this planning package. A top-level roadmap does not replace implementation proposal/design/delta specs/tasks.
4. **Reproduce and establish baseline:** run meaningful, side-effect-reviewed checks. Record expected defects and blocked real dependencies before editing.
5. **Implement a coherent correction:** follow contracts and preserve unrelated work. Update affected specs/tests/documentation when behavior intentionally changes. Avoid incidental model swaps or broad file rearrangement.
6. **Verify final content:** run checks appropriate to consequences, including relevant failure/recovery cases. Repeat affected verification after later edits. Do not rerun unrelated expensive checks without a reason.
7. **Review and record:** check scope, contracts, sources, authority, recovery and evidence. Update the current change's tasks and the status record; store the verification receipt. Missing checks keep their own BLOCKED state.
8. **Commit and deliver:** inspect the staged diff; commit only the completed task's changes with the repository's Conventional Commit practice. Report the final hash, result, limits and next eligible action. No extra commit is needed solely to record its own hash.
9. **Remote and next increment:** push only when explicitly authorized for the current destination. Do not infer merge, deployment, release or the next increment from push permission. Because work proceeds one increment at a time, wait for the owner's next instruction after delivery.

If a meaningful blocker is independent of some authorized work, finish the safe independent part and retain the blocker. Do not claim a complete increment when a known material acceptance condition is unresolved. A plan revision cannot retroactively widen the user's authorization.

## 9. Boundaries and recovery

| Action | Default handling |
| --- | --- |
| Read project code and named source metadata | Within the relevant authorized task; respect secrets/private content |
| Edit code/tests/docs in an authorized increment | Proceed within scope; preserve unrelated work |
| Add a dependency | Ask first, with purpose and alternatives |
| Install existing declared dependencies | Review side effects; proceed within authorized setup scope |
| Delete files, folders, temporary data, build artifacts or entire files through patches | Do not perform; explain the need and leave the action to the owner |
| Change an existing live user database/index | Prepare a reviewable migration/recovery result first; require authorization for named live inputs |
| Read a wider private source root or upload its content | Require scope authorization; do not infer from an adapter design |
| Call cloud models or external services with private input | Require explicit destination/input authorization |
| Download new weights or run resource-heavy experiments | Define model/resource scope first; ask when costs or impact are materially uncertain |
| Commit complete task changes | Commit only task paths after review and checks |
| Push, merge, deploy or release | Separate explicit authorization as applicable |
| Delegate to agents or message another chat | Only when the user or applicable instructions explicitly authorize it |
| Update global Codex memory | Only after a direct request to update it; project handoff notes are different |

Recovery avoids destructive Git reset, force-push and history rewriting. Correct published mistakes with new commits. Retain previous index generations and backups; test restoration without deleting user originals. Under the current filesystem rule, test cleanup is also a prohibited operation, not an exception because files are temporary.

## 10. Project memory and long-running work

Use three different categories:

| Category | Record | Rule |
| --- | --- | --- |
| Engineering memory | Status, current change design/tasks, verification receipts and Git | Records scope, decisions, progress, failures and recovery; never grants permission |
| Scientific knowledge | Original sources, revisions, reviewed notes and evidence locators | Preserve provenance; distinguish original text, personal inference and generated text |
| Conversation history | Bounded application session data | Helps resolve a question; never substitutes for source evidence or authorization |

For project recovery, [REFACTOR_STATUS.md](docs/REFACTOR_STATUS.md) is the single current-state entry. It should remain short: current increment, user authorization reference, branch/baseline, decision/task links, latest applicable verification, unresolved issues and the next action. Store detailed history in the change and Git rather than continually growing duplicate state files.

Before ending an implementation session, persist:

- What actually changed and what remains unfinished.
- The precise resume point and any interrupted operation.
- Final content/commit identity for each applicable verification receipt.
- Actual commands/environment, outcomes and unverified behavior.
- Known limitations and the reason for a blocked condition.
- Any new user constraint, with its scope and direct reference.

On resume:

- Read instructions -> status -> relevant plan increment -> current OpenSpec artifacts -> live Git/code -> verification receipts.
- Treat old hashes, branch state, service availability and source paths as snapshots; refresh relevant facts.
- If authorization is unclear, continue independent read-only preparation and request only the missing decision.
- If a checked task lacks required evidence or the code changed afterward, reopen the affected verification.
- If scope changed, reconcile proposal/design/delta requirements/tasks and status before dependent implementation.

Keep project records in Git free of source excerpts, credentials, private absolute paths and raw session logs. Detailed runtime fixtures belong in a reviewed local artifact root excluded from source commits. Verify exclusion before creating private records; do not assume a directory is ignored.

## 11. Verification and workflow consistency audit

### 11.1 Outcome vocabulary

| Outcome | Meaning |
| --- | --- |
| PASS | A named check ran on identified content and met its condition |
| FAIL | A named check ran and did not meet its condition |
| BLOCKED | A required check/action could not run; state the cause and consequence |
| NOT_APPLICABLE | The check/action is outside this increment, with a reason |

Use PLANNED, ACTIVE, VERIFYING, COMPLETE and DEFERRED for work disposition, not as verification results. COMPLETED DOCUMENTATION is not COMPLETED IMPLEMENTATION. A blocked live adapter check cannot be converted into PASS by a fake test. An expected pre-fix failure is baseline evidence, not a regression fix.

### 11.2 Verification receipt

Each implementation receipt should identify increment/change, tested commit or content hashes, baseline, environment, allowed inputs, commands, results, retained artifacts, skipped/blocked checks, recovery evidence and manual acceptance. Logs alone do not prove which content was tested.

Inspect tests, plugins, subprocesses and tools for side effects before execution. Prevent or avoid forbidden cleanup; retain fixtures. Do not run the normal full suite first and inspect its effects afterward. R01 selects the usable strategy instead of importing a runner or adding a dependency merely because another project used it.

A documentation-only change needs link/structure/scope review, not unrelated application tests. Formal OpenSpec validation is a separate check and must be labeled BLOCKED when its CLI is unavailable.

### 11.3 Audit dimensions

| Audit | Question | Failure handling |
| --- | --- | --- |
| Scope | Does every change belong to the authorized increment? | Remove the change from this increment's scope without deleting unrelated work; re-scope separately |
| Authority | Are user instructions distinguishable from generated plans and memory? | Stop the affected action; locate or request missing authorization |
| Dependency | Are entry conditions satisfied by evidence? | Keep the dependent action pending; finish independent work |
| Contract | Do proposal, design, delta specs, implementation, API, UI and tests agree? | Reconcile intended behavior and affected checks |
| State | Do tasks/status match actual files and Git? | Correct the record; do not fabricate completion |
| Evidence | Does each PASS identify what ran on final content? | Re-run affected verification or mark it unavailable |
| Data | Are source revision, domain, review state and evidence/test isolation preserved? | Reject contaminated or ambiguous intake/publication |
| Recovery | Can failure/interruption preserve and restore a usable state? | Keep migration/publication readiness incomplete |
| Privacy | Are logs, fixtures and published docs within the permitted input/destination? | Stop exposure and correct the affected artifact safely |
| Delivery | Are commit, push, merge and release accurately separated? | Report actual delivery status and do not advance |
| Memory | Can another session resume without hidden chat-only state? | Update the authoritative handoff links and unresolved items |
| Proportionality | Does a mechanism solve a demonstrated problem at personal-use scale? | Simplify the proposal before implementing it |

### 11.4 Scenarios the workflow must handle

Audit the normal completion path and these disruptions:

- A session ends with partially edited files and no commit.
- A user narrows scope while implementation is running.
- Two records disagree about the current increment or acceptance.
- A dependency or service is unavailable after deterministic checks pass.
- A test or plugin would delete temporary files.
- A real corpus or professional annotation has not been provided.
- Index publication or schema migration stops between storage steps.
- A completed check's content is later edited.
- New files contain private source paths or material.
- A push is not authorized or is rejected because of divergence.
- An earlier increment is reopened by a later regression.
- An optional experiment is deferred without pretending that required behavior passed.

Planning review tests whether the rules cover these scenarios. Implementation review must also exercise the relevant actual behavior. A same-agent review is not described as an independent review.

## 12. Program completion and the first next step

The program is complete only when the required refactoring increments satisfy their exits, source integration respects its boundaries, the final personal-use scenarios pass, and the owner accepts the real domain workflow. Optional research experiments can remain explicitly deferred. Engineering readiness and professional usefulness are separate conclusions.

The first implementation step is R01 only. Its initial work packet is: refresh Git/runtime/tooling, map startup/configuration and evaluation contracts, design the retained-artifact verification path, and reproduce the relevant baseline failures. It does not authorize migrating the vault, swapping models, pushing or starting R02.

This plan's current delivery state and the next authorized action are maintained in [REFACTOR_STATUS.md](docs/REFACTOR_STATUS.md).
