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
- `examples/todo-app/`: future minimal existing in-memory Node.js app to demonstrate Task Due Date Management and a date-only to date-and-time change.
- `docs/`: durable architecture and decisions. Discovery management is implemented; Interactive Discovery (`discovery-update`) is implemented for review. The remaining lifecycle is still in design.

## Working rules
- Inspect repository and documentation first; propose a small implementation slice with files and acceptance checks before major coding.
- Git/Markdown/YAML are authoritative, not chat history. **No separate checkpoint.md subsystem.**
- Interactive Discovery keeps identity/lifecycle in `metadata.yaml`, the original idea in `idea.md`, and authoritative append-only history in `discovery.yaml`. Use deterministic updates with revisions and operation IDs; preserve source evidence and do not reinterpret AI assumptions as user facts.
- Stable Epic/Story/Release IDs; deterministic scripts for paths, state and schema mutation; explicit impact review on changes.
- Human approval is required for business refinement, design and implementation plan, QA scenarios and automation review, human code review and release approval. Never fabricate approvals or test results.
- QA test design runs independently and in parallel with engineering work, joining at verification.
- Only completed `ready_for_release` Epics may enter Release Planning in the PoC, selected by PO/PM. Release is an independent entity.
- Specialist skills are externally owned and must be approved and version-pinned. Do not execute arbitrary remote skills. Critical security controls must be enforced by tools and infrastructure, not prompts alone.
- Never add secrets or internal Alza/company information to this public repository. Do not push, merge, deploy or run destructive commands without appropriate user authorization.

## First Codex task
**Read** the specification and decision register. Return a concise understanding of the architecture, PoC scope, remaining open decisions and proposed first small implementation increment **without editing files yet**.
