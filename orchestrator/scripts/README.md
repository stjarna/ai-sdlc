# Discovery, Business Refinement and Approval operation contract

`sdlc.py` is a deterministic Python 3.10+ CLI. It operates on an explicitly selected
existing project directory, independently of that project's application stack.
The conversational entrypoint is [SKILL.md](../skill/SKILL.md).
Interactive updates, provenance rules, recovery and the manual evaluation guide are
documented in [Interactive Discovery](../../docs/interactive-discovery.md).
Increment 3 lifecycle, business document format, revision history, reconciliation
and manual acceptance are documented in
[Business Refinement](../../docs/business-refinement.md).
Increment 4 decisions, immutable baselines, separate advancement and manual acceptance
are documented in [Business Approval](../../docs/business-approval.md).

From the orchestrator repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r orchestrator/requirements.txt
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project new --title "Customer notifications" --idea "Customers need to know when their request changes."
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project open REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project validate REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project validate
```

These are tool-facing arguments. The skill derives a title and passes the user's
description; users need not specify IDs or paths when presenting a business idea.
`--version` reports the orchestrator version independently of the schema version.

## Schema 0.1

`new` creates `requirements/REQ-0001-<derived-slug>/metadata.yaml` and `idea.md`:

```yaml
schema_version: '0.1'
id: REQ-0001
title: Customer notifications
status: discovery
artifacts:
  idea: idea.md
```

All five fields are required; unknown fields, duplicate YAML keys (including nested
keys), aliases, merge keys, non-string mapping keys, unsafe YAML tags, and malformed YAML
are rejected. The title must be nonempty single-line text. IDs are canonical ASCII
`REQ-0001` through `REQ-9999`; exhaustion fails explicitly rather than wrapping.
Schema `0.1` supports `discovery` and `cancelled`: the latter is read-only
compatibility for retained cancelled records so their IDs remain reserved. Increment
3 upgrades an Epic to schema `0.2` only on explicit Discovery completion. Schema
`0.2` supports `discovery`, `ready_for_refinement` and `business_refinement`; its
append-only `lifecycle` entries record each completion, reopening and entry to
refinement. Increment 4 upgrades a target Epic to schema `0.3` on its first explicit
PO decision, adding append-only `business_decisions` and support for
`ready_for_analysis`. Approval itself keeps `business_refinement`; only explicit
advancement changes that lifecycle state. There is no cancellation or Functional
Analysis operation. Existing schema `0.1`/`0.2` records remain readable without migration.

Every immediate subdirectory of `requirements/` is treated as an Epic record.
Each must have a regular, nonsymlink `metadata.yaml`. Ordinary top-level files such
as a README are ignored, but a `REQ-*` file is an invalid Epic entry. Epic-directory
and requirements-directory symlinks are rejected. The metadata ID, not the folder
name, is authoritative: directory renames preserve identity and lookup still works.
No second directory index or ID counter is stored.

`artifacts.idea` must reference an existing UTF-8 file inside its own Epic directory.
Absolute paths, parent traversal, symlink escapes, and references to metadata itself
are rejected. Business content is stored only in the referenced Markdown file.
The template covers Problem, Users, Expected value, Initial scope, Success criteria,
Assumptions, and Open questions. Empty or absent level-two sections produce warnings;
this is a mechanical completeness check, not semantic analysis or a readiness gate.
Nonempty placeholders such as `TBD` and contradictory business statements are not
evaluated. Successful structural validation, even with no warnings, does not establish
business correctness or readiness for approval or implementation.

## Behavior and diagnostics

- `new`: validate the existing records, allocate highest existing numeric ID + 1
  (including cancelled records), derive a safe slug, and exclusively create the
  two files. Existing content is never overwritten. Handled failures remove files
  and the Epic directory created by that invocation. Empty input is allowed for
  business content, with warnings. A title is required.
- `open ID`: scan and validate the repository, find the unique metadata ID, and return
  its metadata, actual directory, content, and warnings without changing anything.
- `validate [ID]`: report structural validity for the requested record or all records.
  Repository-wide structural errors are always reported, including duplicate IDs.
  A repository with no Epic records is structurally valid. Missing business information
  is a warning; missing `idea.md` is a structural error.
- `discovery-update ID --expected-revision SHA256 --operation-id ID --changes-file JSON`:
  append typed records to a separate `discovery.yaml` with optimistic concurrency,
  a shared local write lock and operation idempotency. The changes file contains
  exactly `{"records": [...]}`. An empty list initializes history. This operation
  never changes metadata or the original idea; existing requests without history
  remain valid. See the linked guide for the record schema and examples.
- `discovery-complete ID --expected-revision SHA256 --operation-id ID --requester NAME --decision TEXT`:
  explicitly record Requester completion and enter `ready_for_refinement`. It requires
  persisted Discovery history and returns unresolved questions and proposed assumptions.
  This is not business approval.
- `discovery-reopen ID --expected-revision SHA256 --operation-id ID --requester NAME --decision TEXT`:
  explicitly return from refinement to Discovery. An existing draft/history is kept
  but marked for reconciliation.
- `business-generate ID --expected-source-revision SHA256 [--expected-business-revision SHA256] --operation-id ID --editor NAME --reason TEXT --document-file FILE`:
  persist an AI-written initial draft or explicit regeneration of a stale draft.
  A stale draft requires its current business revision as the expected revision.
- `business-revise ID --expected-source-revision SHA256 --expected-business-revision SHA256 --operation-id ID --editor NAME --reason TEXT --document-file FILE`:
  persist a human-refined draft or reconcile a stale one. The CLI validates structure
  and Discovery IDs, not the meaning of the prose.
- `business-review ID`: read-only draft, revision, source coverage and `current`
  flag, plus `review_revision`, `open_items`, and the latest approval/feedback with
  validity reasons and `can_advance`. An outdated draft is visible for comparison
  only, with `current: false`.
- `business-request-changes ID --expected-review-revision SHA256 --expected-business-revision SHA256 --operation-id ID --reviewer NAME --reason TEXT --feedback TEXT`:
  append declared PO feedback against the exact reviewed snapshot. It supersedes an
  earlier approval without changing the draft or leaving `business_refinement`.
- `business-approve ID --expected-review-revision SHA256 --expected-business-revision SHA256 --operation-id ID --approver NAME --reason TEXT --decision TEXT [--acknowledge-open-item U-001 ...]`:
  freeze all five supporting artifacts and append explicit procedural approval.
  Acknowledgements must exactly cover every displayed U/P item. State stays
  `business_refinement`. Declared identities are unauthenticated.
- `business-advance ID --expected-review-revision SHA256 --expected-business-revision SHA256 --operation-id ID --actor NAME --reason TEXT --approval-id BD-0001`:
  separately validate the selected latest approval, baseline and current source;
  atomically append the transition to `ready_for_analysis`.
- `business-recover ID`: after inspecting an interrupted Epic-local transaction,
  roll it forward if no unrelated changes have occurred.

`open` adds `source_revision` and optional `business` to the Epic view. `business`
includes current content, SHA-256 revision, source revision, reconciliation flag and
revision metadata (historical bytes remain in `business-history.yaml`). Revisions
hash exact bytes. The business document format and recovery constraints are in the
linked Increment 3 guide.
`review_revision` hashes metadata, idea, Discovery, business and business history exact
bytes. `approval` reports the latest decision, validity reasons, `can_advance` and the
active immutable `analysis_input` reference. `open_items` lists unresolved U/P items.
Baseline integrity failures produce read-only review diagnostics with `ok: false`;
mutations fail closed. Exact gate retries preserve the original decision/transition
and return the current Epic view; they never reinstate historical authority.

All output is JSON on stdout. `ok` describes structural success only, accompanied
by `operation`, `diagnostics`, and either `epic` (new/open/update) or `validated_ids`
(validate). Epic views add `revision`, optional `discovery` history and derived
`discovery_state` without changing the existing fields. Updates also return `replayed`
and assigned `record_ids`. Each diagnostic has `severity`, `code`, `file`, `message`, and optional
YAML `line`. Exit status is 0 for success (including warnings), 1 for operational or
validation failure, and 2 for argparse usage errors (which use stderr).

| Code | Meaning |
|---|---|
| `E_PROJECT`, `E_REQUIREMENTS`, `E_EPIC_DIRECTORY` | Invalid project or repository layout |
| `E_METADATA_FILE`, `E_READ`, `E_IO` | Missing/unreadable file or filesystem failure |
| `E_YAML`, `E_METADATA` | Invalid YAML, duplicate keys, or incorrect metadata fields |
| `E_SCHEMA_VERSION` | Unsupported or incorrectly typed schema version; no migration |
| `E_EPIC_ID`, `E_DUPLICATE_ID`, `E_EPIC_NOT_FOUND`, `E_ID_EXHAUSTED` | Invalid, ambiguous, missing, or exhausted identity |
| `E_TITLE`, `E_STATUS`, `E_ARTIFACTS` | Invalid field value or structure |
| `E_ARTIFACT_PATH`, `E_ARTIFACT_FILE` | Unsafe reference or missing artifact |
| `E_PROJECT_BUSY` | Transient local creation lock already exists |
| `W_DISCOVERY_INCOMPLETE` | Missing/empty business section; not a structural error |

History/update-specific diagnostics are listed in the Interactive Discovery guide.
Increment 3 also uses `E_LIFECYCLE`, `E_BUSINESS_DOCUMENT`,
`E_BUSINESS_REFERENCE`, `E_BUSINESS_PROVENANCE`, `E_BUSINESS_COVERAGE`,
`E_BUSINESS_HISTORY`, `E_BUSINESS_MISMATCH`, `E_BUSINESS_FILE`,
`E_BUSINESS_RECOVERY`, `E_WRITE_UNCERTAIN`, `E_REVISION_CONFLICT`,
`E_READ_CONFLICT`, `E_IDEMPOTENCY` and `E_STATUS` with file-specific JSON diagnostics.
Increment 4 adds `E_BUSINESS_DECISIONS`, `E_ACKNOWLEDGEMENT`,
`E_APPROVAL_REQUIRED`, `E_APPROVAL_STALE`, `E_APPROVAL_SUPERSEDED`,
`E_BASELINE_MISSING`, `E_BASELINE_INTEGRITY`, `E_BASELINE_CONTEXT` and
`E_BASELINE_WRITE`. Baseline preparation failures create no approval; retained orphans
can be verified and reused by an exact retry. Metadata publication uncertainty uses
`E_WRITE_UNCERTAIN`. See the approval guide for commit points and inspected recovery.

Creation and updates use a transient `.sdlc-discovery.lock/` directory at the project root;
cooperating concurrent local writers fail closed. The lock is removed after normal
completion or a handled exception and is not a context checkpoint. Independent-clone
coordination, hard process termination/power-loss recovery, and hostile concurrent
filesystem mutation are not covered. A stale lock requires inspection before manual
removal. Retain cancelled records: physically deleted records cannot reserve IDs
because this increment reads existing files only and never consults Git history.
For atomic update publication, idempotent retry and inspected stale-lock recovery,
see the guide. Creation's hard-termination limits remain unchanged.

The CLI never invokes Git or performs Functional Analysis. Unsupported schemas
and inconsistent existing records block creation/opening rather than being repaired.
