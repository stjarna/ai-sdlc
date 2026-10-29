# Existing-project demonstration: reproducible evidence capture

This is a procedure, not a claim that a new CRUD acceptance has already been executed.
The preserved historical due-date demonstrator is not a CRUD application and must remain
unchanged. Prepare a **separate** standalone CRUD application before SDLC adoption.
Keep all human decisions real and interactive; do not synthesize approvals for filming.

## Before installation

1. Build the independent CRUD application without the orchestrator. Keep its source,
   existing project instructions, dependency lockfiles and tests in its own Git repository.
2. With explicit human Git authorization, capture its initial committed product baseline.
   Record `git rev-parse HEAD`, `git status --porcelain=v1`, branch and tool versions.
   A dirty tree is not a clean product baseline; preserve work and resolve it explicitly.
3. Run the existing application tests and retain actual argv, exit codes, output,
   runtime/dependency versions and timestamp. Do not relabel an API test as browser E2E.
4. Start the app and capture initial CRUD screenshots and a short UI recording: create,
   view, edit, complete/reopen and delete as supported by its actual approved behavior.
   Use the host recording tool, e.g. macOS Screenshot/QuickTime; this increment supplies
   no recorder/editor. Retain original media and actual application URL/port/environment.

Keep the capture folder outside the application repository. A suggested layout is:

```text
external-capture/
  before/       # product revision, actual test logs, screenshots, recording
  installation/ # installer/verify JSON, pins, dependency and Codex versions
  sdlc/         # copied request history/baselines and CLI decision/result envelopes
  after/        # final source revision/diff, actual tests, screenshots, recording
  checksums.sha256
```

Run from the application root, supplying the external capture location yourself:

```sh
capture=/absolute/path/outside/application/external-capture
mkdir -p "$capture/before" "$capture/installation" "$capture/sdlc" "$capture/after"
git rev-parse HEAD > "$capture/before/application-revision.txt"
git status --porcelain=v1 > "$capture/before/git-status.txt"
git log -1 --format=fuller > "$capture/before/commit.txt"
```

Record test commands and actual results separately; do not assume a passing command.
Do not put recordings, browser traces or coverage output in fingerprinted source paths.

## Install and adopt

Follow [installation and preflight](installation-and-adoption.md). Save actual installer,
verification and preflight JSON in `installation/`. Record Codex version and observed skill
path in CLI/IDE, plus Python, PyYAML, runtime Git revision/full digest and catalog pins.
Keep the complete installed package for historical skill/template lookup. A preview must
remain labelled a preview; re-verify an approved committed installation before final filming.
Verify that installation and preflight leave original source, tests, project instructions,
Git HEAD and existing history unchanged. Resolve reported conflicts explicitly.

Describe optional task due dates to `$sdlc` as a **new incremental request**. The original
CRUD baseline is observed context, not retrospectively approved SDLC requirements.
Reference its baseline revision and preserve existing behavior with explicit regression
coverage. Clarify consequential unknowns (including past dates and changing/clearing an
assigned date) with the Product Owner before selecting observable behavior.

## Governed workflow and final capture

1. Execute the existing Discovery, Business, Analysis, Engineering and QA workflow.
   Present one decision at a time. Approval, advancement and starting work remain separate.
2. Retain actual decision wording, unresolved questions, explicit limitation consent where
   applicable, canonical documents, version/digest pins and immutable approval baselines.
3. Reuse existing CRUD tests and add source-bound due-date unit/integration/browser tests.
   Save actual failed attempts, defects, authorized remediation and retests. Preserve
   QA expectations rather than altering them to match implementation defects.
4. Execute Security Review and Final Verification through existing operations. Keep
   uncertainty and limitations visible. Verified is not release/deployment authorization.
5. Record final Git HEAD and working-tree status/diff. If final code is uncommitted,
   label it as such; do not claim HEAD identifies changed working files. A final commit
   requires separate explicit human authorization. Preserve baseline ancestry.
6. Capture the final actual UI with the same initial CRUD interactions plus due-date
   behavior. Record the current port, toolchain/browser versions and capture timestamp.
7. Copy the complete request directory and actual evidence outside the app, preserving
   bytes. Retain the initial/final source revisions (optionally a human-requested Git
   bundle) and runtime snapshot. Generate and verify SHA-256 inventories of the capture.

Reviews/status/details supply exact current document links and structured lifecycle,
ownership, approval and execution history. Retain their JSON responses as demonstration
navigation. There is no automatic full conversational transcript or animated timeline;
capture the actual human interaction when needed. New views can resolve current physical
paths; do not rewrite old approved reports or historical absolute links for presentation.
Store a separate navigation index if the evidence moves.

Before sharing, inspect the capture for credentials, private data, host-specific settings,
installed dependencies and caches. Exclude unnecessary caches while preserving the exact
source, reviewed artifacts and actual test evidence. Never regenerate an old result merely
to make a presentation cleaner, and never edit the historical To-Do archive.
