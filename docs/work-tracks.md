# Engineering and QA work tracks

New explicit Functional Analysis advancement atomically creates two pending work tracks
bound to the same approved Analysis baseline and advancement event. Engineering owns
Technical Design, Implementation Planning, application code, unit tests and build checks.
QA owns functional strategy/scenarios, test automation and integration/UI verification.
This is a logical workflow fork, not a Git branch, agent scheduler or automatic parallel
execution. Both tracks may progress independently through explicit authorized operations.

## Authority, ownership and start behavior

The existing accountable owner is retained for both initial tracks. Required roles are
**Engineering Lead** and **QA Lead / Tester**. Neither track starts or assigns a person
as a side effect of the fork. Each has an independent owner, assignee, assignment status,
append-only assignment history and next action. Transfer requires a nomination followed
by separate explicit confirmation. Informational roles are not authenticated RBAC.

`inbox` and `pending assignments` now display one row per track, including request ID/title,
track, role, owner, assignee, stage, pending state and next action. Assigning Engineering
removes only its pending row; QA remains in the previous owner's inbox until assigned.
Legacy requests without tracks retain the old single-row views and assignment behavior. Reopened upstream stages likewise use ordinary request assignment; inactive historical tracks are not treated as current downstream work.
At a later Analysis cycle, retain each previous track's accountable owner pending a new
explicit assignment; do not silently return transferred ownership to the Requester.

Native commands remain Codex `$sdlc COMMAND` and Claude `/sdlc COMMAND`:

```text
status
start engineering
start qa
review qa
approve engineering
advance qa
assign engineering
inbox
pending assignments
```

The agent resolves Epic, profiles, tokens and operations internally. `status`/`details`
may summarize both tracks. With two possible tracks, an action or track-specific review
without a known conversational selection asks one question: Engineering or QA? The CLI
returns `E_TRACK_AMBIGUOUS`; it never guesses the latest modified document or current
profile's role. An explicitly selected conversational track is passed internally with
`--track`; it is not a new checkpoint file.

After Analysis advancement, say: “Two workstreams are ready: Engineering — awaiting
Engineering Lead; QA — awaiting QA Lead / Tester. Who would you like to assign first?”
An unknown assignee leaves that track pending. No notification or work starts automatically.

## Fixed workflows and minimal gates

Engineering uses the existing scalar lifecycle as its backward-compatible projection:

```text
ready_for_technical_design -> technical_design
  human Design approval -> separate advance -> ready_for_implementation_planning
  explicit start/draft -> implementation_planning
  human Plan approval -> separate advance -> ready_for_development
  explicit development-start -> development + unit/build
  human code approval -> separate advance -> verification
  explicit joined-verification advance -> security_review
  current Security review -> separate advance -> final_verification -> explicit finalize
```

Engineering-only plans still declare ordered tasks, safe paths, Analysis coverage,
uncertainty and named checks, but require **unit and build categories only**. They must
not contain integration/UI checks or own the reserved `qa/` code namespace. Plan approval
does not depend on QA strategy/scenarios, and code approval is not QA automation approval.

QA has its own state and artifact history:

```text
ready_for_test_design -> explicit QA start -> test_design
  strategy + scenarios -> one human scenario approval (also binds strategy)
  separate advance -> test_automation
  prepared automation -> human automation approval -> separate advance
  ready_for_verification -> actual approved checks -> explicit QA completion -> verified
```

There is no extra approval gate for the strategy document. QA strategy and functional
scenarios consume the **approved Analysis directly**, with no Technical Design or
Implementation Plan prerequisite. Every active FR/AC receives a coverage disposition;
blocked/proposed requirements cannot acquire specified expected outcomes. Each specified
case has stable `TC-...` ID, references, preconditions, action and observable outcome.
Changing strategy/scenarios invalidates their own approval and dependent automation,
not Engineering approval. An Engineering draft or revision leaves scenario authority intact.

Concrete automation may later consume the approved Design's interface contract. It binds
that exact Design, approved scenarios and its own QA code fingerprint. A changed Design
can make automation require adaptation without invalidating functional expectations.
QA automation lives under reserved `qa/`, including any QA-specific package/lock files;
this keeps code ownership and review fingerprints separate. QA files cannot be used to
hide application changes under Engineering's approved paths. Runtime side effects remain
subject to host permissions; these are audit controls, not an OS sandbox.

## Integrated verification and source binding

Actual integration/UI runs wait for reviewed Engineering implementation and approved QA
automation. A check must name its approved cases and Analysis references, use literal
argv and record actual results. Every specified case must map to automation; both
integration and real UI categories are required in this PoC. Command labels alone do
not prove UI behavior or semantic coverage.

The join requires:

- Active reconciled tracks referencing the same immutable Analysis handoff.
- Valid Engineering Plan and human implementation approval for current application files.
- Valid QA strategy/scenario approval and automation approval for current QA files and interfaces.
- QA coverage of all implemented Engineering acceptance criteria, with blocked/excluded
  coverage and unresolved questions explicitly reported.
- Every required named QA check passed for the exact current combined execution context.
- A separate explicit QA verification-completion event for that context.

Incomplete QA never counts as successful Engineering verification. Engineering readiness
alone does not advance QA; QA completion alone does not advance Engineering. Security and
finalization recheck the join, and the final report retains QA artifact/approval/source
references and actual results. Changing application code invalidates execution evidence
and code approval; changing QA code invalidates automation approval/evidence. Neither
change resolves business uncertainty or silently rewrites the other track's documents.

After authorized remediation, repeat the affected reviews and checks. QA can rerun for a
new reviewed implementation while retaining still-valid functional scenarios. Historical
results and decisions remain auditable; old completion does not authorize a new source.

## Metadata, revisions and recovery

An additive, independently versioned `work_tracks` mapping is created only by explicit
Analysis advancement or legacy adoption. Metadata schemas `0.5/0.6` and existing baseline
formats remain readable; old files are not migrated on read. New writers retain existing
schema versions. Older strict binaries may reject new additive fields, as with ownership.

```yaml
work_tracks:
  schema_version: '0.1'
  cycles:
    - id: analysis-advance-operation
      analysis_baseline: exact-approved-analysis-baseline
      origin: advance
      engineering:
        ownership: {owner: Alice, assignee: null, required_role: Engineering Lead, ...}
        reconciliation: []
        legacy_plan: null
      qa:
        ownership: {owner: Alice, assignee: null, required_role: QA Lead / Tester, ...}
        reconciliation: []
        status: ready_for_test_design
        history: []
  operations: [] # auditable fork/adopt/assignment/reconciliation decisions
```

Engineering artifact history remains `engineering_history`; its scalar lifecycle is
not duplicated in a second state machine. QA artifact/action history belongs to its
cycle. Full past cycles are preserved. Artifact prose remains the sole `content.md`
in immutable bundles; current views provide logical Technical Design, Implementation
Plan, Test Strategy, Test Scenarios and automation documents without mutable duplicates.
Active domain packages are version1.1.0 with orchestrator contract0.10. Exact1.0.0 instruction packages remain in `domain-skills/versions/<name>/1.0.0/`; historical pins match their original bytes. Archived relative links retain the original package layout: restore the snapshot into that layout when replaying its instructions rather than editing the archive.

QA bundles use `qa-baselines/` and the existing canonical manifest/publication functions.
Every artifact records exact Analysis authority and versioned domain instruction pins.

Review tokens are scoped: QA changes do not stale an unrelated Engineering decision,
and Engineering changes do not stale a QA scenario decision. Automation/source review
uses additional file fingerprints. Metadata publication still rechecks the full original
metadata under the common project lock, preventing a stale candidate from dropping an
unrelated update. The lock serializes writes; independent track tokens do not introduce
simultaneous file publication. A busy writer may be retried after reading current state.

All writers reuse exact idempotency, append-only audit prefixes, durable content-addressed
publication and atomic metadata replacement. Pre-commit failure leaves no partial fork;
an orphan complete bundle can be verified/reused. Post-commit uncertainty is resolved by
reading state and retrying the exact operation. No new journal, checkpoint, automatic
lock removal, Git action or identity service is added.

## Changed Analysis and explicit reconciliation

Upstream Discovery reopening deactivates both tracks without deleting artifacts or
history. A newly approved and explicitly advanced Analysis creates a new track cycle.
Both tracks initially require explicit impact assessment (`track-reconcile`) against the
new authority, even when bytes happen to match a prior cycle. Record the actual human
assessment and affected/unchanged behavior. No artifact or approval is silently copied
into the new cycle; create new reconciled revisions and obtain the applicable fresh
approvals. Old cycles remain immutable. Each track can reconcile independently, but the
join remains blocked until both are ready.

## Tool contracts

Existing Engineering operations remain available. New track operations:

```text
track-review ID
tracks-adopt ID --expected-track-revision TOKEN --operation-id OP --decision TEXT
track-reconcile ID --track engineering|qa --expected-track-revision TOKEN --operation-id OP --decision TEXT
assign ID --track engineering|qa --expected-revision TOKEN --operation-id OP --decision TEXT --assignee NAME
command-context COMMAND --request ID --track engineering|qa
qa-review ID
qa-write ID --kind strategy|scenarios|automation --input-file FILE
qa-approve ID --kind scenarios|automation [--acknowledge-open-item ID ...]
qa-request-changes ID --kind scenarios|automation
qa-advance ID --kind scenarios|automation|verification
qa-check-run ID --check-id CHECK --expected-source-revision CURRENT_APPLICATION_HASH
```

QA mutations additionally require `--expected-qa-revision`, `--operation-id`, `--decision`;
automation approval requires `--expected-source-revision` from `qa_source_revision`.
Identity uses the existing local profile and optional expected-profile revision, or an
explicit legacy actor. Decisions retain actual wording, not agent-fabricated quotations.

QA strategy uses `{content, coverage, unresolved}`. Scenarios add `cases` with
`{id, requirements, preconditions, action, expected, status: specified|blocked}`.
Automation adds `paths` under `qa/`, `source_revision` for QA files and `checks` using
the existing named-check schema plus required `cases: [TC-...]`. Only integration/UI
categories belong to QA. The CLI automatically records the approved scenario and Design
bindings. Coverage/uncertainty use the existing engineering field shape and frozen
Analysis IDs; `implemented` in QA coverage means specified scenario coverage, not test execution.

## Legacy compatibility and current acceptance

Legacy Task Due Date Management acceptance must **not be migrated or edited without explicit authorization**.
Its Design approval remains valid, its combined Implementation Plan remains unapproved,
and its immutable snapshots and actual human decisions remain byte-for-byte retained.
Legacy requests continue using the previously implemented sequential operations unless
explicitly adopted; new Analysis advancement creates the fork automatically.

For this pre-development scenario, a human may explicitly authorize `tracks-adopt` after
reviewing its current legacy context. Adoption appends management metadata and creates
pending Engineering/QA responsibility, preserving every old artifact and Design approval.
It records the old unapproved combined plan as a historical legacy revision and blocks
its approval. Prepare a **new Engineering-only Plan revision**, then create QA strategy
and scenarios independently from the approved Analysis. No old QA text is silently
promoted to a new approved QA artifact. Obtain the new Plan and QA decisions separately.
Adoption after development or an approved combined Plan is deliberately rejected: use
explicit upstream impact assessment/reopening instead of inventing a migration policy.
The completed real acceptance later received explicit adoption, separate Engineering/QA approvals, remediation and successful joined verification. Its full preserved history and reproducible demo are now in [examples/todo-app](../examples/todo-app/README.md); this compatibility policy does not retroactively change any earlier snapshot.

## Manual conversational acceptance

Use a new disposable project or a copy of an approved Analysis draft. All decisions are
real human decisions; synthetic setup must be clearly labelled and is not signoff.

1. Review/approve Analysis, then explicitly advance. Verify both tracks appear pending
   with the same approved baseline, retained owner and no generated artifacts/work.
2. Decline one or both nominations. Inspect `inbox` and `pending assignments`; confirm
   both roles remain visible. Assign Engineering with separate confirmation and verify
   only its owner/history changes. Repeat independently for QA when desired.
3. `$sdlc start qa` before any Design exists. Draft strategy/scenarios from frozen FR/AC,
   review uncertainty, explicitly approve and advance QA design. Verify no Engineering
   artifact or lifecycle changed. An ambiguous bare action asks only which track.
4. `$sdlc start engineering`: draft Design with Security input, obtain Design approval and
   separate advancement, then an Engineering-only Plan approval. Verify this works even
   before QA scenarios are approved; do not auto-start coding or advance QA.
5. Authorize development. Implement code/unit tests inside Engineering paths and obtain
   source-bound human code approval. QA separately prepares `qa/` automation using the
   available interface contract, obtains human automation approval and advances readiness.
6. Advance reviewed Engineering code to Verification. Try the integrated gate with QA
   incomplete: expect explicit blocking. Run actual QA integration/browser checks, inspect
   results and coverage, and explicitly complete QA. Only then advance the joined gate.
7. Perform Security Review/remediation and final verification with current combined
   evidence. Change a source or QA automation file in a separate copy: old results must
   become stale while unrelated functional scenarios remain approved.
8. Reopen upstream in another copy, renew Analysis and advance. Verify both tracks require
   explicit reconciliation and fresh current-cycle artifacts/approvals; history remains.
9. Separately exercise opt-in legacy adoption of the unapproved combined plan. Verify
   original approved Design/hash/history remain intact, old Plan approval is blocked,
   and replacement Engineering/QA drafts require distinct human decisions.

Limits remain procedural identities, local POSIX execution, no OS sandbox or cross-clone
locking, source fingerprints excluding dependency directories, snapshot storage growth,
and semantic/human review responsibility. The reserved `qa/` path is a deliberate PoC
constraint, not a module/team model. There is no remote registry, enterprise RBAC, Teams,
custom UI, automatic parallel AI execution, release automation or automatic Git operation.

## Document discovery

[Artifact storage](artifact-names.md) defines canonical physical QA/Engineering names and exact-file links. New snapshots use manifest0.2; legacy content.md/0.1 baselines remain readable without migration. Both reviews and aggregate status/details expose descriptors matching actual files. Naming does not grant lifecycle authority.

## Governance-aware cycles and supplemental QA checks

New Analysis advancements use work-track schema0.2 with governance0.1 as documented in
[Engineering governance](engineering.md#governance-corrections-contract-01). Historical
cycle prefixes remain unchanged, and ordinary managed operations cannot downgrade the
contract or move that prefix. Assignment/reconciliation and independent stage authority
are unchanged. Legacy adoption preserves historical Design authority and stays legacy;
there is no automatic in-progress governance migration.

Governed QA automation requires `limitation_checks: []` even when none exist. Each
supplemental check has the normal `id`, `category`, `argv`, `cwd`, `timeout`, `requirements`
and `scenario`, plus `limitations` listing authorized Design limitation IDs, instead of
product `cases`. Every authorized limitation must have a supplemental check; unknown IDs
or claims outside the affected requirements are rejected. Results are source-bound and
required at the joined gate, but never contribute to product case/AC coverage. The
independent Analysis-derived QA strategy/scenarios remain unchanged by a limitation.
