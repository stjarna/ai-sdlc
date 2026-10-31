# AI-SDLC — Codex instructions

## Purpose

Develop a **reusable Git-native AI SDLC orchestration skill**, not the demo application as a deliverable. The skill coordinates discovery, business refinement, functional analysis, solution design, implementation, independent QA, human approvals, traceability and release readiness.

## Mandatory reading

- [Documentation index](docs/README.md) and [complete CLI inventory](docs/cli-reference.md): current human navigation and operation coverage.
- [Runtime management](docs/runtime-version-management.md): default versus effective request/track authority, explicit promotion, matching context receipts and inspected recovery.
- [README](README.md): human-facing orientation, setup and current capability boundaries.
- [Working specification](docs/specification.md): [D] accepted decisions, [P] PoC limitations, [T] target architecture, [O] open design.
- [Architecture decision register](docs/decisions/architecture-decisions.md): rationale and intentionally deferred approaches.
- [PoC scope ADR](docs/decisions/0001-repository-and-poc-scope.md).

Read these before changing code. Flag conflicting requirements instead of silently choosing an interpretation. Do not mistake illustrative YAML for finalized schema.

## Boundaries

- `orchestrator/`: generic orchestration skill, templates, workflows, deterministic scripts, tests. No To-Do, Node.js or due-date logic here.
- `examples/todo-app/`: preserved verified Task Due Date Management acceptance and rehearsal helper. Keep its `project/`, `acceptance-evidence/` and `acceptance-inputs/` byte-identical to the preservation manifest. Run dependency setup and new tests only in the ignored `.run/` copy via the documented helper. The date-only to date-and-time change remains future work.
- `docs/`: durable architecture and decisions. The implemented request lifecycle runs from Discovery through approved Business/Functional Analysis into independently owned Engineering and QA tracks, ending at `verified`. Read the [workflow overview](docs/workflow.md), [engineering contracts](docs/engineering.md) and [work-track contracts](docs/work-tracks.md) before Engineering/QA changes. Earlier increment descriptions in the specification/register preserve historical scope; they are not the current feature matrix. Story decomposition, Release Planning and deployment are not implemented. Approval and advancement require separate explicit human instructions. The external local identity profile stores declared, unauthenticated identity and informational roles, not RBAC. Setup/editing requires supplied user declarations.

## Working rules

- Inspect repository and documentation first; propose a small implementation slice with files and acceptance checks before major coding.
- Git/Markdown/YAML are authoritative, not chat history. **No separate checkpoint.md subsystem.**
- Interactive Discovery keeps identity/lifecycle in `metadata.yaml`, the original idea in `idea.md`, and authoritative append-only history in `discovery.yaml`. Use deterministic updates with revisions and operation IDs; preserve source evidence and do not reinterpret AI assumptions as user facts.
- Ownership is separate from approval and advancement. New requests have a declared requester as owner; handoff retains accountability while awaiting separately confirmed assignment. Legacy owner evidence must be unambiguous or explicitly supplied. No automatic assignees, notifications or next-stage execution.
- Installed governed writes require the effective pinned runtime and its declared fresh-context receipt. Default update/rollback never promotes requests. Do not mix instructions/CLI versions; require a fresh host conversation after a runtime-context change. Legacy initial binding does not invent historical provenance.
- Preserve stable Epic IDs; Story/Release ID conventions are target design, not implemented operations. Use deterministic scripts for paths, state and schema mutation; explicit impact review on changes.
- Human approval is required for business refinement, design and implementation plan, QA scenarios and automation review, human code review and release approval. Never fabricate approvals or test results.
- New explicitly advanced Analysis forks independent Engineering and QA tracks. QA strategy/scenarios derive from Analysis without Design. Engineering Plan/code review is distinct from QA scenario/automation review; actual verification joins current approved outputs and evidence. Work tracks do not automatically run parallel AI agents. Legacy sequential records are retained without migration.
- Future Release design permits only completed `ready_for_release` Epics selected by PO/PM and treats Release as an independent entity. Do not claim or implement those stages as part of a documentation change; the executable lifecycle ends at `verified`.
- Published template/domain versions are immutable. Placeholder changes need a new pin, matching named generation context, literal-safe one-pass substitution, and legacy/read/approval regression checks. See [template contracts](orchestrator/templates/README.md).
- Read [domain coverage](orchestrator/domain-skills/README.md) before changing early-phase guidance or provenance. The seven packages own specialist content; the coordinator retains gates and deterministic writers record exact new pins.
- Specialist skills are independently owned and must be approved and version-pinned. Bundled `orchestrator/domain-skills/` packages demonstrate the domain-team model locally; their reviewed catalog pins are required and supporting specialties are roadmap outlines. Do not execute arbitrary remote skills. Critical security controls must be enforced by tools and infrastructure, not prompts alone.
- Never add secrets or internal Alza/company information to this public repository. Do not push, merge, deploy or run destructive commands without appropriate user authorization.

## Verification and handoff

- Bootstrap developer tests with `python3 -m venv .venv` and `.venv/bin/python -m pip install -r orchestrator/requirements.txt`.
- Run `.venv/bin/python -m unittest discover -s orchestrator/tests -v` for the full deterministic regression suite; see [test contracts](orchestrator/tests/README.md) for scope. Fixture decisions are fictional, not human approval or browser acceptance.
- Run `.venv/bin/python examples/todo-app/demo.py verify` for read-only archived-demo integrity. Never regenerate historical evidence or run setup/tests in the archive itself.
- For documentation-only work, verify commands against source/help, check links/anchors and render graphics/Markdown at a normal reading width. Do not edit pinned domain packages or templates merely to fix prose; consumed versions are immutable.
- Inspect the complete diff and `git diff --check`. Report actual executed checks and limitations; never turn an unexecuted check into a pass.
- Preserve unrelated working-tree changes. Do not stage, commit or push unless explicitly authorized. Keep temporary validation assets in ignored scratch space; do not add videos, dependencies, secrets or local identity profiles to Git.
