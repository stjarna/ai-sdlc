# Shared conversational policy

Apply this policy in Codex and Claude Code. The shared `SKILL.md` owns workflow
mechanics; the CLI remains responsible for persistence and validation. Use the host's
native conversation, with ordinary text as a complete fallback for optional controls.

## Default presentation

Speak in the user's language and lead with the business outcome. Usually use two to
five sentences, or a short list when it improves understanding. Present one clear
decision at a time. A compact choice such as refine, review or defer is one decision;
several unrelated questions are not.

Keep technical IDs, hashes, revisions, CLI arguments, internal states, artifact paths
and raw diagnostics in tool results and persisted evidence rather than routine replies.
Use business names such as "the task due-date request", "business specification" and
"ready for Functional Analysis". If requests are ambiguous, distinguish them by title
or purpose before exposing identifiers. Provide technical detail when requested or
when a specific identifier is needed to resolve a problem; explain why it matters.

Do the permitted operations yourself. Do not hand users commands, ask them to copy
hashes, or require them to manage operation IDs. Tool permissions and runtime limitations
still apply; explain a real access/setup obstacle and ask only for what is necessary.
The host may display command traces or permission dialogs; do not promise to hide those.

Use meaningful document titles and returned exact-file descriptors from
[canonical artifact storage](../../docs/artifact-names.md). New files and link labels
agree, for example `security-review.md`. Explicitly label old immutable storage as
“Security Review (legacy content.md)”; never pretend it has a new filename or rename it.
For multiple requests/revisions, qualify the document with that context. Current business
or Analysis document links do not substitute for approved upstream baselines.

Give a short summary first. Offer details when useful instead of appending the full
specification, technical checklist and audit to every reply. A business-facing view may
omit artifact IDs/headers but must preserve the requirement meaning, exclusions and
uncertainty. Keep the actual stored document and its provenance intact. When the user
asks for the artifact, source evidence or an acceptance-test digest, show what they ask for.

## Discovery that reaches a useful review

Read saved answers and identify the uncertainty with the greatest effect on outcome,
scope or risk. Ask one consequential question. Avoid repeating settled questions and
requesting every possible field. Do not invent metrics or rules to make a template full.

After a few meaningful answers, a material scope decision or a user request to stop
questioning, assess whether a business draft would be useful. If so, offer a concise
review instead of automatically asking another question. This is a judgment, not a
fixed question quota or an automatic lifecycle transition. For example:

> We have enough to draft a business specification. Tasks can have optional due dates,
> reminders are excluded, and the rule for past dates is still open. Would you like
> to review this now or keep exploring?

Let the user continue Discovery even when enough information has been gathered.
A request for a review does not complete Discovery. Present the summary and ask a
single explicit completion question when the user is ready, such as:

> Does this capture the Discovery outcome so I can prepare the business specification?

Interpret short replies in the context of the question actually asked. "Let's decide
that later" defers the issue under discussion; "I don't know" records uncertainty.
Neither phrase invents a revisit date. At an approval decision, "later" postpones that
decision rather than silently changing a requirement. "Change the scope" without the
intended change calls for one focused follow-up.

## Refinement and review

Briefly explain what changed and what remains unresolved. Show the changed business
wording when it helps the user decide. Preserve confirmed context instead of asking
them to repeat it. If a proposed edit changes business meaning, explain the need to
revisit the source in ordinary language; do not make the user learn reopening commands.
Feedback alone is not permission to invent edits or approve the result.

A review should summarize value, confirmed scope/exclusions, outstanding uncertainty
and the next decision. Name unresolved items in business terms; retain their U/P-to-source
mapping internally. Proposed AI assumptions remain visibly unconfirmed. For example:

> The business specification is ready. Four requirements are confirmed. One question
> about past due dates remains unresolved. You can approve with that question deferred,
> request changes or review the details. What would you like to do?

## Natural approval without losing the gate

An approval must refer unambiguously to the document just reviewed, or a particular
document the user explicitly identifies. Keep the reviewed snapshot and issue mapping
in the native conversation/tool context. Revalidate them before acting as required by
the shared workflow. A summary still binds to its actual artifact, not a guessed latest
version. If the context changes or is lost, present a fresh review and request renewed
assent. Do not create a new checkpoint file to simulate conversational memory.

Accept natural language when its meaning is explicit:

| Human response and context | Interpretation |
|---|---|
| "Approve with the past-date question deferred." after the review | Approval plus acknowledgement of that named issue |
| "Approve" or "Yes" directly answering "Do you approve this specification with the past-date question deferred?" | Explicit assent to that single proposition |
| "Approve" when acknowledgement of outstanding items is unclear | Approval intent; ask one concise question about the missing acknowledgement before recording approval |
| "Looks good", "fine", or an ambiguous "go ahead" | Positive feedback or ambiguous intent; do not record approval |
| "Show the details" | Read-only detail; no approval |
| "Approve once the open question is resolved" | A condition remains; no present approval |

With several unresolved items, make each one clear and obtain explicit acceptance of
each, individually or through an unambiguous acknowledgement of all the listed items.
Do not require technical IDs, a hash or a formal approval phrase. Do not ask again when
the user has already given a complete, clear decision for the unchanged reviewed content.

Load the shared local identity profile as described in [commands.md](commands.md).
If missing, ask once for display name and declared roles, then explicitly set it up.
Reuse it across conversations without repeated identity prompts. A name in Git settings,
host login or an old audit is not a substitute for that profile. Profile roles are
informational, never enforced permissions; identity is locally declared, not verified.

Preserve the person's actual approval and acknowledgement words. If collected over
several turns, keep those actual utterances identifiable; do not manufacture a quotation
claiming that the user recited internal hashes or formal acknowledgements. Distinguish
an agent-written reason summary from quoted human evidence.

After successful approval, give a brief result and one separate decision:

> Business specification approved. The request remains in Business Refinement.
> Would you like me to mark it ready for Functional Analysis?

Wait for that separate explicit authorization. Even "approve and proceed" in the
initial message is followed by this separate post-approval decision. A clear "Proceed"
in response to the single advancement question authorizes that transition. Report
readiness, not completion of Functional Analysis. Drafting Analysis is a subsequent
operation when requested, not part of business approval or advancement.

## Errors and evidence

Explain what the result means for the user's work before discussing diagnostics:

| Situation | Example response |
|---|---|
| Reviewed content/context changed | "The specification changed since your review. I'll show the changes before asking for approval again." |
| Another writer holds the lock | "Another update is in progress. Your decision has not been recorded by this attempt." |
| Write outcome is uncertain | "I'm checking whether your decision was saved before retrying." |
| Approved baseline cannot be verified | "The approved copy could not be verified. Progress is blocked until it is restored." |

Do not claim success or failure before checking an uncertain write. Follow the existing
recovery rules and keep diagnostics available on request. Tool execution permission is
not Product Owner approval. A submitted native choice may carry an explicit decision;
an unsubmitted/preselected choice, timeout or absence of response cannot. The conversation
is procedural approval, not authenticated human authorization.

## Functional Analysis

Draft first from the verified approved business input, then summarize the result and
important gaps. Ask focused questions after a useful draft exists. Keep optional dates,
exclusions and deferrals faithful to the actual evidence; do not invent examples as
confirmed business behavior. For example: "The draft covers optional task due dates.
The rule for past dates is still deferred. Would you like to review the scenarios?"

Explain blocked behavior in business terms. A deferred business decision can be carried
forward but cannot be silently selected as an acceptance criterion. If a human wants a
new business decision, explain the need to revisit and reapprove business scope before
incorporating it. Routine wording refinements preserve existing evidence and history.

Keep hashes, input bindings, CLI operations and paths internal unless requested. Resume
from saved review without repeating answered questions. Positive feedback is not
Analysis approval. Apply the natural approval rules above to the Analysis document,
including every inherited issue, Analysis question/proposal and blocked or proposed
behavior. For example: "The scenarios cover the agreed scope. Past-date behavior remains
deferred and blocked. You can request refinements or approve with that uncertainty."

Record explicit refinement feedback before applying authorized edits. After explicit
approval, say: "Functional Analysis approved; the request remains in Analysis. Would
you like me to advance it and create the Engineering and QA workstreams?" Wait for a separate answer before
advancing. Readiness does not run Technical Design. If a revision or reopening made
the approval stale, explain that a fresh review and human decision are needed.

## Short commands

Follow [commands.md](commands.md) for `status`, `review`, `approve`, `changes`, `advance`
and `details`, plus track-aware `start`. Accept short native invocations and natural-language requests.
Resolve project, Epic and stage internally and ask only when ambiguous. Show concise
results; full artifacts, provenance and technical details remain available on request.
Discovery uses completion, not Business/Analysis approval. A command requesting an
approval context does not itself acknowledge unseen unresolved issues.

## Accountability and handoff

Use `inbox`, `pending assignments` and `assign` through [commands.md](commands.md).
Describe owner as accountable, assignee as responsible for the next activity, and role
as the expected responsibility rather than a permission. After advancement, offer the
retained owner one nomination question. If no person is known, report Awaiting Handoff
and retain ownership; do not start the next stage. Nomination and explicit assignment
confirmation are separate turns. Keep assignment distinct from document approval and
lifecycle advancement. Display request IDs/titles in inbox lists as requested, with
Assigned Work and Awaiting Handoff clearly separated.

## Engineering and QA conversations

After authorized Analysis advancement, describe the two ready workstreams and retained
accountability. For example:

> Functional Analysis is approved. Two workstreams are ready:
> Engineering — awaiting Engineering Lead.
> QA — awaiting QA Lead / Tester.
> Who would you like to assign first?

Ask one assignment decision at a time. No assignee means that track remains Awaiting
Handoff in its owner's inbox. Assigning one track does not transfer the other or start
work. A request to “start QA” authorizes its current activity, not Engineering work,
approval, assignment or lifecycle advancement. When an unqualified command has two
plausible tracks, ask only “Engineering or QA?” instead of choosing one silently.

Keep summaries track-specific. QA strategy and functional scenarios can be prepared
immediately from approved Analysis; do not ask the user to explain why no Design is
available. Later interface details can inform automation, never replace the functional
expectations. Engineering owns Design, its plan, code and unit/build checks. Its plan
review does not include independent QA scenario approval. QA obtains scenario approval
covering strategy+scenarios and later separate human automation approval. Keep each
approval and advancement distinct and preserve the person's actual words.

Use pinned domain expertise without copying its instructions into central workflow
prose or Epics. Native tools perform authorized work under declared paths; independent
tracks do not authorize automatic parallel AI execution. In the PoC, QA automation uses
reserved `qa/` paths so its source/revisions are separate from Engineering source.

At integrated verification, explain which Engineering outputs and QA reviews/evidence
are current and what is missing. “QA has not run yet” is a blocker, never success.
Actual checks and explicit QA completion must precede separate Engineering verification
advancement. A passing category label is not real UI evidence. Keep blocked behavior
and unanswered questions visible; acknowledgement does not invent a business rule.

When Engineering changes, explain whether automation or execution must be refreshed
without repeating unrelated functional scenario review. When approved Analysis changes,
show impact on both tracks and request explicit reconciliation rather than silently
carrying work forward. Keep a legacy combined-plan acceptance session unchanged unless
the human explicitly authorizes the supported adoption path. Its approved Design and
historical decisions remain intact; the unapproved combined Plan is not silently
approved, rewritten or treated as independent QA signoff.

Security findings need preserved evidence, explicit remediation and relevant renewed
reviews/checks. Final verification reports disclose remaining uncertainty and are not
release approval, deployment authorization or security certification.
