# Security Review — local Task Due Date Management demonstrator

Review prepared using Security 1.1.0 at 2026-10-28T21:57:11.296410+00:00. This is a source-bound assessment,
not human approval, certification, release authorization or lifecycle advancement.

## Authority and exact reviewed inputs

Engineering source: 683d07a8c5f7a769b5d52866d594bf2549d37fc1b6d0634ecb38cd9c25ee2eb4
Approved Plan: 6875a98c313457dd5fa9f3f5dfb567e66380d87e8f531f1ae47b915b48a26f0f
Approved implementation: e3195b832a823c3b6412752f88b8187e8e91af254b464ad7be881931d6c97e2a
Approved Technical Design: 97e48e3c6e0fcfdcb07373d0a2cb420bbb67f374e9599a588516765206db899d
Approved Analysis: 0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598
QA automation: 849ac49769433728d8dd75afdc31727ea2c779db00c33619b33a8ccf344e09e5
QA source: 22020008f60e67a62283eab65a5228480884e6afdc4d376d44f915e8362a076f

The completed QA join is current for these exact inputs; scenario/automation and human
code approvals remain valid. All current and historical evidence is preserved. Prior
QA-F-001 was remediated under explicit authorization, reapproved and actually verified
in Chrome; it is not fabricated as a new resolved security finding.

## Scope, assets and trust boundaries

Inspect the local seeded task/date state, process integrity, fixed static assets and
separation from requirements, identity and test evidence. Untrusted boundaries are HTTP
headers/path/body and browser DOM rendering. QA dependencies are executable developer
tooling, separate from the dependency-free application. This is ephemeral local seeded
data on loopback, not a multi-user or production deployment. No real-user data or secrets
were supplied. The review does not establish authentication or authorization business rules.

## Source inspection — observed controls, not unexecuted test claims

src/server.mjs binds 127.0.0.1 on an ephemeral port. src/http.mjs enforces the expected
Host, rejects foreign browser Origin mutations, exposes fixed GET/static and initial-date
routes only, returns controlled JSON errors and omits permissive CORS. It bounds request
bodies at 4096 bytes, strictly decodes UTF-8, checks JSON object keys/task identity and
uses real-calendar validation. No request path is joined into a filesystem path; only
three constant public assets are served. No requirements, evidence or identity file is
served. No request bodies, credentials or exception stacks are logged in HTTP responses.
Headers include CSP restricting script/style/connect to self, nosniff, no-referrer and
no-store. Request/header timeouts and header count are bounded. These are proportionate
local controls, not an OS sandbox or denial-of-service guarantee.

public/app.js uses textContent for task titles, dates and messages, with no dynamic HTML,
eval or shell. API date state is represented as calendar text, not code. Pending-submit
suppression and unknown-outcome retry blocking preserve data consistency but do not
constitute authentication or idempotency for arbitrary clients. The repository keeps
isolated seeded in-memory records and returns copies. No SQL, durable store, account,
network synchronization or external application service is introduced.

The only child-process execution in application-owned tooling is the declared Engineering
unit/build runner with literal Node argv; QA uses a fixed installed Chrome executable
and approved test sources. Browser test routing limits test-page requests to the local
fixture. Runners have host permissions and are not a security sandbox.

## Actual executed evidence considered

- Current Engineering C-UNIT: 41 passed, zero failed; C-BUILD passed. Unit/build evidence
  alone is not security or browser proof.
- Current QA-INTEGRATION: six real HTTP tests passed. Supplementary negative assertions
  verify foreign Origin rejection, malformed JSON, impossible date, extra keys, oversized
  body/state preservation, unserved artifact/source paths, nosniff and CSP script source.
  UTF-8 failure handling and Host restrictions were inspected, not separately exercised
  by those named tests; do not claim every control has dynamic coverage.
- Current QA-UI: eight real Chrome scenarios passed, including literal hostile seed-title
  rendering without an image element or injected global. Screenshot/trace and test reports
  are retained with captured hashes. These are scoped assertions, not a comprehensive XSS
  or application penetration test.
- npm audit --package-lock-only --ignore-scripts --json ran in the physical qa directory,
  exit 0. Locked playwright/playwright-core 1.64.1 returned zero known registry advisories
  (info/low/moderate/high/critical all zero), including dev dependencies. This is advisory
  lookup of the exact lockfile, not malware detection or an audit of Node/Chrome/OS binaries.
  Raw response hash: 6d31e957dc14f2847573c528dd4fdfd3b80883e8f4d401404880b25afa9bf1b6. Output and actual invocation/exit record are retained
  in evidence/security-npm-audit.json and security-npm-audit-execution.json.
- A scoped source inventory of 17 text/source/manifest files excluded node_modules and
  requirements. Explicit private-key/AWS/GitHub-token regex checks found no matches.
  This limited check is not a comprehensive secrets scanner; no sensitive matches or
  credentials are copied into reports. Scope is recorded in security-scoped-inspection.json.

## Findings and recommendation

No open security findings identified within this stated scope; structured findings list
is empty. There is no previous Security finding to remove or silently mark resolved.
The evidence supports presenting the current local PoC for the separate Final Verification
readiness decision. No automatic progression is authorized by this recommendation.

## Preserved uncertainty and review limitations

Past-date behavior remains deferred/blocked pending support consultation, and changing
or clearing assigned dates remains undefined. Acknowledgement is not resolution. The
technical unsupported response chooses neither business acceptance nor rejection. Their
absence from executable product acceptance coverage remains in the final report.

Local processes can access loopback; there is no authenticated multi-user isolation.
This is an approved isolated synthetic-data demonstrator limitation, not a claim of
production safety. No internet-facing deployment, production data, TLS, enterprise IAM,
RBAC, durable retention or recovery has been reviewed or silently added. Runtime/OS/
browser vulnerabilities, supply-chain malware, full DAST, fuzzing, resource-exhaustion,
load testing and independent penetration testing were not performed. Static inspection
and selected tests cannot prove absence of vulnerabilities. Dependency advisory results
reflect only the actual lookup time. No external Security scanner was claimed run.

No source, QA automation, dependencies, test assertions, business decisions or approvals
were modified by this review. All earlier failed/passed evidence remains available.
Separate explicit human advancement is required; this report does not certify security,
authorize deployment/release, or stage/commit/push anything.
