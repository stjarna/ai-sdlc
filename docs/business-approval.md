# Procedural Human Business Approval Gate — Increment 4

Increment 4 records explicit Product Owner decisions and separately advances an Epic
to `ready_for_analysis`. Functional Analysis itself is not implemented. The human
declares an identity and supplies decision text; neither is authenticated. An
unrestricted AI agent can invoke these operations while claiming a human identity.
This PoC does **not** technically guarantee human-only authorization. SHA-256 is
content identity and corruption detection, not a signature or authorization receipt.

## Lifecycle

```text
business_refinement --business-approve---------> business_refinement
business_refinement --business-request-changes-> business_refinement
business_refinement --business-advance---------> ready_for_analysis
ready_for_analysis  --discovery-reopen---------> discovery
```

Approval and advancement require separate explicit instructions. No
`business_approved` state exists. Requesting changes supersedes earlier approval;
it records feedback without modifying the business document. A later explicit
approval may supersede that feedback after appropriate refinement and review.
Feedback that introduces a substantive new requirement must still be captured
through Discovery reopening and reconciliation before becoming confirmed business
content. The CLI does not decide whether feedback has been addressed semantically.

## Metadata and review revision

Metadata schemas `0.1` and `0.2` remain readable without migration. The first new
decision operation upgrades only its target Epic to `0.3`, adding an append-only
`business_decisions` list. Existing lifecycle/history entries are preserved. Subsequent
Discovery completion, reopening and refinement retain schema `0.3` and its decisions.

Each decision has a script-assigned `BD-0001` ID, operation ID, typed action
(`approve` or `request_changes`), declared actor, reason, explicit text, UTC timestamp,
expected review revision, exact business digest, business revision operation ID,
source revision, Discovery completion operation ID, acknowledged open item IDs and
baseline ID (null for request changes). Advancement is an append-only lifecycle event
referencing the selected approval and baseline; it does not create a second approval.

`business-review` adds `review_revision`, `open_items` and `approval` to its existing
output, also exposed by `open`. The review revision hashes the exact bytes of metadata,
original idea, Discovery history, business document and business history, including
absence. Existing Epic, source and business revision meanings stay unchanged. Directory
renames do not affect these revision tokens. A concurrent decision changes the review
revision even when the business document has not changed.

`approval` reports `latest_decision`, `status`, `valid`, reason codes, `can_advance`
and the active `analysis_input` reference when in `ready_for_analysis`. Review does
not write or migrate files. Baseline corruption produces `ok: false`, a file-specific
diagnostic and an invalid approval view, retaining safely readable context for inspection.
Mutation fails closed, including corruption of a historical referenced baseline.

## CLI contracts

Use the environment in the [operation contract](../orchestrator/scripts/README.md).
All three new writers require Epic ID and:

```text
--expected-review-revision R --expected-business-revision B --operation-id UNIQUE_ID
```

Here `R` and `B` come from a fresh `business-review`. These are tool-facing arguments;
humans review the displayed content and make decisions, rather than manage hashes.

| Operation | Additional required arguments | Effect |
|---|---|---|
| `business-review ID` | None | Read-only review, decision and baseline integrity view |
| `business-request-changes ID` | `--reviewer NAME --reason TEXT --feedback TEXT` | Append PO feedback, keeping `business_refinement` |
| `business-approve ID` | `--approver NAME --reason TEXT --decision TEXT` | Freeze the current input and append explicit approval, keeping `business_refinement` |
| `business-advance ID` | `--actor NAME --reason TEXT --approval-id BD-0001` | Verify the selected effective approval and enter `ready_for_analysis` |

For approval, repeat `--acknowledge-open-item U-001` for **every** unresolved `U-...`
item and proposed `P-...` item shown by review. The supplied set must match exactly;
duplicates and unknown IDs are rejected. The skill must obtain the human's explicit
acknowledgement rather than infer it. Acknowledgement does not resolve questions or
promote AI assumptions into confirmed requirements. In the established To-Do example,
`U-001` carries deferred question `D-0006`; the approval text should explicitly state
that this rule remains deferred pending the support discussion.

All writers require a current, reconciled draft and `business_refinement`. After
advancement, further business/source changes require explicit Discovery reopening.
No Analysis operation or artifact is introduced.

## Immutable approved input

```text
business-baselines/<SHA-256-of-canonical-manifest>/
├── manifest.json
├── business.md
├── idea.md
├── discovery.yaml
├── metadata.yaml
└── business-history.yaml
```

The five supporting artifacts preserve exact bytes from immediately before approval.
The manifest records their hashes, Epic/schema identity, original idea reference,
business digest and revision operation ID, source revision and Discovery completion
operation ID. The original idea can have another local path; its frozen role is
`idea.md`, with that original reference retained in the manifest and metadata.
The canonical manifest excludes its own ID. Its SHA-256 identifies the directory.

The frozen metadata is historical evidence, not a second live state authority. An
approval record in live metadata references this baseline. The CLI never overwrites
a baseline; existing content is verified before reuse. All referenced baseline files
must be regular and nonsymlink, with the exact declared set and hashes. Validation
also checks frozen Discovery provenance, document references and business history.
The snapshot does not copy application code or external resources mentioned in prose.

An approval is effective only while it is the latest PO decision and its business
digest **and revision operation ID**, source revision and Discovery completion
operation ID still match. Request changes, a business revision (even identical bytes),
or Discovery reopening invalidates its authority. New completion/reconciliation
requires fresh approval. Returning A → B → A cannot reactivate an old approval.
Historical decisions and baseline contents remain preserved.

## Publication, concurrency and recovery

All writers use the existing project lock and optimistic revision checks. Approval
publishes and fsyncs a complete baseline directory before atomically replacing
`metadata.yaml`. That replacement is the approval commit point. Before it, even a
fully published baseline has no authority. Request changes and advancement each have
their own single-file metadata commit point. The existing business revision journal
and `business-recover` continue to handle business document multi-file publication.

A failed baseline preparation returns `E_BASELINE_WRITE`, without an approval. A
hard exit may leave `.pending-*` directories or a complete unreferenced baseline,
plus the project lock. Inspect these and establish that the writer is no longer
active before removing an abandoned lock. Do not remove an approved/referenced
baseline. A retry verifies and fsyncs a reusable orphan before publishing its decision.
Temporary/orphan directories are never treated as approval evidence. No automatic
garbage collection or cross-host recovery protocol is implemented.

An uncertain metadata durability result returns `E_WRITE_UNCERTAIN`. Retry the exact
operation ID and inputs: if publication happened, it returns `replayed: true` with
the original decision/transition ID and the **current** state. A replay never appends
a replacement approval or restores superseded authority. Reusing an ID with changed
inputs fails with `E_IDEMPOTENCY`. Missing/corrupt referenced baselines must be restored
from known-good evidence; the CLI never regenerates them from the mutable draft.

Concurrent decisions against the same review token cannot both commit. Approval
followed by revision is allowed and makes the approval stale. Revision first makes
the earlier approval/advance request stale. Advancement first prevents further
revision through lifecycle checks. Busy writers fail with `E_PROJECT_BUSY`.

Important gate diagnostics are `E_ACKNOWLEDGEMENT`, `E_APPROVAL_REQUIRED`,
`E_APPROVAL_STALE`, `E_APPROVAL_SUPERSEDED`, `E_BUSINESS_DECISIONS`,
`E_BASELINE_MISSING`, `E_BASELINE_INTEGRITY`, `E_BASELINE_CONTEXT`,
`E_BASELINE_WRITE`, and the existing revision, status, write and idempotency codes.

## Future Functional Analysis handoff

The advancement event carries the approval and baseline IDs. In `ready_for_analysis`,
review derives `analysis_input` from that event. A future Analysis operation must
verify the baseline, consume its frozen business/source artifacts and reference its
ID in outputs. Unresolved issues remain unresolved. Reopening clears the active
handoff view while preserving the historical event. Increment 4 does not run Analysis.

## Manual acceptance with the established To-Do example

Use a disposable copy of the Increment 3 acceptance project, including its business
history. If unavailable, reconstruct the documented fictional Discovery example and
label it as test data. Obtain actual human responses at each decision point; do not
simulate them. Keep all artifacts outside the orchestrator repository.

1. Run `business-review REQ-0001`. Inspect the exact business revision and source
   revision, B-003 references to D-0005/D-0004, and U-001 carrying deferred D-0006.
2. Ask the Product Owner for feedback. If changes are requested, record their exact
   words with `business-request-changes`, fresh R/B tokens and declared identity.
   Verify state stays `business_refinement`, draft bytes stay unchanged and no
   approval exists. Apply explicitly requested refinements through `business-revise`.
3. Present a fresh review and exact digest. **Stop for explicit approval**, including
   acknowledgement that D-0006 remains deferred pending support discussion. With the
   human's actual identity/text, run:

   ```text
   business-approve REQ-0001 --expected-review-revision R --expected-business-revision B --operation-id O --approver NAME --reason TEXT --decision EXPLICIT_APPROVAL_TEXT --acknowledge-open-item U-001
   ```

4. Run review again. Verify `approval.valid: true`, `can_advance: true`, the baseline
   contains all five exact supporting artifacts, U-001 remains unresolved and the
   lifecycle is still `business_refinement`. Approval alone must not advance.
5. **Stop for a separate human advancement instruction.** After receiving it, use
   fresh R/B values and the returned approval ID:

   ```text
   business-advance REQ-0001 --expected-review-revision R --expected-business-revision B --operation-id O2 --actor NAME --reason EXPLICIT_ADVANCEMENT_REASON --approval-id BD-0001
   ```

   Verify `ready_for_analysis` and the selected `analysis_input`. No Analysis files
   should have been created.
6. On a disposable branch copied after step 4 and before advancement, obtain a human
   refinement/reopen instruction and change the draft or source through documented
   operations. Use fresh review tokens to attempt advancement with the earlier
   approval ID. Verify `E_APPROVAL_STALE` (or revision conflict for stale tokens).
   For a business-only wording change, revise back to the exact earlier bytes and
   verify approval remains stale. For a source change, reconcile against the new
   source revision rather than restoring an obsolete source header. A new explicit
   approval is required. Do not infer it from the earlier signoff.

## Limitations

The CLI enforces logical append-only history and write-once baselines for cooperating
writers. Unrestricted filesystem edits can bypass those rules. Hashes detect ordinary
corruption, not a coordinated rewrite of the audit and every digest. Semantic fidelity
and whether deferred issues are acceptable require human judgment. Full snapshots and
retained histories increase storage and validation time; no compaction, external
identity service, workflow engine or independent-clone coordination is added.
