# Independent QA automation — proposed for human review

Authority: approved QA strategy/scenarios derived from the frozen Functional Analysis.
Technical Design supplies interface bindings only, never functional expectations.
Testing 1.1.0 is pinned by the orchestrator when this automation artifact is recorded.

## Dependencies and setup proposal

Playwright 1.64.1 is pinned in this QA-only manifest and npm lockfile. The lockfile was
resolved without installing modules or running scripts. No QA package or browser has
been installed. The existing Chrome executable is:
`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
This host path is a disclosed local PoC portability limitation.

After explicit automation approval and separate advancement, the proposed local setup
is `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --prefix qa --ignore-scripts --no-audit --no-fund`.
This installs only the reviewed QA dependency tree under qa/node_modules; no global
install, production dependency or browser download. Setup is not itself a QA test.
Inspect actual locked dependency/advisory evidence during Security Review; no clean
security result is inferred from pinning. Never change the lockfile to obtain a pass.
No external AI service or credentials. Browser/runtime incompatibility is a real blocker.

## Named checks (not executed yet)

- QA-INTEGRATION: `node --test qa/integration.test.mjs`, cwd project root, 90 seconds.
  Six actual HTTP tests: permitted undated reads, exact future-date assignment and
  independent readback across three calendar examples, task isolation, plus supplementary
  structural-input/origin and fixed-route/header controls from the approved Design.
- QA-UI: `node qa/ui.mjs`, cwd project root, 120 seconds. Eight real browser scenarios:
  undated reload; three exact calendar assignments with HTTP readback; preserved draft/
  focus; committed save with lost response; unknown outcome and blocked retry; literal
  hostile-title rendering. Real input/select/submit interactions and observable assertions.
  Local interception in failure regressions controls delivery, not application answers.

Both checks map to TC-001/002/003 and FR-001/002, AC-001/002. Parameterized dates are
future relative to injected 2026-10-28 test data, not an approved business range or UTC
product policy. TC-004 (past-date behavior) and TC-005 (changing/clearing existing dates)
remain blocked: there are no assertions accepting/rejecting these undefined capabilities.
Supplementary Design controls and R1/R2 regressions do not create new business criteria.

## Execution and evidence

Run only the named checks through qa-check-run after explicit approval/advancement and
current Engineering approval. Do not treat source generation or syntax inspection as a
passing integration/browser check. Each test uses isolated seeded in-memory state on an
ephemeral 127.0.0.1 port, then closes the server. No app artifacts or source are modified.
QA evidence is appended under this Epic's test-evidence/qa-KIND-UUID/; no earlier run
is overwritten. Each report, screenshot and trace path/hash is printed into CLI-captured
output. Browser scenarios retain screenshots and traces on success/failure where possible.
An early browser/setup failure remains failed/not-run, not an empty success. Node assertions
and JSON reports carry outcomes: Playwright library traces capture browser activity, not
assertion semantics. No task data other than synthetic fixtures is used.

There is no Technical Design, Plan, code, QA, lifecycle or release approval embedded in
these files. Automation needs its own human approval and separate readiness advancement.
Actual QA execution and explicit completion are later decisions; Engineering does not
advance automatically. Security Review remains separate and production readiness unclaimed.

API references used to prepare the runner:
https://playwright.dev/docs/api/class-browsertype
https://playwright.dev/docs/api/class-tracing
