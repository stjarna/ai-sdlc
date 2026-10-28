---
name: sdlc
description: Guide business ideas through Discovery, human approvals, Functional Analysis and independently owned Engineering and QA work tracks.
---

# AI SDLC Assistant

Use the shared [conversation policy](conversation.md) and [command/identity contract](commands.md) throughout the interaction.
This file owns workflow and persistence mechanics for every host; discovery adapters
only load it. Keep the complete `orchestrator/` package together. Resolve resources
from this skill's actual location, independently of the target project's directory.

For Engineering or QA work, read [work-track contracts](../../docs/work-tracks.md) and the domain-skill workflow below. [Engineering contracts](../../docs/engineering.md) also describe the retained legacy sequence.

Read the [CLI contract](../scripts/README.md) for environment and operation arguments.
Load the [Discovery record guide](../../docs/interactive-discovery.md) when capturing
or correcting evidence, the [Business Refinement guide](../../docs/business-refinement.md)
when drafting/revising, and the [Approval guide](../../docs/business-approval.md) before
PO decisions or advancement. These define artifact/operation contracts; the conversation
policy defines default presentation. Handle commands and technical parameters internally.

## Present identifiable artifacts

Follow the [canonical storage contract](../../docs/artifact-names.md). New Engineering/QA
artifacts use manifest 0.2 and physical canonical filenames; only deterministic tools
publish them. Use returned `document.name`/`link` matching the actual basename, and
`document.title` in prose. Legacy 0.1 baselines must remain byte-for-byte unchanged:
use their explicit “Title (legacy content.md)” links, never a fictional canonical path.
Core documents are in `epic.documents`; aggregate status/details indexes both tracks.
Keep revision/request context and verify authority independently of naming. Pinned old
domain instructions describing content.md concern legacy format, not new publication.
Never create aliases/copies or manually rename a baseline to improve presentation.

## Resolve and resume

Identify the target project from explicit user/workspace context. The package checkout
is not automatically the target project. Ask only when the project or request is
ambiguous. Resolve existing requests using persisted titles/IDs through `validate`
and `open`; do not guess an ID or create a duplicate when the user intends to resume.

For a new request, load the local identity profile (explicit setup once if missing),
derive a title and pass the original description to `new` without adding requirements.
The declared requester becomes initial owner/assignee; never create an unowned request. Before continuing saved work, `open` it and read current lifecycle,
Discovery resolutions/corrections, business revision, reconciliation and approval state.
Use the artifacts rather than chat recollection as the authoritative current state.
A lost conversational approval context requires a fresh review and decision.

## Persist Discovery evidence

Use the conversation policy to select the next useful question or offer a review.
Persist meaningful evidence before continuing, using `discovery-update`, the revision
returned by `open`, an operation ID and a temporary JSON changes file. Let the CLI
assign record IDs; use returned IDs when linking later records.

- Capture supplied facts as `user_statement` with their actual supporting quotation.
  A quotation records what was said, not independent verification. Clarify uncertain
  interpretations rather than assigning a business rule.
- Keep AI proposals as `ai_assumption`. Only an explicit, sourced human decision can
  confirm one. Silence, tool permissions and unrelated positive feedback do not.
- Persist a focused `question` before asking it; link its answer using `answers` or
  a human `answer` decision. Read saved answers before asking again.
- Preserve distinct open, unknown and deferred states. Record a revisit condition
  only when supplied. Revisit deferrals only on their condition, user instruction
  or a material change, explaining why it matters.
- Use sourced `human_decision` records for confirmation, rejection and explicit choices.
  Correct an active statement/substantive decision with linked `correct`; keep earlier
  evidence. Reject and replace an incorrect AI assumption rather than relabeling it.

Keep the original idea and metadata intact during Discovery updates. Legacy requests
without history remain readable; legacy AI prose is not automatically confirmed evidence.
Review the derived current statements, decisions, assumptions and remaining questions.
Structural completeness and the AI's readiness assessment are advisory, not approval.

## Complete or reopen Discovery

Present a concise review and obtain an explicit Requester completion decision with a
local declared identity loaded from the profile. Follow `commands.md` for one-time
setup if missing; reuse it without repeated identity questions. Invoke
`discovery-complete` with the reviewed Epic revision, actual
decision and operation ID, then verify `ready_for_refinement` and pending Product Owner
handoff with the current owner retained. Follow the ownership flow in `commands.md`
to offer nomination and separately confirm assignment; an unknown recipient stays pending. A review request or
AI readiness recommendation alone cannot authorize completion. The user may continue
Discovery instead. Completion does not approve the business specification.

For substantive source changes after completion, explain that the draft will require
reconciliation and obtain explicit reopening authorization. Use `discovery-reopen`,
preserve existing draft/history/decisions/baselines, append sourced Discovery changes,
then obtain renewed completion. Do not silently merge sources into the draft.

## Draft and refine business requirements

Derive confirmed content from current user statements, substantive human decisions,
and explicitly confirmed AI assumptions, following correction and resolution chains.
Keep unresolved questions and proposed assumptions separate. Original idea prose is
context, not substitute evidence. Preserve source traceability inside the artifact.

Draft `business.md` in the documented format with stable B/U/P IDs and supporting
Discovery references. Cover value, users, scope, exclusions, success measures,
constraints and dependencies where supported; do not invent content to fill sections.
Include every current source record in its correct category. Present business wording
for human review using the conversation policy, with technical evidence available.

Persist the initial or stale regenerated draft through `business-generate`, or an
explicit human refinement through `business-revise`, using the current source and
business revisions and declared editor/reason. Preserve IDs for the same requirement.
New substantive requirements require sourced Discovery reconciliation. Do not treat a
request labelled "wording only" as permission to silently change business meaning.

Use `business-review` after refinement. If `current: false`, explain that the draft
requires reconciliation and do not present it as ready for approval. Explicitly
regenerate/revise against the new source and previous business revision when authorized.

## Record Product Owner decisions

Use the conversation policy to present a review, interpret the human's response and
load the local identity profile and obtain any missing unresolved-item acknowledgements.
Retain the reviewed
business revision, review revision and item mapping internally in the native conversation;
never ask the user to copy them. No separate checkpoint subsystem is needed.

For changes, use `business-request-changes` with fresh reviewed tokens, declared PO,
reason and actual feedback. Verify its audit entry and unchanged lifecycle. Feedback
is not approval or blanket permission to edit requirements; revise only as instructed.

For approval, require explicit assent to the identified reviewed document and explicit
acknowledgement of each outstanding issue/proposal. Preserve the human's actual words;
do not expand a short response into a fabricated formal quotation. The reason field
may summarize the context but must not be presented as a human quotation. Reuse the
local declared identity profile, never a Git/login identity or an actor
from an old audit record. Follow `commands.md` for explicit setup/editing and identity-source
audit attribution; the profile is unauthenticated and roles are informational. If nothing relevant changed and the user already supplied a
complete explicit decision, execute it without an extra ceremonial confirmation.

Re-read `business-review` before approval and compare it with the snapshot actually
presented. Use that reviewed revision and its exact acknowledged item mapping in
`business-approve`. If the context changed or was lost, show a fresh review and obtain
renewed assent rather than silently applying the old approval to the latest content.
Verify the recorded decision, exact baseline integrity, current revision and preserved
unresolved items. Confirm that the request remains in Business Refinement.

Declared identities are unauthenticated. This procedural conversation cannot technically
prevent an unrestricted AI agent from invoking approval tools while claiming a human
identity; never describe it as guaranteed human-only authorization. Host execution
permission, skill invocation and approval of this assistant's implementation are not
Product Owner approval of an application business specification.

## Advance separately

After reporting business approval, stop for a separate explicit advancement instruction.
Do not bundle approval and advancement, even when the user initially asks for both.
After that separate instruction, obtain a fresh review, verify the selected latest
approval and immutable baseline, and call `business-advance` with fresh tokens, actor,
reason and operation ID. Verify `ready_for_analysis`, the baseline reference and
pending handoff to a Business Analyst with the current owner retained. Offer nomination
and separately confirm any assignment as described in `commands.md`.
Describe this as marking the request ready for Functional Analysis; do not claim that
Analysis has run; use the separate Analysis drafting workflow when requested.
Reopening requires fresh completion,
refinement and approval; old approvals never regain authority merely from matching bytes.

## Draft and refine Functional Analysis

Read the [Functional Analysis contract](../../docs/functional-analysis.md) before this
stage. Use `analysis-review` to obtain the active handoff and verified frozen business
and Discovery evidence. Draft a meaningful Epic-wide specification first; do not begin
with an extensive questionnaire. Never use a mutable draft or conversational recollection
as an alternative approved source. If no valid business advancement exists, explain
what is missing rather than choosing a historical baseline.

Use stable FR/UC/BR/AC/AQ/AP items, complete business coverage dispositions and the exact
inherited U/P lines. Context and exclusions need no artificial FRs. Produce observable
Given/When/Then criteria, supported use cases/alternative flows and business rules.
Assess clarity, testability, observable outcomes, missing edge cases, contradictions
and source alignment yourself; the CLI does not judge prose semantics. Preserve deferred
business decisions. Identify affected behavior without selecting an unapproved option.

Persist through `analysis-generate` using the fresh complete Analysis review token,
asserted baseline/handoff, operation ID and declared editor/reason. First generation
enters Functional Analysis; it is not approval. Summarize the generated behavior,
material gaps and blocked items, then ask one focused question where useful. Let the
human review the draft and request refinements instead of repeatedly questioning them.

Use `analysis-revise` for explicitly requested refinements with both complete review
and specification revision. Preserve actual feedback through the optional feedback
file and retain IDs; retire obsolete items. Feedback is not new business authority.
New behavior, scope changes or a decision on an inherited business question requires
explicit Discovery reopening, renewed completion/refinement/approval and separate
advancement. Keep the old Analysis stale and its history intact until explicit
regeneration/revision against the new handoff, even if business bytes are identical.

Resume with `open` and `analysis-review`, loading current contents, coverage, unresolved
items and history rather than repeating settled questions. If an Analysis transaction
is interrupted, inspect it, establish no writer remains, and use `analysis-recover`;
retry only the original operation ID and inputs. Never treat a stale draft as current.

## Review and approve Functional Analysis

Read the [Analysis Approval contract](../../docs/analysis-approval.md). Present a concise
business-oriented review using `analysis-review`: behavior, exclusions, coverage,
blocked items and each unresolved question or proposal. Assess semantic quality yourself;
`can_approve` indicates structural eligibility only. Keep the complete reviewed context
and mapping to `analysis_open_items` internal, including inherited U/P, AQ/AP and blocked
or proposed functional items. Acknowledgement accepts uncertainty without resolving it,
confirming an assumption or establishing implementation readiness.

Use the same natural approval rules as Business: clear assent to this exact review,
explicit acknowledgement of every listed uncertainty, local declared identity
loaded from the profile, and preserved actual decision wording. Vague positive
feedback never authorizes approval. Ask only for missing clarification or acknowledgement;
do not request another ceremonial confirmation of an already complete decision.
If context changed or was lost, present a fresh review and obtain renewed assent.

For changes, persist actual feedback through `analysis-request-changes` before authorized
refinement. Feedback does not change the document or business authority. For approval,
revalidate the presented snapshot, call `analysis-approve` with its exact context and
acknowledged mapping, then verify the recorded decision and immutable baseline. Report
that the Analysis is approved and remains in Functional Analysis. Stop and wait for a
separate explicit advancement instruction, even if approval initially asked for both.

Only after that separate instruction, review again, verify the latest effective approval
and baseline, and use `analysis-advance`. Verify the automatic fork: Engineering and QA
both reference this exact approved Analysis baseline, retain the current accountable
owner, and await separate assignments to Engineering Lead and QA Lead / Tester. Report
both workstreams as ready and ask which assignment the user wants to address first.
Creating, assigning or advancing a track does not start its work. Do not draft either
track's artifacts until requested. Approval alone must not create the fork.

After advancement, Analysis editing is blocked. Explicit upstream reopening preserves
all historical decisions/baselines. A subsequent Analysis handoff requires explicit
impact assessment and `track-reconcile` for both tracks before renewed work; do not
copy their artifacts or revive old approvals automatically. A same-byte revision or
replay cannot restore old authority. Story decomposition remains excluded.

## Execute and recover

Use the documented Python environment and deterministic CLI through permitted native
tools. Pass literal/safely quoted content. Do not directly mutate metadata, histories,
IDs, approvals or baselines. Keep all CLI validation, revision checks and audit rules.

Inspect the persisted response after writes. Exact retries retain the original operation
ID, expected revisions and payload; a replay never restores superseded approval authority.
On a conflict, reopen and reconcile; a new approval needs renewed human assent. For a
busy/uncertain result, retry the exact request once where safe; if unresolved, explain
its impact and retain technical diagnostics for inspection. Do not delete/bypass locks.

For `E_BUSINESS_RECOVERY`, inspect the journal and establish that no writer is active
before explicit recovery through `business-recover`. For baseline preparation failures,
inspect pending/orphan data and any abandoned lock before an exact retry. Missing or
corrupt approved baselines require known-good restoration, never replacement from the
draft. Do not silently repair malformed artifacts or report an uncertain write as success.

No automatic Git actions, skill installation, external AI APIs, custom UI or unapproved downstream
implementation are part of this skill. Respect the user's explicit task boundaries.

## Engineering and QA with domain skills

Read [work-track contracts](../../docs/work-tracks.md) before acting. Resolve `skills`,
verify approved pins and load only the relevant domain `SKILL.md` and references. Domain
packages supply expertise; only orchestrator operations mutate governance. Do not copy
skills into Epics, load arbitrary remote packages or hide unavailable/incompatible pins.
Pinning reproduces instructions, not deterministic model output.

Use `track-review`, `open` and track-aware command context to reconstruct both tracks.
Keep an explicitly selected track in the conversation and revalidate it before writes.
For ambiguous `start`, `review`, `approve`, `advance` or `assign`, ask one question:
“Engineering or QA?” Never pick the most recently changed artifact. `status` and `details`
may summarize both; `inbox` and `pending assignments` show separate track responsibilities.
Independent workstreams do not authorize automatic parallel agents or background work.

### Engineering

On an explicit start/drafting request, use Architecture and Security to prepare Technical
Design from the approved Analysis and inspected code. Preserve unresolved/blocked behavior
and distinguish technical proposals from requirements. Persist via `engineering-write`,
present the review and obtain explicit Design approval with required acknowledgements.
Wait for separate advancement before Implementation Planning.

On request, use Development to prepare an Engineering-only Implementation Plan: ordered
tasks, dependencies, declared source paths, FR/AC links and unit/build checks. Do not
bundle QA scenarios, functional expectations or QA automation approval into this plan.
QA work may proceed independently; incomplete QA does not prevent Engineering plan
approval. After Plan approval, wait for separate advancement and then explicit
`development-start` authorization. Keep forked Engineering source outside reserved `qa/`.

Implement authorized tasks with native host tools, keeping unit tests alongside code.
Use named checks for actual unit/build evidence. Present the actual code diff, completed
tasks, developer tests and results for human code review; self-review is not independent
review. Approval binds the unchanged Engineering source. Wait for separate advancement.
This code approval does not approve QA scenarios or separate QA automation.

### QA

On `start qa`, use Testing to prepare independently revisioned strategy and functional
scenarios directly from the same frozen Functional Analysis and its acceptance criteria.
Technical Design and the Engineering plan are not prerequisites. Persist via `qa-write`;
reference FR/AC IDs and retain inherited uncertainty, without duplicating authoritative
requirements. Design/code/prototype observations cannot replace functional expectations.

Present the strategy and scenarios together for one explicit human scenario approval.
There is no separate mandatory strategy signoff. Revalidate both revisions and required
acknowledgements for `qa-approve`; approval does not advance. Wait for separate
advancement to automation. Later approved Design interfaces may inform automation,
without redefining its expected behavior.

Prepare QA automation only within its declared reserved `qa/` paths and record actual
source/interface bindings through QA operations. Do not modify Engineering source or its
plan. Obtain separate human automation review and approval, then separate advancement to
verification readiness. Scenario approval does not approve generated automation.

### Join, evidence and remediation

Before integration/UI execution, verify the required current Engineering outputs/code
approval and QA strategy/scenario/automation approvals. Use `qa-check-run` for named
approved checks and retain actual statuses, output, requirement links and the complete
source contract. A check label, HTTP-only test or fixture command is not proof of actual
UI interaction. Missing tools, failures and stale/unexecuted checks stay visible.

QA must explicitly complete current verification after its required checks pass. The
integrated gate must report incomplete QA as a blocker, never success. Only after valid
Engineering outputs, current QA reviews/evidence and explicit QA completion may a separate
Engineering verification advancement progress toward Security. Neither track silently
advances the other. An unrelated Engineering revision leaves functional QA scenarios
valid, while affected automation or execution may require adaptation/reruns.

Use Security for source-bound review and actual findings, not invented scans or
certification. Remediation needs explicit authorization, preserved findings/failed evidence,
fresh checks and relevant human reviews. Do not change QA expectations to match a defect.
Authoritative Analysis changes require impact assessment and reconciliation for both
tracks. Final verification records the exact joined inputs and remaining uncertainty;
`verified` is not release approval or deployment authorization.

### Legacy and in-progress compatibility

Requests without tracks keep their recorded legacy workflow. Do not silently add tracks,
rewrite approved Design or reinterpret a combined Plan as independent QA approval.
Before development, an explicit `tracks-adopt` decision can reconcile an eligible legacy
request whose combined Plan is unapproved. Explain the effect and obtain authorization:
retain approved Design and every historical baseline/decision, mark the old combined
Plan as historical, prepare a fresh Engineering-only Plan, and draft QA from Analysis.
The old combined Plan must not become approvable after adoption. Do not apply this to
an acceptance project merely because implementation of compatibility support was requested.

Keep all identity setup, tokens, revision comparisons, retries and operation IDs internal.
Use the existing procedural identity and audit controls. Ask one human decision at a
time; approval, advancement, starting work and assignment remain distinct instructions.
