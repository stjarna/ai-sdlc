# Implementation Plan — Task Due Date Management PoC

Status: proposed for explicit human Plan and QA scenario approval. No application source,
package installation, generated automation or test execution is authorized by this draft.
The user's "$sdlc start" answers the preceding offer to prepare this plan; it does not
mean development-start or approval. Work remains sequential.

## Authority and fixed scope

Approved Technical Design: 97e48e3c6e0fcfdcb07373d0a2cb420bbb67f374e9599a588516765206db899d
Approved Analysis baseline: 0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598
Analysis advancement: human-working-app-analysis-advance-33dd5e96-60d2-4eb2-ad14-7de118c23927

Read these exact immutable inputs before implementation. Architecture/Security choices
were approved for the PoC. Development 1.0.0 and Testing 1.0.0 instruction pins are recorded
on this plan. Their supporting specialty outlines are not installed tools.

Implement only initial future-date assignment to an existing seeded task and permitted
undated task state. Retain all inherited uncertainty: past-date policy stays deferred,
FR-003 stays blocked, and changing/clearing assigned dates stays undefined. Neither
acknowledgement nor a passing demo check defines these missing product rules.

## Runtime and dependency proposal

Use observed Node.js v25.9.0/npm 11.12.1 with built-in HTTP and node:test; plain HTML/CSS/JS;
no production third-party package, database, account, synchronization or notifications.
Use exact development dependency playwright@1.64.1, as observed in the registry during
planning, and commit no changes. Its dependency tree/integrity will be captured by the
application package-lock.json during authorized setup. Use the already installed Chrome
156.0.8078.74 at /Applications/Google Chrome.app/Contents/MacOS/Google Chrome; do not
silently download browsers or change the host runtime. This records the local acceptance
environment, not a production runtime recommendation or frozen toolchain guarantee.

After explicit development start only: create the approved package manifest and use
npm install --ignore-scripts --no-audit --no-fund --save-dev --save-exact playwright@1.64.1,
with PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1. Installation is limited to this disposable
project and its lockfile/node_modules. No global install, credentials, skill installation,
external infrastructure or orchestrator edits. A dependency incompatibility/advisory or
unavailable registry/browser is a reported blocker; do not switch versions or omit checks
without the necessary plan review.

## Ordered tasks and allowed source boundaries

T-001 — Prepare the local project manifest, exact development dependency/lockfile,
check runner and run instructions. Allowed: package.json, package-lock.json, scripts/,
README.md. References FR-001, FR-002, AC-001, AC-002. No preceding task.

T-002 — Implement calendar parsing, injected clock, task repository and initial-date
service together with domain unit tests. Allowed: src/domain.mjs, src/repository.mjs,
test/unit.test.mjs. Depends on T-001. References FR-001, FR-002, AC-001, AC-002.

T-003 — Implement the loopback HTTP server, route/static-asset allowlist and JSON adapter,
alongside real HTTP integration/security-boundary tests. Allowed: src/http.mjs,
src/server.mjs, test/integration.test.mjs. Depends on T-002. Same four references.

T-004 — Implement the minimal browser UI and the approved UI scenarios below as browser
automation. Allowed: public/, test/ui.mjs. Depends on T-003. Same four references.

T-005 — Finish the check runner/build integrity checks and run unit/build checks through
the orchestrator. Prepare actual file changes, task completion, test automation and
results for human code and automation review. Allowed: scripts/, README.md. Depends on
T-004. Same four references. Completion means review material is prepared, not that a
human review or approval has occurred.

The union of these paths is the complete application source boundary. Do not modify
requirements metadata/history/baselines directly. Do not add task CRUD/completion,
reminders, persistence, accounts or other business capabilities. A scope/design change
requires renewed upstream decisions instead of an improvised correction.

## Intended interfaces and demonstration boundary

Repository records contain id, seeded title, and dueDate null or YYYY-MM-DD. Persist only
in the running process. GET /api/tasks reads tasks; a narrowly validated JSON mutation
route performs initial future-date assignment. Static routes serve only the declared
index, stylesheet and browser script. Runtime server listens on 127.0.0.1 and an ephemeral
port; the standalone entrypoint reports its actual URL. Tests construct isolated servers.

Keep calendar strings unchanged, validating actual calendar dates without JS date rollover.
For tests inject a fixed reference day. The interactive UI displays the server's UTC
reference day as an explicit demonstration/testing convention, never a new business rule.
Use separate seeded tasks per scenario; provide an explicit undated state and initial
assignment form. After assignment show the exact date and no edit/clear controls.

A valid past/today date or an existing-date change/clear attempt receives an explicit
not-implemented-in-this-demonstrator response, with stored state unchanged. Do not label
that result "past dates forbidden" or imply a final product rule. Structural malformed
inputs, unknown IDs/routes and oversized bodies receive controlled errors. The app remains
a deliberately incomplete demonstrator of the approved acceptance subset, not a complete
To-Do product. Restarting discards task data; do not claim a retention requirement.

## QA scenarios proposed for approval before automation

TS-001 / AC-002 / FR-002 — With an undated seeded task, load the API and browser UI and
leave the date unspecified. Assert JSON dueDate is null, the UI explicitly shows no date,
and merely viewing/reloading does not assign one. No empty-date mutation is required.

TS-002 / AC-001 / FR-001 — For another undated task, select a known future calendar day,
fill the actual browser date field and submit through the real UI. Assert the displayed
day/month/year exactly match the selection, then independently read the API and reload
the UI to confirm the same in-process state. Assert the other undated task is unchanged.

TS-003 / AC-001, AC-002 — In unit tests, cover exact date preservation, absence as null,
valid calendar boundaries, impossible dates and malformed types, using an injected clock.
Cover nonexistent task identity and isolation of separate task records.

TS-004 / AC-001, AC-002 — Through real HTTP requests, verify undated and initial-assignment
results, response/content types, no hidden assignment on reads, exact readback and
controlled malformed/oversized JSON errors. Cleanly close every ephemeral server.

TS-005 / AC-001, AC-002 — Verify fixed-route/static-asset boundaries, traversal attempts,
foreign-Origin mutation rejection, request-size limits, security response headers and
safe rendering through text nodes. Check seeded titles resembling HTML/script appear as
literal text without execution, network egress or unsafe DOM insertion.

TS-006 / AC-001, AC-002 — Verify that the demonstrator identifies unsupported past/today
and reassignment/clear paths as unimplemented without silently changing state. This is
a harness boundary check only: it is NOT FR-003 coverage or a decision on AQ-001/AQ-002.
No test claims whether the final product should accept or reject a past date or allow edits.

TS-007 / AC-001, AC-002 — Inspect the exact locked development dependency tree with npm
audit, preserving actual registry output and exit status. Report advisory or availability
failures honestly; they are not passes and must not be bypassed to progress.

## Named deterministic checks

C-UNIT (unit): node scripts/check.mjs unit. Execute node:test domain tests (TS-003),
using isolated fixtures and clock, and retain real exit/output. No server/browser run.
C-BUILD (build): node scripts/check.mjs build. Syntax-check all declared JS/MJS source and
runners, verify static assets/import references and package/lock consistency; no bundler,
HTTP verification or browser launch is implied by the build result.
C-INTEGRATION (integration): node scripts/check.mjs integration. Execute actual HTTP
integration and security-negative scenarios TS-001, TS-002, TS-004, TS-005, TS-006.
C-DEPENDENCIES (integration): node scripts/check.mjs dependencies. Run npm audit --json
with the project lockfile and preserve actual results, including dev dependencies.
Nonzero audit/network errors remain failures, with no suppression or claimed clean scan.
C-UI (ui): node scripts/check.mjs ui. Launch installed Chrome through pinned Playwright,
start the real loopback application, navigate and exercise actual form interactions
TS-001/TS-002 and applicable TS-005/TS-006. Assert meaningful browser outcomes, not only
HTTP status or a screenshot. Browser launch failure is not a pass.

Only C-UNIT/C-BUILD execute in Development. After the human reviews actual code and
new automation, explicitly approves the exact implementation/source and separately
advances, execute C-INTEGRATION, C-DEPENDENCIES and C-UI sequentially in Verification.
A passing process exit is not a substitute for assertion quality; inspect actual results.

## Execution evidence and security review

All named checks use literal argv, cwd '.', per-check deadlines and no generated shell.
Record tool versions, scenario/requirement IDs, actual status, exit/output and source
fingerprint through check-run. Test outputs must not modify hashed source inputs.
Only test runners (never the application server) may additionally write fresh, uniquely
named output under this Epic's test-evidence/ directory. Store UI screenshots, browser
trace, check reports and their checksums there; print relative evidence paths and hashes
into captured stdout so the immutable check record references the actual retained files.
Never overwrite prior evidence, metadata or baselines. Browser profiles/caches may use
system temporary directories and must be cleaned up. No app server serves requirements/
or test-evidence/. No implementation is permitted in the orchestrator checkout.

After Verification, wait for separate advancement to Security Review. Use Security
instructions to inspect the current source and real test/advisory evidence: input/route
controls, XSS/origin handling, dependency exposure, secrets and unnecessary capabilities.
Record findings and limitations with source/requirement links; no certification claim.
Any finding requires explicit remediation authorization. Fix only within this plan,
retain failing evidence, rerun checks, obtain fresh human code/automation approval, and
repeat Verification/Security as required. Changing the dependency or scope beyond the
approved pin requires corresponding renewed approval, not an automatic install upgrade.

Final report binds exact Analysis/Design/Plan, source fingerprint, actual named check
results and browser evidence, Security report and unresolved business items. Finalization
and every stage advancement require separate human authorization. A report of this
specified subset is neither full product completeness nor release/deployment approval.

## Human decision requested

Approve this ordered Plan and QA scenarios, including the exact development dependency,
local-only installation boundary and retained business uncertainty. Approval does not
advance to Development readiness or start coding. Wait for a separate advancement and
then separate explicit development-start authorization. No code, package install or test
execution has occurred while preparing this plan.
