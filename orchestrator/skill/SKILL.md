---
name: sdlc
description: Guide an informal business idea through Discovery, business specification refinement, and explicit Product Owner decisions using the AI SDLC Assistant.
---

# AI SDLC Assistant

Use the shared [conversation policy](conversation.md) throughout the interaction.
This file owns workflow and persistence mechanics for every host; discovery adapters
only load it. Keep the complete `orchestrator/` package together. Resolve resources
from this skill's actual location, independently of the target project's directory.

Read the [CLI contract](../scripts/README.md) for environment and operation arguments.
Load the [Discovery record guide](../../docs/interactive-discovery.md) when capturing
or correcting evidence, the [Business Refinement guide](../../docs/business-refinement.md)
when drafting/revising, and the [Approval guide](../../docs/business-approval.md) before
PO decisions or advancement. These define artifact/operation contracts; the conversation
policy defines default presentation. Handle commands and technical parameters internally.

## Resolve and resume

Identify the target project from explicit user/workspace context. The package checkout
is not automatically the target project. Ask only when the project or request is
ambiguous. Resolve existing requests using persisted titles/IDs through `validate`
and `open`; do not guess an ID or create a duplicate when the user intends to resume.

For a new request, derive a title and pass the original description to `new` without
adding requirements. Before continuing saved work, `open` it and read current lifecycle,
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
declared identity. Use an identity already declared for that role in this interaction;
ask when missing. Invoke `discovery-complete` with the reviewed Epic revision, actual
decision and operation ID, then verify `ready_for_refinement`. A review request or
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
obtain any missing identity or unresolved-item acknowledgements. Retain the reviewed
business revision, review revision and item mapping internally in the native conversation;
never ask the user to copy them. No separate checkpoint subsystem is needed.

For changes, use `business-request-changes` with fresh reviewed tokens, declared PO,
reason and actual feedback. Verify its audit entry and unchanged lifecycle. Feedback
is not approval or blanket permission to edit requirements; revise only as instructed.

For approval, require explicit assent to the identified reviewed document and explicit
acknowledgement of each outstanding issue/proposal. Preserve the human's actual words;
do not expand a short response into a fabricated formal quotation. The reason field
may summarize the context but must not be presented as a human quotation. Reuse only
an identity declared in the current interaction, never a Git/login identity or an actor
from an old audit record. If nothing relevant changed and the user already supplied a
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
reason and operation ID. Verify `ready_for_analysis` and the baseline reference.
Describe this as marking the request ready for Functional Analysis; do not claim that
Analysis has run or create Analysis artifacts. Reopening requires fresh completion,
refinement and approval; old approvals never regain authority merely from matching bytes.

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

No automatic Git actions, skill installation, external AI APIs, custom UI or later SDLC
implementation are part of this skill. Respect the user's explicit task boundaries.
