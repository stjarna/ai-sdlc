# QA execution report — incomplete

Authorized local npm ci installed two locked QA packages, with scripts/browser download
disabled. QA source and lockfile remained unchanged. Existing Chrome 156.0.8078.74 was
used with Playwright 1.64.1; no browser installation or application code edit.

QA-INTEGRATION: PASSED, exit 0, 6/6 actual HTTP tests passed.
QA-UI: FAILED, exit 1. First four browser scenarios passed: undated reload and all three
initial exact-date assignments/readbacks. Scenario 5 failed; scenarios 6–8 did not run.

Finding QA-F-001, P3, R1 focus restoration regression:
During the real-browser R1 scenario, the other task's draft and active-input preservation
assertions passed. Saving the second task then displayed its assigned date, but focus
was not on that task's heading, so qa/ui.mjs line 88 failed. This is not an accepted pass.
The application disables the submit button before its response handling; render later
checks document.activeElement to decide whether to restore focus. Losing focus when the
button is disabled is a likely cause; the DOM test double did not model browser blur.
A source correction and actual browser re-verification are required before closing R1.
Do not weaken the approved expected focus behavior merely to match this failure.

Screenshot and trace: project/requirements/REQ-0001-task-due-date-management/test-evidence/
qa-ui-07be7cc3-6df7-4e23-9cee-8f47ff045c7b/5-failed.png and 5-trace.zip.
CLI evidence binds actual sources, approvals, literal commands, exit/output/hash and
all referenced artifact hashes were verified (6 integration + 15 UI evidence files).

Both unresolved business topics remain open, not tested as defined product behavior.
Engineering remains in Verification with unchanged approved source. QA remains ready for
Verification, incomplete, with no explicit completion. No Security or later advancement.
No source, automation, baseline approval, Git staging/commit/push or orchestrator edits.
No fixes applied. Await explicit Engineering remediation authorization and renewed reviews.
