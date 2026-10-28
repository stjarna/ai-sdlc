---
name: sdlc
description: Guide interactive requirements Discovery from an informal business idea, persist sourced statements and explicit decisions, and resume or review local requests with the AI SDLC Orchestrator.
---

# Interactive Discovery

Read the [operation contract](../scripts/README.md) for environment setup. For the
record schema, update payloads and recovery rules, read the
[Interactive Discovery guide](../../docs/interactive-discovery.md). Keep this
checkout's `orchestrator/` directory together; host catalog installation is separate.

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

The Epic remains in `discovery`. This increment does not transition to refinement or
Analysis, create Stories, implement later stages, commit, push, install skills or call
external AI APIs. No separate context checkpoint is used.
