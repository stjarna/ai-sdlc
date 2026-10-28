# Shared command and local identity contract

Read this for short SDLC commands and identity setup in either host. Natural-language
requests remain equivalent. These commands describe conversational intent; they are
not shell commands or replacements for the deterministic approval gates.

## Native invocation

- Codex CLI/IDE: `$sdlc <command>`. Select the skill mention or use `/skills`; trailing
  text is ordinary prompt context. Do not assume Claude argument substitution.
- Claude Code CLI/IDE: `/sdlc <command>`. Claude supplies trailing arguments to the skill.
  Keep execution in the current interactive conversation, without background/fork mode.

The shared verbs are `status`, `start`, `review`, `approve`, `changes`, `advance`,
`details`, `inbox`, `pending assignments` and `assign`. The two words `pending assignments` form
one project-level command; the user need not quote them in the conversation.
An optional request title or ID selects an Epic; `changes` may include actual feedback.
Engineering/QA commands also accept an optional track in the native conversation: for
example `$sdlc start engineering`, `$sdlc start qa`, `$sdlc review qa` or their Claude
`/sdlc` equivalents. Track words are conversational context, not a new host parser.
A bare host `/approve`, `/review` or `/status` is not an SDLC command. Do not interpret
an unsubmitted native control or skill selection alone as a decision.

## Resolve context and route

Resolve the actual target project from the current interaction/workspace. The skill
package checkout is not automatically the target. Retain an explicitly selected Epic
in the conversation and revalidate it from artifacts. When ambiguous, ask which project
or request the user means. Do not select the most recently modified record or create
an Epic as a side effect of a short command.

Use the read-only helper:

```text
sdlc.py --project PROJECT command-context COMMAND [--request TITLE_OR_ID] [--track engineering|qa]
```

Pass the known active ID internally. With no selector, request-level commands require exactly one
Epic. Inbox and pending assignments are project-level and require no selected Epic. It resolves stable IDs before titles; exact titles are case-insensitive. Missing
or ambiguous context fails explicitly. Its JSON includes the current review, suggested
operation and identity/setup diagnostic. It never executes a decision or creates a
profile. `requires_human_decision` is a reminder, not evidence of authorization.

For a forked request, retain an explicitly selected track from the current interaction
and pass it internally. If a track-specific command has two plausible targets,
`E_TRACK_AMBIGUOUS` means ask one question: “Engineering or QA?” Do not guess from file
modification times or perform either write while waiting. `status`/`details` can aggregate
both tracks; `inbox`/`pending assignments` are project views with a row per responsibility.

| Verb | Discovery | Business Refinement | Functional Analysis |
|---|---|---|---|
| status | Progress, unanswered/unknown/deferred issues and next step | Draft currency and approval/advancement status | Input currency, uncertainties and approval/advancement status |
| review | Derived Discovery summary | business-review | analysis-review |
| approve | Explain that Discovery has completion rather than an approval gate; no mutation | business-approve | analysis-approve |
| changes | Sourced discovery-update, including linked corrections where needed | business-request-changes, then authorized business-revise | analysis-request-changes, then authorized analysis-revise |
| advance | Explicit Requester completion through discovery-complete | Separate business-advance after valid approval | Separate analysis-advance after valid approval |
| details | Evidence, assumptions and question history | Full document, sources, decisions or baseline | Specification, criteria, coverage, uncertainty, decisions or baseline |

At `ready_for_refinement` and `ready_for_analysis`, report that the next draft can be
prepared; do not silently generate it. A review with no draft reports its absence.
After new Analysis advancement, report both ready tracks from the same approved
baseline. Start their work only on an explicit request; the legacy scalar
`ready_for_technical_design` is not evidence that QA depends on Design. Cancelled records have no write route. An already
completed advancement is a status result, not permission to start another stage.
After reopening, route from the persisted lifecycle even when old drafts still exist.

## Local identity preferences

Use the same local profile in both hosts. Read it through `identity-show` or the context
helper; never derive identity from Git configuration, host login or historical audits.
The profile is a declaration, not an authenticated identity. Its roles are informational
project-role labels, reused across projects, not enforced RBAC or grants of permission.

If missing, ask once: “What display name and declared roles should I save for your
local SDLC profile?” Use only supplied information. If a name was previously declared,
you may suggest it, but obtain explicit profile setup instruction; do not silently
create a profile from that name or inferred roles. The setup question does not approve
any specification. Execute `identity-setup` only after the answer, then reuse the profile
across conversations without repeated identity questions. Do not ask for role membership
at every stage or block actions solely because a role label is absent.

For a requested name/role edit, load `identity-show`, apply only the requested fields
through `identity-edit` with its expected profile revision, and verify the result.
Do not rewrite previous actors or decision records. A missing/bad/unsafe profile requires
setup or explicit repair, not a fallback to Git/login names. Never request credentials.

For Discovery completion/reopening, Business decisions/advancement and Analysis decisions/
advancement, omit the legacy actor flag so the CLI loads the profile and records
`identity_source: local_profile`. Pass `--expected-profile-revision` from the reviewed
context internally. If it changed, reload and clarify attribution when needed rather
than silently switching the actor. Explicit legacy actor flags still work for existing
callers; never use them to hide a profile error or erase the identity source.
Use the same local-profile attribution for Engineering/QA approvals, advancements and
track assignment/reconciliation. A track owner or historical actor is not the current
user identity. For document editing, retain the existing editor arguments and use the
loaded display name when attributing human feedback; identify AI drafting honestly. Actual human feedback remains separate from the
agent's explanatory reason. Neither profile roles nor host tool permissions replace
an explicit human decision.

## Short approval flow

Resolve context and load the current review before acting on `approve`. If that exact
snapshot has not been presented, show a concise business-oriented review and ask for
an explicit decision. The initial command is approval intent, not approval of unseen
content. If it has been reviewed and there are no missing acknowledgements, the short
approval command itself can be an explicit decision; do not demand formal wording.

Summarize outstanding questions, proposed assumptions and affected blocked behavior in
business terms. Group related records representing the same unresolved issue; keep the
full mapping to technical acknowledgement IDs internal. Ask for acknowledgement only
when not already supplied. Acknowledgement does not resolve an issue or promote a
proposal. “Looks good”, silence, conditional assent and tool permission are insufficient.
Ask one focused follow-up if intent is ambiguous.

Preserve the actual approval and acknowledgement messages, including a short command or
contextual “Yes”. If collected over several turns, keep actual utterances identifiable
in the decision text, in order, without manufacturing a formal quotation. Revalidate
the exact review/revision and the identity profile before invoking the existing gate.
If content changed or review context was lost, present a fresh review and obtain renewed
assent. Generate operation IDs and pass all technical parameters internally.

If the current revision already has an effective approval, report it rather than
creating a duplicate decision unless the user explicitly requests a new signoff.
Report the verified result briefly. Approval leaves its current Business, Analysis,
Engineering or QA lifecycle stage unchanged. Wait for a separate advancement instruction; never bundle it with
approval, even if initially requested together. Respect an explicit “do not advance”.
An `advance` command separately authorizes the named readiness transition after checking
the latest valid approval/baseline. It does not approve a stale draft, run Analysis,
create a Design/QA draft or automatically start implementation. Use `start` for the
selected track's current activity only after its required preceding decisions. Starting
work does not itself approve an artifact or authorize a readiness transition.

For `changes`, a bare command asks for the requested refinement. Preserve actual feedback
through the stage-specific operation before applying only explicitly requested edits.
Business scope changes still require explicit Discovery reopening and reconciliation.
Read-only commands never record approval, mark an issue resolved or change lifecycle.

## Ownership and assignment

Read the [Ownership guide](../../docs/ownership.md) for data/tool contracts and legacy
handling. New requests use the local declared Requester as initial owner and assignee.
Load/setup the profile before `new`; never create an unowned request or invent a requester.
An explicit requester declaration is available for existing headless callers.

`status` and `details` include current owner, assignee, responsibility and assignment
status. `inbox` and `pending assignments` use read-only project views. Show request IDs
and titles in these lists, grouped as **Assigned Work** and **Awaiting Handoff**; include
role, stage, responsibility, status and next action. Pending assignments also show the
retained owner and elapsed waiting time when known. These are not SLA notifications.

After an authorized completion/advancement, verify persisted pending handoff and tell
the current owner the target role, then ask one nomination question. For example:
“Discovery completed and is ready for Business Refinement. Required role: Product Owner.
Who should take ownership?” An unknown/deferred recipient leaves the current owner
accountable with no assignee: “No Product Owner assigned. The request remains in your
inbox as Awaiting Handoff.” Do not start the next stage or auto-assign the current user.
If the current conversation's user is not the recorded owner, report whose inbox retains
the handoff; do not claim to have contacted that person or received their consent.
No external messages or notifications are sent by this workflow.

For `assign`, resolve the request, load its revision and required role, and ask for an
assignee if missing. A nomination alone is not a transfer. Present a separate explicit
confirmation: “Assign REQ-0001 to John Smith as Product Owner?” Wait for the answer,
then revalidate the request/profile and invoke `assign` with actual confirmation wording.
Retain hashes/operation IDs internally. Verify owner/assignee transfer, unchanged lifecycle
and approvals, retained history and removal from pending assignments. A separate explicit
reassignment follows the same confirmation process. If it is already assigned to that
person, report that fact instead of creating another event without a new instruction.

For a legacy request, use a single unambiguous recorded Requester as initial owner.
This is historical accountability evidence, not the current actor's identity. If missing
or ambiguous, ask who was the requester/accountable initial owner and record their actual
declaration with `ownership-initialize` before proceeding. Never derive an owner from
Git, business editors, an AI record or the current profile merely because it is available.
The assignment actor always remains the actual local declared user. Ownership questions
and nominations are management context; do not add them as business requirements,
Discovery facts or Analysis questions.

Approval, advancement and assignment are three independent decisions. Confirming an
assignment does not approve content or authorize advancement. Existing approved content
and immutable baselines survive ownership transfer; pending review tokens still require
fresh validation after metadata changes. For forked requests, assignment transfers only the selected track; the other track
retains its current owner/assignee. Resolve the track first and use the corresponding
required role in the confirmation, for example “Assign this request's QA track to Jane
as QA Lead / Tester?” Legacy requests retain their recorded assignment
semantics, including their Engineering Lead / Architect handoff.

## Forked Engineering and QA commands

Read [work-track contracts](../../docs/work-tracks.md). Explicit advancement of an
approved Functional Analysis automatically creates both track contexts. It does not
start either activity, assign a person or record a downstream approval. Initially both
retain the existing accountable owner and await separate handoffs:

> Functional Analysis is approved. Two workstreams are ready:
> Engineering — awaiting Engineering Lead.
> QA — awaiting QA Lead / Tester.
> Who would you like to assign first?

Ask for one nomination/confirmation at a time. An unknown recipient leaves that track
pending in the retained owner's inbox; assigning one must not hide the other. Show each
track's owner, assignee, role, status and next action without requiring technical IDs.
Roles remain informational, and no external notification or work initiation is implied.

| Intent | Engineering | QA |
|---|---|---|
| start | Prepare requested Design/Plan or explicitly start approved development at the available stage | Prepare strategy/scenarios from Analysis, or authorized automation at its stage |
| review/details | Design, Engineering Plan, code/unit/build evidence and decisions | Strategy, functional scenarios, automation and actual test evidence |
| approve | Current Design/Engineering Plan/code gate only | Scenario approval covering strategy+scenarios, or separate automation approval |
| changes | Record requested Engineering feedback before authorized refinement | Record requested QA feedback before authorized refinement |
| advance | Separate authorized Engineering readiness transition | Separate QA progression/completion after its required decisions/evidence |
| assign | Transfer Engineering accountability after confirmation | Transfer QA accountability after confirmation |

Use the context helper's actual route and [CLI contract](../scripts/README.md), not
improvised commands. Tool-facing QA operations are `qa-review`, `qa-write`, `qa-approve`,
`qa-request-changes`, `qa-advance` and `qa-check-run`. Management uses `track-review`,
`track-reconcile`, `tracks-adopt` and `assign --track`; keep tokens and arguments internal.

QA functional strategy/scenarios need only the common approved Analysis baseline, not
Technical Design or an Engineering plan. Later automation can bind Design interfaces
without deriving expected behavior from them. Engineering Plan approval covers code,
work decomposition and unit/build checks; it does not approve QA scenarios. Human
Engineering code approval does not approve independent QA automation. Do not add an
extra mandatory strategy signoff: one scenario gate reviews strategy and scenarios.

The integrated verification gate requires valid Engineering outputs/code approval,
current QA strategy/scenario and automation approvals, actual current integration/UI
checks and explicit QA completion. Report missing/unexecuted/failed QA as a blocker,
never a passing empty track. QA completion does not automatically advance Engineering;
Engineering verification advancement is a separate decision. A source change can stale
execution evidence without invalidating unrelated functional scenarios. A final report
binds the exact joined inputs and uncertainty; it does not authorize release or deployment.

If approved Analysis changes, show impact on both tracks and obtain explicit per-track
reconciliation before renewed work. Preserve old history; never copy approvals or
scenarios into a new cycle silently. A legacy request stays legacy unless an eligible,
explicitly authorized `tracks-adopt` operation reconciles it before development. Preserve
approved Design and the unapproved combined Plan's history, but prepare a fresh
Engineering-only Plan and QA artifacts from Analysis; do not approve the old combined
Plan as though it were separated. See the compatibility guide before proposing adoption.

Logical track independence does not schedule parallel agents, processes or Git branches.
Never infer approval, advancement, assignment or execution from track creation.

## Document discovery and names

Use [canonical artifact storage](../../docs/artifact-names.md) descriptors for status,
review, details and reports. New manifest0.2 files have canonical physical names;
`document.name`, link label and basename agree. Format0.1 baselines retain content.md
and explicit legacy labels, without migration. Never rename immutable files, create
aliases or imply legacy links target a canonical file. Track reviews include `document`;
aggregate views index both tracks and core payloads expose `epic.documents`.
