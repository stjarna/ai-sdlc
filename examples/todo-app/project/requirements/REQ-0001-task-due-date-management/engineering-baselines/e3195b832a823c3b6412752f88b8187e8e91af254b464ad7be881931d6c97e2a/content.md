# Engineering implementation review — focus remediation QA-F-001

Status: source remediation prepared for renewed human code approval. Not approved.
Human explicitly authorized Engineering remediation, regression tests and renewed code
review while preserving QA evidence. verification-remediate links the actual failed
QA-UI check and returns Engineering to Development; old decisions/baselines remain.
The approved Technical Design and Engineering-only Plan are unchanged. Development
1.1.0 instruction pin is recorded by the CLI. All T-001..T-005 remain complete.

## Scope and changes

Only public/app.js and test/unit.test.mjs changed from the last approved source.
QA-F-001: disabling a focused submit button moved focus before render checked whether
to restore it. The prior DOM test double did not model that behavior. Its updated disabled
setter now models this blur and reproduced the exact focus assertion failure: 39 of 40
unit tests passed, 1 failed, before modifying application behavior. Evidence retained.

The submit button now remains focusable during the pending request and exposes
aria-disabled=true. The existing row.busy guard rejects duplicate submissions before
any mutation. On successful assignment, the existing renderer restores focus to the
task heading if focus is still inside that form, and preserves user focus on another
task. After failure, busy/ARIA state resets; an unknown save outcome still actually
disables retries until reload. No event bypass creates a second mutation.

The original focus-removal and other-task-draft tests remain. A new gated pending-request
regression verifies focused-button retention, ARIA state, duplicate-submit suppression
and eventual heading focus. Other save-reconciliation regressions remain unchanged.
These controller tests execute the actual browser script with DOM/fetch doubles, not a
real browser. Real Chrome confirmation is pending; QA-F-001 is not declared closed.

## Actual current Engineering verification

C-UNIT passed, exit 0: 41 tests, 41 passed, 0 failed/skipped/cancelled.
C-BUILD passed, exit 0: syntax of seven JS/MJS files, local imports, fixed assets and
package scripts. Both ran through check-run against this exact source fingerprint.
Earlier reproduction failure and all prior successful/failing evidence are retained.
Incremental actual diff: evidence/engineering-focus-remediation.patch.

## Preserved functionality, authority and boundaries

The small dependency-free local HTTP/browser application implements initial exact
future-calendar-date assignment and permitted undated tasks only, as in the approved
Analysis/Design/Plan. Seeded data is in-memory and resets on server restart. No CRUD,
completion, reminders, notifications, persistence, accounts or synchronization are added.
The accepted UTC reference day remains a testing convention, not a product business rule.
Past-date behavior (U-001/AQ-001, FR-003) stays deferred/blocked pending support consultation.
Changing or clearing assigned dates (AQ-002) remains undefined. Demonstrator unsupported
responses define no product acceptance/rejection policy. No business question is resolved.

QA source, scenario/automation approvals, ownership and append-only QA history/evidence
are unchanged. The previous integration pass and UI failure belong to the earlier source;
they cannot serve as verification of this changed source. No QA check was rerun. Preserve
those outputs and obtain renewed source-bound QA execution only after fresh human code
approval and separate Engineering advancement. QA stays ready for Verification, incomplete.
No dependencies, Engineering Plan, QA automation or orchestrator implementation changes.
No Git stage/commit/push, automatic advancement or Security/final readiness claim.

## Human review requested

Review the exact source diff and current Engineering evidence. Obtain fresh explicit
implementation approval with both unresolved topics acknowledged. Approval leaves
Engineering in Development; subsequent Verification advancement is a separate decision.
QA failure remains historical evidence, and real browser re-verification remains required.
