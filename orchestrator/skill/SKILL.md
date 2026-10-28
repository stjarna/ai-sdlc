---
name: sdlc
description: Guide sourced Discovery and Business Refinement, persist reviewed business drafts with traceable revisions, and resume local requests with the AI SDLC Orchestrator.
---

# Interactive Discovery and Business Refinement

Read the [operation contract](../scripts/README.md) for environment setup. For the
record schema, update payloads and recovery rules, read the
[Interactive Discovery guide](../../docs/interactive-discovery.md). Keep this
checkout's `orchestrator/` directory together; host catalog installation is separate.
For completion, document format, revision history and recovery, read
[Business Refinement](../../docs/business-refinement.md). All CLI operations are
tool-facing; the user need not supply revision hashes or operation IDs.

## Start or resume

Establish the target project from workspace or explicit user context. Ask if it is
ambiguous; the orchestrator checkout is not automatically the target project.
Resolve an existing request from known ID/context, asking if multiple ideas match.
`validate` returns local IDs and `open` retrieves their titles. Do not guess IDs or
silently create a duplicate request when the user intends to continue an existing one.

For a new idea, derive a concise title and pass the user's original description to
`new` without adding requirements. Users need not provide technical IDs or paths.
Read the returned original idea, metadata, revision and any history. Use `open`
before resuming: load `discovery` and `discovery_state`, including earlier answers,
corrections, unconfirmed assumptions and deferred questions. Legacy requests without
history remain valid; do not automatically treat AI-written legacy prose as confirmed.

## Conduct the conversation

Identify the uncertainty that most affects the user's goal, scope, risk or a later
solution decision. Normally ask one meaningful question at a time, in the user's
language. Explain briefly why it matters when useful. Adapt to the answer rather
than following a questionnaire. Do not demand completion of every content category.
Relevant topics can include the problem, desired outcome, users, scope/exclusions,
capabilities, business rules, dependencies, constraints, quality expectations and
success criteria; these are considerations, not a mandatory sequence.

Read saved answers before asking. Do not repeat answered questions. Leave deferred
questions aside until their revisit condition, user instruction or a material change
justifies revisiting them; explain that reason. An explicitly unknown answer remains
unknown. Ask what is needed to resolve ambiguity instead of choosing a business rule.

## Capture evidence and decisions

- Store explicitly supplied information as `user_statement`, with a supporting exact
  quotation. A user statement records what they said, not independent verification.
  Paraphrase only without changing meaning; ask if the interpretation is uncertain.
- Store your unconfirmed proposals as `ai_assumption`. Show a proposal before seeking
  confirmation; neither silence nor an unrelated answer confirms it.
- Store the focused `question` before asking it so interruption does not lose context.
  Link the subsequent user answer using `answers`, or a human decision with `answer`.
- Record explicit "I don't know" as `unknown` and explicit postponement as `defer`,
  with the user's quotation. Save a revisit condition only when actually provided.
- Use a sourced `human_decision` to confirm/reject a particular assumption or record
  an explicit choice. If "yes" could refer to several proposals, clarify first.
- Correct a statement or substantive decision with a linked `correct` record and
  user evidence. Keep the old record. Reject and replace an incorrect AI proposal;
  never relabel it as a user fact or rewrite previously captured history.

Persist each meaningful answer before continuing. Keep `idea.md` and metadata intact;
`discovery.yaml` is the authoritative evolving history. An assistant cannot create
authentic human evidence by labeling its own words as a user quotation.

## Invoke deterministic operations

Use `scripts/sdlc.py` relative to the parent `orchestrator/` directory with the setup
from the contract. Pass content through literal arguments or safe shell quoting.
Use `discovery-update` with the revision from `open`, a newly generated operation ID
and a JSON changes file containing typed records. Let the script assign record IDs;
link new records after their assigned IDs are returned. Never manage IDs, change
metadata or edit history with improvised shell commands or direct model edits.

On a successful response, read the persisted state before deciding what to ask next.
Keep the same operation ID, revision and payload for retries. For a busy or uncertain
write result, retry the exact request once; if unresolved, report the code and file.
Never delete a lock or change an operation ID to bypass a failure. On a revision
conflict, reopen, reconcile the saved records with the user's answer, and submit a
new operation only if it is still needed. Do not silently repair malformed artifacts.

## Review Discovery

On a review/summary request, reopen and derive a human-readable view from the current
history and resolution state. Summarize active user statements and explicit decisions,
show unconfirmed assumptions separately, distinguish open/unknown/deferred questions,
and cite relevant record IDs. Follow corrections rather than repeating superseded
answers. Include original context where relevant, clearly identifying its provenance.

Offer a reasoned AI assessment of whether the content is developed enough for human
review, with the important gaps. This is advisory. Structural validation and legacy
empty-section warnings do not establish business correctness or readiness. Never fill
gaps to make the document look complete or report approval that has not occurred.

## Complete or reopen Discovery

Before completion, reopen the Epic and present a concise review of active confirmed
statements/decisions, open/unknown/deferred questions and proposed assumptions with
record IDs. Ask the Requester for an explicit completion decision. Do not infer it
from a positive summary or an AI recommendation. Capture their declared identity
and exact words. Invoke `discovery-complete` with the current Epic revision and a
stable operation ID. The result is `ready_for_refinement`, not business approval.
The operation reports remaining unresolved questions and proposed assumptions; do
not hide them or describe completion as proof of business readiness.

When a substantive Discovery correction is needed after completion, explain that
the draft will need reconciliation. Obtain an explicit Requester reopen decision,
then use `discovery-reopen`. Preserve `business.md` and its history. Continue
Discovery through sourced `discovery-update` records, then request a new explicit
completion. Do not silently merge the changed source into the draft.

## Draft and refine the business specification

For a request in `ready_for_refinement`, derive the current source sets from
`discovery.yaml`. Follow corrections and resolutions. Treat current user statements,
explicit substantive human decisions and confirmed AI assumptions as confirmed;
show open/unknown/deferred questions and proposed assumptions separately. Do not
use superseded statements, rejected assumptions or AI prose from `idea.md` as
confirmed facts. `idea.md` provides original context, not replacement evidence.

Draft a human-readable `business.md` using the exact section and ID format in the
Business Refinement guide. Cover business value, target users, scope, exclusions,
success measures, constraints and dependencies where supported. Give each confirmed
item a stable `B-...` ID and cite its `D-...` source IDs. Use `U-...` for unresolved
issues and `P-...` for unconfirmed proposals. Include every current source record in
its correct category. Do not invent a requirement to fill an empty subsection.
Present the draft and its traceability to the Product Owner for iterative review;
the CLI's structural validation does not establish semantic correctness.

Write a UTF-8 draft file in a temporary working location and call
`business-generate` with the source revision returned by `open`, an operation ID,
declared editor and reason. For later human changes, show the diff and use
`business-revise` with both current source and business revisions. Retain IDs for
the same requirement; give new requirements new IDs. If the Product Owner introduces
a new substantive fact, reopen Discovery and capture it as a sourced human decision
before including it as confirmed. For an outdated draft, explicitly regenerate or
revise against the new source revision and previous business revision.

Use `business-review` before seeking any later approval. Report the exact revision,
source coverage, unresolved issues and `current` flag. If `current: false`, label
the old draft as needing reconciliation and do not present it as current. Never
approve or transition to Analysis. On `E_BUSINESS_RECOVERY`, inspect the journal,
verify no writer is active, then run `business-recover` and retry the original
operation ID. On a stale revision, reopen and reconcile; never overwrite blindly.

This increment does not create Stories, implement approval or Analysis, commit,
push, install skills or call external AI APIs. No separate context checkpoint is used.
