# Engineering implementation review — Task Due Date Management

Status: prepared for explicit human code approval. Not approved, not advanced.
Development was explicitly authorized by `$sdlc start engineering` after separate Plan
approval and readiness advancement. Implementation follows the approved Technical Design
and Engineering-only Plan. Development 1.1.0 instruction pin is recorded by the CLI.

## Implemented tasks and scope

T-001: dependency-free package.json, local run documentation, named check runner.
T-002: strict real-calendar validation, exact YYYY-MM-DD preservation, seeded in-memory
repository, isolated unit assertions. Reads return copies; separate repositories isolate state.
T-003: loopback ephemeral HTTP server, fixed asset routes, JSON task read and initial-date
assignment, bounded UTF-8 JSON/shape checks, controlled errors, same-origin/Host checks,
CSP/nosniff/no-store headers. No credentials, arbitrary file serving or remote service.
T-004: plain labelled browser form, optional undated display and exact assigned-date output,
safe text rendering, disabled in-flight submission and explicit save-versus-refresh feedback.
T-005: completed unit/build runner and actual source-bound check evidence for review.

Only the declared paths were used. No QA source, dependencies or application package
installation. No orchestrator implementation edits or Git operations. Application source
is the 11 files listed in the accompanying acceptance review evidence. The actual new-file
diff is retained outside the project at evidence/engineering-implementation-source.patch.

## Actual Engineering checks

C-UNIT: passed, exit 0; 40 tests, 40 passed, 0 failed/skipped/cancelled.
C-BUILD: passed, exit 0; syntax validated for seven JS/MJS files, fixed asset references,
local imports and dependency-free package scripts. This is validation, not a bundling build.
Both ran through the deterministic CLI against this exact application source fingerprint.
Their immutable evidence retains literal arguments, actual output/hash and Analysis links.
No HTTP integration or browser test has run. Unit/build evidence cannot prove the full
user-facing flow or the effectiveness of all security controls. Code review is pending;
this agent's source inspection is not independent human review.

## Preserved uncertainty and limitations

Past-date behavior remains deferred pending support consultation; FR-003 stays blocked.
Changing/clearing an assigned date remains undefined. The approved demonstrator returns
an explicit unsupported response with unchanged state for these paths, never a product
acceptance/rejection rule. Unit boundary checks do not resolve or cover the missing policy.
UTC reference day is only a testing convention; no new timezone/today-date requirement.
Seeded fixtures are preconditions, no CRUD/completion; reminders/notifications excluded.
Data is in-memory and resets on restart; no persistence/accounts/sync or production claim.

QA strategy/scenarios were separately approved by the human during Development and remain
in Test Design. No QA advancement, automation approval or execution is inferred. Current
QA integration/UI evidence and explicit QA completion are required before the join. Security
Review, remediation if needed, final verification and all relevant human gates remain ahead.

## Decision

Review the actual source diff and current unit/build evidence. Explicit human implementation
approval must bind this source and acknowledge the inherited unresolved topics. Approval
does not advance Engineering; await separate authorization before Verification. No release,
deployment, Git action or final product readiness is authorized by this review.

## Requested remediation — review findings R1 and R2

Human feedback: “Yes, fix both findings, add regression tests and rerun verification.
Present the results for review before approval.” Recorded through engineering-request-changes.

R1 (P3), public/app.js: task-keyed DOM rows retain existing undated-task forms, draft
values and active controls across unrelated saves. When a successful assignment removes
the currently focused form, focus moves to its task heading. No new task business behavior.

R2 (P3), public/app.js: a failed mutation response triggers read-only reconciliation,
not an automatic retry. If the requested date is present, report confirmation; if the
task remains undated, retain the draft and permit manual retry with the useful original
error; if a different date is present, report it without claiming the attempted save
succeeded. If readback also fails, disable resubmission and disclose an unknown outcome
until reload. A known successful mutation is rendered even if subsequent refresh fails.

Added eight controller-level regressions in the existing test/unit.test.mjs, exercising
the actual browser script via Node vm with small DOM/fetch doubles: other-task draft/focus
preservation, focused-control removal, lost successful response, failed readback with
retry blocked, confirmed no-save/manual retry, saved result with failed refresh, retained
server diagnostic and different-date reconciliation. Six initial regressions failed on
the original implementation before remediation; earlier failing evidence is retained.
Final full Engineering suite: 40 passed, 0 failed; build validation passed, both exit 0
and recorded against this exact source revision through check-run. These are unit-level
regressions, not real HTTP/browser or independent QA evidence.

Only public/app.js and test/unit.test.mjs changed for remediation. Incremental diff:
evidence/engineering-ui-remediation-source.patch. Full updated source diff:
evidence/engineering-implementation-v2-source.patch. Earlier source diff, immutable
implementation baseline, failing/passing evidence and human decisions remain available.
QA stage, artifacts, ownership and scenario approval remain unchanged. Application
source change is visible in the shared execution fingerprint; no QA automation exists.
No dependency installation, approval, advancement or implementation repository edits.
This revised implementation requires a fresh explicit human code review decision.
