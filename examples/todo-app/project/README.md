# Task Due Date Management — local acceptance demonstrator

Dependency-free Node.js application, using the observed Node v25.9.0 runtime.
No installation is needed. From this disposable project run `node src/server.mjs`
and open the printed **http://127.0.0.1:PORT** URL. Stop with Ctrl-C.
The port is ephemeral. No public deployment is configured.

Two seeded existing tasks start without due dates. Leave them undated or assign an
initial future calendar date. The exact date is stored in process and displayed in
YYYY-MM-DD notation; this is not an instant/timezone conversion. Reloading the page
retains in-process state. Restarting the server resets fixtures.

Past-date behavior remains deferred pending support consultation. Changing or clearing
an assigned date remains undefined. Those capabilities are not implemented here; the
explicit unsupported response is a demo boundary, not a product acceptance/rejection
policy. The displayed server UTC reference day is only the accepted testing convention.
No reminders/notifications, task CRUD/completion, accounts, synchronization or durable
storage are implemented. This is not a full task manager or production-ready service.

## Interface for independent QA

`createApp({repository, referenceDay})` in `src/http.mjs` constructs a Node HTTP server
without listening; defaults use the seeded repository and current UTC reference day.
QA can inject isolated seeds with `createRepository(seeds)` and a function returning a
fixed YYYY-MM-DD test day, then listen on port 0 on 127.0.0.1 and close after each run.

- GET `/api/tasks`: `{tasks: [{id, title, dueDate}], referenceDay}`.
- POST `/api/tasks/TASK_ID/due-date`: UTF-8 JSON `{dueDate: "YYYY-MM-DD"}`;
  success returns `{task}`. Read back with GET to inspect actual state.
- `/`, `/app.js`, `/styles.css` are the only static routes. Other routes return 404.
- Errors: `{error: {code, message}}` with appropriate HTTP status. Unsupported demo
  paths use `DEMO_NOT_IMPLEMENTED`/501 and preserve state, not FR-003 coverage.
- HTTP Host must match the printed 127.0.0.1 origin; foreign browser Origins cannot
  mutate state. Bodies are limited to 4096 bytes. No authentication is claimed.

## Engineering verification

Approved named operations: `node scripts/check.mjs unit` and
`node scripts/check.mjs build`. Use the SDLC evidence operation for official results.
The first runs domain unit assertions only; the second validates syntax, local imports,
fixed assets and package scripts without bundling. Neither proves HTTP or browser behavior.
Independent QA owns integration/UI automation, dependencies and checks under `qa/`,
with separate scenario/automation approvals and explicit execution/completion gates.
No QA package is installed by Engineering. No release or security certification claim.
