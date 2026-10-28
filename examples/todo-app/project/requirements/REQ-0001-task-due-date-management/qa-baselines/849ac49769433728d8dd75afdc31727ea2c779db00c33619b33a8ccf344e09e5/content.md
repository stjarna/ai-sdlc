# QA automation review — Task Due Date Management

Status: prepared for explicit human automation approval. Not approved, not run.
Prepared using Testing 1.1.0 in response to `$sdlc start qa` after separate approval
of strategy/scenarios and explicit QA advancement. No Engineering authority is changed.

## Frozen authority and bindings

Functional Analysis baseline: 0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598
Approved QA strategy/scenarios remain the functional oracle; the CLI records exact
scenario approval, approved Technical Design/interface and QA source bindings. Current
Engineering implementation is approved and in Verification. No code/Plan/Design is edited.

TC-001: an existing task can remain undated, AC-002 / FR-002.
TC-002: assign a selected future calendar date and preserve exact day/month/year, AC-001 / FR-001.
TC-003: the target receives that exact date while the second task stays undated, both ACs.
TC-004: past-date outcome remains blocked/deferred pending consultation with support.
TC-005: changing or clearing an assigned date remains undefined and blocked.
Neither blocked case is executed or counted as a pass. Acknowledgement is not resolution.

## Source/dependency boundary

Six files under qa/: package.json, package-lock.json, helpers.mjs, integration.test.mjs,
ui.mjs, README.md. Source fingerprint and paths are recorded in the structured contract.
The original Engineering source, developer unit/build tests and all approved baselines
remain unchanged. No dependency is added to the application package.

Proposed QA-only development dependency: playwright 1.64.1 with exact playwright-core
1.64.1 and registry integrity hashes in a portable npm lockfile. Registry metadata and
lockfile resolution were performed; no node_modules, package installation, scripts or
browser download. Proposed setup after approval and separate advancement: from project
root run PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --prefix qa --ignore-scripts --no-audit
--no-fund, using the physical project path to avoid /tmp symlink lockfile differences.
No global installation, runtime replacement, external AI service or credentials.
Installed Chrome at /Applications/Google Chrome.app/Contents/MacOS/Google Chrome supplies
the browser. Compatibility/launch remains unverified; the exact observed runtime/version
is printed at actual execution. Host-specific Chrome path is a local PoC limitation.

## Named checks and real assertions

QA-INTEGRATION: node --test qa/integration.test.mjs, cwd '.', timeout 90s. Six real HTTP
tests with isolated servers: undated reads; initial assignment and independent readback
for three calendar examples; supplementary malformed-body/origin/state-preservation and
fixed-route/header assertions from approved Design. Those controls do not define new
business expected outcomes or replace Security Review. TC-001/002/003 map to the actual
first four tests, not just labels.

QA-UI: node qa/ui.mjs, cwd '.', timeout 120s. Eight real Chrome scenarios: undated reload;
three parameterized assignments through labelled date inputs and actual submission,
exact output/reload and independent HTTP state; preserved other-task draft/focus and
focus fallback; server commit with lost response/readback/no duplicate mutation; failed
readback with unknown outcome and disabled retry; literal hostile-title rendering.
Failure interception changes delivery, not product expected outcomes. API-only calls are
not UI evidence; assertions require actual input, clicking, DOM state and focus.

Both named checks link all three specified case IDs and their FR/AC references. Future
dates 2026-12-31, 2027-01-01 and 2028-02-29 use injected reference day 2026-10-28 solely
as reproducible test fixtures, not a production business range or UTC/timezone policy.
No assertions choose past-date acceptance/rejection or change/clear capability.

## Evidence, safety and actual preparation results

Each execution uses ephemeral loopback servers and isolated seeded in-memory data.
Sources, business content and baselines are not edited by runners. New evidence goes to
this Epic's test-evidence/qa-KIND-UUID/; no previous run is overwritten. JSON per-test
reports and real browser screenshot/trace files print paths and SHA256 into captured
CLI output. Browser trace records activity; Node assertions/reports carry test outcomes.
Failures retain available evidence, remain failures and are never converted to passes.
Browser/context/server cleanup runs in finally blocks after normal assertion failures.
All commands are literal argv and require current approvals via qa-check-run; these
runners are not an OS sandbox. No production data or network service is used.

Actual preparation verification: node --check succeeded for helpers.mjs,
integration.test.mjs and ui.mjs; package/lock JSON parses, exact versions/integrity and
portable node_modules-relative entries were checked. This proves syntax/structure only.
No integration/browser checks, dependency installation, advisory scan or UI launch have
run. No test is reported passed merely because its source exists. Existing 40 unit tests
and build evidence still apply to unchanged Engineering source; QA readiness is separate.

## Review and next gates

Review the complete QA source diff, exact local dependency/setup boundary, case mapping
and retained uncertainty. Explicit human automation approval binds these exact QA bytes;
approval leaves QA in Test Automation. Wait for separate readiness advancement before
installing reviewed QA dependencies and executing the named checks. Actual passed checks
and explicit QA completion are still required; Engineering does not advance automatically.
Security Review, joined final verification and separate lifecycle decisions remain ahead.
No approval, stage advancement, release, Git action or production readiness is inferred.
