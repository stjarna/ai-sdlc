# QA Test Strategy — Task Due Date Management

Status: proposed for human QA scenario review. No approval, automation or execution.
Instruction package: Testing 1.1.0, exact pin recorded by the orchestrator.
Authority: immutable approved Functional Analysis baseline 0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598.
The Business dependency and acknowledged unresolved items remain authoritative through
that baseline. This strategy does not depend on Technical Design, an Engineering Plan,
the historical combined plan, prototype behavior or implemented code.

## Objective and scope

Verify the two specified acceptance paths: an undated task is permitted, and a user can
assign a supplied future calendar date to an undated task with the exact day/month/year
retained. Reference FR-001/FR-002 and AC-001/AC-002; do not create another requirements
source. Use existing or seeded tasks solely to satisfy the approved use-case precondition.
Task creation/completion/deletion, reminders and notifications are not introduced here.

FR-003 is blocked. The past-date question U-001/AQ-001 remains deferred pending support
consultation. Changing/clearing an already assigned date is AQ-002, still undefined.
No functional test may choose acceptance/rejection, date replacement or date removal
as an expected product outcome. A technical demo's unimplemented-path response is not
an answer to these questions and cannot be treated as FR-003 acceptance coverage.

## Risk-based cases and data

TC-001 covers absence of an assigned date as a valid task state. TC-002 covers exact
initial future-date assignment, parameterized with an ordinary future date and future
month/year/leap-day examples where applicable. These are test data, not a product date
range, timezone rule or future-only restriction. TC-003 uses two tasks to observe correct
task selection and combine exact assignment with the other task remaining undated.
TC-004/TC-005 explicitly document blocked past-date and changing/clearing paths.

Choose dates demonstrably in the future under a controlled reference clock for repeatable
checks. A test reference day is a fixture, never a new business rule; no production UTC,
per-user timezone, date-range limit, display locale or today-date policy is inferred.
Compare calendar day/month/year, not an assumed timestamp or a required display format.
Do not manufacture an expected answer to a missing rule to make the suite green.

## Verification levels

Development owns unit tests and build checks. QA may review their coverage but will not
create a second unit-test stream or bundle its approval into the Engineering Plan.
Later integration checks will exercise actual application boundaries to assign and read
back the selected task's calendar date, and observe a permitted absent date value. Any
API shape or storage representation is an implementation detail inspected later, not
the functional oracle. Cross-process persistence is not part of the approved criteria.

Later UI/E2E checks must open the real running interface, identify the intended existing
task, leave one task undated, and perform initial assignment through real controls.
Assert observable resulting state matching AC-001/AC-002. HTTP calls alone, category
labels, code inspection or screenshots alone do not establish UI acceptance.
Automation wiring and tool choices will be prepared after scenario approval and separate
advancement, using available approved interfaces without replacing these expectations.

## Reviews, execution and evidence

Present this Strategy and the independently versioned Test Scenarios together for one
explicit human scenario approval, acknowledging all inherited unresolved items. That
approval does not advance QA or approve automation. Engineering Plan/code approval is
independent. Concrete QA automation later stays under its approved qa/ paths and receives
its own human review, exact source binding and separate advancement.

Do not execute integration/UI checks until current Engineering implementation is approved
and made available, and QA scenario/automation approvals and readiness are valid. Use
actual named qa-check-run operations, preserving case/FR/AC links, reviewed sources,
commands, exit status, output and available browser evidence. Failed, unavailable,
blocked, skipped or not-run results cannot become passes. Inspect assertion quality;
structural validation is not business correctness or executed verification.

Report defects with the case, requirement, reviewed source, expected/observed behavior,
reproduction and evidence. Keep requirements/scenarios authoritative rather than altering
expectations to match a defect. Explicit remediation and new current evidence are needed
for affected Engineering changes. Require explicit QA completion before the joined gate;
missing QA is not successful verification. Security review remains a separate downstream
responsibility; technical security-negative checks are selected later against approved
interfaces and controls and do not redefine functional acceptance.

## Current limitations and handoff

No application or QA automation exists yet; no case has executed and no result is passed.
The coverage disposition called implemented in the structural schema means planned
scenario coverage only, not implemented code or successful test execution. The three
specified cases cover AC-001/AC-002; both unresolved business topics remain explicit.
Do not claim full product completeness, retention guarantees, security certification,
release approval or deployment readiness. Engineering artifacts, approvals and ownership
are unchanged by this QA drafting activity.
