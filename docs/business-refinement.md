# Discovery Completion and Business Refinement — Increment 3

Increment 3 ends with a reviewed business draft. It does **not** approve business
requirements or begin Functional Analysis. The Requester explicitly completes
Discovery; a Product Owner then refines `business.md`. The same person may fill both
roles, but completion is not approval. The human declares an identity; the PoC does
not authenticate it and cannot prevent an unrestricted agent from calling operations.

## Lifecycle and artifacts

```text
discovery --discovery-complete--> ready_for_refinement
ready_for_refinement --business-generate/revise--> business_refinement
ready_for_refinement/business_refinement --discovery-reopen--> discovery
```

`metadata.yaml` schema `0.1` remains valid and is unchanged for old Discovery Epics.
The first completion upgrades only that Epic to schema `0.2` and adds append-only
`lifecycle` entries. No global migration occurs. `idea.md` stays unchanged.
`discovery.yaml` remains the authoritative sourced Discovery history. The current
business draft is `business.md`; `business-history.yaml` stores full UTF-8 document
bytes as base64 for every revision, plus SHA-256 digest, previous digest, source
revision, declared editor, reason, timestamp, mode and operation ID. The sidecar is
Epic-local; it is not a general event store. Historical bytes are recoverable from
the sidecar without Git commits.

The source revision hashes the exact `idea.md` and `discovery.yaml` bytes (including
absent history), independent of metadata status. `open` also returns the existing
Epic revision, which hashes metadata, idea and Discovery. Business revisions hash the
exact `business.md` bytes. A change of line endings changes that digest.

## Business document contract

The AI skill drafts the prose. The CLI checks only document shape, current source
references, classification and persistence; it cannot verify semantic fidelity.
Use this form, including the three top-level categories in order:

```markdown
# Business Refinement — REQ-0001

Source revision: <64-character SHA-256 from open>

## Confirmed information
### Business value
- **B-001** [D-0001] A sourced, human-readable business statement.

## Unresolved issues
- **U-001** [D-0002] A question that is still open, unknown or deferred.

## Unconfirmed proposals
- **P-001** [D-0003] An AI assumption awaiting confirmation.
```

Under Confirmed information, use descriptive `###` subsections for business value,
target users, initial scope, exclusions, success measures, constraints and
dependencies where supported. Each substantive line is an ID item with at least one
Discovery reference. The CLI requires every current confirmed statement/decision,
every unresolved question and every proposed assumption to be represented. It rejects
superseded statements and proposals cited as confirmed. Use `None recorded.` for an
empty Unresolved issues or Unconfirmed proposals section; do not infer an answer.
Keep an item's ID when refining the same requirement and allocate a new ID for a new
requirement. The CLI checks ID uniqueness, not semantic identity across revisions.

Human refinement changes wording and business organization through `business-revise`.
For a new substantive requirement or a corrected Discovery fact, use
`discovery-reopen`, append sourced Discovery records, complete Discovery again and
then explicitly regenerate or revise against the new source revision. The skill
shows the diff and traces each changed requirement to source evidence. It must never
invent requirements to fill a section.

## Review and reconciliation

`discovery-complete` needs an explicit Requester decision, declared identity, exact
Epic revision and operation ID. It reports questions that remain open, unknown or
deferred and assumptions still proposed. Those issues do not automatically block
completion; the Requester sees them and makes the decision. Completion is not an
approval of `business.md`.

`discovery-reopen` records a separate explicit decision and returns the Epic to
`discovery`. The existing draft and all its revision history stay intact. The draft
is marked `needs_reconciliation: true` while the Epic is in Discovery or
`ready_for_refinement`, and remains stale after new Discovery records are captured
and completed. `business-review` reports `current: false`; it still exposes the old
draft for comparison but does not present it as current. A `business-generate` or
`business-revise` operation with the **new** source revision and the previous
business revision performs the explicit reconciliation. No automatic merge occurs.

## Concurrency, idempotency and recovery

All writers share the Increment 1/2 project lock. Lifecycle operations atomically
replace one metadata file. Business publication writes an Epic-local transaction
journal, then publishes `business.md`, its history and, when entering refinement,
metadata. `open`, `validate` and `business-review` reject an interrupted transaction
instead of presenting mixed versions. After inspecting the journal and confirming
that no writer is active, `business-recover` rolls it forward. It checks that each
target is either its recorded old version or the intended new version. It refuses
unrelated edits. Do not delete the journal to bypass this check.

An identical operation retry returns `replayed: true` even after later revisions.
An operation ID reused with different inputs fails. Stale source or business
revisions fail rather than overwrite. Handled write uncertainty returns
`E_WRITE_UNCERTAIN`; inspect, recover if needed, then retry the same operation.
This is local cooperating-writer safety, not a security boundary. External/manual
edits and filesystem corruption can still require Git or backup recovery.

## Manual acceptance: Task Due Date Management

Use a fresh temporary project, not proprietary data. The generic orchestrator does
not require the demonstration app to be implemented. Start with the example idea:
"People forget commitments. Let them record deadlines against tasks." Then:

1. Run `new`; use `discovery-update` to save that quoted user statement, a question
   about optional deadlines and a question about reminders. Save the user's explicit
   answer that deadlines are optional and reminders are excluded. Review the
   persisted `D-...` IDs in a new CLI process.
2. Ask the Requester to inspect the derived Discovery view and explicitly confirm
   completion. Run `discovery-complete` with their declared identity, decision,
   current Epic revision and a unique operation ID. Verify `ready_for_refinement`.
3. Ask the AI skill to draft `business.md` from the confirmed records. It should
   describe business value, target users and scope only where supported, cite each
   `D-...` record and keep any unresolved point separate. Run `business-generate`.
4. Ask the Product Owner to refine wording or priority. Show the diff; persist it
   through `business-revise` with the current source and business revisions. Inspect
   both exact document snapshots in `business-history.yaml` and their editor/reason.
5. Run `business-review`. Check `current: true`, all source IDs, unresolved items and
   the SHA-256 revision. No approval or Analysis status should exist.
6. Reopen Discovery, add a sourced change such as "Deadlines must include a time of
   day", then complete it again. Verify `business-review` says `current: false` and
   the former draft is preserved. Explicitly regenerate or revise against the new
   source revision; verify it becomes current and retains the older snapshot.

Review semantic accuracy manually: the script cannot tell whether a grammatically
valid statement faithfully represents its cited Discovery record.
