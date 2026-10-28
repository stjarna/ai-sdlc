# Technical Design — Task Due Date Management acceptance application

Status: proposed for human review; not approved. This is an acceptance demonstrator,
not a complete personal task manager or a production deployment design.

## Approved authority and observations

Consume the exact approved and explicitly advanced Functional Analysis baseline selected
by the current handoff. Its approved Business dependency and Discovery history remain
authoritative. The original requirement is unchanged. FR-001/AC-001 specify assigning
a supplied future calendar date to an undated task; FR-002/AC-002 permit an undated task.
FR-003 remains blocked. U-001/AQ-001 and AQ-002 remain unresolved, despite acknowledgement.
No business rule for past dates or changing/clearing an assigned date is established.

Inspection: the disposable project contains requirements artifacts only. There is no
existing application, repository stack, schema or build convention to extend. Seeded
task records are demonstration fixtures satisfying the use-case precondition that a
task is available; they are not a new task-creation requirement.

## Proposed architecture

Use one local process serving a small browser UI and a same-origin JSON API. Separate:
1. Domain module: Task {id, title, dueDate: null | YYYY-MM-DD}; initial-date assignment
   and undated-task representation. Store the date as a calendar string, not an instant.
2. In-memory task repository: fixed seeded task fixtures; no database, accounts or synchronization.
3. HTTP adapter: explicit route allowlist and JSON input/output; no arbitrary filesystem access.
4. Browser adapter: list seeded tasks, clearly show an absent date, and provide a labelled
   initial future-date assignment form for undated tasks. Render returned values as text.

Request flow: browser -> same-origin API -> domain service -> in-memory repository ->
JSON result -> browser renders the persisted-in-process task state. An independent API
read must return the assigned date, so this is working application state rather than
only a client-side display change.

## Proposed technology and alternatives

Use the already installed Node.js v25.9.0, built-in HTTP modules, and plain HTML/CSS/
JavaScript. This is a local acceptance environment observation, not a production runtime
support recommendation. Avoid a frontend framework, database, runtime dependencies or
build bundler for this small scope. No runtime or package is installed at the design stage.
Use Node's built-in test runner for domain and HTTP integration checks. Propose Playwright
as a pinned development-only dependency for an actual browser UI runner, using installed
Chrome. Chrome is present; Playwright is not currently resolvable from this project.
Dependency/version resolution, browser launch and executable test commands belong to the
subsequent reviewed Plan; no browser test is claimed executed now.

Alternative: a browser-only local-storage application would be smaller but would not
exercise a real HTTP/component boundary and would add an unapproved persistence choice.
A framework/database stack adds unnecessary installation and configuration for two
approved acceptance paths. The proposed in-memory process is intentionally disposable.

## Scope boundaries and explicit technical proposals

Due-date entry is calendar-only, with strict real-calendar YYYY-MM-DD parsing; preserve
exact day/month/year through the API and UI. Invalid encoding/shape/non-calendar values
are structural input errors, not a decision about valid past dates.

Demonstrate initial assignment of future dates and tasks remaining undated. Do not add
task creation/deletion/completion, reminders/notifications, date clearing or date editing.
Once assigned, show the assigned date without edit/clear controls; this means those
capabilities are absent from the demonstrator, not prohibited by an approved product rule.

For attempts outside specified behavior (a valid past/today date or reassigning/clearing
an existing date), return an explicit not-implemented-in-this-demonstrator response,
not a business validation message claiming that past dates or edits are forbidden.
These paths have no product acceptance criteria and remain blocked/open. This technical
boundary is proposed for review; it must not be represented as resolving U-001/AQ-001,
FR-003 or AQ-002. The final report must state the application demonstrates only the
specified subset, even if its executable checks pass.

For reproducible tests, inject a reference calendar day. In the live demo, display the
server UTC reference day explicitly and use it only to identify the demonstrated future
path. No production per-user timezone or today-date policy is inferred. The UI must
identify this as an acceptance demonstration with incomplete date policies.

In-memory data resets when the process restarts. This is a proposed test-environment
limitation, not a user-approved retention requirement. No sensitive production data,
external services, network deployment or authenticated user behavior is introduced.

## Security-by-design contribution

Assets are seeded task titles/dates, local process integrity, and integrity of the test
and SDLC artifacts. Treat browser input and HTTP requests as untrusted. Bind the server
to loopback on an ephemeral port; make no internet-facing deployment claim. Use explicit
routes and fixed static assets; no path-to-file concatenation, executable input, eval,
dynamic shell or external content. Bound request sizes and validate content type, object
keys, task identity and calendar syntax; return controlled JSON errors without stack traces.

Use same-origin UI/API, reject foreign origins for mutating requests, do not enable
permissive CORS, and use proportionate response headers (nosniff and a local-content CSP).
Render untrusted text through textContent, with no untrusted HTML insertion. Do not log
request bodies or credentials. There is no authentication because this is an isolated
seeded-data local demonstration; authentication and multi-user authorization are not
claimed or silently added as product requirements. Loopback alone is not a universal
security boundary; localhost misuse and dependency risks remain review concerns.

Keep the application server away from requirements/, approval artifacts, local identity
files and test evidence. Serve only the declared public assets. Source and tests remain
within the later approved Plan paths. Playwright is development-only, pinned with a
lockfile, and reviewed before use; inspect actual dependency/advisory evidence when available.
These are proposed design controls from Security 1.0.0, not an executed Security Review,
vulnerability scan, human signoff or certification.

## Verification seams and traceability

FR-001 -> domain initial-date assignment -> JSON endpoint -> browser form -> AC-001:
assert exact selected future YYYY-MM-DD in the returned task, subsequent HTTP read and
rendered browser state. FR-002 -> nullable dueDate -> JSON null and explicit undated UI
state -> AC-002. FR-003 stays blocked; never add a test asserting acceptance or business
rejection of past dates. Tests may check that the demo reports an unsupported path as
unimplemented, but must not relabel that as the missing product rule.

Plan unit checks for calendar parsing, state mutation and optionality; integration checks
for real HTTP requests, returned/read state, structural errors and route boundaries;
and actual browser tests that open the running UI, leave a fixture undated, assign a
selected future date through its form and assert the resulting display/state. Include
appropriate security-negative checks for the proposed controls. Test scenarios and
commands will be reviewed in the Plan; generated automation and code require later human
review. This document records design intent only; no tests or implementation have run.

## Review and handoff

Architecture 1.0.0 and Security 1.0.0 instruction pins are recorded by the orchestrator.
All stack, component, environment and control choices above are proposals until explicit
human Design approval. That approval must acknowledge both unresolved business topics;
it neither resolves them nor authorizes coding. After approval, wait for separate
advancement before Implementation Planning. No assignment or next-stage work is automatic.
