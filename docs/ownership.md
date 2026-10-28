# Ownership, Assignment and Stage Handoff

Ownership tracks accountability independently of content approval and lifecycle.
Owner means the person accountable for moving the request forward. Assignee means
the person responsible for its next activity. Required role describes that activity;
it is not an enforced permission or verified professional qualification.

## New requests and legacy compatibility

New requests require the local declared identity profile, or the additive explicit
`new --requester NAME` argument. The initial requester becomes both owner and assignee
for Discovery. Missing identity fails before creating any files; no unowned request
or invented identity is created. Existing callers without a local profile must now
supply a requester. Other creation, ID allocation and cleanup behavior is unchanged.

Existing schemas remain readable without migration. When metadata has no ownership,
a single unambiguous Requester recorded in completion/reopening lifecycle evidence is
shown as the accountable owner. Multiple distinct recorded Requesters are ambiguous;
Discovery `user` labels, business editors, host login and Git names are not substituted.
If unknown, explicitly declare the initial requester/owner before assignment or handoff.
The read-only view reports `initialization_required` and never rewrites legacy files.

An explicit legacy assignment/handoff materializes the recorded Requester in the audit
before applying the change. No separate initialization question is needed when the
historical Requester is unambiguous. Unknown legacy owners appear in the project overview
as `owner_declaration_required`; they cannot be attributed to a person's inbox until
that missing historical information is explicitly supplied.

## Responsibilities and atomic handoff

| Target activity | Required role |
|---|---|
| Discovery | Requester / Business Stakeholder |
| Business Refinement | Product Owner |
| Functional Analysis | Business Analyst |
| Technical Design readiness | Engineering Lead / Architect |

Discovery completion enters `ready_for_refinement`; Business advancement enters
`ready_for_analysis`; Analysis advancement enters `ready_for_technical_design`.
In the same atomic metadata replacement as each authorized transition, retain the
current owner, clear the assignee and mark `awaiting_assignment` for the next role.
Explicit upstream reopening similarly returns responsibility to the Discovery role
while retaining the owner until a confirmed assignment. Starting a draft within its
already selected stage does not silently assign anyone.

The agent offers nomination after reporting successful advancement. If the next person
is unknown, leave the pending state unchanged and retain the owner in Awaiting Handoff.
A crash or lost response after advancement cannot hide the pending handoff: it is already
persisted. Approval never creates a handoff. Assignment never approves, advances, changes
a specification, alters a baseline, or starts the next stage. Technical Design execution
remains unavailable even when a responsible architect has been nominated.

## Shared commands

Codex uses `$sdlc inbox`, `$sdlc pending assignments` and `$sdlc assign [request-id]`.
Claude uses the equivalent `/sdlc` invocations. Natural-language requests remain supported.
The six existing commands retain their meanings. Resolve `assign` by active context or
an unambiguous title/ID, using the read-only context helper; never guess a request.
Inbox and pending assignments are project-level views and need no active Epic selection.

Inbox uses the external local profile and displays two distinct groups:

- **Assigned Work:** requests whose current assignee matches the declared user.
- **Awaiting Handoff:** requests whose owner is still accountable while assignment is pending.

Rows show request ID/title, lifecycle, owner, assignee, responsibility, assignment status,
required role/target stage, elapsed waiting time where known, and a recommended next action.
The project-wide pending view lists all pending handoffs, including those in the current
owner's inbox. It also exposes legacy records needing an owner declaration. Elapsed time
is derived on read from a recorded UTC timestamp; there is no SLA, escalation or timer job.

For assignment, determine the required role from lifecycle and ask for a recipient if
missing. Then ask a separate explicit confirmation naming request, person and role:

> Assign REQ-0001 to John Smith as Product Owner?

Only a submitted explicit confirmation authorizes the transfer. Preserve its actual
wording. The successful assignment sets both owner and assignee to the nominated person,
removes it from pending assignments and makes it visible in that person's inbox. A person
may also be reassigned explicitly. Names do not provision user accounts or notifications.
If the current user differs from the recorded owner, do not claim the owner has been
contacted or has consented. Keep responsibility visible; any explicit delegated transfer
is procedurally attributed to its actual declared actor, not authenticated or role-enforced.

## Persistence and tool contracts

Metadata gains one optional `ownership` mapping without rewriting old schemas or records:

```yaml
ownership:
  owner: Alice
  assignee: null
  required_role: Product Owner
  assignment_status: awaiting_assignment
  target_stage: business_refinement
  since: '2026-10-28T12:00:00Z'
  history: # ordered initialize / handoff / assign events
    # operation_id, action, actor, identity_source, timestamp, expected_revision,
    # from_owner, to_owner, assignee, required_role, assignment_status, target_stage,
    # lifecycle_id, decision
```

The current values must reproduce the retained history. Handoff events bind to the
actual lifecycle event, role and timestamp. Assignment events cannot change stage or
required role. Actors are declared and unauthenticated; profile roles remain informational.
Ownership matching uses complete display names (case-insensitive, trimmed), not fuzzy
identity inference. Distinct people with the same name cannot be distinguished in this PoC.

Tool operations, invoked internally by the agent:

```text
sdlc.py --project PROJECT inbox
sdlc.py --project PROJECT pending-assignments
sdlc.py --project PROJECT command-context assign [--request TITLE_OR_ID]
sdlc.py --project PROJECT assign ID --assignee NAME --expected-revision REV --operation-id OP --decision ACTUAL_CONFIRMATION
sdlc.py --project PROJECT ownership-initialize ID --owner NAME --expected-revision REV --operation-id OP --decision ACTUAL_DECLARATION
```

Assignment actors come from the local profile, or the existing-style explicit `--actor`
argument. Optional `--expected-profile-revision` protects attribution against profile
changes since review. Request revision/operation IDs remain internal to the agent.
A missing owner requires explicit initialization; this operation cannot silently replace
an already tracked owner. Use assignment for subsequent transfers.

All writes use the existing project lock, revision checks, atomic metadata persistence
and operation ledger patterns. Concurrent assignments against one revision cannot both
commit. Exact retries return current state without duplicating events or restoring an
older owner. Changed retry inputs produce `E_IDEMPOTENCY`. Metadata write uncertainty
uses the existing `E_WRITE_UNCERTAIN` recovery rule; no separate checkpoint or journal
is introduced. Assignment history is append-only through management operations.

Business/Analysis document bytes, audit decisions and lifecycle entries remain unchanged
by assignment. New metadata revision tokens change, so a pending content approval using
an older review must be revalidated. Already approved content remains valid: immutable
baselines are neither rewritten nor reselected. Frozen ownership history prefixes are
checked against retained live history; appending assignments preserves that prefix.
Original legacy baseline formats and hashes remain readable and unchanged. Older binaries
with strict metadata fields may reject new ownership mappings, as with other additive
PoC extensions; there is no automatic downgrade or backward writer migration.

## Manual Codex acceptance

Use a disposable project and explicit human decisions. Keep all artifacts outside the
implementation checkout; do not simulate Product Owner nominations or confirmations.

1. Set up the local identity as the actual requester and start a new request. Verify
   the requester is owner and assignee in Assigned Work.
2. Review Discovery and explicitly authorize completion through `$sdlc advance`.
   Verify `ready_for_refinement`, retained owner, no assignee and required Product Owner.
   Completion is the advancement; do not perform a second artificial Discovery approval.
3. When asked who should receive the request, answer that no recipient is known yet.
   Expect “No Product Owner assigned; the request remains in your inbox as Awaiting Handoff.”
4. `$sdlc inbox`: verify the request appears under Awaiting Handoff with its ID/title,
   current responsibility, role, status and suggested nomination action.
5. `$sdlc pending assignments`: verify the same request, retained owner, target Business
   Refinement stage and elapsed waiting time appear in the project overview.
6. `$sdlc assign REQ-0001`: nominate a real test recipient. Verify a separate confirmation
   question names that person, request and Product Owner role. Before answering, verify
   ownership has not changed. Then explicitly confirm.
7. Inspect `$sdlc details`: verify old/new owner, actual assignment actor, timestamp and
   confirmation in retained history. Lifecycle remains `ready_for_refinement`; no business
   document or next-stage execution has been started by assignment.
8. Verify the request disappears from pending assignments and the requester's inbox.
9. In a new conversation/profile representing the recipient's declared identity, run
   `$sdlc inbox`. Verify Assigned Work contains the request and ownership is reconstructed
   from persisted metadata without repeating the prior nomination.
10. On a separate copy with actual approved Business/Analysis evidence, assign explicitly
    and verify approvals, immutable baseline bytes and historical decisions remain valid.

Static adapter checks and fixture-based automated tests do not prove Claude runtime or
human conversational behavior. Claude runtime remains outside PoC acceptance.

## Limitations

This is local Epic accountability, not IAM, verified delegation, enforced owner-only
permissions, a user directory or notifications. Display-name collisions and separate Git
clone concurrency remain unresolved. Legacy records missing requester evidence require
human clarification, never invented ownership. Direct filesystem edits can bypass logical
append-only rules; baselines detect retained-prefix inconsistencies but not a coordinated
rewrite of every digest and audit. No Stories, module routing, escalation, SLA management,
Teams/Entra integration, custom UI, workflow engine or Technical Design execution is added.

## Sequential engineering extension

The separately authorized [engineering slice](engineering.md) now consumes the approved Analysis handoff through Technical Design, planning, controlled development, verification, Security review and a final report. Earlier increment scope statements describe their historical boundaries. The extension preserves approval separation, existing audit/baseline formats and declared identity semantics.

For new Analysis advancements, the [Engineering/QA fork](work-tracks.md) now creates two independently owned pending tracks. Existing non-fork records retain their historical contracts; adoption and upstream reconciliation are explicit.
