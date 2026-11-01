# Deterministic CLI inventory and argument reference

[Documentation index](README.md) · [Conversational commands](command-reference.md) · [Operation contract](../orchestrator/scripts/README.md)

This is the tool-facing index for engineers maintaining integrations or inspecting a
failure. Business users normally use the conversational commands. **57 operations**
were extracted from the actual `sdlc.main` argparse tree at documentation baseline
`d5009d8aae78be6bfefe5aac466a03f080599fbd` plus this early-domain increment,
before dispatch, without executing writes.
Installer/adoption entrypoints are listed separately below. This inventory complements,
rather than replaces, the [operation contract](../orchestrator/scripts/README.md) and
stage-specific schema/recovery contracts. No operation is hidden from the coverage table.

## Invocation, results and recovery

```text
PYTHON orchestrator/scripts/sdlc.py --project PROJECT [--runtime-session RECEIPT] OPERATION ARGUMENTS
PYTHON orchestrator/scripts/sdlc.py templates [TEMPLATE_ID]
PYTHON orchestrator/scripts/sdlc.py --version
```

Managed installed writes require the effective runtime and a matching procedural
context receipt through global `--runtime-session`; legacy source-checkout tooling
is not represented as managed runtime-provenance execution. Read-only inspection does
not require a write receipt. See [runtime management](runtime-version-management.md).

`PYTHON` means the installed pinned environment (or contributor `.venv/bin/python`),
not a literal executable. PROJECT is an existing directory; every operation except
`templates` requires it. Global `--help` and operation `--help` show parser usage.
Required parser arguments below are exhaustive; **semantic preconditions are additional**.
Optional flags may be mandatory for an applicable semantic gate, such as current source
revision for QA automation approval or an existing draft revision during replacement.

Managed results are JSON with `ok`, `operation`, `diagnostics` and operation-specific
context, artifact, revision, decision or evidence fields. Diagnostics include severity,
code, file and human-readable message, with a line when available. Exit 0 means structural
success (warnings allowed), 1 means operational rejection, and 2 is argparse usage failure
on stderr. Check execution can return `ok: true` with a **failed** test: inspect actual
recorded status/exit code. Never equate validation, eligibility or evidence persistence
with human approval, semantic correctness or test success.

For mutations obtain tokens from a **fresh stage review**, use the actual supplied human
decision where required, and retain operation ID/inputs on retry. Exact replay returns
current state without restoring old authority. Revision conflict requires reload and
reconciliation; `E_IDEMPOTENCY` requires inspecting the old intent, not replacing its ID.
`E_PROJECT_BUSY` requires waiting/inspection, never automatic stale-lock deletion.
`E_WRITE_UNCERTAIN` requires inspecting persisted state and exact retry. Document
transaction journals use inspected `business-recover` / `analysis-recover`; immutable
bundle corruption (`E_BASELINE_*`) requires known-good restoration, never regeneration
from today's draft. See [diagnostics](../orchestrator/scripts/README.md#behavior-and-diagnostics).

## Family preconditions, results and failure handling

| Operation family | Preconditions and records affected | Result to inspect / representative blockers |
|---|---|---|
| Context/read/catalog | Unambiguous request except project/catalog views; existing records/resources structurally valid. No managed writes. | Routing/review or catalog/scaffold; E_CONTEXT_MISSING, E_CONTEXT_AMBIGUOUS, E_TRACK_AMBIGUOUS, E_EPIC_NOT_FOUND, E_SKILL. Correct selection or restore valid resources. |
| Identity/assignment | Explicit supplied declarations, external profile path; confirmation and fresh ownership token for transfers. Profile or metadata/history only. | Identity/revision or ownership context; E_IDENTITY_MISSING, E_IDENTITY_REVISION, E_REVISION_CONFLICT. Inspect/setup/reload; never impersonate Git identity. |
| Discovery | Valid local records; updates only in discovery; completion requires history and explicit Requester decision. Metadata/idea at creation, sidecar on update, lifecycle/ownership on completion/reopen. | Epic, revision, derived state and record IDs/replay; E_YAML, E_DUPLICATE_ID, E_DISCOVERY_REFERENCE, E_STATUS. Fix proposed input, preserve existing content. |
| Business | Completed Discovery; draft bound to current source; gate requires current reconciled business_refinement. Markdown/history, decision metadata and approval baseline as applicable. | Business review, current flag, approval/can_advance; E_BUSINESS_COVERAGE, E_BUSINESS_PROVENANCE, E_ACKNOWLEDGEMENT, E_APPROVAL_STALE. Reconcile sources or obtain missing human decision. |
| Analysis | Active approved Business handoff; current specification for gates; no editing after Analysis advancement. Specification/history, decisions/baseline and authorized track fork. | Input, details, analysis_review_revision, analysis_approval, can_approve; E_ANALYSIS_COVERAGE, E_ANALYSIS_UNRESOLVED, E_APPROVAL_STALE. Return to the supported source/refinement flow. |
| Engineering | Active Analysis cycle, reconciled track if forked, stage/kind eligible; source and upstream approvals current. Immutable bundles, audit and declared execution evidence. | Engineering review/artifact, approvals and development_start eligibility; E_STATUS, E_ENGINEERING_PLAN, E_IMPLEMENTATION_BOUNDARY, E_CONFORMANCE, E_LIMITATION_CONSENT, E_VERIFICATION. Stop on failure; explicit replanning/remediation as eligible. |
| QA/tracks | Active reconciled cycle; independent scenario authority, approved Design interface for automation and current reviewed source for runs. QA bundles/metadata history; check output for execution. | Track/QA review, approvals, coverage and actual check statuses; E_TRACK_AMBIGUOUS, E_INTEGRATION_NOT_READY, E_APPROVAL_STALE, E_VERIFICATION. Resolve exact blocker; never count missing evidence as passing. |
| Recovery | Inspect unfinished publication and establish no writer remains; targets must match recorded before/after bytes. Only recorded transaction targets roll forward. | Current inspected state/replay; E_BUSINESS_RECOVERY, E_ANALYSIS_RECOVERY, E_WRITE_UNCERTAIN or integrity errors. Retain original operation and restore known-good evidence when required. |

These representative diagnostics are not an exhaustive error enum; stage contracts own
all code meanings. No single result shape is promised across families. Detailed argument
entries below plus the global invocation define syntax without duplicating executable
schemas. Scope/lifecycle restrictions are enforced even if argparse accepts a flag.

## Source-to-documentation coverage

Every name below is a parser operation, not necessarily an extra user command. An
“internal” purpose means the skill handles it or an operator performs inspected recovery;
it does not imply an unsupported private entrypoint. Legacy sequential Engineering uses
the same operations with its original combined Plan/check contract. Forked cycles use
independent QA gates; do not reuse legacy approval semantics for them.

| Actual operation | Conversational route or internal purpose | Syntax and contract |
|---|---|---|
| `command-context` | all ten routed verbs (read-only helper) | [Arguments](#command-context) · [policy](command-ux.md) |
| `open` | resume/details (internal read) | [Arguments](#open) · [policy](command-ux.md) |
| `validate` | requested validation (internal read) | [Arguments](#validate) · [policy](command-ux.md) |
| `templates` | internal pinned scaffold resolution | [Arguments](#templates) · [policy](command-ux.md) |
| `skills` | internal domain guidance resolution | [Arguments](#skills) · [policy](command-ux.md) |
| `adoption-preflight` | internal adoption check | [Arguments](#adoption-preflight) · [policy](command-ux.md) |
| `identity-show` | internal attribution lookup | [Arguments](#identity-show) · [policy](ownership.md) |
| `identity-setup` | explicit local profile setup | [Arguments](#identity-setup) · [policy](ownership.md) |
| `identity-edit` | explicit local profile edit | [Arguments](#identity-edit) · [policy](ownership.md) |
| `inbox` | inbox | [Arguments](#inbox) · [policy](ownership.md) |
| `pending-assignments` | pending assignments | [Arguments](#pending-assignments) · [policy](ownership.md) |
| `assign` | assign | [Arguments](#assign) · [policy](ownership.md) |
| `ownership-initialize` | internal explicit legacy-owner declaration | [Arguments](#ownership-initialize) · [policy](ownership.md) |
| `new` | new shorthand | [Arguments](#new) · [policy](interactive-discovery.md) |
| `discovery-update` | Discovery conversation / changes | [Arguments](#discovery-update) · [policy](interactive-discovery.md) |
| `discovery-complete` | Discovery advance | [Arguments](#discovery-complete) · [policy](interactive-discovery.md) |
| `discovery-reopen` | explicit upstream reopening | [Arguments](#discovery-reopen) · [policy](interactive-discovery.md) |
| `business-generate` | explicit Business drafting | [Arguments](#business-generate) · [policy](business-approval.md) |
| `business-revise` | authorized Business refinement | [Arguments](#business-revise) · [policy](business-approval.md) |
| `business-review` | Business review/status/details | [Arguments](#business-review) · [policy](business-approval.md) |
| `business-request-changes` | Business changes | [Arguments](#business-request-changes) · [policy](business-approval.md) |
| `business-approve` | Business approve | [Arguments](#business-approve) · [policy](business-approval.md) |
| `business-advance` | Business advance | [Arguments](#business-advance) · [policy](business-approval.md) |
| `business-recover` | internal inspected recovery | [Arguments](#business-recover) · [policy](business-approval.md) |
| `analysis-generate` | explicit Analysis drafting | [Arguments](#analysis-generate) · [policy](analysis-approval.md) |
| `analysis-revise` | authorized Analysis refinement | [Arguments](#analysis-revise) · [policy](analysis-approval.md) |
| `analysis-review` | Analysis review/status/details | [Arguments](#analysis-review) · [policy](analysis-approval.md) |
| `analysis-request-changes` | Analysis changes | [Arguments](#analysis-request-changes) · [policy](analysis-approval.md) |
| `analysis-approve` | Analysis approve | [Arguments](#analysis-approve) · [policy](analysis-approval.md) |
| `analysis-advance` | Analysis advance | [Arguments](#analysis-advance) · [policy](analysis-approval.md) |
| `analysis-recover` | internal inspected recovery | [Arguments](#analysis-recover) · [policy](analysis-approval.md) |
| `engineering-review` | Engineering review/status/details | [Arguments](#engineering-review) · [policy](engineering.md) |
| `engineering-write` | Engineering start / authorized revision | [Arguments](#engineering-write) · [policy](engineering.md) |
| `engineering-approve` | Engineering approve | [Arguments](#engineering-approve) · [policy](engineering.md) |
| `engineering-request-changes` | Engineering changes | [Arguments](#engineering-request-changes) · [policy](engineering.md) |
| `engineering-advance` | Engineering advance | [Arguments](#engineering-advance) · [policy](engineering.md) |
| `development-start` | explicit Engineering start only | [Arguments](#development-start) · [policy](engineering.md) |
| `check-run` | Engineering approved named check | [Arguments](#check-run) · [policy](engineering.md) |
| `verification-remediate` | explicit failed-check remediation | [Arguments](#verification-remediate) · [policy](engineering.md) |
| `security-remediate` | explicit Security remediation | [Arguments](#security-remediate) · [policy](engineering.md) |
| `engineering-finalize` | Engineering final advance/finalization | [Arguments](#engineering-finalize) · [policy](engineering.md) |
| `track-review` | internal status/details | [Arguments](#track-review) · [policy](work-tracks.md) |
| `qa-review` | QA review/status/details | [Arguments](#qa-review) · [policy](work-tracks.md) |
| `tracks-adopt` | internal explicit legacy adoption | [Arguments](#tracks-adopt) · [policy](work-tracks.md) |
| `track-reconcile` | internal explicit upstream impact reconciliation | [Arguments](#track-reconcile) · [policy](work-tracks.md) |
| `qa-write` | QA start / authorized revision | [Arguments](#qa-write) · [policy](work-tracks.md) |
| `qa-approve` | QA approve | [Arguments](#qa-approve) · [policy](work-tracks.md) |
| `qa-request-changes` | QA changes | [Arguments](#qa-request-changes) · [policy](work-tracks.md) |
| `qa-advance` | QA advance/completion | [Arguments](#qa-advance) · [policy](work-tracks.md) |
| `qa-check-run` | QA start approved checks | [Arguments](#qa-check-run) · [policy](work-tracks.md) |
| `runtime-probe` | internal read-only candidate contract/input probe | [Arguments](#runtime-probe) · [policy](runtime-version-management.md) |
| `runtime-status` | inspect default/effective selection and artifact runtime receipts | [Arguments](#runtime-status) · [policy](runtime-version-management.md) |
| `runtime-session` | declare loaded instructions in a fresh context; external receipt only | [Arguments](#runtime-session) · [policy](runtime-version-management.md) |
| `runtime-check` | read-only future-scope compatibility preview | [Arguments](#runtime-check) · [policy](runtime-version-management.md) |
| `runtime-bind` | explicit initial legacy future-work selection; no past attribution | [Arguments](#runtime-bind) · [policy](runtime-version-management.md) |
| `runtime-promote` | explicit compatible future-stage/track selection | [Arguments](#runtime-promote) · [policy](runtime-version-management.md) |
| `runtime-recover` | inspected completion of original provenance/known transaction | [Arguments](#runtime-recover) · [policy](runtime-version-management.md) |

## Context, catalogs and validation

Read-only; never grants permission or repairs persisted state.

See [stage policy and diagnostics](command-ux.md) for eligibility, artifact schemas and recovery.

### command-context

**Mode:** read-only. **Purpose:** all ten routed verbs (read-only helper).

**Required after the operation:** `COMMAND {start,status,review,approve,changes,advance,details,inbox,pending assignments,assign}`.

**Optional:** `--request SELECTOR`, `--track {engineering,qa}`.

### open

**Mode:** read-only. **Purpose:** resume/details (internal read).

**Required after the operation:** `ID`.

**Optional:** None.

### validate

**Mode:** read-only. **Purpose:** requested validation (internal read).

**Required after the operation:** None.

**Optional:** `ID`.

### templates

**Mode:** read-only. **Purpose:** internal pinned scaffold resolution.

**Required after the operation:** None.

**Optional:** `TEMPLATE_ID {idea,business,specification,technical-design,implementation-plan,code-review,security-review,verification-report,test-strategy,test-scenarios,test-automation}`.

### skills

Optional `--stage ACTIVITY` selects pinned expertise for a lifecycle/readiness or QA
activity (see `skills --help` for choices), adding `selection` without replacing the
existing `skills` catalog response. This is read-only and authorizes no work.

**Mode:** read-only. **Purpose:** internal domain guidance resolution.

**Required after the operation:** None.

**Optional:** None.

### adoption-preflight

**Mode:** read-only. **Purpose:** internal adoption check.

**Required after the operation:** None.

**Optional:** None.

## Identity and ownership

Profile writes are external to Git. Assignment writes metadata only after explicit confirmation; it neither approves nor advances.

See [stage policy and diagnostics](ownership.md) for eligibility, artifact schemas and recovery.

### identity-show

**Mode:** read-only. **Purpose:** internal attribution lookup.

**Required after the operation:** None.

**Optional:** None.

### identity-setup

**Mode:** write / explicit managed operation. **Purpose:** explicit local profile setup.

**Required after the operation:** `--display-name DISPLAY_NAME`, `--role ROLE (repeatable)`.

**Optional:** None.

### identity-edit

**Mode:** write / explicit managed operation. **Purpose:** explicit local profile edit.

**Required after the operation:** `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

**Optional:** `--display-name DISPLAY_NAME`, `--role ROLE (repeatable)`.

### inbox

**Mode:** read-only. **Purpose:** inbox.

**Required after the operation:** None.

**Optional:** None.

### pending-assignments

**Mode:** read-only. **Purpose:** pending assignments.

**Required after the operation:** None.

**Optional:** None.

### assign

**Mode:** write / explicit managed operation. **Purpose:** assign.

**Required after the operation:** `ID`, `--expected-revision EXPECTED_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--assignee ASSIGNEE`.

**Optional:** `--actor ACTOR`, `--track {engineering,qa}`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### ownership-initialize

**Mode:** write / explicit managed operation. **Purpose:** internal explicit legacy-owner declaration.

**Required after the operation:** `ID`, `--expected-revision EXPECTED_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--owner ASSIGNEE`.

**Optional:** `--actor ACTOR`, `--track {engineering,qa}`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

## Discovery

New creates metadata/idea and, in installed managed execution, runtime-history.json; updates append Discovery history. Completion/reopening write lifecycle/ownership metadata, retaining original idea and downstream history.

See [stage policy and diagnostics](interactive-discovery.md) for eligibility, artifact schemas and recovery.

### new

Optional `--idea-details-file PATH` supplies a strict mapping of six section strings/nulls:
`users`, `expected_value`, `initial_scope`, `success_criteria`, `assumptions`, `open_questions`.
The original Problem comes only from `--idea`. No inference or semantic classification
is performed. Unknown keys/types/duplicate keys reject with `E_TEMPLATE_CONTEXT`.

**Mode:** write / explicit managed operation. **Purpose:** new shorthand.

**Required after the operation:** `--title TITLE`.

**Optional:** `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`, `--requester REQUESTER`, `--idea IDEA`.

### discovery-update

**Mode:** write / explicit managed operation. **Purpose:** Discovery conversation / changes.

**Required after the operation:** `ID`, `--expected-revision EXPECTED_REVISION`, `--operation-id OPERATION_ID`, `--changes-file CHANGES_FILE`.

**Optional:** None.

### discovery-complete

**Mode:** write / explicit managed operation. **Purpose:** Discovery advance.

**Required after the operation:** `ID`, `--expected-revision EXPECTED_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`.

**Optional:** `--requester REQUESTER`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### discovery-reopen

**Mode:** write / explicit managed operation. **Purpose:** explicit upstream reopening.

**Required after the operation:** `ID`, `--expected-revision EXPECTED_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`.

**Optional:** `--requester REQUESTER`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

## Business Refinement and approval

Draft writes business.md/history via recoverable publication. Decisions/advance append metadata; approval publishes an immutable Business baseline.

See [stage policy and diagnostics](business-approval.md) for eligibility, artifact schemas and recovery.

### business-generate

**Mode:** write / explicit managed operation. **Purpose:** explicit Business drafting.

**Required after the operation:** `ID`, `--expected-source-revision EXPECTED_SOURCE_REVISION`, `--operation-id OPERATION_ID`, `--editor EDITOR`, `--reason REASON`, `--document-file DOCUMENT_FILE`.

**Optional:** `--expected-business-revision EXPECTED_BUSINESS_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`.

### business-revise

**Mode:** write / explicit managed operation. **Purpose:** authorized Business refinement.

**Required after the operation:** `ID`, `--expected-source-revision EXPECTED_SOURCE_REVISION`, `--operation-id OPERATION_ID`, `--editor EDITOR`, `--reason REASON`, `--document-file DOCUMENT_FILE`.

**Optional:** `--expected-business-revision EXPECTED_BUSINESS_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`.

### business-review

**Mode:** read-only. **Purpose:** Business review/status/details.

**Required after the operation:** `ID`.

**Optional:** None.

### business-request-changes

**Mode:** write / explicit managed operation. **Purpose:** Business changes.

**Required after the operation:** `ID`, `--expected-review-revision EXPECTED_REVIEW_REVISION`, `--expected-business-revision EXPECTED_BUSINESS_REVISION`, `--operation-id OPERATION_ID`, `--reason REASON`, `--feedback FEEDBACK`.

**Optional:** `--reviewer GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### business-approve

**Mode:** write / explicit managed operation. **Purpose:** Business approve.

**Required after the operation:** `ID`, `--expected-review-revision EXPECTED_REVIEW_REVISION`, `--expected-business-revision EXPECTED_BUSINESS_REVISION`, `--operation-id OPERATION_ID`, `--reason REASON`, `--decision DECISION`.

**Optional:** `--approver GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--acknowledge-open-item ACKNOWLEDGE_OPEN_ITEM (repeatable)`.

### business-advance

**Mode:** write / explicit managed operation. **Purpose:** Business advance.

**Required after the operation:** `ID`, `--expected-review-revision EXPECTED_REVIEW_REVISION`, `--expected-business-revision EXPECTED_BUSINESS_REVISION`, `--operation-id OPERATION_ID`, `--reason REASON`, `--approval-id APPROVAL_ID`.

**Optional:** `--actor GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### business-recover

**Mode:** write / explicit managed operation. **Purpose:** internal inspected recovery.

**Required after the operation:** `ID`.

**Optional:** None.

## Functional Analysis and approval

Draft writes specification.md/history; gate decisions append metadata. Approval freezes Analysis inputs; advancement creates pending work tracks for new cycles.

See [stage policy and diagnostics](analysis-approval.md) for eligibility, artifact schemas and recovery.

### analysis-generate

**Mode:** write / explicit managed operation. **Purpose:** explicit Analysis drafting.

**Required after the operation:** `ID`, `--expected-analysis-review-revision EXPECTED_ANALYSIS_REVIEW_REVISION`, `--expected-baseline-id EXPECTED_BASELINE_ID`, `--expected-handoff-id EXPECTED_HANDOFF_ID`, `--operation-id OPERATION_ID`, `--editor EDITOR`, `--reason REASON`, `--document-file DOCUMENT_FILE`.

**Optional:** `--expected-analysis-revision EXPECTED_ANALYSIS_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`, `--feedback-file FEEDBACK_FILE`.

### analysis-revise

**Mode:** write / explicit managed operation. **Purpose:** authorized Analysis refinement.

**Required after the operation:** `ID`, `--expected-analysis-review-revision EXPECTED_ANALYSIS_REVIEW_REVISION`, `--expected-baseline-id EXPECTED_BASELINE_ID`, `--expected-handoff-id EXPECTED_HANDOFF_ID`, `--operation-id OPERATION_ID`, `--editor EDITOR`, `--reason REASON`, `--document-file DOCUMENT_FILE`.

**Optional:** `--expected-analysis-revision EXPECTED_ANALYSIS_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`, `--feedback-file FEEDBACK_FILE`.

### analysis-review

**Mode:** read-only. **Purpose:** Analysis review/status/details.

**Required after the operation:** `ID`.

**Optional:** None.

### analysis-request-changes

**Mode:** write / explicit managed operation. **Purpose:** Analysis changes.

**Required after the operation:** `ID`, `--expected-analysis-review-revision EXPECTED_ANALYSIS_REVIEW_REVISION`, `--expected-analysis-revision EXPECTED_ANALYSIS_REVISION`, `--expected-baseline-id EXPECTED_BASELINE_ID`, `--expected-handoff-id EXPECTED_HANDOFF_ID`, `--operation-id OPERATION_ID`, `--reason REASON`, `--feedback FEEDBACK`.

**Optional:** `--reviewer GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### analysis-approve

**Mode:** write / explicit managed operation. **Purpose:** Analysis approve.

**Required after the operation:** `ID`, `--expected-analysis-review-revision EXPECTED_ANALYSIS_REVIEW_REVISION`, `--expected-analysis-revision EXPECTED_ANALYSIS_REVISION`, `--expected-baseline-id EXPECTED_BASELINE_ID`, `--expected-handoff-id EXPECTED_HANDOFF_ID`, `--operation-id OPERATION_ID`, `--reason REASON`, `--decision DECISION`.

**Optional:** `--approver GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--acknowledge-open-item ACKNOWLEDGE_OPEN_ITEM (repeatable)`.

### analysis-advance

**Mode:** write / explicit managed operation. **Purpose:** Analysis advance.

**Required after the operation:** `ID`, `--expected-analysis-review-revision EXPECTED_ANALYSIS_REVIEW_REVISION`, `--expected-analysis-revision EXPECTED_ANALYSIS_REVISION`, `--expected-baseline-id EXPECTED_BASELINE_ID`, `--expected-handoff-id EXPECTED_HANDOFF_ID`, `--operation-id OPERATION_ID`, `--reason REASON`, `--approval-id APPROVAL_ID`.

**Optional:** `--actor GATE_ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### analysis-recover

**Mode:** write / explicit managed operation. **Purpose:** internal inspected recovery.

**Required after the operation:** `ID`.

**Optional:** None.

## Engineering

Mutations publish typed immutable Engineering bundles and append metadata/audit. Checks also capture actual output; development-start snapshots source boundaries. Application edits are separate native-agent actions.

See [stage policy and diagnostics](engineering.md) for eligibility, artifact schemas and recovery.

### engineering-review

**Mode:** read-only. **Purpose:** Engineering review/status/details.

**Required after the operation:** `ID`.

**Optional:** None.

### engineering-write

**Mode:** write / explicit managed operation. **Purpose:** Engineering start / authorized revision.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {design,plan,implementation,security}`, `--input-file INPUT_FILE`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`.

### engineering-approve

**Mode:** write / explicit managed operation. **Purpose:** Engineering approve.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {design,plan,implementation,security}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--acknowledge-open-item ACKNOWLEDGE_OPEN_ITEM (repeatable)`, `--authorize-limitation AUTHORIZE_LIMITATION (repeatable)`.

### engineering-request-changes

**Mode:** write / explicit managed operation. **Purpose:** Engineering changes.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {design,plan,implementation,security}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### engineering-advance

**Mode:** write / explicit managed operation. **Purpose:** Engineering advance.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {design,plan,implementation,security,verification}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### development-start

**Mode:** write / explicit managed operation. **Purpose:** explicit Engineering start only.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### check-run

**Mode:** write / explicit managed operation. **Purpose:** Engineering approved named check.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--check-id CHECK_ID`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### verification-remediate

**Mode:** write / explicit managed operation. **Purpose:** explicit failed-check remediation.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--check-id CHECK_ID (repeatable)`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### security-remediate

**Mode:** write / explicit managed operation. **Purpose:** explicit Security remediation.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--finding FINDING (repeatable)`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### engineering-finalize

**Mode:** write / explicit managed operation. **Purpose:** Engineering final advance/finalization.

**Required after the operation:** `ID`, `--expected-engineering-revision EXPECTED_ENGINEERING_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`.

## Independent QA and track reconciliation

QA writes publish qa-baselines and track history in metadata. Check execution retains output; adoption/reconciliation are explicit authority changes, never implicit migrations.

See [stage policy and diagnostics](work-tracks.md) for eligibility, artifact schemas and recovery.

### track-review

**Mode:** read-only. **Purpose:** internal status/details.

**Required after the operation:** `ID`.

**Optional:** None.

### qa-review

**Mode:** read-only. **Purpose:** QA review/status/details.

**Required after the operation:** `ID`.

**Optional:** None.

### tracks-adopt

**Mode:** write / explicit managed operation. **Purpose:** internal explicit legacy adoption.

**Required after the operation:** `ID`, `--expected-track-revision EXPECTED_TRACK_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### track-reconcile

**Mode:** write / explicit managed operation. **Purpose:** internal explicit upstream impact reconciliation.

**Required after the operation:** `ID`, `--expected-track-revision EXPECTED_TRACK_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--track {engineering,qa}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`.

### qa-write

**Mode:** write / explicit managed operation. **Purpose:** QA start / authorized revision.

**Required after the operation:** `ID`, `--expected-qa-revision EXPECTED_QA_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--input-file INPUT_FILE`, `--kind {strategy,scenarios,automation,verification}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-source-revision EXPECTED_SOURCE_REVISION`, `--expected-template-digest EXPECTED_TEMPLATE_DIGEST`.

### qa-approve

**Mode:** write / explicit managed operation. **Purpose:** QA approve.

**Required after the operation:** `ID`, `--expected-qa-revision EXPECTED_QA_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {strategy,scenarios,automation,verification}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-source-revision EXPECTED_SOURCE_REVISION`, `--acknowledge-open-item ACKNOWLEDGE_OPEN_ITEM (repeatable)`.

### qa-request-changes

**Mode:** write / explicit managed operation. **Purpose:** QA changes.

**Required after the operation:** `ID`, `--expected-qa-revision EXPECTED_QA_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {strategy,scenarios,automation,verification}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-source-revision EXPECTED_SOURCE_REVISION`.

### qa-advance

**Mode:** write / explicit managed operation. **Purpose:** QA advance/completion.

**Required after the operation:** `ID`, `--expected-qa-revision EXPECTED_QA_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--kind {strategy,scenarios,automation,verification}`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-source-revision EXPECTED_SOURCE_REVISION`.

### qa-check-run

**Mode:** write / explicit managed operation. **Purpose:** QA start approved checks.

**Required after the operation:** `ID`, `--expected-qa-revision EXPECTED_QA_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--check-id CHECK_ID`.

**Optional:** `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--expected-source-revision EXPECTED_SOURCE_REVISION`.

## Runtime selection, compatibility and provenance

These operations preserve existing artifact/approval formats and never imply artifact
approval, advancement or assignment. Selection writes only the Epic's runtime-history.json;
ordinary managed writes journal an exact runtime/file receipt under the existing lock.
Context receipts stay outside Git. Compatibility probes use installed local Python and
actual read-only validators, not AI APIs. Use the [version-management contract](runtime-version-management.md)
for safe boundaries, exact retry, interruption recovery and procedural trust limits.

### runtime-probe

**Mode:** read-only. **Purpose:** internal read-only candidate contract/input probe.

**Required after the operation:** None.

**Optional:** `ID`.

### runtime-status

**Mode:** read-only. **Purpose:** inspect default/effective selection and artifact runtime receipts.

**Required after the operation:** None.

**Optional:** `ID`, `--track {engineering,qa}`, `--skill-root SKILL_ROOT`, `--artifact ARTIFACT`.

### runtime-session

**Mode:** explicit write / external receipt or inspected recovery. **Purpose:** declare loaded instructions in a fresh context; external receipt only.

**Required after the operation:** `--fresh-context-id FRESH_CONTEXT_ID`, `--instructions-digest INSTRUCTIONS_DIGEST`.

**Optional:** `ID`, `--track {engineering,qa}`, `--skill-root SKILL_ROOT`.

### runtime-check

**Mode:** read-only. **Purpose:** read-only future-scope compatibility preview.

**Required after the operation:** `ID`, `--runtime RUNTIME`.

**Optional:** `--track {engineering,qa}`.

### runtime-bind

**Mode:** explicit write / external receipt or inspected recovery. **Purpose:** explicit initial legacy future-work selection; no past attribution.

**Required after the operation:** `ID`, `--runtime RUNTIME`, `--expected-runtime-revision EXPECTED_RUNTIME_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--reason REASON`.

**Optional:** `--track {engineering,qa}`, `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--reconciliation RECONCILIATION`.

### runtime-promote

**Mode:** explicit write / external receipt or inspected recovery. **Purpose:** explicit compatible future-stage/track selection.

**Required after the operation:** `ID`, `--runtime RUNTIME`, `--expected-runtime-revision EXPECTED_RUNTIME_REVISION`, `--operation-id OPERATION_ID`, `--decision DECISION`, `--reason REASON`.

**Optional:** `--track {engineering,qa}`, `--actor ACTOR`, `--expected-profile-revision EXPECTED_PROFILE_REVISION`, `--reconciliation RECONCILIATION`.

### runtime-recover

**Mode:** explicit write / external receipt or inspected recovery. **Purpose:** inspected completion of original provenance/known transaction.

**Required after the operation:** None.

**Optional:** None.

## Additional entrypoints: installation and preflight

These are outside `sdlc.py`'s 57-operation count. Arguments come from their parsers.
See [installation](installation-and-adoption.md) for defaults, exact output, safe
registration retirement and read-only preflight interpretation.

| Entrypoint | Required flags | Optional flags | Effects / diagnostics |
|---|---|---|---|
| `install.py install` | `--revision REV --project PROJECT` | `--source SOURCE --runtime-root DIR --skill-root DIR --python PYTHON --preview-working-tree` | Writes external pinned runtime and non-overwriting loader; never application source. Validates environment/resources/pins. Preview must be explicit and bound to HEAD. |
| `install.py prepare` | `--source SOURCE --revision SHA --project PROJECT` | `--runtime-root DIR --python PYTHON --preview-working-tree` | Publishes/validates an immutable snapshot without selecting it. |
| `install.py update` | `--source SOURCE --revision SHA --project PROJECT --expected-default DIGEST --operation-id OP --actor NAME --decision TEXT` | `--skill-root DIR --runtime-root DIR --python PYTHON --preview-working-tree` | Prepares candidate beside old snapshot and explicitly switches verified owned default with audit/recovery. |
| `install.py rollback` | `--expected-default DIGEST --operation-id OP --actor NAME --decision TEXT` | `--runtime EXACT_RECORDED_PATH --skill-root DIR` | Restores previous verified default only; never request/application state. |
| `install.py show` | None | `--skill-root DIR` | Read default registration, resolver and administrative history. |
| `install.py list` | None | `--runtime-root DIR` | Read/verify installed snapshots, including explicit corrupt-entry diagnostics. |
| `install.py recover` | None | `--skill-root DIR` | Explicitly restore prior registration from inspected before/after intent; reject unrelated edits. |
| `install.py verify` | `--runtime RUNTIME` | `--expected-digest DIGEST --skill-root DIR` | Reads/verifies files, interpreter, catalogs and registration; never repairs. |
| `adoption.py` | `--project PROJECT` | `--runtime RUNTIME --skill-root DIR` | Read-only Git/layout/source/output/instruction/registration/environment checks; JSON ready and baseline_ready are not approvals. |

Installation requires a retained interpreter, compatible dependencies, accessible Git
revision and external destinations; a conflicting registration must be inspected, not
overwritten. Installer errors are structured diagnostics; successful installation is
not proof of host UI discovery. The shared administrative parser also accepts --skill-root for prepare/list; those two
operations do not use it to activate a registration. Default root help lists delegated
operations; each OPERATION --help describes its actual parser.

The isolated discovery smoke is a contributor test
helper, not a product operation or an automatic approval mechanism.

## Important semantic restrictions beyond argparse

- `new` needs a supplied requester or valid profile; `identity-setup` never overwrites.
  `identity-edit` replaces only supplied fields and uses the reviewed profile token.
- Business/Analysis `--expected-*-revision` assertions bind current artifacts and
  supporting history. Existing draft replacement needs its exact revision even where
  argparse makes that flag optional. Analysis baseline/handoff assertions refer to
  **Business** authority, not an arbitrarily chosen Analysis snapshot.
- Actor flags are optional when the external profile supplies attribution; do not combine
  an explicit actor with expected-profile attribution or impersonate a historical actor.
- `engineering-write` kinds: design, plan, implementation, security. Approval and feedback
  support design/plan/implementation only; advancement additionally supports verification
  and security. Parser choices are shared and broader than each operation's policy.
- QA writing supports strategy/scenarios/automation; approval supports scenarios/automation.
  `qa-request-changes` supports scenarios/automation; `qa-advance` supports scenarios,
  automation or verification. Parser acceptance of a kind is not lifecycle eligibility.
- Engineering Plan approval/advance/start reject a changed generation source. Only explicit
  Plan feedback before any current-cycle Development start permits return from readiness.
- Governed Design requires exact explicit limitation consent. Source-bound implementation
  review rejects unsupported authority. QA limitation checks do not count as product cases.
- QA checks require Engineering verification/Security/final-verification context, reviewed
  code, approved QA automation and current source. Completion is explicit and separate
  from both running checks and Engineering advancement.
- Track adoption is a restricted pre-development legacy operation; reconciliation is an
  explicit impact decision after changed Analysis, not migration by metadata editing.

The read-only helper's known `advance` → `development-start` suggestion at Development
readiness conflicts with shared conversation policy. Use explicit `start engineering`
and inspect its successful result before edits. No executable change fixes it here.


## Optional Git collaboration entrypoint

`git_collaboration.py` is a separate deterministic publication wrapper, leaving the
57 existing core parser operations intact. Its configuration, strict request envelopes,
event mapping, status/sync, run/publish, recover/confirm/abandon, baseline and read-only
integration check are documented in [Git-native collaboration](git-native-collaboration.md).
It is bundled with the external runtime. Existing local CLI calls stay unchanged when
unconfigured; configured writes require bridge context and existing runtime sessions.
