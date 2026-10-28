# Verified Task Due Date Management demo

This is the **real human-approved acceptance project**, preserved after Engineering and
QA reached `verified`. It is a small local in-memory due-date demonstrator, not a full
To-Do product. Historical approvals, failures, remediation, successful retests and the
final report are retained; no signoff or evidence was regenerated for this archive.

## Layout and preservation

- `project/`: exact accepted application, QA source and complete SDLC request/baselines.
- `acceptance-evidence/`: actual CLI execution/review envelopes, human decision inputs,
  regression reproduction and Security dependency-audit output.
- `acceptance-inputs/`: original authoring/review inputs and historical provenance note.
- `preservation-manifest.json`: SHA-256 for every copied file, original path mappings and
  documented exclusions. Installed dependencies, caches and source-generator scratch
  scripts are excluded. No active local identity profile, credentials or tokens are included; historical declared identity fields remain in the audit/CLI records.
- [Evidence navigation](EVIDENCE.md): current state, documents and historical results.
- `.run/`: ignored rehearsal copy, installed QA dependencies and **fresh** execution logs.
  Nothing here is part of historical acceptance or a new approval.

Keep `project/`, `acceptance-evidence/` and `acceptance-inputs/` unchanged. Even the captured
inner READMEs are source-bound historical text: some still say “proposed/not run” because
they were written before the subsequent approvals/results. Persisted audit and final
report establish actual completion. `.gitattributes` disables newline conversion for
preserved bytes and pinned domain instructions so Git checkout cannot alter their hashes.

## Prerequisites

Run commands below from the repository root. The verified environment used macOS,
Node **25.9.0**, npm **11.12.1**, Chrome **156.0.8078.74**, Python 3.13 and
PyYAML **6.0.3**. Playwright and playwright-core are locked to **1.64.1** in the QA lockfile.
Application code has no third-party runtime dependencies.

The **unchanged approved QA runner** uses installed Google Chrome at
`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. This is a disclosed macOS
limitation, not cross-platform acceptance. No browser download, host upgrade, Chromium
substitution or QA-source rewrite is automatic. Different host/runtime/browser versions
must be recorded as a fresh rehearsal environment, not claimed identical to acceptance.

Bootstrap the orchestrator environment on a fresh checkout if needed:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r orchestrator/requirements.txt
```

This uses pinned PyYAML. It does not configure a human identity or create approvals.
The original acceptance used a declared local identity; this archive needs no profile
for read-only inspection or rehearsal commands.

## Verify and install

```bash
.venv/bin/python examples/todo-app/demo.py verify
.venv/bin/python examples/todo-app/demo.py setup
```

`verify` checks all preservation hashes, read-only CLI validation, both Verified states,
current joined evidence, original referenced evidence hashes and historical skill pins.
`setup` creates `.run/project` once, then runs the reviewed lockfile's `npm ci` in its
`qa/` directory with lifecycle scripts and browser downloads disabled. No global install.
It never overwrites changed rehearsal inputs; preserve/move a changed workspace manually
before creating a fresh one. No identity or environment secrets are copied.

## Launch the application

```bash
.venv/bin/python examples/todo-app/demo.py start
```

Open the printed `http://127.0.0.1:PORT` URL. The port is selected at startup, not hard-coded.
Stop with Ctrl-C. Two seeded tasks begin undated; select an initial future calendar date
or leave a task undated. Server restart resets in-memory data. The displayed UTC reference
day is the approved testing convention, not a newly decided business timezone rule.

## Rehearse the checks

```bash
.venv/bin/python examples/todo-app/demo.py unit
.venv/bin/python examples/todo-app/demo.py build
.venv/bin/python examples/todo-app/demo.py integration
.venv/bin/python examples/todo-app/demo.py ui
```

These execute the exact existing unit/build, real HTTP and real Chrome runner commands
from the rehearsal copy. Unit tests use the existing Node runner; integration/UI create
isolated servers automatically, so the interactive server need not be running. Fresh
JSON results, screenshots and traces use new UUID directories under the rehearsal's
`requirements/.../test-evidence/`. Command output/exit status is retained separately in
`.run/executions/`. Old evidence is never replaced, and these runs do **not** append
SDLC audit, grant approvals, complete a lifecycle stage or certify a release.

Inspect [preparation results](../../docs/demo-finalization.md) for the commands actually
executed during preservation. A command failing, timing out or not being run is never a
pass. Rehearsal setup does not imply a clean dependency/security result; the original
actual dependency audit is preserved and time-bound.

## Inspect the accepted workflow

```bash
.venv/bin/python examples/todo-app/demo.py details
.venv/bin/python orchestrator/scripts/sdlc.py --project examples/todo-app/project open REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project examples/todo-app/project engineering-review REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project examples/todo-app/project qa-review REQ-0001
```

These are read-only. Links are reconstructed for the current permanent checkout, not
old temporary directories. [Evidence navigation](EVIDENCE.md) provides relative links.
Historical stdout, traces and audit preserve original temporary paths **as evidence**.
`verify` resolves them through the manifest's root mappings and hashes the local copies;
the old directories need not exist. Do not search/replace paths inside immutable bundles.
No recorded historical command is rerun merely to inspect the archive.

## Boundaries and remaining work

Past-date behavior is deferred pending support consultation; changing/clearing an assigned
date remains undefined. Both remain acknowledged open business topics, with blocked
scenarios rather than invented expected outcomes. No CRUD/completion, notifications,
persistence, authentication, synchronization, Stories, Release or deployment is added.
The UTC fixture day and synthetic seeds are demo/test preconditions, not business rules.

Verified describes the agreed subset and exact accepted evidence, not production readiness,
security certification or release approval. Local roles/identities are unauthenticated,
roles informational; source path controls are not an OS sandbox. Claude runtime acceptance
and other browsers/platforms remain outside the demonstrated PoC. Naming format0.2 requires
an updated reader; immutable format0.1 artifacts remain explicit legacy storage.
