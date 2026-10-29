# AI-SDLC

**Status:** Discovery management, Interactive Discovery Increment 2 and Discovery
Completion/Business Refinement Increment 3 are implemented. Procedural Business
Approval Gate Increment 4 is implemented, with immutable baselines and
separate advancement to `ready_for_analysis`. Increment 5 implements AI-assisted Functional
Analysis for review: drafting, traceability, refinement and recoverable history. Increment 6 adds
shared procedural approval and separate advancement to Technical Design readiness.
The [sequential engineering slice](docs/engineering.md) adds pinned Architecture, Development, Testing and Security skills, design/plan/code approval gates and source-bound verification through `verified`. The [verified due-date demonstration](examples/todo-app/README.md) is preserved with real human decisions and reproducible rehearsal instructions. Story decomposition and Release execution remain planned.
Shared native conversational guidance and thin Codex / Claude Code discovery adapters
are provided. Codex is the PoC acceptance target; Claude Code runtime remains an
unverified portability target.

A reusable Git-native AI-powered SDLC orchestration capability for existing software projects. It coordinates Epic/Story/Release workflows, human approvals, traceability and approved versioned specialist skills; it does not replace project management tools or own every engineering standard.

## Documentation and agent setup

- [Working specification](docs/specification.md) — detailed design; **[D]** accepted, **[P]** PoC boundary, **[T]** target, **[O]** open.
- [Architecture decision register](docs/decisions/architecture-decisions.md) — rationale, rejected/deferred approaches and open implementation questions.
- [PoC scope decision](docs/decisions/0001-repository-and-poc-scope.md).
- [Codex instructions](AGENTS.md) — required reading and safe implementation workflow.
- [Interactive Discovery](docs/interactive-discovery.md) — start, persist, resume and
  review a conversation; includes a fictional demonstration and manual evaluation guide.
- [Business Refinement](docs/business-refinement.md) — complete/reopen Discovery,
  draft and revise `business.md`, review traceability and recover interrupted writes.
- [Business Approval](docs/business-approval.md) — explicit PO decisions, unresolved
  item acknowledgement, immutable baselines and separate advancement; includes manual acceptance.
- [Functional Analysis](docs/functional-analysis.md) — draft from approved immutable
  business input, refine and review; includes the To-Do manual acceptance scenario.
- [Agent setup and shared skill](orchestrator/skill/README.md) — Codex and Claude Code
  native entries using one workflow, conversation policy and CLI.
- [Cross-agent conversational evaluation](docs/agent-ux-evaluation.md) — manual scenarios
  and evidence requirements for each CLI and IDE surface.

## Use the assistant

Open this complete checkout in Codex or Claude Code and describe the business idea or
request you want to continue. Optional explicit entries are `$sdlc` / `/skills` in Codex
and `/sdlc` in Claude Code. Specify the target project when it is outside this checkout.
The agent handles CLI operations and revision parameters internally, presents concise
business reviews, and provides technical evidence when requested. Separate explicit
approval and advancement decisions remain required.

## Repository layout

- `orchestrator/` — generic Discovery, Business Refinement and Approval skill, templates,
  deterministic operations, Functional Analysis and tests; later workflows remain planned.
- `examples/todo-app/` — preserved verified in-memory due-date application, SDLC baselines/evidence and rehearsal helper, **not** part of the orchestrator's generic logic.
- `docs/` — versioned architecture and decisions.

## Demonstration scope

The completed **Task Due Date Management** acceptance demonstrates initial optional future-date assignment in a minimal seeded in-memory application. Its complete verified request, approvals and evidence are preserved under [examples/todo-app](examples/todo-app/README.md). The later date-only to date-and-time impact-analysis scenario remains future work; it was not implemented or approved by this acceptance. The orchestrator stays independent of this domain and stack.

## Development approach

Read `AGENTS.md`, the specification, and the decision register before changes.
New Epics start in `discovery`. Increment 2 adds a separate authoritative
`discovery.yaml`; the initial idea and metadata remain intact during conversational
updates. Increment 3 requires explicit Requester completion before Business
Refinement, retains every business draft revision and supports source reconciliation.
Existing requests without history remain valid.
Increment 4 records declared, unauthenticated PO identity and explicit decisions.
Approval keeps the Epic in refinement. Advancement requires a separate operation;
the PoC does not technically guarantee human-only authorization.
Increment 5 starts `functional_analysis` only from a valid approved business handoff.
The AI drafts semantics; the CLI preserves revisions and validates structure/references.
Analysis approval and separate advancement are implemented in [Increment 6](docs/analysis-approval.md);
Technical Design and Engineering/QA execution through `verified` are implemented; see the [domain/work-track contracts](docs/work-tracks.md).

See [the operation contract](orchestrator/scripts/README.md) for environment setup,
the minimal schema, CLI examples, diagnostics, and limitations; see
[the skill entrypoint](orchestrator/skill/SKILL.md) for conversational routing and
[the tests](orchestrator/tests/README.md) for the automated verification command.
The CLI never stages, commits, or pushes. Later increments and the demonstration
remain subject to separate review.

Contributions must not include secrets, proprietary company material or unapproved external skills. This public repository is an experimental case-study PoC, not a production deployment system.

The [six-command SDLC interface and local identity profile](docs/command-ux.md) support
Codex `$sdlc <command>` and Claude `/sdlc <command>`, with natural language as an
alternative. The profile is an unauthenticated local declaration outside the repository;
its roles are informational and approval still requires an explicit human decision.

[Ownership and handoff management](docs/ownership.md) adds `inbox`, `pending assignments`
and explicit `assign`. New requests have a declared requester as owner; pending handoffs
retain accountability until a confirmed transfer. Assignment does not approve content,
advance lifecycle or start the next stage.

The domain packages are independently versioned local instruction examples. Human approvals and separate advancement remain mandatory; Engineering and QA can progress independently and join for verification; no parallel AI execution is automatic. There is no new runtime, external AI API, remote registry or automatic Git operation.

The [Engineering/QA work-track extension](docs/work-tracks.md) atomically forks new
Analysis advancements into independently owned Engineering and QA responsibilities.
QA functional expectations derive from Analysis before Design; scenario and automation
approvals are separate from Engineering Plan/code approval. Integrated verification
rejects incomplete or stale QA. Existing acceptance artifacts are not migrated; explicit
pre-development adoption preserves history and requires replacing an unapproved combined
Plan with separate current Engineering and QA artifacts.

New Engineering/QA artifacts use canonical physical filenames with explicit manifest0.2; legacy content.md baselines and approvals remain unchanged. See [Artifact storage and names](docs/artifact-names.md).

[Final preparation and proposed commits](docs/demo-finalization.md) records executed checks, preservation evidence, limitations and the approval boundary. No commits or pushes are automatic.

Human-readable documents use [versioned, domain-owned artifact templates](orchestrator/templates/README.md).
Inspect the pinned catalog with `.venv/bin/python -B orchestrator/scripts/sdlc.py templates`.
Templates define layout; skills provide domain judgment and existing validators enforce
structural/governance contracts. Historical artifacts are never retrospectively templated.

[External installation and adoption](docs/installation-and-adoption.md) keeps a pinned
runtime outside an existing application, registers a user-scoped Codex loader and
provides read-only adoption preflight. The [before/after demo runbook](docs/existing-project-demo.md)
covers real product baselines, UI capture and governed evidence without changing the
preserved historical demonstrator.
