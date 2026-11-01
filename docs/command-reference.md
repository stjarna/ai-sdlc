# Conversational command reference

[Documentation index](README.md) · [First request](getting-started.md) · [Workflow](workflow.md) · [Deterministic CLI](cli-reference.md)

These commands express intent to the SDLC skill in the coding agent's conversation.
They are **not terminal commands**. The agent resolves project, request, stage, identity,
revisions and operation IDs, then invokes deterministic operations. Examples below are
illustrative inputs and outcomes, not recorded transcripts or guaranteed literal replies.

## Invocation and selection

- **Codex CLI/IDE:** `$sdlc <command>`; select the skill mention or `/skills`. Trailing
  text is prompt context, not a shell argument parser.
- **Claude Code:** `/sdlc <command>`; its adapter receives trailing arguments differently.
  Adapter availability/static validation does not establish runtime acceptance. Codex is
  the demonstrated acceptance target.
  The external installer registers Codex only; including the Claude adapter in the
  runtime does not register it with Claude. See [installation architecture](installation-architecture.md).
- Natural language expresses the same intent and obeys the same gates: “Review the
  current business specification” or “Show requests waiting for assignment.”

There are **ten routed commands**, plus skill-guided **`new`** creation shorthand.
`open`/`validate` are available CLI operations the skill can invoke on request; they are
not additional routing verbs. There are no implemented Story, Release, `move-story`,
automatic commit/push or deployment commands.

Select a request with an ID or an exact title, for example `$sdlc review REQ-0001`
or “Review Export saved results.” The agent passes this selector internally. IDs take
precedence; titles match case-insensitively, not fuzzily. Without an active selection,
the helper requires exactly one request. Missing or ambiguous context causes a question,
not selection by modification time. Project-level inbox/pending views need no request.

For forked requests use `engineering` or `qa`, such as `$sdlc review qa REQ-0001`.
Those words are conversational selectors, not a guarantee of every possible argument
order. `status`/`details` can show both tracks. Other track actions/reviews need a known
selection or ask “Engineering or QA?” Explicit track flags do not apply to legacy
single-track requests. `new`, `inbox` and `pending assignments` do not select one track.

## Decisions and effects at a glance

| Command | Reads / writes | Approval | Lifecycle | Ownership |
|---|---|---|---|---|
| `new` | Creates metadata and original idea | No | New `discovery` request | Requester is initial owner/assignee |
| `status` | Reads | No | Unchanged | Unchanged |
| `start` | Requested activity can write artifacts or execute checks | No | May enter the requested active stage | No transfer |
| `review` | Reads | No | Unchanged | Unchanged |
| `approve` | Appends exact-revision decision and immutable baseline | Eligible gates only | Unchanged | Unchanged |
| `changes` | Records feedback; separately authorized refinement writes revisions | Supersedes affected approval | Usually unchanged; eligible Plan recovery returns to planning | No transfer |
| `advance` | Appends authorized transition/finalization | No new artifact approval | Eligible transition only | Shared handoff retains owner pending assignment |
| `details` | Reads | No | Unchanged | Unchanged |
| `inbox` | Reads project responsibilities | No | Unchanged | Unchanged |
| `pending assignments` | Reads project pending handoffs | No | Unchanged | Unchanged |
| `assign` | Appends confirmed transfer | No | Unchanged | Transfers selected responsibility |

“Read-only” describes managed state. Reviews can include AI semantic assessment, which
is advisory. Local identity is declared and unauthenticated; its roles are informational,
not enforced RBAC. Missing profiles need explicit one-time setup, never a Git-name fallback.
See [identity details](command-ux.md#local-profile).

## `new` — create a requirement

**Syntax:** `$sdlc new` followed by the business idea, or “Create a requirement for
exporting saved results.” No existing request/track is selected. The agent needs the
project and a declared requester/profile. It preserves the user's original idea using
the pinned idea template, allocates the next local ID and creates `metadata.yaml` and
`idea.md`; the first conversational update creates `discovery.yaml`.

No approval, downstream draft or automatic advancement occurs. Git publication is
absent by default; an explicitly configured collaboration workflow publishes creation
as a separate recorded event. The typical
result identifies the request and asks one consequential clarification question. Missing
identity, namespace conflicts, malformed existing records, duplicate IDs and exhaustion
block creation; existing files are never overwritten. See [first-request example](getting-started.md#worked-example-first-requirement).

## `status` — see where work stands

**Syntax:** `$sdlc status [request] [engineering|qa]`.
Use it to resume an unambiguously selected request. A bare downstream status can
summarize both tracks, owners, approval currency, blockers and the next available action.
It writes no records and does not assign, approve, advance or initiate activity.

Example: `$sdlc status REQ-0001`. Expect a stage/progress summary, not a new draft.
No matching request yields `E_CONTEXT_MISSING`; multiple choices need selection
(`E_CONTEXT_AMBIGUOUS`). A failed integrity check remains a blocker, not a healthy status.

## `start` — initiate the selected activity

**Syntax:** `$sdlc start engineering [request]` or `$sdlc start qa [request]`.
Use it after the necessary preceding decisions. The agent must inspect actual persisted
readiness, approved inputs and any requested execution/setup permissions.

| Current context | Requested activity / resulting records |
|---|---|
| Shared Discovery | Continue adaptive conversation and persist sourced records; no automatic completion. |
| Business/Analysis readiness | Explicitly request the Business/Analysis draft in natural language. The generic helper provides read context, not a universal draft-generation route. Generation enters `business_refinement` / `functional_analysis`. |
| Engineering Design/Plan readiness | Draft through `engineering-write`; create a canonical immutable revision and enter `technical_design` / `implementation_planning`. |
| `ready_for_development` | Explicit `development-start`; successful result enters `development` and establishes implementation boundary. |
| Engineering active review/verification stages | Perform only the requested eligible review/check activity; no generic restart or implicit next-stage transition. Use the stage operations, not an invented universal start primitive. |
| QA ready/test design | Prepare strategy then scenarios from approved Analysis; first write enters `test_design`. |
| QA `test_automation` | Prepare reviewed-scenario automation and `test-automation.md`; no automatic execution or approval. |
| QA verification readiness | Execute named approved checks after required approvals and setup authorization; retain actual evidence. Starting checks does not complete QA. |

There is no approval or ownership transfer. Drafting, development boundary, artifacts,
check logs and QA evidence can change. Example: `$sdlc start engineering` at Development
readiness. **Before edits require exit 0, `ok: true` and returned `development`**, not
just eligibility or a pending call. Stale Plans, missing approvals, unresolved required
consent, incomplete QA and missing tools can block activity. Never infer a new permission
from a failed start. [Recovery example](#revision-or-failed-check-example).

## `review` — inspect before deciding

**Syntax:** `$sdlc review [request] [engineering|qa]`.
Discovery review derives confirmed statements, assumptions and unanswered questions from
history. Business/Analysis review shows the current document, source currency and gate
context. Engineering/QA review shows that track's eligible artifact, coverage, uncertainty,
results and readiness. An absent draft is reported honestly.

Example: `$sdlc review qa`. Expect strategy/scenarios or automation appropriate to the
stage, with blocked cases visible. No approval, lifecycle/ownership update or regenerated
artifact is implied. Missing request/track selection and corrupt/stale dependencies are
common blockers. Exact artifacts and raw evidence are available through `details`.

## `approve` — accept a reviewed exact revision

**Syntax:** `$sdlc approve [request] [engineering|qa]`.
The exact current content must have been presented. Otherwise the initial invocation
requests the review and a subsequent explicit decision; it cannot approve unseen content.
The agent summarizes remaining uncertainty, obtains any missing acknowledgements and
revalidates the revision and identity before recording the actual human wording.

| Stage | Approval meaning / persistence |
|---|---|
| Discovery | No approval gate. Review and explicitly complete Discovery instead. |
| Business Refinement | Append PO decision in metadata; freeze Business inputs in `business-baselines/`. |
| Functional Analysis | Append Analysis decision; freeze exact specification/history and Business dependency in `analysis-baselines/`. |
| Engineering Design | Approve current Design bundle; proposed observable prototype limitations need explicit consent in addition to uncertainty acknowledgement. |
| Engineering Planning | Approve current Engineering Plan bound to current Design and source snapshot. |
| Engineering Development | Approve source-bound implementation / `code-review.md` after required unit/build and conformance review. |
| QA test design | One scenario decision binds both strategy and scenarios; no separate strategy signoff. |
| QA automation | Separate approval binds automation and its current QA source/interfaces. |
| Security / Final Verification / readiness / Verified | No extra artifact approval operation. Use actual review, evidence, advancement/finalization gates. |

Engineering/QA decisions create typed immutable bundles and append audit; approval never
advances lifecycle, transfers ownership or creates Git commits. An already effective
approval is reported without duplication. “Looks good,” silence, tool permission and
conditional assent are insufficient. Acknowledgement neither answers questions nor
confirms assumptions. Generic Design approval does not authorize prototype limitations.

Example: after review, `$sdlc approve engineering`; if needed, answer one focused question
acknowledging the disclosed issues and explicitly authorizing proposed observable effects.
Missing acknowledgement (`E_ACKNOWLEDGEMENT`), limitation consent (`E_LIMITATION_CONSENT`),
unsupported conformance, stale source/revision or corrupt baselines block approval.
The next action, when ready, is a **separate** advancement instruction.

## `changes` — record feedback and refine

**Syntax:** `$sdlc changes [request] [engineering|qa]` plus actual feedback.
A bare invocation asks what should change. Feedback is persisted before only the
explicitly requested refinement is applied. No positive approval or ownership transfer
is created. Upstream business scope changes need explicit reopening and reconciliation.

| Stage | Effect |
|---|---|
| Discovery | Append sourced statements/linked corrections; original idea and prior records remain. |
| Business / Analysis active draft | Append actual feedback superseding affected approval; authorized revision updates document/history without advancing. |
| Engineering Design / Plan / implementation | Record change request against that kind; revise through the eligible stage workflow. |
| Engineering ready for Development | Plan feedback may return to `implementation_planning` **only before Development has started in the current cycle**. Preserve prior Design, Plan history and independent QA authority. |
| QA design / automation / verification | Record eligible QA rework and preserve history; automation/scenario consequences follow the current kind. Verification rework is not permission to change expected product behavior. |
| Other readiness, completed or upstream contexts | Ask for the applicable draft preparation, reopening or supported remediation. No universal rewind. |

Example: “Request changes to the Engineering Plan: refresh it against the current project
fingerprint; keep scope and Design unchanged.” Old baselines remain historical; fresh
Plan generation, approval, advancement and start are required. Late Plan recovery,
stale tokens, invalid kinds and lifecycle conflicts reject rather than rewriting history.
Actual operation-kind restrictions remain in the [CLI contracts](cli-reference.md).

## `advance` — separately authorize progression

**Syntax:** `$sdlc advance [request] [engineering|qa]`.
Requires an explicit human instruction and current required approval/evidence. It does
not approve stale work, assign a recipient or automatically start another activity.

| Stage | Eligible result |
|---|---|
| Discovery | Record explicit Requester completion → `ready_for_refinement`; not Business approval. |
| Business | Valid approved Business → `ready_for_analysis`. |
| Functional Analysis | Valid approved Analysis → `ready_for_technical_design`, with both pending tracks. |
| Engineering Design / Plan | Separate advancement → Planning readiness / Development readiness. |
| Engineering Development | Current implementation approval → `verification`. |
| Engineering Verification | Current joined QA checks/completion and Engineering authority → `security_review`. |
| Engineering Security | Current clean source-bound review → `final_verification`. |
| Engineering Final Verification | Explicit finalization generates the report and marks `verified`; no Release. |
| QA test design / automation | Approved scenarios → `test_automation`; approved automation → `ready_for_verification`. |
| QA verification readiness | After current passing checks, explicitly complete QA → `verified`; Engineering unchanged. |

Shared handoffs retain the owner and set next-role pending assignment; track advancement
does not transfer ownership to another person. Transitions/audits and finalization bundles
change; advancement is separate from ordinary artifact approval. Example: after QA results
review, `$sdlc advance qa` explicitly completes that verification only. No further automatic
transition exists from Verified; source changes can require renewed applicable evidence.

**Known implementation inconsistency:** the low-level helper suggests `development-start`
for `advance` at `ready_for_development`. Conversation policy still requires a separate
explicit **`start engineering`**. This documentation does not fix that mismatch. Missing,
superseded or stale approvals, incomplete QA and open Security findings block progression.

## `details` — inspect exact documents and evidence

**Syntax:** `$sdlc details [request] [engineering|qa]`.
Read the original idea/history, current or approved document links, revisions, decisions,
source bindings and actual results. Bare downstream details can aggregate both tracks.
No approval, lifecycle, assignment or file mutation occurs. Example: `$sdlc details
engineering REQ-0001`. Expect exact canonical filenames or explicit legacy `content.md`
links, not a regenerated report or silently repaired baseline. Missing/corrupt dependencies
are reported. See [artifact guide](artifact-names.md).

## `inbox` — see your work and retained accountability

**Syntax:** `$sdlc inbox`.
Needs the target project and local declared profile, not an active request or track.
Shows assigned work and owned pending handoffs, with downstream rows per track. It reads
only: no notification, assignment, approval, transition or activity start. Example:
`$sdlc inbox` after declining a recipient still shows Awaiting Handoff. Missing/invalid
profile needs explicit setup/repair; name matching is not authenticated identity.

## `pending assignments` — see project handoff needs

**Syntax:** `$sdlc pending assignments` (no conversation quoting required).
Read-only project view, no selected request/profile required for listing. Shows retained
owner, required role and pending target; legacy unknown owners remain visibly undeclared.
No transfer, approval, lifecycle update or work initiation. Example: use it after Analysis
advancement to see Engineering Lead and QA Lead / Tester responsibilities independently.
A corrupt request can block the scan; this is not a notification service or SLA scheduler.

## `assign` — confirm responsibility transfer

**Syntax:** `$sdlc assign [request] [engineering|qa]`, or “Assign REQ-0001 QA to Jordan.”
Resolve request, required role and recipient, then obtain a **separate confirmation**
naming request, person and role. Unknown legacy requester evidence requires explicit
initial-owner declaration; never substitute the current login or artifact editor.

On confirmation, update the selected ownership values and append assignment history;
owner/assignee transfer to the recipient. Other track ownership, lifecycle, documents
and existing approvals remain unchanged. Example: nominate Jordan as Product Owner,
then confirm “Yes, assign Jordan as Product Owner for REQ-0001.” That person's declared-name
inbox can show the work; no message or account is provisioned. Ambiguous context,
missing owner evidence, stale revisions and concurrent writes block transfer. See the
[handoff example](ownership.md#worked-example-delayed-handoff).

## Revision or failed-check example

Illustrative, not a recorded recovery: a presentation file changes after Plan approval.
`start engineering` rejects the stale source and edits must stop. Before Development
starts, explicitly request Plan changes. The agent records feedback, returns to planning
and regenerates against the frozen current source. Review/reapprove, advance separately,
then start successfully. Historical Plan baselines remain intact; unrelated QA scenario
authority is preserved. Keep new presentation captures outside the source boundary.

After Development starts, use applicable verification/Security remediation with actual
failed evidence, controlled fixes, fresh code review and relevant reruns. QA rework must
not silently change approved expected behavior. A persisted check operation's `ok: true`
means evidence was saved: inspect `passed`/`failed`/`timeout`/`not_run` and exit status.
Never bypass a blocker by editing metadata, deleting audits or creating a different retry ID.

## Runtime management intentions

“Which runtime is active?” reads the default registration. “Which runtime produced this
Design?” reads runtime-status artifact receipts, including exact baseline files; legacy
missing attribution stays unknown. “Use the new runtime for Analysis” requests a
compatibility review and separate explicit future-scope promotion decision. “Roll back
the default” changes installation selection only. These natural-language intentions use
[implemented runtime operations](runtime-version-management.md), not extra routing enums.
Approval and advance never imply promotion. A lost/mismatched runtime context requires
correct instructions and a fresh conversation/receipt before managed writes.
