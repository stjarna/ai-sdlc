# Plan, checks and review guidance

Use the pinned `implementation-plan` and `code-review` templates for layout. The
following topics explain engineering judgment, not additional required sections. Existing
validators own structured fields and lifecycle operations.

## Useful plan contents

- State the approved Design revision and Analysis baseline used. Describe any existing
  code, build environment or standards inspected and the limits of that inspection.
- Give each task a stable ID, purpose, Analysis FR/AC links, dependencies, allowed paths,
  expected result and verification. Keep dependency order executable without a task
  depending on itself or on an unapproved future task.
- Keep tasks small enough to inspect and test, grouping production code with its unit
  tests. Distinguish environment preparation, implementation, regression and review.
- Declare Engineering unit/build checks with literal executable/argument arrays and
  requirement coverage; QA declares integration/UI checks in its own artifacts. Explain the expected observable result in the plan prose.
  Existing project tools and lockfiles take precedence over invented infrastructure.
  The plan may describe test seams or interface coordination without owning QA scenario
  expectations. QA expectations come from approved Analysis.
- Identify excluded behavior and requirements blocked by unresolved questions. A complete
  reference list does not prove complete behavioral coverage.

Changing assertions to match a defect is a scope or test-review decision, not routine
remediation. When coordinating with QA, UI/E2E assertions must exercise the intended interaction;
merely labelling a unit command `ui` does not make it a UI test. The integrated PoC
requires a real UI check; report a non-UI applicability limitation rather than inventing
a passing browser result. An applicability exception remains future work.

## Review inputs and outcomes

Review against the exact approved Analysis, Design and Plan; inspect the actual source
changes and developer tests, not only the author's summary. Engineering plan/code
approval and QA scenario/automation approval remain separate decisions. Consider behavior and error paths,
component boundaries, compatibility, dependency changes, maintainability, sensitive data
handling and assertion quality. Findings need severity, affected requirement/task,
file or evidence reference and a concrete expected correction. Record unavailable
checks and residual risks. Keep recommendations separate from actual human decisions.

Before presenting code for human approval, check that named unit/build results apply
to the current source fingerprint. After any remediation, retain earlier failing evidence
and obtain new source-bound results. No review or passing check authorizes release,
deployment, a Git action or broader implementation on its own.

## Possible later supporting skills

These are roadmap outlines, not installed or executable dependencies:

| Supporting area | Intended contribution |
|---|---|
| Language / Framework Guidelines | Version-specific idioms, error handling and framework constraints |
| Clean Code & Refactoring | Safe structural change with characterized behavior |
| Code Review | Independent inspection and actionable finding conventions |
| Unit Testing | Boundary, failure-path and regression assertions alongside code |
| Dependency Management | Locked versions, compatibility and dependency changes |
| CI/CD Practices | Reproducible checks and external delivery controls |

Engineering Enablement would own releases, evaluation scenarios, compatibility checks,
deprecation and rollout guidance for this package. Project requests consume a pinned
approved release; changing shared instructions does not silently alter existing artifacts.
