---
name: sdlc-development
description: Prepare Engineering implementation plans and guide controlled application changes, unit tests, build verification and code review from approved SDLC inputs.
---

# Development and Implementation Planning

This package provides development expertise. The orchestrator owns lifecycle,
revision enforcement, approvals, persistence, identity and ownership. Use its documented
CLI operations; never edit lifecycle metadata, approve on a person's behalf or invent
an independent audit. The package manifest identifies its version, owner, compatible
validation contract and supported stages. Record the resolved version and immutable instruction
fingerprint in every generated or reviewed artifact. Pinning reproduces instructions,
not LLM output.

Legacy requests retain their recorded workflow and instruction pins. Do not reinterpret
an old combined plan as independent QA approval or rewrite an approved artifact; use
the orchestrator's explicit compatibility/reconciliation path when authorized.

## Document templates and validation

Use `implementation-plan` for Engineering plans and `code-review` for source-bound reviews.
Resolve each template using `sdlc.py templates <template-id>` before drafting. The
pinned catalog owns document headings, their order and optional sections; use the returned
scaffold rather than creating a second layout here. Domain guidance below supplies
content expertise, not a competing structure. Deterministic writers record the exact
template ID, version and digest. Existing validators remain authoritative for structured
fields and governance; template, skill and CLI versions are independent. Preserve legacy
artifacts and their historical pins instead of adding provenance retrospectively.

## Engineering track authority

The Engineering and QA tracks reference the same approved Analysis baseline and have
independent ownership and revisions. The orchestrator creates tracks only after explicit
Analysis advancement; creating or assigning one does not start work. Resolve the active
track before acting, asking one question when ambiguous. This package does not launch
parallel agents or a separate runtime.

## Prepare the implementation plan

Read the exact approved Technical Design and its approved Analysis dependency, plus
project conventions, existing code, dependencies and build/test configuration. Inspect
before proposing files or technology. Explain unavailable context. Use
[planning and review guidance](references/planning.md) for task and check details.

Prepare a small ordered plan with stable task IDs, prerequisites, observable outcomes,
Analysis FR/AC references, allowed project-relative paths and named unit/build checks.
Keep unit tests alongside development. QA owns its strategy, functional scenarios,
automation and integration/UI checks separately; do not bundle their approval into the
Engineering Plan. An incomplete QA track does not block initial Engineering plan
approval, but it must block a claim of integrated verification. Carry blocked behavior and
unresolved decisions explicitly. An acknowledged uncertainty is not authorization to
choose a business rule. Stop a task when its behavior depends on that missing decision.

Persist the plan through the orchestrator as an immutable revision in
`engineering-baselines/<hash>/`, containing human-readable `implementation-plan.md` and its
`artifact.json` traceability contract. Do not copy skill implementations into requests.
Present scope, boundaries, risks, dependencies and checks in business-oriented language.
Obtain human approval of the exact Engineering plan, then wait for separate explicit
advancement. That decision does not approve QA scenarios or automation.
Approval of a plan does not start coding.

## Execute within the approved boundary

Begin only after the orchestrator verifies the approved plan and the human explicitly
authorizes development. Reopen the persisted context when resuming. Implement tasks
sequentially, with unit tests, using native host tools inside the approved project paths.
Keep original user work and requirements artifacts intact. Do not stage, commit, push,
install remote skills, create external infrastructure or launch parallel agents as a
side effect. Workstreams are independent workflow contexts, not permission to run AI
work automatically. In forked requests, leave reserved `qa/` automation files to QA;
Engineering source/task boundaries must not overlap that namespace.

Use literal argument arrays for named approved checks; do not evaluate generated shell
strings. Run checks through the orchestrator's evidence operation so actual command,
exit status, output and source fingerprint are retained. Commands may have side effects;
an approved path list and fingerprint comparison are audit controls, not an operating
system sandbox. Host permissions remain necessary. If a check cannot run, report
`not_run` or `blocked`; never substitute a claimed pass or an unrelated check.

For a task, distinguish implemented code from verified behavior. Keep code, unit tests,
build results, defects and FR/AC links inspectable. Changes outside the allowed paths,
new dependencies, changed architecture, environment changes or new behavior require
impact review and the relevant revised approval before continuing. Do not silently
expand the approved scope or rewrite frozen artifacts.

## Review and remediation

Provide the actual change set, plan traceability, unit/build results and known issues
for code review. A self-review is not independent review. Human code approval is bound
to the reviewed code revision; subsequent advancement remains a separate instruction.
Human code approval concerns the Engineering change and unit/build evidence; it does
not approve separate QA automation. QA obtains its own human automation review.
Before integrated verification, require the current Engineering outputs and approvals
plus current QA scenarios, automation approval and actual execution evidence through
the orchestrator join. Never report an incomplete QA track as successful verification.
Security Review follows the integrated verification conditions.

When Security or Testing returns findings, link each fix to its original finding and
affected task/requirement. Reproduce the failure where possible, make only authorized
corrections, rerun affected checks and regression checks, and preserve earlier evidence.
New code invalidates earlier source-bound verification. Do not declare a finding fixed
merely because a patch was written; retest and obtain the required review.

## Semantic conformance (governance 0.1)

Before implementing an unresolved edge, seek clarification. An uncertainty ACK, absence
of an implementation, or a positive acceptance scenario does not authorize a negative
runtime restriction. Use only approved requirements or specifically authorized Design
limitations. Keep `limitation_refs` in Plan, implementation/code review and Security
artifacts; definitions remain solely in the immutable Design. Plan tasks/checks implementing
an exception reference its `limitations` IDs and affected requirements without promoting
blocked coverage. Every authorized limitation needs implementation and check traceability.

During Code Review examine consequential negative conditions, defaults, validation and
unsupported-operation responses against their authority. Persist `conformance` in the
existing source-bound implementation artifact: `reviewer`, `independence` (author_review
or independent), `summary`, `reviewed_categories` (negative_condition, default, validation,
unsupported_operation), and `behaviors`. Each material behavior records `category`,
`path`, `line`, `observable_behavior`, `authority: {kind: requirement|limitation|none,
id: ID|null}`, `assessment: conforms|unsupported`, and `reason`. Source locations must
refer to current Engineering files. An empty inventory requires an honest assessment
that no material behavior exists; never omit a discovered restriction to pass a gate.

A review finding with no authority is `unsupported` and blocks code approval. Request
correction or upstream clarification; do not relabel it as technical validation. Review
new source revisions afresh, even if old test output was green. Record actual reviewer
independence; self-review is not independent. Prefer a fresh read-only reviewer when
available, followed by human code approval. The CLI validates recorded evidence and
binding, not the semantic truth or completeness of the inventory.
