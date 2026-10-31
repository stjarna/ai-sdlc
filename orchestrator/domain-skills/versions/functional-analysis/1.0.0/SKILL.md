---
name: sdlc-functional-analysis
description: Functional Analysis domain skill expertise for the governed functional-analysis phase; generate and review content without authorizing lifecycle changes.
---

# Functional Analysis domain skill

Use this package to translate the handoff-selected approved Business baseline into
precise, testable behavior for Engineering and independent QA. The orchestrator resolves
and verifies that baseline, persists revisions and coordinates human approval/separate
advancement. Never substitute mutable business drafts or chat recollection.

## Draft from approved input

Prepare a useful Epic-wide draft first rather than starting an extensive questionnaire.
Use testable language for observable requirements and acceptance criteria, relevant
preconditions/postconditions, normal/alternative flows, validation/error behavior and
data rules. Preserve stable identities and source relationships. Business context and
exclusions need no fabricated functional requirements. Do not introduce architecture,
stack or implementation choices as functional requirements.

Trace every confirmed behavior to approved business evidence. Preserve inherited unresolved
questions/proposals and their exact source relationships; do not resolve them by writing
an acceptance criterion. Surface missing or contradictory behavior as Analysis questions,
with affected items and honest blocked/proposed coverage. Scope changes or new business
choices require upstream reconciliation through the coordinator. An unresolved requirement
cannot silently become a default, runtime restriction or rejection. Not implementing an
unspecified capability and explicitly rejecting it are distinct observable effects.

## Assess functional quality

Check that acceptance criteria describe verifiable Given/When/Then outcomes and align
with their requirements. Review relevant edge conditions, empty/invalid input, error
handling, alternative flows, state changes, data preservation and functional consistency
where the approved scope calls for them. Do not invent universal validation policies,
error wording or edge-case business choices merely because they sound sensible.
Describe evidence gaps and ask one focused clarification after a useful draft exists.
Keep examples illustrative unless actually supported; preserve original IDs in excerpts.

For refinements, preserve IDs, retire obsolete items under existing rules and keep actual
human feedback. A request labelled wording-only must not alter business meaning. Review
for clarity, testability, observable outcomes and source alignment; Python does not judge
those semantics. Resume from persisted contents/coverage/questions without repeating
answered questions. Deferred behavior stays deferred until a real sourced decision.

## Template, review and handoff

Resolve `sdlc.py templates specification` and use the pinned scaffold, not a duplicate
section list in this skill. Validators own supported item fields, coverage dispositions
and references. The writer records the exact package and template pins alongside its
revision operation; managed execution also records the runtime revision/digest.

Present behavior, acceptance expectations, exclusions, blocked items and every inherited
or newly identified question/proposal concisely. Explain whether the draft is useful for
Engineering/QA, distinguishing semantic recommendation from structural eligibility and
human approval. Accepting uncertainty does not resolve it or establish implementation
readiness. Return the review for explicit Analysis approval; separate advancement alone
creates/advances work tracks. Do not authorize Design, coding, tests or lifecycle changes.
