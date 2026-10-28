# AI-SDLC

**Status:** design / pre-implementation proof of concept. The orchestration skill and To-Do demonstration are not yet implemented.

A reusable Git-native AI-powered SDLC orchestration capability for existing software projects. It coordinates Epic/Story/Release workflows, human approvals, traceability and approved versioned specialist skills; it does not replace project management tools or own every engineering standard.

## Documentation and Codex handover

- [Working specification](docs/specification.md) — detailed design; **[D]** accepted, **[P]** PoC boundary, **[T]** target, **[O]** open.
- [Architecture decision register](docs/decisions/architecture-decisions.md) — rationale, rejected/deferred approaches and open implementation questions.
- [PoC scope decision](docs/decisions/0001-repository-and-poc-scope.md).
- [Codex instructions](AGENTS.md) — required reading and safe implementation workflow.

## Repository layout

- `orchestrator/` — future generic skill, workflows, templates, scripts and tests.
- `examples/todo-app/` — future small pre-existing Node.js/JavaScript To-Do application with in-memory state, **not** part of the orchestrator's generic logic.
- `docs/` — versioned architecture and decisions.

## Demonstration scope

Implement **Task Due Date Management** in an existing minimal To-Do application. Then change the requirement from date-only to date-and-time and show impact analysis across requirements, design, implementation tasks and tests. Keep the reusable orchestrator independent of the app's business domain and tech stack.

## Development approach

1. Open this repository in Codex and ask it to read `AGENTS.md`, `docs/specification.md` and the decision register, then summarize its understanding **without editing**.
2. Agree on minimal command interface, YAML schema, state transitions and approvals.
3. Implement the first orchestration workflow in small reviewable increments.
4. Build the To-Do example separately and validate end-to-end SDLC flow and release-readiness evidence.

Contributions must not include secrets, proprietary company material or unapproved external skills. This public repository is an experimental case-study PoC, not a production deployment system.
