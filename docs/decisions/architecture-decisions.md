# Architecture decision register

Companion to [the working specification](../specification.md), not a replacement. Based on design discussion, 2026-10-28. `[D]` accepted; `[P]` PoC boundary; `[T]` target; `[O]` open.

| ID | Decision | Status |
|---|---|---|
| 001 | One generic orchestration skill coordinates domain-specific, approved external skills, rather than owning every engineering rule. | D |
| 002 | Git-native local-first Markdown/YAML and source code are authoritative. Stable IDs; no separate checkpoint subsystem. | D |
| 003 | Epic → Story, independent from module/team mapping; Stories can change with traceable impact review. `move-story` is limited to the same Epic, preserving Story ID and parent; cross-Epic moves must be rejected without mutation. | D |
| 004 | Requester confirmation is not PO approval. Discovery saves locally without automatic commit/push. PO approves the business artifact before functional analysis. Approvals bind to particular revisions. | D |
| 005 | Analysis produces functional requirements, acceptance criteria and scenarios. Prototypes and screenshots are versioned references, not self-authorizing specifications. | D |
| 006 | Flexible Definition of Ready allows owned nonblocking warnings; blocking unknowns prevent advancing. | D |
| 007 | Agent must inspect existing code before solution design. Tech Lead approves design and implementation plan before coding. Major changes require reassessment. | D |
| 008 | Engineering and QA proceed in parallel. QA approves scenarios and reviews automated tests. Neither QA scenario signoff nor test generation blocks initial engineering plan approval. | D |
| 009 | Independent AI reviewer should operate in an isolated read-only context, followed by human review and actual quality evidence. Self-review is not independent. | D |
| 010 | Reproducible app/test environment (Docker for PoC); coding agent works on host. Environment belongs to project/module, not each Story. | D/P |
| 011 | Epic readiness, business Release Planning and joint Release Readiness are distinct. Release may contain multiple complete Epics; deployment is external. Only ready Epics in PoC release plans. | D/P |
| 012 | Security and governance are cross-cutting; permissions, sandbox, CI and Git protections enforce critical rules beyond prompt instructions. | D |
| 013 | Federated ownership of specialist skills with central governance; immutable revision references, compatibility review and controlled upgrades. | D/T |
| 014 | Confirmed PoC scenario (ADR-0001): public repo with generic `orchestrator/` and separate `examples/todo-app/`; existing minimal in-memory Node.js To-Do app, Task Due Date Management and a date-only to date-and-time requirements change. | D/P |
| 015 | First approved increment: generic `new`, read-only `open` and `validate`; schema 0.1 with metadata separate from idea content. Allocate highest existing local Epic number + 1, retaining cancelled IDs; reject duplicates and inconsistent records. Create only `discovery`; conversational refinement, Requester confirmation and lifecycle transitions follow later. See [operation contract](../../orchestrator/scripts/README.md). | D/P |
| 016 | Approved Increment 2: adaptive clarification in the host skill; authoritative append-only typed history in optional `discovery.yaml`, separate from unchanged original idea and metadata. Deterministic updates use artifact revisions, a common local write lock, atomic publication and persisted operation IDs for idempotent retries. Sourced human decisions resolve assumptions/questions; review is derived from history and does not approve or advance the Epic. See [Interactive Discovery](../interactive-discovery.md). | D/P |
| 017 | Approved Increment 3: explicit Requester completion of Discovery, `ready_for_refinement`, AI-drafted `business.md` from confirmed Discovery, revision-controlled human refinement, read-only review, explicit Discovery reopening and source reconciliation. Exact document bytes and attribution remain recoverable in an Epic-local history. No business approval or Functional Analysis in this increment. See [Business Refinement](../business-refinement.md). | D/P |
| 018 | PoC business approval is deferred to Increment 4: explicit operation, declared approver identity, exact artifact revision, timestamp, decision, append-only audit, immutable approved baseline and separate lifecycle transition. Procedural approval does not technically prevent an unrestricted AI agent from invoking approval operations and must not be called guaranteed human-only authorization. No cryptographic receipts or signing infrastructure. | D/P |

## Rejected / deferred
- **Rejected:** storing state only in chat; `checkpoint.md`; giant bootstrap Story; automatic release of a ready Epic; Release nested under Epic; treating self-review as independent; copying specialist skills into orchestrator.
- **Deferred:** greenfield bootstrap; corporate skill catalog and identity infrastructure; Jira/Teams integration; incomplete-Epic release planning; production deployment; unverified cross-host portability.

## Remaining open design work
- Host catalog installation and cross-host invocation beyond the checkout-based CLI.
- Business approval records/revision binding and subsequent lifecycle transition; no approval operation is part of Increment 3.
- FR/AC/TC references and test-to-requirement traceability without duplicated authorities.
- Concurrent ID allocation, migration and compatibility policy.
- Skill discovery and version manifest implementation for the demo.

**Handover:** Codex should first read the complete [specification](../specification.md), identify inconsistencies and propose the smallest working increment, before implementation.
