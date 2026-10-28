# Functional Analysis — Increment 5

Increment 5 drafts and refines one Epic-wide `specification.md` from the immutable
business baseline selected by the current business advancement. The AI skill writes
and assesses meaning; the CLI validates structure, evidence links and publication.
Human review is required. [Increment 6](analysis-approval.md) adds explicit Analysis
approval and separate onward advancement. Technical Design, Story decomposition and
application test execution remain excluded.

## Workflow and authority

```text
business_refinement --business-advance--> ready_for_analysis
ready_for_analysis --analysis-generate--> functional_analysis
functional_analysis --analysis-revise/review--> functional_analysis
functional_analysis --explicit discovery-reopen--> discovery
```

Draft first using the available approved evidence. Do not start a lengthy clarification
questionnaire. Review the draft, identify material gaps and ask focused questions.
Reviewing, refining, structural validity and an AI readiness opinion are not approval.

Live schema `0.4` adds `functional_analysis` and an `analyze` lifecycle event. It is
used only when Analysis starts; existing schema `0.1`–`0.3` remains readable. The start
event identifies the preceding business advancement, approval and baseline. Approval
validity and the active input remain visible in Analysis. Existing business review
hashes and approved baseline layouts retain their meanings.

The CLI derives input from the active lifecycle handoff, checks its current approval
and verifies the full immutable baseline before a write. `analysis-review` returns the
frozen business and Discovery records for drafting; the agent must use these, not the
live draft, original chat or a separately selected historical baseline. Original idea
prose is contextual evidence, not a substitute for confirmed business requirements.

After Discovery reopening, retain the specification and all historical bytes, but mark
them as needing reconciliation. No new Analysis writes are allowed until renewed
Discovery completion, Business Refinement, business approval and separate advancement.
Then explicitly regenerate/revise against the new input and previous Analysis revision.
A new handoff invalidates the old Analysis binding even if business bytes match.
No silent merge or restoration of historical approval authority is permitted.

## Artifacts and exact format

```text
requirements/<epic>/
  specification.md
  analysis-history.yaml
  .analysis-transaction.json     # transient; blocks reads until inspected recovery
  business-baselines/<digest>/  # existing five frozen artifacts and manifest
```

Use one constrained Markdown source; there is no second authoritative YAML requirements
catalogue. The parser accepts these first five lines, with the blank second line:

```markdown
# Functional Analysis — REQ-0001

Baseline: <SHA-256 baseline ID>
Approval: BD-0002
Handoff: <business-advance operation ID>
```

Then use all sections in this order: `Functional requirements`, `Use cases`,
`Business rules`, `Acceptance criteria`, `Business coverage`, `Inherited unresolved
items`, `Analysis questions`, `Analysis proposals`. Empty Business rules, questions,
proposals or inherited items use `None recorded.`. Other sections require content.

Items use `### FR-001 — Title` (and UC/BR/AC/AQ/AP respectively), followed by exact
`Field: value` lines. For multiline prose, indent each continuation by two spaces.
References are unique IDs separated by comma and space, or `-` for no references.
IDs are scoped to the Epic; refer to them across Epics as `REQ-0001/FR-001` in future
integrations. Existing IDs cannot disappear: retain a `retired` item instead. Retired
IDs cannot reactivate. Wording/title edits preserve IDs; semantic identity still
requires human/AI judgment.

| Kind | Required fields in addition to Business sources, Discovery evidence, Status |
|---|---|
| FR | Questions, Statement |
| UC | Requirements, Questions, Actor, Preconditions, Trigger, Main flow, Alternative flows, Outcome |
| BR | Requirements, Questions, Statement |
| AC | Requirements, Questions, Given, When, Then |
| AQ | Affected items, Statement |
| AP | Affected items, Statement |

FR/UC/BR/AC statuses are `specified`, `blocked`, `proposed`, `retired`; these are draft
classifications, never approval. AQ statuses are `open`, `unknown`, `deferred`, `retired`.
AP statuses are `proposed`, `rejected`, `retired`. A retired item can clear obsolete
source links using `-` after reconciliation while retaining its ID and historical
contents. Each specification needs at least one FR and UC. BRs are included only when
supported. Main flows use consecutive `1. ...`, `2. ...` steps; alternative flows remain
prose. Acceptance criteria require nonempty Given/When/Then, not keyword-based semantic
scoring.

Example block, illustrating structure rather than approving a requirement:

```markdown
### AC-001 — Optional due date
Business sources: B-003
Discovery evidence: D-0005
Status: specified
Questions: -
Requirements: FR-001
Given: A task has no due date.
When: Its due-date requirement is evaluated.
Then: A due date is not required.
```

## Traceability, coverage and unresolved items

Every active normative item must cite approved B items and frozen Discovery evidence
supporting those B items. Effective human confirmations and their originating AI
assumptions are accepted together. AC/UC/BR reference FRs; specified dependent items
must retain supporting business traceability and cannot depend on blocked/proposed FRs.
Each specified FR requires at least one specified AC. Questions reference AQ items;
specified items cannot list an unresolved question dependency. Blocked items must do so.

Every approved B item has exactly one coverage line:

```markdown
- **B-001** [contextual] - | Explains the intended value.
- **B-002** [elaborated] FR-001 | Describes the supported behavior.
- **B-003** [unresolved] FR-002 | Behavior is blocked by a recorded question.
- **B-004** [excluded] - | Reminders remain outside scope.
```

These are alternative examples of dispositions, not a fixed mapping for all fixtures.
`elaborated` references supported specified FR/UC/BR items; `unresolved` references
supported blocked items. `contextual` and `excluded` require explanation without
artificial functional coverage. Proposed/rejected/retired items cannot satisfy coverage.
The AI checks whether each disposition is semantically justified.

Copy every frozen U/P item line unchanged into `Inherited unresolved items`, including
its ID, source references and wording. Business approval acknowledgement accepts an
uncertainty; it does not resolve it or confirm a proposal. AQ/AP items can explain
impacts or possible alternatives while preserving that inherited evidence. An AQ citing
a still-unresolved frozen business question cannot be retired; an inherited deferral
remains deferred.

For the established To-Do scenario, U-001/D-0006 remains deferred pending support
consultation. Do not decide whether past dates are allowed, and do not encode either
answer as specified acceptance criteria. Mark affected behavior blocked where necessary.

An explicit human wording refinement can use `analysis-revise`. New business behavior,
changed scope or resolution of a deferred business decision requires explicit Discovery
reopening and renewed business approval. Do not promote new conversation into the
approved baseline. Analysis feedback is retained as feedback, not new business authority.

## CLI contracts

Use the Python environment and project argument in the
[operation contract](../orchestrator/scripts/README.md). These are agent-facing operations;
the user converses naturally and need not copy tokens or run commands.

- `analysis-review ID`: read-only specification, current input, full Analysis review
  token, coverage, questions, proposals and history summary. Before first drafting it
  returns verified input and no specification. Historical drafts remain visible but
  labelled stale after reopening. Structural success is not semantic validation.
- `analysis-generate ID`: initial draft, or explicitly regenerate a stale draft.
- `analysis-revise ID`: refine an existing draft or explicitly reconcile it to a new input.
- `analysis-recover ID`: roll forward an inspected interrupted Analysis publication.

Both writers require:

```text
--expected-analysis-review-revision R
--expected-baseline-id BASELINE --expected-handoff-id ADVANCEMENT
--operation-id UNIQUE --editor NAME --reason TEXT --document-file FILE
```

Whenever a draft exists, also pass `--expected-analysis-revision SHA256`, including
regeneration. An initial revise is rejected. Generate cannot overwrite a current draft.
The complete Analysis token hashes the existing business review context plus the exact
specification/history fingerprints, including absence. Baseline and handoff arguments
assert current authority; they cannot select an arbitrary historical input.

Optional `--feedback-file FILE` accepts strict YAML (JSON is also valid YAML):

```yaml
actor: Declared human editor
text: Actual human feedback, preserved without invented quotations.
items: [FR-001]
```

Feedback must reference existing Analysis items. The agent reason is distinct from
actual human text. Declared identities remain unauthenticated procedural attribution.

Outputs are JSON with existing `ok`/diagnostics conventions. `analysis-review` includes
`input`, `details` (typed items, coverage, inherited items), `current`,
`analysis_review_revision`, `approval_implemented: true` and
`semantic_assessment: not_performed_by_cli`. `open` adds `analysis` and its review token.
Missing/corrupt referenced baselines fail closed; no baseline is reconstructed from
a mutable draft. Key new codes are `E_ANALYSIS_INPUT`, `E_ANALYSIS_DOCUMENT`,
`E_ANALYSIS_REFERENCE`, `E_ANALYSIS_PROVENANCE`, `E_ANALYSIS_COVERAGE`,
`E_ANALYSIS_UNRESOLVED`, `E_ANALYSIS_HISTORY`, `E_ANALYSIS_MISMATCH`,
`E_ANALYSIS_FILE` and `E_ANALYSIS_RECOVERY`, alongside existing conflict/busy/idempotency,
baseline and write-uncertainty diagnostics.

## History, concurrency and recovery

`analysis-history.yaml` stores append-only revisions with SHA-256, previous digest,
full base64-encoded exact Markdown bytes, baseline/approval/handoff, editor, reason,
UTC timestamp, operation ID, expected complete review token, mode and optional actual
human feedback. Every retained revision is checked against its own immutable input.
A new operation with identical bytes remains a distinct revision event and changes
the complete review token. Exact retries return current state without duplicating
history or restoring an old handoff's authority. Changed retry inputs are rejected.

Reuse the project lock, optimistic revision checks and the existing small journaled
publication helper with a fixed Analysis artifact allowlist. Initial publication
includes metadata, specification and history; revision includes specification/history.
Durable journal intent is written before replacement. The visible transaction completes
only after all artifacts and journal removal are durable. Readers reject unfinished
publication; several filesystem replacements are not described as intrinsically atomic.

After interruption, inspect the journal and establish no writer remains. An abrupt
process exit may leave the project lock; remove it only after inspection. Run
`analysis-recover` to roll forward known before/after contents; unrelated edits or
unsafe paths block recovery. Retry the original operation ID and exact payload to
verify idempotent completion. Do not bypass a conflict with a new ID, delete audit
history or silently rewrite sources. Recovery does not run Analysis or approve it.

## Manual acceptance: established To-Do baseline

Keep all artifacts and transcripts outside the source checkout. Copy the established
approved and advanced To-Do fixture, preserving its actual decisions and baseline.
If unavailable, reconstruct the documented fictional Discovery scenario using CLI
operations and label setup data fictional; obtain real human completion, approval,
U-001 acknowledgement and separate advancement. Never simulate these responses.

1. Tell Codex: "Use the SDLC skill to start Functional Analysis for the task due-date
   request in this disposable project. Draft first from the approved business baseline."
2. The agent runs `analysis-review`, verifies input and drafts a meaningful specification
   through `analysis-generate`. It summarizes scope and material ambiguities before
   asking a focused question. Verify `functional_analysis` and unchanged business audit.
3. Review optional due-date behavior, supporting use case, optionality rule and observable
   Given/When/Then criteria. Check coverage of all four B items without inventing extra
   features for value or exclusions. Inspect FR → B → D and AC → FR evidence on request;
   D-0005 remains the human confirmation, D-0004 the originating assumption.
4. Verify U-001/D-0006 remains deferred and visible; neither allowed nor rejected past
   dates is specified. Confirm reminders/notifications stay excluded. Assess ambiguity,
   contradictions, missing edge cases and testability manually; no Python score does this.
5. Request a genuine wording refinement, keeping scope and deferral unchanged. Verify
   `analysis-revise`, retained actual feedback, previous contents and unchanged input.
6. Start a fresh Codex conversation, point to the same project and ask to resume. Expect
   a short accurate review with preserved questions, not a repeated questionnaire.
7. Say "Looks good" or ask for review. Verify no Analysis approval/onward transition.
8. In separate disposable copies, corrupt/remove the baseline and attempt a write;
   verify rejection. Reopen Discovery through explicit real instruction and verify
   the prior Analysis is stale. A renewed approved business cycle requires explicit
   Analysis reconciliation, even if business text returns to identical bytes.
9. Finish with `analysis-review`, retaining the exact revision and remaining questions
   as evidence. Do not proceed to Technical Design or Story decomposition.

Codex conversational acceptance is the PoC target. Claude Code CLI/IDE are unverified
portability targets and do not block PoC acceptance. The shared adapters load the same
instructions and CLI; runtime behavior must not be claimed verified by static checks.

## Limits and approval boundary

The CLI verifies structure, provenance links and consistency of declared statuses, not
semantic entailment, completeness or whether an exclusion was correctly classified.
It cannot detect an invented rule hidden in otherwise valid prose. AI assessment and
human review remain necessary. Local locking does not coordinate independent clones;
unrestricted filesystem edits can bypass procedural controls. Full histories and
baseline revalidation trade storage/read cost for simple inspectability.

The existing architecture also supports Story specifications; Increment 5 intentionally
uses its Epic-wide option and defers decomposition. Future Story links should reference
this authority rather than duplicate it. [Increment 6](analysis-approval.md) binds approval
to the exact revision operation, complete review, Business handoff and acknowledged
open items. Analysis editing is blocked after separate advancement; explicit reopening
starts a new cycle without deleting historical evidence. Technical Design and a workflow
engine remain excluded.

## Sequential engineering extension

The separately authorized [engineering slice](engineering.md) now consumes the approved Analysis handoff through Technical Design, planning, controlled development, verification, Security review and a final report. Earlier increment scope statements describe their historical boundaries. The extension preserves approval separation, existing audit/baseline formats and declared identity semantics.
