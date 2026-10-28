---
name: sdlc-testing
description: Derive requirement-linked verification scenarios, review test coverage and report actual integration or UI test evidence for an approved SDLC engineering change.
---

# Testing and Verification

Use this skill for verification and final-verification work coordinated by the
[SDLC orchestrator](../../skill/SKILL.md). Package version, domain owner, supported
stages, dependencies and compatibility are declared in `manifest.yaml`. The responsible
owner is QA / Quality Engineering. This package supplies testing expertise; only the
orchestrator's deterministic operations persist artifacts, record decisions or advance
lifecycle. Do not create an alternative audit or approval mechanism.

Read the exact approved Analysis, Technical Design and Implementation Plan selected by
the current handoff, plus implementation changes and developer unit/build evidence.
Load the package versions pinned for this work. Do not substitute a mutable draft or
an old conversation for an approved input. Missing or changed authority blocks a claim
of readiness; ask the orchestrator to reconcile it.

## Scope and review

Derive meaningful scenarios from active, approved FR/AC and observable outcomes. Include
relevant failure paths, boundaries and regression risks. Keep scenario IDs stable and
link each planned check to acceptance criteria and its test implementation. Record
coverage gaps and excluded or blocked behavior explicitly. An acknowledged open question
is still unresolved; do not choose its behavior to make a test executable.

Review developer unit coverage where useful. Unit tests belong alongside development;
do not establish a second unit-test implementation stream. Run integration and UI/E2E
verification sequentially after development and required review. This increment does
not orchestrate parallel application development, QA or security work.

Present scenarios for explicit human QA review before automation, and have generated
automation reviewed for assertions, isolation and robustness before treating it as
accepted verification. Preserve these decisions through supported orchestrator operations;
authorization to run a command is not a substitute for a required content review.

## Execute and assess

Use only checks authorized by the approved plan and host permissions. The orchestrator
runs declared argument arrays and records command, working directory, exit status,
output and source fingerprint. Do not manufacture execution evidence or manually turn
an unsuccessful result into a pass. Missing tools, unavailable environments or omitted
checks remain blocked or not run, with their impact explained.

A passing exit code is command evidence, not proof of assertion quality or meaningful
business coverage. Inspect test behavior. A UI/E2E claim needs actual user-interface
interaction and observable assertions; an HTTP-only check is integration/API evidence.
See [verification guidance](references/verification.md) for traceability and reports.

When defects are found, preserve the failing evidence, identify affected requirements
and return the findings for controlled remediation. Re-run affected and required
regression checks on the new source revision. Earlier evidence remains historical and
must not authorize a newer implementation.

For final verification, bind the report to the current source fingerprint, approved
inputs, actual unit/build/integration/UI results and current security review. Describe
unresolved findings and unexecuted checks before recommending readiness. Report what
was tested, what failed and what remains unknown. A verification recommendation is not
human approval, release authorization or permission to deploy.

## Supporting skill roadmap

Scenario Design, Integration Testing, API Testing, UI Automation / Playwright, Test
Data Management, Accessibility Testing and Performance Testing are future specialist
extensions. This package currently provides high-level guidance for these concerns;
it does not claim that separate implementations, tools or runtime integrations exist.
