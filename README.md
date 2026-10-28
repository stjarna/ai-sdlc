# AI-SDLC

**Status:** initial Discovery management increment implemented for review. `new`,
`open`, and `validate` are available; conversational refinement, the remaining
SDLC workflow, and the To-Do demonstration are not yet implemented.

A reusable Git-native AI-powered SDLC orchestration capability for existing software projects. It coordinates Epic/Story/Release workflows, human approvals, traceability and approved versioned specialist skills; it does not replace project management tools or own every engineering standard.

## Documentation and Codex handover

- [Working specification](docs/specification.md) — detailed design; **[D]** accepted, **[P]** PoC boundary, **[T]** target, **[O]** open.
- [Architecture decision register](docs/decisions/architecture-decisions.md) — rationale, rejected/deferred approaches and open implementation questions.
- [PoC scope decision](docs/decisions/0001-repository-and-poc-scope.md).
- [Codex instructions](AGENTS.md) — required reading and safe implementation workflow.

## Repository layout

- `orchestrator/` — generic Discovery skill, template, deterministic operations and tests; later workflows remain planned.
- `examples/todo-app/` — future small pre-existing Node.js/JavaScript To-Do application with in-memory state, **not** part of the orchestrator's generic logic.
- `docs/` — versioned architecture and decisions.

## Demonstration scope

Implement **Task Due Date Management** in an existing minimal To-Do application. Then change the requirement from date-only to date-and-time and show impact analysis across requirements, design, implementation tasks and tests. Keep the reusable orchestrator independent of the app's business domain and tech stack.

## Development approach

Read `AGENTS.md`, the specification, and the decision register before changes.
The approved first increment covers local Discovery management only; new Epics
start in `discovery` and no lifecycle transitions are implemented.

See [the operation contract](orchestrator/scripts/README.md) for environment setup,
the minimal schema, CLI examples, diagnostics, and limitations; see
[the skill entrypoint](orchestrator/skill/SKILL.md) for conversational routing and
[the tests](orchestrator/tests/README.md) for the automated verification command.
The CLI never stages, commits, or pushes. Later increments and the demonstration
remain subject to separate review.

Contributions must not include secrets, proprietary company material or unapproved external skills. This public repository is an experimental case-study PoC, not a production deployment system.
