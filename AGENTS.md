# AI-SDLC — Codex instructions

## Purpose
Develop a **reusable Git-native AI SDLC orchestration skill**, not the demo application as a deliverable. The skill coordinates discovery, business refinement, functional analysis, solution design, implementation, independent QA, human approvals, traceability and release readiness.

## Mandatory reading
- [Working specification](docs/specification.md): [D] accepted decisions, [P] PoC limitations, [T] target architecture, [O] open design.
- [Architecture decision register](docs/decisions/architecture-decisions.md): rationale and intentionally deferred approaches.
- [PoC scope ADR](docs/decisions/0001-repository-and-poc-scope.md).

Read these before changing code. Flag conflicting requirements instead of silently choosing an interpretation. Do not mistake illustrative YAML for finalized schema.

## Boundaries
- `orchestrator/`: generic orchestration skill, templates, workflows, deterministic scripts, tests. No To-Do, Node.js or due-date logic here.
- `examples/todo-app/`: preserved verified Task Due Date Management acceptance and rehearsal helper. Keep its `project/`, `acceptance-evidence/` and `acceptance-inputs/` byte-identical to the preservation manifest. Run dependency setup and new tests only in the ignored `.run/` copy via the documented helper. The date-only to date-and-time change remains future work.
- `docs/`: durable architecture and decisions. Discovery, Business Refinement and procedural Business Approval through ready_for_analysis are implemented. Functional Analysis drafting/refinement/review is implemented in Increment 5. Increment 6 shares the Business gate infrastructure with Analysis approval and separate advancement to ready_for_technical_design. The engineering/QA fork now creates independently owned work tracks after explicit Analysis advancement; Engineering and QA synchronize only for verified execution. The existing engineering slice supports Technical Design, Implementation Planning, controlled development, verification and Security review through `verified`; Stories and Release execution remain in design. Read [engineering contracts](docs/engineering.md) and [work-track contracts](docs/work-tracks.md) before engineering or QA work. Approval and advancement require separate explicit human instructions; declared identities are unauthenticated. The shared six-command UX uses an external local identity profile for routine attribution; setup/editing requires supplied user declarations, and roles are informational rather than RBAC.

## Working rules
- Inspect repository and documentation first; propose a small implementation slice with files and acceptance checks before major coding.
- Git/Markdown/YAML are authoritative, not chat history. **No separate checkpoint.md subsystem.**
- Interactive Discovery keeps identity/lifecycle in `metadata.yaml`, the original idea in `idea.md`, and authoritative append-only history in `discovery.yaml`. Use deterministic updates with revisions and operation IDs; preserve source evidence and do not reinterpret AI assumptions as user facts.
- Ownership is separate from approval and advancement. New requests have a declared requester as owner; handoff retains accountability while awaiting separately confirmed assignment. Legacy owner evidence must be unambiguous or explicitly supplied. No automatic assignees, notifications or next-stage execution.
- Stable Epic/Story/Release IDs; deterministic scripts for paths, state and schema mutation; explicit impact review on changes.
- Human approval is required for business refinement, design and implementation plan, QA scenarios and automation review, human code review and release approval. Never fabricate approvals or test results.
- New explicitly advanced Analysis forks independent Engineering and QA tracks. QA strategy/scenarios derive from Analysis without Design. Engineering Plan/code review is distinct from QA scenario/automation review; actual verification joins current approved outputs and evidence. Work tracks do not automatically run parallel AI agents. Legacy sequential records are retained without migration.
- Only completed `ready_for_release` Epics may enter Release Planning in the PoC, selected by PO/PM. Release is an independent entity.
- Specialist skills are independently owned and must be approved and version-pinned. Bundled `orchestrator/domain-skills/` packages demonstrate the domain-team model locally; their reviewed catalog pins are required and supporting specialties are roadmap outlines. Do not execute arbitrary remote skills. Critical security controls must be enforced by tools and infrastructure, not prompts alone.
- Never add secrets or internal Alza/company information to this public repository. Do not push, merge, deploy or run destructive commands without appropriate user authorization.

## First Codex task
**Read** the specification and decision register. Return a concise understanding of the architecture, PoC scope, remaining open decisions and proposed first small implementation increment **without editing files yet**.
