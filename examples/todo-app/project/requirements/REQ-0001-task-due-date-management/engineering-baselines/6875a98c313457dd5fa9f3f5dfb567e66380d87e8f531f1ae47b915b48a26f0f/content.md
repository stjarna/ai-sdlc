# Engineering Implementation Plan — Task Due Date Management

Status: replacement draft for explicit human Engineering Plan review. Not approved.
This draft responds to `$sdlc start engineering` after authorized work-track adoption.
It authorizes neither lifecycle advancement nor coding, installation or test execution.

## Authority and preserved history

Approved Technical Design: 97e48e3c6e0fcfdcb07373d0a2cb420bbb67f374e9599a588516765206db899d
Approved Functional Analysis: 0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598
Analysis handoff: human-working-app-analysis-advance-33dd5e96-60d2-4eb2-ad14-7de118c23927
Historical unapproved combined Plan: a3edcd499adfe7464a0beb524121eee26296247f51b7af32d0a72ac0e363a4e7

The approved Design, decisions and original combined Plan remain immutable evidence.
The current approved Design governs technical choices despite its original draft-status
wording. This replacement separates Engineering duties from independent QA; it does not
amend Design or approve any QA artifact. Development 1.1.0 is resolved from the approved
catalog; the immutable instruction digest is recorded by the CLI.

## Inspected context and runtime

The disposable project currently contains only requirements artifacts: no application,
build configuration or existing source conventions. Node v25.9.0 is installed. Use its
built-in HTTP and node:test modules plus plain HTML/CSS/JavaScript, matching the approved
Design. No third-party Engineering dependencies, package installation, browser download,
global tools, external infrastructure or orchestrator changes are needed. package.json
will contain local start/unit/build scripts. There is no dependency tree to install.
This observed runtime is a local acceptance environment, not a production recommendation.

Playwright, any QA-specific manifest/lockfile, HTTP/browser automation and their runners
belong to the separately reviewed QA automation under reserved qa/. This Plan selects
no QA dependency version or QA installation. The old combined Plan's proposed Playwright
pin is historical only; it is not carried forward as authorization. The Design's browser
verification intent remains and must be fulfilled by QA before integrated verification.

## Implemented subset and uncertainty

FR-001/AC-001: initial assignment of a supplied future calendar date to an existing
undated seeded task, preserving the exact day/month/year in state and display.
FR-002/AC-002: an existing task may remain undated; dueDate is null and the UI makes the
absence clear. Coverage dispositions denote planned implementation, not completed work.
Seeded tasks meet the existing-task precondition, not a new task-creation requirement.
No task CRUD/completion, reminders, notifications, accounts, synchronization or persistence.

U-001/AQ-001 stay deferred pending support consultation. FR-003 remains blocked: no
product acceptance or rejection policy for past dates. AQ-002 remains undefined:
changing or clearing an assigned date is not an implied capability or prohibition.
As approved in Design, outside-subset attempts (past/today or reassignment/clear) receive
an explicit demonstrator-not-implemented response with unchanged state. This technical
boundary must never be presented as the unresolved product rule or FR-003 coverage.
Do not proceed with a task that requires selecting a missing business decision.

## Ordered tasks, source boundary and outcomes

T-001 — Create package.json, scripts/ and README.md with local startup and named check
commands. Outcome: dependency-free application/check entry points; no install.

T-002 — After T-001, implement src/domain.mjs, src/repository.mjs and test/unit.test.mjs.
Outcome: strict real-calendar strings, seeded isolated in-memory tasks, nullable dates
and initial assignment with exact preservation, accompanied by isolated unit assertions.

T-003 — After T-002, implement src/http.mjs and src/server.mjs. Outcome: an ephemeral
127.0.0.1 listener, GET /api/tasks, narrow initial-assignment mutation and fixed static
routes. Export isolated server construction for later independent QA. Bound body sizes,
validate content type/keys/task identity, reject foreign origins on mutation, provide
controlled errors without stack leakage, CSP and nosniff. Never expose requirements/,
identity, evidence or arbitrary paths. Do not create integration automation in Engineering.

T-004 — After T-003, implement public/ assets. Outcome: labelled date input for an
undated task, exact assigned date display, explicit undated state, safe textContent
rendering and controlled feedback. No edit/clear control for assigned dates. Display
server UTC reference day as the accepted testing convention, not a timezone/product rule.
No browser runner or QA automation is included in this task.

T-005 — After T-004, finish scripts/, README.md and test/unit.test.mjs. Outcome: complete
unit/build runner, real results and source diff ready for human Engineering code review.
Every task links FR-001, FR-002, AC-001 and AC-002; detailed safe paths and dependencies
are in the structured contract. The union of those paths is the full Engineering source
boundary. Leave reserved qa/ and requirements artifacts untouched by application edits.

## Interfaces and demonstration limitations

Task records have id, seeded title and dueDate null or YYYY-MM-DD. Keep calendar strings
unchanged rather than converting them into instants; reject impossible calendar values
without JavaScript rollover. Isolate reference-day injection for deterministic unit tests.
The server and browser exchange same-origin JSON and display actual in-process state.
A later independent read must see the selected date. Fixed static routes serve only
public assets. In-memory data resets on process restart: demo limitation, no retention rule.
No sensitive or real-user data, remote deployment or authentication claim is introduced.

## Named Engineering checks — planned, not run

C-UNIT: literal argv [node, scripts/check.mjs, unit], cwd '.', timeout 60 seconds.
Use node:test with isolated fixtures/reference-day injection. Assert exact calendar date
preservation, permitted absence, real-calendar validity and task isolation; include
applicable month/year/leap-day examples as test data, not new business range rules.
Check controlled demonstrator unsupported responses without asserting a product policy.

C-BUILD: literal argv [node, scripts/check.mjs, build], cwd '.', timeout 60 seconds.
Syntax-check JS/MJS and verify fixed asset/import references and package script targets.
This is a dependency-free validation build, not a bundling, HTTP or browser result.

Run these only during separately authorized Development, through check-run to preserve
actual exit status, output, requirement links and current source fingerprint. Nonzero,
unavailable or unexecuted checks never count as passing. Keep outputs out of hashed
source and preserve each orchestrator evidence record. No checks have run for this Plan.

## Human gates and independent QA join

First obtain explicit Plan approval, acknowledging all inherited uncertainty. Approval
leaves Engineering in Implementation Planning. Wait for separate readiness advancement,
then separate explicit Development start before changing application files. Engineering
ownership remains David Krzystek pending separate assignment; no transfer is inferred.

After implementation, present actual diff, task completion and current unit/build evidence
for separate human source-bound code approval. Self-review is not independent review.
Code approval does not approve QA automation; lifecycle advancement remains separate.
QA strategy/scenarios remain drafts until their own human decision, and automation has
its own review gate. This Plan neither edits those artifacts nor defines their oracle.

Integrated verification requires current approved Engineering implementation, separately
approved QA strategy/scenarios and automation, actual integration and browser evidence,
and explicit QA completion. Missing QA blocks the join. No passing unit/build result
substitutes for working application acceptance or Security Review. Later Security Review
must inspect actual source and evidence; findings require explicit linked remediation,
relevant renewed reviews/checks and retained prior results. Final verification binds the
exact baselines, source, QA and Security evidence and still preserves unresolved topics.
No release, deployment, Git operation or security certification is authorized.

## Decision requested

Approve this Engineering-only Plan with past-date behavior deferred/blocked and changing
or clearing assigned dates undefined. QA approval is a separate decision. No coding,
dependency installation, advancement or automatic next-stage work follows this approval.
