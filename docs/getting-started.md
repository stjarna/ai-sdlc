# Getting started

[Project overview](../README.md) · [Workflow](workflow.md) · [Installation contract](installation-and-adoption.md)

Use this guide to adopt the skill in **your existing application**, not to generate a
new product or edit the orchestrator's demonstration archive. The current local setup
supports POSIX filesystem/process semantics. macOS with Codex is the demonstrated host;
Windows and Claude runtime behavior are not acceptance-tested substitutes.

## 1. Prepare the application

Identify its Git repository root, inspect existing work and retain the initial commit
ID. Review existing project instructions and run its own baseline tests. The installer
will not initialize Git, make commits, overwrite instructions or install application
packages for you. Do not discard uncommitted work to satisfy a preflight warning.

The PoC reserves `requirements/` for request records and `qa/` for managed QA automation.
If your application already uses these names for something else, preflight may block
adoption. It reports the conflict; it cannot safely relocate those directories for you.

## 2. Install a pinned runtime

Use the [terminal commands in the README](../README.md#quick-start). They install:

| Location | What lives there |
|---|---|
| Separate orchestrator checkout | Reviewed source and the selected Git revision. |
| `~/.local/share/ai-sdlc/venv/` | Permanent Python environment with the pinned PyYAML dependency. |
| `~/.local/share/ai-sdlc/runtimes/<revision-prefix>-<digest-prefix>/` | Exact runtime, shared skill, domain packages, templates and supporting documentation. |
| `~/.agents/skills/sdlc/` | Thin user-scoped Codex loader pointing to that runtime. |
| Your application's `requirements/` | Request-specific artifacts, approvals and evidence, after creation. |

The selected Python environment must remain available. Installation does not copy the
runtime into your application. There is no separate `init` command or checkpoint file.

An existing registration is never replaced, even if another folder declares `name: sdlc`.
An identical install can be verified/replayed. For a different installed revision, inspect
its loader and recorded runtime first; deliberate registration retirement/replacement is
an operator task. There is no automatic overwrite, upgrade or uninstaller. See the
[installation details](installation-and-adoption.md) before changing a registration.

## 3. Verify installation

The install result is JSON. Copy its `runtime` and `snapshot_digest` values into these
variables; do not substitute an artifact hash or a domain-skill version:

```bash
SDLC_RUNTIME=/absolute/runtime/path/from/install
SDLC_DIGEST=exact_snapshot_digest_from_install

"$SDLC_PYTHON" -B "$SDLC_RUNTIME/orchestrator/scripts/install.py" verify \
  --runtime "$SDLC_RUNTIME" --expected-digest "$SDLC_DIGEST" \
  --skill-root "$HOME/.agents/skills"
```

This checks runtime files, environment, pins and registration. `ok: true` is a structural
installation result, not proof that a host has discovered the skill.

Open your **application** in Codex CLI or the IDE integration. Inspect `/skills` or type
`$sdlc status` and confirm the installed user loader is selected. Restart/reload the host
if a new registration is not visible. The tested backend discovery is not a guarantee
that every IDE version, permission setting or disabled-skill configuration behaves identically.

## 4. Run adoption preflight

**Terminal command**, using the variables from setup:

```bash
"$SDLC_PYTHON" -B "$SDLC_RUNTIME/orchestrator/scripts/adoption.py" \
  --project "$SDLC_PROJECT" --runtime "$SDLC_RUNTIME" \
  --skill-root "$HOME/.agents/skills"
```

Or ask the skill to run the read-only adoption preflight and explain the result.

Look for `ready: true` and `baseline_ready: true`. Review warnings as well as errors.
The checks cover Git, initial commit and working tree; directory conflicts; source
symlinks; build/test output hazards; project instructions; competing registrations;
and runtime compatibility. `ready` does not mean tests passed or work was approved.
`baseline_ready` additionally requires a clean working tree.

Ignored files are **not automatically excluded** from source fingerprints. Freeze
existing presentation assets before a source-bound Plan; put new presentation captures
outside the application repository. Store governed execution evidence through the
reviewed workflow. Do not add broad ignore/exclusion rules to bypass stale approvals.

## 5. Create and clarify a request

**Inside Codex**, not in a shell:

```text
$sdlc new
Help users export saved search results as CSV.
```

`new` is conversational shorthand handled by the skill, backed by the actual deterministic
`new` operation. It is not a shell executable or a new host command parser.

The assistant needs your explicitly declared display name and roles once to set up a
local profile outside Git. It never derives these from Git configuration or a host login.
The profile is reused across conversations, contains no credentials and is not verified
identity or enforced RBAC. Ask the assistant to edit it when your declarations change.

Creation writes a request directory with `metadata.yaml` and the original `idea.md`.
Conversational records are stored separately in `discovery.yaml`. The assistant reads
saved answers, asks one consequential question at a time, and distinguishes statements,
assumptions and unknown/deferred questions. Not every possible field needs an answer.

You can say **“Stop asking questions and show the Discovery review.”** This requests a
summary, not completion. When satisfied, explicitly confirm Discovery is complete and
authorize Business Refinement readiness. The AI's judgment that there is enough context
is advisory; human completion is recorded separately. Open issues do not become invented rules.

Resume with **“Continue REQ-0001”**. The ID is stable even if its directory is renamed.
There is no need to maintain a separate conversational checkpoint.

## 6. Review, approve, advance and start

These four actions are different:

1. **Review:** inspect content and unresolved issues; read-only.
2. **Approve:** explicitly accept the presented exact revision and acknowledge required
   open items. Missing acknowledgements need a focused follow-up. “Looks good” is insufficient.
3. **Advance:** separately authorize the eligible lifecycle transition. The CLI rejects
   stale or incomplete authority/evidence. An approval is not an advancement instruction.
4. **Start:** request the next available activity. Reaching readiness does not start it.

For Business and Analysis preparation, a natural request such as **“Prepare the business
specification from the confirmed Discovery”** or **“Draft the Functional Analysis from
the approved Business baseline”** makes the intended activity explicit. Use track-specific
`start` during Engineering/QA. Review the resulting artifact before approving it.

Discovery completion is distinct from Business approval. QA has one approval for
strategy/scenarios together and a later automation approval. Security review/finalization
use their actual review/evidence/advancement gates, not an invented `approve` operation.

After Analysis advancement, the owner remains accountable while Engineering and QA await
assignment. Declining to name a recipient leaves a visible pending handoff. Assigning
someone requires a separate confirmation and does not approve artifacts, advance stages,
notify that person or start work.

## Command reference

Codex uses `$sdlc …`; the unverified Claude adapter uses `/sdlc …`. These examples are
**conversational text**. There is no promise of identical host argument parsing.

All request actions need an explicit application context and an unambiguous active
request; a title or ID can select it. Track actions also need Engineering or QA context.
The profile is required for routine attributed decisions and inbox views. The assistant
manages revision hashes, operation IDs, current stage and low-level flags internally.

| Example | Prerequisite / when to use | Result and decision boundary |
|---|---|---|
| `$sdlc new` + description | Adoption checked, declared requester supplied; no existing request required. | Creates a new Discovery record; does not approve or advance. |
| `$sdlc status` | Active request, or a fresh application to see that none exists. | Read-only state/owners/next action; missing context does not create a request. |
| `$sdlc review` | Current request; add `engineering` or `qa` when ambiguous. | Read-only summary, uncertainty and readiness; reports absent drafts honestly. |
| `$sdlc details` | Current request; optional track. | Full exact-file links, history and evidence; no mutation. |
| `$sdlc start engineering` | Design/Plan readiness, approved Development readiness, or current review/verification activity as supported. | Starts only the requested activity after checking prerequisites; no approval/advancement. Development edits require a successful deterministic start. |
| `$sdlc start qa` | Current QA stage and its required inputs/approvals. | Drafts strategy/scenarios or automation, or executes approved checks at readiness; package/browser setup requires its own authorization. |
| `$sdlc approve qa` | Exact current artifacts reviewed; required uncertainty acknowledged. | Approves strategy/scenarios together or automation at its gate; lifecycle unchanged. |
| `$sdlc approve engineering` | Reviewed Design, Engineering Plan or code revision; current source where required. | Records that gate's approval only. Observable prototype limitations need separate explicit consent; acknowledgement is not consent. |
| `$sdlc changes engineering` + feedback | Current artifact or eligible pre-development Plan; clarify unspecified feedback first. | Records actual feedback and authorized refinement. Plan feedback before Development starts can return to planning; fresh approval is required. Business scope changes need upstream reopening. |
| `$sdlc advance` | Explicit Discovery completion, or current Business/Analysis approval. | Records the separately authorized transition. Add a track downstream. |
| `$sdlc advance qa` | Current QA approval, or current passing checks for completion. | Advances that track / explicitly completes QA verification. Does not advance Engineering. |
| `$sdlc advance engineering` | Current stage's approvals and evidence. | Advances only that track; joined verification needs current QA completion. Finalization marks Engineering Verified, not Released. |
| `$sdlc inbox` | Application context and local profile; no active request needed. | Read-only assigned work and owned pending handoffs. |
| `$sdlc pending assignments` | Application context; no active request needed. | Read-only project view of responsibilities awaiting assignment. |
| `$sdlc assign qa REQ-0001` | Request/track and recipient resolved; explicit confirmation naming person/role. | Transfers that responsibility with audit history. No approval, advancement or work start. |

`status`, `start`, `review`, `approve`, `changes`, `advance`, `details`, `inbox`,
`pending assignments` and `assign` are the shared routing vocabulary. Creation (`new`)
and requests to reopen/read/validate a request are handled by skill guidance and existing
CLI operations; they are not extra `command-context` enum values. `open` and `validate`
are deterministic CLI operations, not a reason to ask users for technical arguments.
Stories, `move-story`, release commands and automatic Git publishing are not implemented.

The low-level routing helper still offers `development-start` for `advance` at
`ready_for_development`; this does not override the conversational policy requiring
an explicit start instruction. Use `start engineering` at that point. This existing
routing inconsistency is recorded in the [documentation audit](documentation-audit.md#remaining-gaps);
it has not been changed in this documentation refresh.

## If something blocks progress

- **No skill visible:** inspect the selected path, competing registrations and host
  enablement; restart/reload. Do not copy only the repository's thin adapter into a
  personal skill folder—it needs its complete package. Use the installer.
- **Namespace/output warning:** inspect it before adoption; no automatic restructuring.
- **Stale approval or source fingerprint:** review what changed. Before Development
  starts, explicit Plan feedback supports [safe replanning](engineering.md#pre-development-plan-recovery).
  Later work needs the applicable remediation/reconciliation flow. Never edit metadata
  or skip a stale check to force progress.
- **Missing dependency or browser:** obtain the required setup authorization and record
  actual execution. A named check or an unexecuted test is not a passing result.

For exact operations, diagnostics and recovery, use the [CLI contract](../orchestrator/scripts/README.md).
