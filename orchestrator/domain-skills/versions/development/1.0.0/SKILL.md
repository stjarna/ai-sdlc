---
name: sdlc-development
description: Prepare traceable implementation plans and guide controlled application changes, unit tests, build verification and code review from approved SDLC inputs.
---

# Development and Implementation Planning

This package provides development expertise. The orchestrator owns lifecycle,
revision enforcement, approvals, persistence, identity and ownership. Use its documented
CLI operations; never edit lifecycle metadata, approve on a person's behalf or invent
an independent audit. The package manifest identifies its version, owner, compatible
orchestrator and supported stages. Record the resolved version and immutable instruction
fingerprint in every generated or reviewed artifact. Pinning reproduces instructions,
not LLM output.

## Prepare the implementation plan

Read the exact approved Technical Design and its approved Analysis dependency, plus
project conventions, existing code, dependencies and build/test configuration. Inspect
before proposing files or technology. Explain unavailable context. Use
[planning and review guidance](references/planning.md) for task and check details.

Prepare a small ordered plan with stable task IDs, prerequisites, observable outcomes,
Analysis FR/AC references, allowed project-relative paths and named verification checks.
Include unit tests and build checks alongside development; integration and UI/E2E checks
belong to the subsequent sequential verification activity. Carry blocked behavior and
unresolved decisions explicitly. An acknowledged uncertainty is not authorization to
choose a business rule. Stop a task when its behavior depends on that missing decision.

Persist the plan through the orchestrator as an immutable revision in
`engineering-baselines/<hash>/`, containing human-readable `content.md` and its
`artifact.json` traceability contract. Do not copy skill implementations into requests.
Present scope, boundaries, risks, dependencies and checks in business-oriented language.
Obtain human approval of the exact plan, then wait for separate explicit advancement.
Approval of a plan does not start coding.

## Execute within the approved boundary

Begin only after the orchestrator verifies the approved plan and the human explicitly
authorizes development. Reopen the persisted context when resuming. Implement tasks
sequentially, with unit tests, using native host tools inside the approved project paths.
Keep original user work and requirements artifacts intact. Do not stage, commit, push,
install remote skills, create external infrastructure or launch parallel application
workstreams as a side effect.

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
Leave integration/UI verification and Security Review to their sequential activities.

When Security or Testing returns findings, link each fix to its original finding and
affected task/requirement. Reproduce the failure where possible, make only authorized
corrections, rerun affected checks and regression checks, and preserve earlier evidence.
New code invalidates earlier source-bound verification. Do not declare a finding fixed
merely because a patch was written; retest and obtain the required review.
