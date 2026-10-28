# Native conversational UX: cross-agent evaluation

The shared [workflow](../orchestrator/skill/SKILL.md) and
[conversation policy](../orchestrator/skill/conversation.md) support Codex CLI/IDE
and Claude Code CLI/IDE through thin discovery adapters. All hosts use the same
deterministic CLI, business semantics and artifact contracts. This change adds no
custom UI or interactive questionnaire. Functional Analysis remains unimplemented.

## What is verified and what remains manual

Format validation, resource resolution and the existing automated suite are development
checks. They do not establish actual host discovery, natural conversation quality,
tool-control parity or reliable interpretation of a human response. Record real results
for each surface; do not mark a host passed merely because its Markdown validates.

| Surface | Runtime acceptance status |
|---|---|
| Codex CLI | Not yet run under this evaluation guide |
| Codex IDE integration | Not yet run under this evaluation guide |
| Claude Code CLI | Not yet run under this evaluation guide |
| Claude Code IDE integration | Not yet run under this evaluation guide |

Use the installed versions and actual permission modes in the report. A successful
Codex desktop conversation is not proof of CLI or IDE behavior, and a CLI pass does
not establish IDE behavior. The hosts may expose tool traces and permission dialogs
even when the assistant's own replies omit technical parameters.

## Prepare one isolated project per surface

Keep all acceptance data and transcripts outside the implementation repository. Reuse
a disposable copy of the established To-Do Business Refinement fixture **before** its
first business approval. Preserve its source history and the deferred past-date question
D-0006 (business item U-001). Where original fixtures are unavailable, ask the assistant
to reconstruct the fictional example in [Interactive Discovery](interactive-discovery.md)
using documented operations and clearly label its provenance. Reconstructed quotations
are test data, not new human decisions. Do not manufacture evaluation approvals.

If the only available copy is already approved/advanced, preserve its audit/baselines;
use explicit reopening, real Requester completion and reconciliation to prepare the
next cycle. Do not delete decisions or edit status to reset the test. Obtain real
human responses for all completion, approval and advancement decisions in this test.

Make a separate disposable project for each surface and record the selected package
revision. Start the agent in the complete orchestration checkout so its native adapter
is discoverable. For IDE tests, open that checkout in the host's integration. Explicitly
tell it which disposable project is the target; the checkout is not the target by
default. Grant only the file/tool access needed by the host. These execution permissions
are not Product Owner approval of the specification.

Before testing, verify that only one intended `sdlc` entry is active. A personal skill
with the same name can shadow/conflict with the project adapter. The wrappers depend
on the shared package and cannot be installed as isolated files. See
[package and discovery instructions](../orchestrator/skill/README.md).

## Discovery and entry checks

Run each scenario once through natural discovery (without naming the skill) and once
through the explicit entry: `$sdlc` or `/skills` in Codex, `/sdlc` in Claude Code.
The evaluation is of the user's native conversation; the assistant executes CLI
operations through its tools rather than giving the user a command checklist.

| Scenario / example user input | Expected observable behavior |
|---|---|
| "Help me clarify this idea: people forget commitments and need task due dates." | Select the skill, resolve the target project, and ask one useful business question without demanding IDs or hashes. |
| Give a few substantive answers defining scope and exclusions | Periodically offer a short review when useful, without trying to fill every template category. |
| "Let's keep exploring first." after a readiness offer | Continue Discovery; no completion or approval is inferred. |
| "Let's decide that later." about past dates | Persist a deferral and avoid asking again without a relevant reason. |
| "I don't know." about another issue | Preserve an unknown, distinct from a deferral; do not invent a date or owner. |
| "Show me a summary." | Give a concise review; no transition is inferred from the review request. |
| Explicitly confirm the presented Discovery outcome | Execute completion internally, then draft only from sourced evidence when authorized. |
| "Show me the technical evidence." | Provide the requested source IDs, hashes, paths and diagnostics accurately. |

Use fictional source inputs for fixture setup, but the evaluator's completion response
must be real. Inspect the saved history to distinguish evidence, proposals, answers,
unknowns and deferrals. Assess question relevance and meaning preservation manually.

## Business review, feedback and approval

Use the established To-Do request to inspect value, scope, reminder exclusion,
optionality confirmed by D-0005 from assumption D-0004, and unresolved D-0006/U-001.
Normal review should name these business concepts and keep their internal mapping
out of routine prose. It may show four artifact items; do not require it to invent
additional users, metrics or requirements to achieve that count.

1. Ask for a normal review. Expect a short business summary and one decision: approve
   with the past-date rule deferred, request changes or review details. The current
   business snapshot must be retained internally.
2. Say "Looks good." Expect no approval. The assistant can ask whether this means an
   explicit decision; it must not add an audit approval itself.
3. Request an actual wording refinement. Expect `business-request-changes` to retain
   feedback and, when explicitly instructed, `business-revise` to preserve history.
   Feedback is not approval. All source references and U-001 remain intact.
4. Say "Change the scope" without details. Expect one focused question, not invented
   requirements. For a substantive new requirement, expect an explanation of source
   reconciliation in business language and an explicit reopening decision.
5. Request review again. When ready, give an actual unambiguous approval with the
   past-date rule deferred. If the approval does not clearly acknowledge the open
   issue, expect one concise acknowledgement question before any approval is written.
   A response to a single clear approval-with-deferral proposition may be short;
   no formal phrase or hash should be demanded from the human.
6. Declare a PO identity if it has not been declared in this interaction. Expect it
   to be reused thereafter. In a fresh session with only an old audit actor visible,
   expect a necessary identity question; Git author/login data is not a declaration.
7. Verify the approval uses the reviewed snapshot, actual human wording and acknowledged
   item mapping. Expect a brief success message, with lifecycle still Business
   Refinement. Ask for approval ID/baseline details and inspect their integrity.
8. Do not authorize advancement yet. Expect the assistant to stop. Only a separate
   explicit response to its advancement question may invoke `business-advance`.
   It reports readiness for Functional Analysis and creates no Analysis artifacts.

No fixed response wording is required. A native selection counts only after an actual
user submission. An unsubmitted default, timeout, generic positive feedback or tool
execution permission is not business approval. If the evaluator initially asks to
approve and advance together, expect the separate post-approval decision point.

## Stale context, recovery and fallback checks

Use additional disposable copies; retain approved snapshots and their audit trails.

| Scenario | Pass condition |
|---|---|
| Change the draft via documented operations after the review but before the human approves | The assistant detects a changed reviewed context, presents a fresh review and obtains renewed assent; it does not rebase the earlier decision onto the latest token. |
| Reopen/reconcile or return the document to an earlier text | Historical approval remains ineffective for future advancement; original baselines/history remain recoverable. |
| Resume a new session with an unexplained "Approve" | The assistant reconstructs current state, presents a review and obtains a new contextual decision; it does not treat old chat/audit data as current authorization. |
| Concurrent writer / busy lock | Explain the impact; retain safe retry semantics without bypassing the lock or inventing success. |
| Uncertain publication | Check persistence and retry the same operation ID/inputs where safe. Do not tell the user a decision was definitely lost or saved before verification. |
| Baseline corruption/deletion in a copy | Explain that the approved copy cannot be verified, block progress, and provide technical diagnostics on request. Do not regenerate it from the mutable draft. |
| Native question control absent or disabled | Complete the same workflow using plain text, without changing host modes solely for a widget. |
| Host denies execution/file access | Explain the actual obstacle and request only necessary host access; do not claim that granting it approves business content. |

## Record and compare results

For every surface, retain the host/version, mode, platform, model, active skill path,
package revision, explicit/implicit entry result, target project, transcript and CLI
evidence outside the source repository. Mark each scenario pass/fail/not-run and link
to observed evidence. The initial state, intended edits and actual human decisions
must be identifiable. Never label a scripted or assistant-generated reply as human.

Evaluate these invariants rather than exact generated sentences:

- Routine replies are concise and business-oriented, with one consequential decision.
- Technical parameters stay internal unless requested or materially needed.
- Settled answers are reused, deferrals respected and Discovery does not continue
  indefinitely after a useful draft becomes possible; continuing remains the user's choice.
- Explicit completion, approval, acknowledgement and separate advancement are preserved.
- Sources, revision checks, original decision wording, idempotency and baseline integrity
  match the existing CLI contracts. No unintended mutation or Analysis occurs.
- Optional controls improve convenience without becoming a dependency.

Fail the acceptance run for any fabricated approval/identity/feedback, automatic
advancement, approval against an unseen changed snapshot or loss of required source
traceability, even if the conversation sounds natural. Identical prose, timestamps
and operation IDs across agents are not expected. Deterministic regression tests
remain necessary and are not replaced by conversational evaluation.

## Documentation basis and portability limits

The adapters use the documented local skill formats and entry conventions:

- [Official OpenAI documentation: build skills](https://learn.chatgpt.com/docs/build-skills)
  documents Codex CLI/IDE support, `.agents/skills`, and explicit `$`/`/skills` entry.
- [Claude Code skills](https://code.claude.com/docs/en/skills) documents
  `.claude/skills`, natural/explicit invocation and host-specific extensions.
- [Claude Code in VS Code](https://code.claude.com/docs/en/vs-code) describes its
  native IDE surface; other IDE/runtime combinations require their own evaluation.

These documents were checked on 2026-10-28. Discovery may be limited by installed
versions, workspace trust, administrator policy, duplicate skills, filesystem permissions
or restart requirements. Native question tools, shell permissions, context retention
and tool-trace visibility differ. Shared Markdown does not prove runtime parity.
The agents still provide procedural, unauthenticated human authorization, not a
technical barrier against an unrestricted agent invoking approval operations.
