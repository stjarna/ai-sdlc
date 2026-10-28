# Engineering vertical slice and legacy sequential contract

The original engineering increment adds a fixed, agent-native sequence after explicitly advanced Functional
Analysis. The orchestrator owns identity, ownership, lifecycle, audit and persistence;
versioned domain packages supply the expertise. The CLI does not generate designs or
application code, interpret business meaning, or call an AI API. The native assistant
reads the selected package and uses normal host tools to do the work.

New requests now use the [Engineering/QA work-track extension](work-tracks.md). Its independent QA gates and unit/build-only Engineering Plan supersede the combined Plan/QA sequence below for forked requests. This document retains the exact legacy contracts for existing non-fork requests; adoption is explicit, never automatic.

## Original sequence and gates

```text
ready_for_technical_design
  -- explicit design drafting --> technical_design
  -- human design approval, then separate advancement --> ready_for_implementation_planning
  -- explicit plan drafting --> implementation_planning
  -- human plan approval, then separate advancement --> ready_for_development
  -- separate authorization to start --> development (code + unit tests + build)
  -- human implementation/code and automation review, then advancement --> verification
  -- passing integration/UI checks, then advancement --> security_review
  -- current security review with no open findings, then advancement --> final_verification
  -- explicit finalization --> verified
```

`verified` is not release approval, deployment or `ready_for_release`. Technical Design
and Implementation Plan approval do not advance; advancement does not automatically
start drafting or coding. A plan review explicitly includes QA scenario approval; the
implementation review includes human code and test-automation review. The assistant
must present both responsibilities before obtaining the respective decisions. Roles
remain declared responsibilities, not enforced RBAC. Independent review is requested
through the host when available, not inferred from the author's self-review.

The current implementation is **sequential**. The older parallel engineering/QA target
in the specification remains a future architecture option; it is not executed by this
slice. Parallel agents were used to build the orchestrator's domain packages, not to
orchestrate application development. Security participates in design and again after
verification. No general workflow engine, Stories or release implementation is added.

## Domain instruction packages

The initial packages live independently of Epics in `orchestrator/domain-skills/`:

| Package | Maintainer responsibility | Usable instruction stages |
|---|---|---|
| architecture 1.0.0 | Architecture Team | Technical Design, including security-by-design |
| development 1.0.0 | Engineering Enablement | Implementation Planning and Development |
| testing 1.0.0 | QA / Quality Engineering | Plan/scenario and automation review, integration/UI verification and final report |
| security 1.0.0 | Application Security | Technical Design and Security Review |

A small manifest declares name, description, semantic version, domain owner, stages,
inputs, outputs, standards, exact dependency versions and the compatible orchestrator
minor contract (`0.9`). `catalog.yaml` approves exact versions and SHA-256 package pins.
The package digest covers the manifest, SKILL.md and reference files, independent of
its parent path. Malformed metadata, symlinks, changed bytes, missing/cyclic dependencies
and incompatible versions/stages fail closed. Architecture depends on Security 1.0.0.
No remote registry, installation, network discovery or executable plugin loader exists.

The bundled packages are usable **instruction-level** PoC skills. Their supporting
specialties (API/data/ADRs, language guidelines, test data/accessibility/performance,
OWASP/dependency/authentication review) are outlines and roadmap items, not implemented
specialist tools or claims of certification. The orchestrator remains generic; no stack
or demonstration application's requirements are encoded in its scripts.

Artifacts record the exact resolved skill versions and content pins used for drafting,
review and check execution. Historical pins do not require today's catalog to stay
unchanged to validate the artifact. Reproducing old instruction execution requires
retaining that package separately. Pinning reproduces instructions, **not deterministic
LLM outputs**. These local packages are initial demonstrations of independently owned
specialist skills, not a replacement for the external enterprise skill ownership model.

Domain teams should own releases, evaluation scenarios, standards, compatibility tests,
practice updates, deprecation and rollout guidance. A reviewed catalog pin change is the
local consumption decision. No team-management or distribution infrastructure is built.

## Persistence and compatibility

The first engineering write explicitly upgrades only its Epic to schema `0.6`, adding
append-only `engineering_history`. Schemas `0.1–0.5` remain readable; existing baseline
formats, hashes and audit entries are unchanged. Upstream reopening preserves `0.6`
and every historical engineering record. A new Analysis advancement creates a new
engineering cycle; old documents and approvals cannot authorize the new cycle.

Every engineering operation first publishes a content-addressed bundle:

```text
requirements/REQ-0001-example/engineering-baselines/<manifest-sha256>/
  manifest.json
  metadata.yaml       # exact pre-operation metadata; retained audit prefix
  artifact.json       # typed traceability, input/skill/source pins and original intent
  content.md          # sole authoritative human-readable artifact prose
```

There is no mutable duplicate `design.md` or `plan.md`; review returns the current
immutable revision and its prose. Drafts are revisioned snapshots too. Each bundle binds
the exact approved Analysis baseline and advancement, whose Business dependency remains
immutable. Approval binds the specific draft bundle; even a same-content new revision
needs fresh approval. Audit entries preserve actual decision wording, actor, identity
source, timestamp, operation ID, expected revision, cycle and bundle ID. New lifecycle
events bind the published bundle; responsibility changes atomically create pending ownership handoffs using
the existing mechanism. Assignment stays separate and never starts work.

Existing project locks, durable immutable publication, optimistic revision checks,
append-only metadata prefixes, exact idempotent retries and atomic metadata replacement
are reused. Metadata publication is the sole commit point; no multi-file draft transaction
or new checkpoint is needed. A pre-commit failure may leave a verified orphan bundle;
exact retry reuses it. A lost response after replacement uses `E_WRITE_UNCERTAIN` and
an exact retry, never a new fabricated decision. An abandoned lock requires operator
inspection after establishing the writer has stopped. Corrupt referenced bundles require
known-good restoration. No automatic lock removal or repair is performed.

Historical bundle validation checks the exact file set, all hashes, canonical identity,
audit and lifecycle prefixes, ownership prefixes and retained upstream handoff. Direct
coordinated rewriting by an unrestricted filesystem editor is outside procedural trust.

## Tool-facing operation contract

The assistant resolves IDs, tokens, profiles and temporary input files internally.
Normal users use the existing `$sdlc` or `/sdlc` vocabulary and natural language.

```text
skills
engineering-review ID
engineering-write ID --kind design|plan|implementation|security --input-file FILE
engineering-approve ID --kind design|plan|implementation [--acknowledge-open-item ID ...]
engineering-request-changes ID --kind design|plan|implementation
engineering-advance ID --kind design|plan|implementation|verification|security
development-start ID
check-run ID --check-id NAME
verification-remediate ID --check-id NAME [--check-id NAME ...]
security-remediate ID --finding SF-001 [--finding SF-002 ...]
engineering-finalize ID
```

All mutations require `--expected-engineering-revision`, `--operation-id`, and
`--decision` with actual human wording for human decisions. Omit `--actor` for the local
profile, optionally binding `--expected-profile-revision`; explicit declared actors remain
available to headless callers. Artifact drafting uses an actual declared editor and a
clear drafting instruction; this is not human approval. Request changes records feedback
before explicitly authorized revision; it never rewrites prose automatically.

The engineering review token covers the complete existing Analysis review (metadata,
source and histories), plus the application-file fingerprint. No content change is
silently accepted into an earlier approval. Operation ID reuse with different intent
fails with `E_IDEMPOTENCY`; exact replay reports current state without restoring authority.

New diagnostics include `E_SKILL`, `E_ENGINEERING_INPUT`, `E_ENGINEERING_DOCUMENT`,
`E_ENGINEERING_TRACE`, `E_ENGINEERING_PLAN`, `E_IMPLEMENTATION_BOUNDARY`, `E_VERIFICATION`
and `E_SECURITY_FINDINGS`. Existing revision, approval, lock, integrity and uncertain-write
codes retain their meanings. Validation is structural, not business or security approval.

### Structured artifact inputs

Inputs are JSON objects (the CLI's strict YAML reader also accepts JSON) with these fields:

- All documents: `content` (human-readable Markdown), `coverage` (every non-retired FR/AC
  ID mapped to `{disposition: implemented|excluded|blocked, reason: TEXT}`), and
  `unresolved` (`[{id: ID, text: TEXT}]`). Preserve every inherited Analysis uncertainty;
  blocked/proposed behavior cannot become implemented scope. Downstream coverage cannot
  expand the upstream implemented scope. New technical questions may be added and must
  be explicitly acknowledged at approval, without resolving them.
- Plan additionally: `tasks` and `checks`. A task has `id` (`T-001`), `description`,
  `requirements` (available FR/AC IDs), `depends_on` (earlier tasks) and `paths` (allowed
  project-relative files/directories). A check has `id`, `category` (`unit`, `build`,
  `integration`, `ui`), `argv` (literal string array), `cwd` (`.` or a safe relative
  directory), `timeout` (1–120 seconds), `requirements` and `scenario`. All four categories
  are required in this demonstration slice (a non-UI applicability exception is future work); implemented ACs need integration/UI coverage.
- Implementation additionally: `source_revision`, exact approved `plan` bundle ID, and
  `completed_tasks` (all task IDs). Present the actual code diff and test automation for
  human review; prose claiming completion is not test evidence.
- Security additionally: `source_revision`, exact `plan`, and `findings`. Each finding has
  `id` (`SF-001`), `severity` (`critical|high|medium|low`), `status` (`open|resolved`),
  `requirements`, `evidence` and `remediation` text. Retain prior finding IDs. Resolution
  requires a prior finding, explicit linked remediation and fresh source-bound reruns.
  Every open finding blocks onward final verification; risk acceptance is not implemented.

### Controlled execution and actual evidence

The assistant edits application files through native tools only after explicit
`development-start`, using the approved ordered plan. The CLI snapshots application paths
at start. It rejects later out-of-plan additions, modifications or deletions before checks
or approval. File symlinks are rejected. Root `requirements/`, Git internals, `.venv`,
`node_modules`, Python/test caches and `.DS_Store` are excluded from application hashing;
source, dependency manifests/locks and application test files remain included.

`check-run` executes only the named approved argument array, never a generated shell
string. Explicit Git and shell-interpreter entrypoints are rejected; use a reviewed project runner. This does not sandbox a runner. It captures actual exit status (passed, failed, timeout, not_run), command,
scenario, requirement links, output/hash, exact plan and application fingerprint. Only
unit/build may run during Development; integration/UI follows human code/automation
approval. A changed source fingerprint makes old evidence unusable. Failed/latest or
missing results never count as passing. Timeouts and leftover child processes in the
check's process group are terminated. Checks must not modify fingerprinted application
inputs; such a run is rejected and must be inspected/rerun. Captured output is capped at
1 MB, with full-output hash and a truncation flag.

`check-run` returning `ok: true` means execution evidence was persisted, not that the test passed; inspect its recorded `status` and exit code. Verification requires all named checks for the same current source. Explicit `verification-remediate` links failed current check evidence and returns to Development for controlled fixes, fresh code review and reruns. Security remediation
returns to Development, retains findings/history and requires fresh human implementation
approval and new check runs, even if file bytes happen to be unchanged. Finalization
produces a source-bound report of actual results, coverage, retained uncertainty and
Security review. It does not send notifications, deploy, stage, commit or push.

These controls are **audit and gate controls, not a filesystem/process sandbox**.
Approved commands and an unrestricted agent can have side effects or edit governance
files outside the managed CLI. Host permissions/isolation remain the security boundary.
A check's `ui` label is a declared category; Python cannot prove browser interaction or
semantic test quality. The skill and human must review actual browser tests and evidence.
Automated fixtures use real tiny commands but do not claim live browser acceptance.

## Manual end-to-end acceptance

Use an isolated project outside this checkout and an existing small application (for
example, a personal task list with a browser UI). Use its actual build/test environment;
do not assume a technology stack in the orchestrator. Preserve any original fixture.

1. Use the existing business and Analysis gates interactively, obtaining real human
   approvals and separate advancements. Start from `ready_for_technical_design`.
2. Ask the SDLC assistant to design the approved scope. It loads Architecture and Security
   pins, inspects the existing code and drafts traceable components/interfaces/data,
   trade-offs and security considerations. Review known uncertainty and explicitly approve;
   verify the stage does not change until a separate advancement instruction.
3. Request the Implementation Plan. Review ordered tasks, allowed paths, unit/build checks,
   integration scenarios and an actual browser/UI check (for example, a project-owned
   Playwright runner). Explicitly approve the plan including QA scenarios. Advance separately,
   then explicitly authorize development. None of these decisions is simulated by the agent.
4. Let the assistant implement the approved small change and unit tests sequentially.
   Run named unit/build checks; inspect real output. Request an implementation review,
   inspect the code diff and test automation, and give explicit human code/automation approval.
   Authorize advancement separately. Verify changing one source file invalidates earlier
   evidence and approval in a second disposable copy.
5. Execute named integration and real UI checks through `check-run`; inspect browser
   artifacts/output and FR/AC coverage. Authorize progression to Security Review only
   after all checks pass for this source revision.
6. Request Security review using the pinned Security instructions. Inspect actual dependency,
   secrets, input/authentication checks as applicable; record unavailable tools as limitations.
   If an actual finding exists, explicitly authorize its remediation, preserve its ID,
   fix within approved scope, rerun unit/build, obtain fresh human code/automation approval,
   repeat integration/UI and Security review. Do not invent a finding or a remediation result.
7. With current clean Security review, advance separately to Final Verification. Ask for
   finalization and inspect the generated report, exact source, actual check evidence,
   inherited unresolved questions and immutable dependencies. `verified` is not release approval.
8. Resume in a fresh conversation and inspect `$sdlc status`, `details`, `inbox` and pending
   assignments. Verify every stage/handoff and decision reconstructs from files. No Git
   operations, automatic assignment or downstream work should occur.

Claude runtime acceptance is out of scope. Both thin adapters remain structurally valid.
Full browser acceptance is a real manual exercise; passing CLI fixture tests is not a
claim that an arbitrary application has been tested or that these skills always behave correctly.

## Remaining limits

This is one Epic and a fixed sequence, not a workflow engine or parallel application
scheduler. Local POSIX rename/fsync/process-group behavior is the execution target;
Windows, network filesystems and cross-clone concurrency are unverified. There is no
enterprise IAM, authenticated approval, remote skill registry, automatic package migration,
security risk acceptance, release/deployment automation or semantic correctness guarantee.
Histories retain exact snapshots and grow without pruning. An unrestricted editor can
rewrite all audits; hashes do not authenticate people. Dependency directories and toolchain
binaries are not frozen by the application fingerprint; environments must be recorded and
pinned by the application's approved plan. Automated governance checks cannot prove
requirements completeness, code-review independence, UI realism or vulnerability absence.

## Human-facing document identity

[Artifact storage](artifact-names.md) defines canonical physical filenames and manifest0.2 for new Engineering documents/events. Existing manifest0.1 content.md snapshots remain immutable and explicitly labelled legacy. Reviews and final reports link exact physical files; no old approval or snapshot is migrated.

The completed real human acceptance and byte-preserved artifacts are available in [the permanent demo](../examples/todo-app/README.md). Rehearsal commands operate on a separate copy; historical evidence is not regenerated.
