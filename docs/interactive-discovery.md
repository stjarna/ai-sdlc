# Interactive Discovery — Increment 2

This increment uses the Codex skill for conversational reasoning and deterministic
local scripts for persistence. Load [the skill](../orchestrator/skill/SKILL.md) from
this checkout, then describe a business idea, ask to continue a request, or request
a Discovery review. Host catalog installation is not supplied by this increment.
For example: "Help me clarify this idea", "Continue Discovery for REQ-0001", or
"Review what we have learned so far". These are natural-language requests, not a
new host command API. The assistant selects one consequential question at a time.

## Storage and compatibility

```text
requirements/REQ-0001-example/
├── metadata.yaml       # existing schema 0.1: identity, lifecycle, technical links
├── idea.md             # original human-readable business idea; not rewritten
└── discovery.yaml      # optional, authoritative typed Discovery history
```

`new` still creates only the first two files. `open` and `validate` never initialize
history. The first `discovery-update` creates `discovery.yaml`; an empty records list
can initialize it explicitly. Metadata is not migrated or changed. Sidecar placement
is a fixed convention, so the strict existing `artifacts: {idea: ...}` remains intact.
The idea reference must not alias metadata or the reserved Discovery file.

`open` and `new` retain their existing payload fields and add `revision`, `discovery`
and `discovery_state`. Missing history is returned as `null`. `discovery_state` is a
derived view of question/assumption resolutions and corrections, not another stored
source of truth. Existing metadata statuses and all old command arguments remain.
Only `discovery` requests accept updates; cancelled requests remain readable.

The original idea can remain incomplete after substantial conversation. Existing
`W_DISCOVERY_INCOMPLETE` diagnostics still describe its empty template sections;
they do not measure the evolving structured history. No semantic business validation,
placeholder heuristics, contradiction detector or lifecycle readiness gate is added.

## History and update schema

The Discovery schema is independently versioned from the orchestrator and metadata:

```yaml
schema_version: '0.1'
request_id: REQ-0001
operations:
  - id: capture-001
    base_revision: '<64 lowercase hexadecimal characters>'
    records:
      - id: D-0001
        kind: user_statement
        topic: problem
        text: Customers repeatedly call to ask who owns their request.
        source:
          actor: user
          quote: Customers repeatedly call to ask who owns their request.
```

The revision above is illustrative; actual CLI output supplies it. History operations
and records are logically append-only. Atomic publication rewrites the YAML file,
preserving all existing record values and order. There is no delete/replace operation.
Local `D-0001` record IDs are assigned sequentially by the script. Topics are free
text; Python does not interpret their business meaning or require a questionnaire.

Every record requires `kind`, `topic`, `text`, `source`; persisted records also have
the script-assigned `id`. Missing or unknown fields are rejected. Record text,
topics and user quotations must be nonempty UTF-8-encodable strings; invalid Unicode
is rejected before publication.

| Kind | Provenance and additional fields |
|---|---|
| `user_statement` | `source: {actor: user, quote: ...}`; optional `answers` pointing to an earlier question |
| `ai_assumption` | `source: {actor: ai}`; never converted into a user statement |
| `question` | AI or sourced user provenance; initially open |
| `human_decision` | User actor and nonempty quote; required `action` and a `target` except for `decide` |

User evidence must be an actual quotation supporting the record. There is no
authenticated user identity or proof that a submitted quotation is genuine: scripts
enforce provenance structure, while the skill and human retain responsibility for
accuracy. A direct user answer does not need an extra ritual confirmation; an AI
assumption does require an explicit human decision before it is treated as confirmed.
Confirmation of one assumption is not approval of the Epic or permission to advance.

| Decision action | Target and effect |
|---|---|
| `decide` | No target; records an explicit standalone business choice |
| `answer` | Earlier unresolved question → answered |
| `defer` | Earlier unresolved question → deferred; optional user-provided `revisit` text |
| `unknown` | Earlier unresolved question → unknown; optional `revisit` text |
| `reopen` | Resolved/deferred/unknown question → open |
| `confirm` | Proposed AI assumption → confirmed, preserving its original kind and evidence |
| `reject` | Proposed or confirmed AI assumption → rejected |
| `correct` | Current user statement or substantive `decide`/`answer`/`correct` decision → superseded by the sourced correction |

An answered question must be explicitly reopened or its existing answer corrected.
An already superseded statement cannot be overwritten by targeting it again. A
correction chain determines the latest answer without deleting the earlier one.
To change an AI proposal, reject it and record a new proposal. To change a prior
deferral or unknown answer, resolve/reopen the question. Invalid references,
duplicate operation IDs, out-of-sequence record IDs, wrong provenance and unsupported
history versions fail validation with file-specific diagnostics.

## Tool-facing persistence

Use the Python environment from [the operation contract](../orchestrator/scripts/README.md).
The assistant creates a UTF-8 JSON changes file in a temporary working directory:

```json
{
  "records": [
    {
      "kind": "question",
      "topic": "access",
      "text": "Who should be able to see request ownership?",
      "source": {"actor": "ai"}
    }
  ]
}
```

Then invoke:

```text
python sdlc.py --project PROJECT open REQ-0001
python sdlc.py --project PROJECT discovery-update REQ-0001 --expected-revision REVISION --operation-id UNIQUE_OPERATION_ID --changes-file CHANGES.json
```

These are script arguments, not parameters the business requester must provide.
Use the returned ID when linking subsequent answers or decisions. Request IDs remain
stable after directory renames. The history file retains both the records and their
operation IDs so a resumed process can inspect prior work without chat history.

The expected revision hashes the exact bytes of target metadata, the referenced
original idea, and Discovery history, including its absence. Changing any of those
invalidates a fresh write based on an older revision. Directory names are not part
of the revision. Under the common project lock, the operation rescans the repository
for structural errors and duplicate Epic IDs, checks the revision and publishes the
new history. `new` uses that same lock. Other Epics are validated again; their content
is not part of this target's revision because it is not used to build its history.

Choose one unique operation ID for a batch, typically a UUID, and retain it through
retries. IDs allow 1–128 ASCII letters, digits, `.`, `_`, `:`, `-`, beginning with a
letter or digit. An identical retry uses the original ID, base revision and payload:
it returns `replayed: true`, the original `record_ids`, and the **current** Epic view,
without appending or rewriting history, even after intervening successful updates.
Reusing an ID with a different revision or records produces `E_IDEMPOTENCY`.

## Failures and recovery

| Diagnostic | Required response |
|---|---|
| `E_REVISION_CONFLICT` | Reopen, reconcile with saved context, then submit a new operation only if still needed |
| `E_PROJECT_BUSY` | Another writer or stale lock exists; do not bypass or automatically delete it |
| `E_IDEMPOTENCY` | Inspect the saved operation; do not change its meaning under the same ID |
| `E_WRITE_UNCERTAIN` | Publication occurred but durability confirmation failed; retry the exact operation |
| `E_UPDATE_INPUT` | Correct malformed JSON/arguments; diagnostic references the input file when applicable |
| `E_DISCOVERY_FILE`, `E_DISCOVERY_VERSION`, `E_DISCOVERY_HISTORY` | Inspect the sidecar; do not overwrite malformed or unsupported history |
| `E_DISCOVERY_RECORD`, `E_DISCOVERY_REFERENCE`, `E_DISCOVERY_PROVENANCE` | Correct the proposed record shape, reference or evidence |
| Existing `E_YAML`, `E_READ`, artifact and metadata errors | Inspect the reported file and line; no automatic repair |

Publication writes and fsyncs a temporary file in the Epic directory, then atomically
replaces `discovery.yaml` and fsyncs the directory. Existing file permissions are
retained; newly initialized history is private to the creating OS user. Before
publication, a handled write failure leaves the previous file intact and removes the
temporary file and lock. A retry is safe because records and the operation ID are
published together. A lost response can also be recovered with the same operation ID.

A hard process exit can leave `.sdlc-discovery.lock/` and `.discovery-*.tmp` files.
The previous published history remains usable if exit preceded replacement; after
replacement the operation ledger supports retry. There is no automatic stale-lock
removal: verify the writer is no longer active, inspect the published file, remove
only the abandoned lock/temp files, reopen and retry the original operation. Never
perform this cleanup against a live writer. There is no separate context checkpoint.

## Review and demonstration

Ask "Review Discovery for REQ-0001". The skill reopens the request and summarizes
current statements, explicit decisions, unconfirmed assumptions and unresolved
questions, following corrections and citing record IDs. The summary is derived from
history, not persisted as a competing authoritative document. It may assess whether
the information is developed enough for human review; it cannot grant approval.
The Epic stays in `discovery`, with no transition to refinement or Analysis.

The following is a fictional case-study example, not a completed AI evaluation:

1. User: "People forget commitments. Let them record deadlines against tasks."
   The skill creates a request, preserves those words and captures a sourced statement.
2. Assistant: "Should this cover recording deadlines, or reminders as well?"
   User: "Recording dates only. Reminders are outside this first scope."
   Save the answer linked to the question, with its quotation.
3. Assistant proposes: "I am assuming deadlines can be optional. Is that right?"
   User: "Yes, deadlines are optional." Save a confirmation linked to the assumption.
4. Assistant: "Should users be allowed to choose a date in the past?"
   User: "Defer that until I discuss it with support." Save a deferred decision.
5. Start a new chat and resume by ID. The assistant loads the answered and deferred
   questions instead of repeating them, then asks the next relevant unresolved question.
6. Request a review. It shows dates-only scope, reminders excluded, the confirmed
   optionality assumption, and the deferred past-date rule. It does not invent a
   support answer or mark the request ready for implementation.

Application/domain details belong in this demonstration only; the skill and scripts
remain generic. Later date-to-date-and-time impact analysis is outside Increment 2.

## Manual conversational evaluation

Run the skill in a temporary project with two ideas: the example above, and an
unstructured service-desk request to reduce repeated status calls. Keep a transcript
and inspect `idea.md`, `discovery.yaml`, and the derived review after each exchange.

- Start with incomplete context: expect one consequential question, no questionnaire.
- Answer indirectly or ambiguously: expect clarification rather than a guessed rule.
- Say "I don't know", then explicitly defer another issue: expect distinct states.
- Let an AI assumption remain unanswered: it must remain proposed, without user evidence.
- Confirm one proposal and reject another: expect correctly linked user decisions.
- Correct an earlier answer: expect preserved original evidence and a current correction.
- Resume in a fresh chat: expect use of saved context and no repetition of answered questions.
- Request review: expect clear provenance, unresolved gaps, record references and no approval.

Evaluate semantic fidelity and question quality manually. Passing deterministic
tests or the skill format validator does not prove the assistant reasons correctly.

## Known limitations

- Local cooperating writers only. Lock creation is atomic but has no wait queue;
  callers can receive busy errors. Hostile/manual edits can ignore the lock; observed
  changes are checked again before publication, but this is not a security boundary.
- Filesystem atomic rename/fsync behavior is assumed. Network filesystems, Windows
  portability and protection against every power-loss scenario are not validated.
- Missing sidecars are intentionally valid for legacy requests. External deletion
  changes the old revision, but after a fresh open it cannot be distinguished from
  a request that never had history. Retain history and use Git/backups for recovery.
- The entire ledger is replayed and rewritten per update. This is suitable for a
  small PoC, with no compaction, cryptographic tamper evidence or authenticated quotes.
- User evidence can contain sensitive material. The public repository must not hold
  proprietary company content; use fictional examples or an appropriately scoped project.
- No autonomous lifecycle transitions, Analysis, subsequent SDLC stages, external
  AI service, ticketing integration, automatic Git actions or host skill installation.
