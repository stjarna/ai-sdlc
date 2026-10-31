---
name: sdlc-discovery
description: Discovery domain skill expertise for the governed discovery phase; generate and review content without authorizing lifecycle changes.
---

# Discovery domain skill

Use this package to understand the business problem, expected value, affected people
and useful scope boundaries. Read the saved evidence before selecting the next question.
The orchestrator owns identity, record persistence, completion, reopening and handoffs;
this package recommends content and questions, never lifecycle decisions.

## Work from intent and evidence

Preserve the original idea verbatim. Treat it as context; distinguish supplied statements,
explicit human decisions, proposed AI assumptions, unknown answers and deferred questions.
Follow correction and resolution chains rather than repeating settled questions or treating
superseded statements as current. A supporting quotation is what a person said, not
independent verification. Never promote an assumption through silence or positive feedback.

Explore stakeholders/affected users, the problem, expected value, constraints, dependencies
and boundaries only where consequential to this request. Do not require a checklist of
answers, invent success metrics or add features simply to fill a document. Prefer the
question whose answer most changes scope, outcome or risk. Ask one consequential question
at a time and wait; adapt the follow-up to the actual answer. Offer sensible options as
proposals when useful, not decisions. Unknown and deferred answers are valid outcomes;
record a revisit condition only if supplied.

## Reach a useful review

After meaningful answers, a material scope decision or a user request to stop questioning,
assess whether a useful review can be presented. There is no fixed question quota or
semantic completeness test in Python. Respect a request to review now; summarize gaps
instead of continuing interrogation. The person may also continue exploring.

Summarize the original intent, confirmed scope/exclusions, expected value, constraints,
explicit assumptions, unresolved/deferred questions and consequential risks. Distinguish
readiness advice from approval. A review request does not complete Discovery. Return the
review to the orchestrator for a separate explicit Requester completion decision; never
claim downstream readiness, business approval or advancement on your own.

## Template and records

Resolve the pinned `idea` template through `sdlc.py templates idea`; its scaffold owns
human-readable structure. Do not rewrite idea.md during conversation. `discovery.yaml`
is an append-only typed history, not a templated document: the existing deterministic
record schema and orchestrator operations own IDs, links and validation. Provide actual
user quotations for statements/decisions and preserve AI provenance for proposals.
Do not add a second business specification or checkpoint. Persist through the coordinator;
its writer records this package's exact version/digest. Template, skill, CLI and validator
versions are independent. Reproduce pinned instructions, not deterministic AI wording.


## Idea 1.1 generation slots

The coordinator deterministically renders the original idea into `problem`. Other slots
are `users`, `expected_value`, `initial_scope`, `success_criteria`, `assumptions` and
`open_questions`. Supply optional section text through the internal `--idea-details-file`
only when actually provided by the person; never infer facts from a blank section or
extract new decisions with Python. Missing/null/empty values render `Not provided.` and
remain completeness warnings, not structural errors or approval blockers.

Unknown is distinct from a human-confirmed absence (`Confirmed: none.`), an `Unconfirmed
proposal: ...`, or a `Deferred: ...` question. Preserve those actual declarations in
section text and then use typed Discovery records as authoritative conversational history.
Do not default assumptions/questions to none. Keep the original description in Problem
and never rewrite idea.md during later answers. New requests use the effective runtime's
catalog; existing requests retain their original Idea/template pin. Literal braces in
user input are data and are never evaluated as another template.
