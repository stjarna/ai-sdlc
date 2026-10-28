# Shared Approval Infrastructure and Analysis Approval — Increment 6

Increment 6 reuses the procedural Business gate infrastructure for Functional Analysis.
The skill assesses meaning and captures the human's actual decision; the CLI enforces
structure, exact revision bindings, acknowledgement, persistence and lifecycle.
Declared identities are unauthenticated. Hashes identify content, not people; an
unrestricted agent or filesystem editor can bypass procedural authorization.

## Lifecycle and human decisions

```text
functional_analysis --analysis-request-changes--> functional_analysis
functional_analysis --analysis-approve----------> functional_analysis
functional_analysis --analysis-advance----------> ready_for_technical_design
ready_for_technical_design --discovery-reopen----> discovery
```

Approval and advancement require separate explicit human instructions. Approval does
not authorize Technical Design execution or implementation. After advancement,
Analysis revisions and new gate decisions are blocked; an exact retry of an earlier
operation may report current state. Reopen Discovery explicitly for a new cycle.
Historical decisions, revisions and baselines remain intact. Reconciliation and fresh
approval are required, even when a subsequent cycle returns to identical text.

The skill presents a concise business-oriented review of behavior, coverage, exclusions
and uncertainty. It accepts clear natural-language approval referring to that exact
review, with explicit acknowledgement of every listed uncertainty. Vague positive
feedback, silence and tool permissions are not approval. Preserve the actual decision
wording and the local declared identity loaded from the shared profile. See
[Command UX and Local Identity](command-ux.md) for explicit one-time setup, editing
and automatic attribution; roles remain informational and unauthenticated.
Agent-written reason summaries are distinct from human quotations. After recording
approval, report success and wait for a separate advancement instruction.

## CLI contracts

All three mutating commands require a request ID and:

```text
--expected-analysis-review-revision R
--expected-analysis-revision A
--expected-baseline-id B --expected-handoff-id H
--operation-id UNIQUE --reason TEXT
```

`R` is the complete `analysis_review_revision` returned by a fresh `analysis-review`;
`A` is the specification SHA-256. `B` and `H` retain their Increment 5 meaning: the
active **Business** baseline and Business advancement operation, not Analysis baseline
selection. The complete token covers metadata, original idea, Discovery, business
document/history, specification and Analysis history. Audit changes in metadata also
change the token. Specification digest plus revision operation identifies the revision;
a same-content new revision invalidates approval.

| Operation | Additional arguments | Effect |
|---|---|---|
| `analysis-review ID` | None | Read-only document/input, uncertainty, current approval and readiness context |
| `analysis-request-changes ID` | `--reviewer NAME --feedback TEXT` | Append actual feedback; supersede approval without editing the document |
| `analysis-approve ID` | `--approver NAME --decision TEXT` | Freeze inputs and append approval; keep lifecycle unchanged |
| `analysis-advance ID` | `--actor NAME --approval-id AD-0001` | Verify the latest effective approval and advance separately |

For approval, repeat `--acknowledge-open-item ITEM` for exactly the IDs shown in
`analysis_open_items`: inherited U/P items, active AQ questions (open/unknown/deferred),
AP proposals, and blocked/proposed FR/UC/BR/AC items. Duplicate, missing and unknown
acknowledgements fail. Acknowledgement does not answer a question, confirm an assumption,
remove blocked status, establish business correctness or establish implementation
readiness. Humans decide whether proceeding with these disclosed risks is appropriate.

`analysis-review` preserves its existing keys and adds `analysis_approval`,
`analysis_open_items` and `can_approve`; `approval_implemented` now reports `true`.
`can_approve` means structurally eligible for an explicit decision, not AI or human
approval. `semantic_assessment` remains `not_performed_by_cli`. `open` also exposes
Analysis approval and uncertainty. Existing `approval` and `open_items` remain Business
fields. The Analysis approval view exposes status, validity/reasons, latest decision,
`can_advance` and, after advancement, the frozen `technical_design_input` reference.

Diagnostics reuse `E_STATUS`, `E_UPDATE_INPUT`, `E_REVISION_CONFLICT`,
`E_IDEMPOTENCY`, `E_PROJECT_BUSY`, `E_ACKNOWLEDGEMENT`, `E_APPROVAL_REQUIRED`,
`E_APPROVAL_SUPERSEDED`, `E_APPROVAL_STALE`, `E_BASELINE_*` and `E_WRITE_UNCERTAIN`.
`E_ANALYSIS_DECISIONS` identifies invalid Analysis audit/provenance;
`E_APPROVAL_AUDIT` protects shared persistence against truncating audit prefixes.
Existing Business diagnostics and command arguments remain unchanged. If otherwise
valid live Business supporting bytes differ from their approved baseline (for example,
manual reformatting of history), `can_approve` is false and Analysis approval rejects
with `E_APPROVAL_STALE` before any decision is published. Reconcile upstream explicitly;
the CLI does not silently freeze a different source or repair supporting files. Changes to approved Analysis supporting bytes also
make that approval stale.

## Persistence and baseline dependencies

The first Analysis decision upgrades its target metadata to schema `0.5`, adding
append-only `analysis_decisions`. Older schemas `0.1–0.4` remain readable with no
read-time migrations. Every subsequent writer preserves `0.5` and both decision histories.

An `AD-0001` decision records operation/action, declared actor, actual decision or
feedback, reason, UTC timestamp, complete reviewed context, specification digest and
revision operation, upstream Business baseline/approval/advancement, acknowledged IDs,
and the Analysis baseline ID (null for request changes).

```text
analysis-baselines/<SHA-256-of-canonical-manifest>/
├── manifest.json
├── metadata.yaml
├── specification.md
└── analysis-history.yaml
```

These are exact pre-approval bytes. The canonical manifest schema `0.1` identifies the
request, all file hashes, specification revision and operation, Business baseline,
Business approval, Business advancement and acknowledgement set. It references the
existing content-addressed Business baseline rather than duplicating its business
content. Retain every Business dependency referenced by Analysis history. The original
idea and Discovery evidence remain available through those immutable dependencies.

Verification checks canonical identity, exact file set, safe nonsymlink paths, all
hashes, frozen lifecycle, upstream approval and handoff, Analysis history/provenance,
acknowledgements, reproduction of the original review token, and retained audit/history
prefixes. All referenced historical approvals are checked, not only the latest.
Corruption blocks mutation; review may expose safely readable context with `ok: false`.
Historical baseline validation reads frozen context and dependencies, never evaluates
it by recursively reopening the current live Epic.

Business baseline schema, canonical serialization, artifact roles, IDs and hashes are
unchanged. A new Business baseline may freeze schema `0.5` metadata after reopening;
old baselines are never migrated. Lifecycle action `analysis_advance` is distinct from
the existing Business `advance`. The latter retains its original fields and meaning.

## Shared transaction and recovery

`approval_common.py` provides revision fingerprints, canonical manifests, durable
baseline publication/read verification, exact replay checks, acknowledgement sets,
audit-prefix preservation and revision-checked metadata publication. Business and
Analysis modules retain their artifact sets, manifest rules, decision bindings,
unresolved-item rules and effective-approval policies. There is no workflow engine,
policy registry or authentication abstraction.

All gate and document writers share the existing project lock. Under that lock, a gate
loads/validates current inputs, checks exact replay before stale/status rejection,
checks expected context, publishes/verifies a complete durable baseline, rechecks
context and atomically replaces metadata. Metadata replacement is the decision commit
point. Request changes and advancement require only that metadata write.

Handled preparation failures clean pending directories. A crash can leave a pending
or unreferenced complete baseline and an abandoned lock, but no approval without the
audit commit. Inspect and establish that the writer has ended before operator cleanup
of a lock; never automatically bypass it. Exact retry verifies and fsyncs an orphan
before reuse. `E_WRITE_UNCERTAIN` requires reading persisted state and retrying the
same operation ID and inputs. Replay returns current state and never restores old
authority. Corrupt referenced baselines require known-good restoration.

Existing Business/Analysis document journals and their fixed recovery allowlists remain
unchanged. No additional approval journal or checkpoint system is introduced.

## Manual conversational acceptance

Use a disposable project outside this checkout with a genuinely approved/advanced
Business baseline and current Functional Analysis. Fictional setup must be labelled
as test data. A real Product Owner supplies all decisions below; do not simulate answers.
Use the shared SDLC skill, retaining transcripts and CLI responses as evidence.

1. Ask: “Review the Functional Analysis.” Expect a concise behavior/coverage summary
   and each uncertainty in business terms, including blocked behavior and assumptions.
   Inspect full artifacts and references on request; routine interaction should not
   require IDs, paths, hashes or command arguments.
2. Request a real wording refinement without changing approved business meaning.
   Verify `analysis-request-changes` preserves the actual feedback and lifecycle,
   followed by authorized `analysis-revise`. A substantive scope change requires
   upstream reopening rather than an invented requirement.
3. Say “Looks good.” Verify no approval or advancement. Then explicitly approve the
   reviewed document, acknowledging each listed unresolved question, proposal and
   affected blocked behavior. Set up the local declared identity profile once if missing. Verify
   actual words in the AD audit and a baseline bound to this exact revision operation.
4. Reopen/read review: approval is valid and lifecycle remains `functional_analysis`.
   Questions remain deferred/open and proposals remain unconfirmed. The agent reports
   approval and waits; it does not bundle onward advancement.
5. Give a separate explicit instruction to mark it ready for Technical Design.
   Verify `analysis-advance` enters `ready_for_technical_design`, keeps the Business
   handoff valid and exposes the frozen Analysis baseline. No design/Story is created.
   A new Analysis revision must be rejected.
6. In a separate disposable copy saved before step 5, authorize a revision, including
   a same-content revision test. Attempt advancement with the prior approval using
   fresh review tokens: expect `E_APPROVAL_STALE`; an old token produces conflict.
   A newer request-changes/approval makes the old selection superseded.
7. In another copy, explicitly reopen Discovery after approval/advancement. Verify
   both current approvals/handoffs become ineffective without deleting history.
   Renew completion/refinement/Business approval/advancement, explicitly reconcile
   Analysis, and verify the old Analysis approval remains stale. Obtain fresh human
   approval before any new advancement.
8. Resume in a fresh Codex conversation. Expect reconstruction from persisted artifacts,
   preserved identities as historical evidence (not a new declaration), no automatic
   approval/advancement and no repeated settled business questions.

Automated fixture decisions are not a substitute for this live conversational test.
Claude runtime verification remains outside PoC acceptance.

## Limitations

No authenticated identity, signatures, semantic correctness guarantee, external AI API,
custom UI, Technical Design, Stories, cross-clone locking or automatic Git operations.
Direct coordinated edits can bypass logical append-only guarantees. Full histories
and repeated baseline validation favor inspectability over storage/read efficiency;
there is no pruning or general migration framework. Advancing with uncertainty is an
explicit human risk decision, not implementation readiness.
