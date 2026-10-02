# Refactoring Status and Resume Point

Updated: 2026-10-02, America/New_York

This is the current-state entry for [the refactoring plan](../REFACTOR_INTEGRATION_PLAN.md). User instructions grant authority; this file records that authority and never creates it.

## Current work packet

| Field | Current value |
| --- | --- |
| Packet | PLAN-00: write and review the refactoring/integration plan |
| Authorized scope | Markdown planning and project recovery records in Insight; workflow consistency review |
| User reference | 2026-10-02 request to proceed one item at a time, using software-engineering and personal-use standards, with refactoring, boundaries, implementation planning, memory and consistency review |
| Planning disposition | COMPLETE |
| Implementation disposition | NOT_STARTED |
| Active implementation increment | NONE |
| Branch | `codex/refactor-integration-plan` |
| Application baseline | `abb59d7515119e9dcc4ee13bc307cbdc4bed8841` |
| Delivery scope | Three new Markdown files; existing application/specification/source contents remain unchanged |
| Remote delivery | Not authorized; retain the planning commit locally |
| Next eligible increment | R01, after the owner instructs work to start |

## Authoritative references

- [Plan, contracts and increment sequence](../REFACTOR_INTEGRATION_PLAN.md).
- [Planning consistency review and verification limits](reviews/2026-10-02-refactor-plan-consistency.md).
- [Current main behavior specifications](../openspec/specs).
- Existing user working instructions and any applicable future `AGENTS.md` take precedence over this record.

No implementation OpenSpec change exists for this program yet. The roadmap is not a completed proposal/design/delta-specification/task package. A future implementation packet must use the applicable workflow and its live CLI/schema instructions.

## Implementation ledger

| Increment | Disposition | Completion evidence |
| --- | --- | --- |
| R01 | PLANNED | None; baseline and safe verification setup are first |
| R02 | PLANNED | None |
| R03 | PLANNED | None |
| R04 | PLANNED | None |
| R05 | PLANNED | None |
| R06 | PLANNED | None; real source-root/corpus scope must be named |
| R07 | PLANNED | None; adapter contracts and optional experiments are separate tracks |
| R08 | PLANNED | None; engineering and professional acceptance are separate |

## Known constraints and verification gaps

- OpenSpec CLI is unavailable in the current shell; formal validation is BLOCKED. No CLI was installed in PLAN-00.
- The ordinary local Python environment lacks required application/test dependencies. PLAN-00 is a documentation-only delivery and does not claim application tests ran on it.
- Prior syntax/lint, pure-memory tests and GitHub CI apply to the investigation/application baseline. They do not qualify future refactoring code, adapters or professional correctness.
- Existing 144 file-mode differences are unrelated work. They must not enter this packet's staged diff or later refactoring commits accidentally.
- Real Ollama/Milvus, complex PDF parsing and cancellation propagation require later real checks.
- There is no established real meteorology corpus or annotated domain test set. The twelve Atmos-RAG seeds are not formal evaluation data.
- Filesystem deletion is prohibited, including temporary/test cleanup. A usable retained-artifact strategy must be established before affected tests run.
- Original Atmos-RAG/Obsidian material is preserved. No wider scan, source rewrite, migration, model download, cloud call or global Codex-memory update is authorized by PLAN-00.

## Resume instructions

1. Read applicable user/project instructions, this file, the relevant plan increment, and any current OpenSpec artifacts.
2. Inspect live Git, configuration/code and referenced evidence. Treat dates, branches, hashes and availability in this file as snapshots.
3. If the owner authorizes R01, prepare only its work packet. Follow the plan's entry/exit and side-effect-review rules; use routine judgment within that scope.
4. If no implementation instruction has arrived, keep implementation NOT_STARTED. Do not infer permission from this plan, its completion, or a future push authorization.
5. Before each session ends, update the active scope, unfinished work, verification identity/limits and precise next action; keep details in the current change and receipts.

## Locating the planning delivery commit

The delivery commit is identified in Git history rather than copied into a self-referential tracking commit:

```sh
git log -1 --format='%H %s' -- REFACTOR_INTEGRATION_PLAN.md docs/REFACTOR_STATUS.md docs/reviews/2026-10-02-refactor-plan-consistency.md
```

At later increments, record existing relevant commit references and receipt links. Do not create an additional commit solely to record a document's own new hash.
