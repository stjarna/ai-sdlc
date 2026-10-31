# Getting started

[Documentation index](README.md)

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

For why these locations are separate and how Codex loads the domain packages, see
[installation architecture](installation-architecture.md). The venv above is explicitly
created by the setup instructions, not automatically by the installer. The installer
registers Codex only; the bundled Claude adapter is not a Claude installation.

The selected Python environment must remain available. Installation does not copy the
runtime into your application. There is no separate `init` command or checkpoint file.

An ordinary install never replaces an existing registration, including another folder
declaring `name: sdlc`.
An identical install can be verified/replayed. For a different installed revision, inspect
its loader and runtime first; use the explicit [update/rollback operations](runtime-version-management.md),
not registration deletion or ordinary install as a switch. Defaults and effective request
runtimes are distinct; promotion is a separate human decision. There is no automatic
upgrade or uninstaller.

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

The assistant also resolves the effective request/track runtime before work, loads its
instructions and uses a matching context receipt internally. After a runtime change,
start a fresh conversation when requested; changing a loader cannot clear cached model
instructions. Existing unpinned requests need explicit initial future-work binding,
without inventing which runtime produced their history.

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

See the [complete conversational command reference](command-reference.md) for all
commands, request/track selectors, effects and stage-specific examples. Use `$sdlc …`
in Codex; the Claude adapter uses `/sdlc …` with runtime acceptance still outside PoC.
For tool arguments, see the separate [CLI inventory](cli-reference.md).

## Worked example: first requirement

This is an illustrative exchange, not preserved human approval evidence.

| User action | Outcome / persisted change | Next human decision |
|---|---|---|
| “Create a requirement for exporting saved results as CSV.” | New Discovery metadata and original idea; no existing application code changes. | Supply identity setup if missing, then answer the consequential question. |
| “Only the currently filtered results; no scheduled exports.” | Sourced answer in append-only Discovery history; assumptions remain separate. | Continue clarification or ask for review. |
| “Stop asking and show the Discovery review.” | Derived summary only; state remains Discovery, no new approval. | Correct gaps or explicitly complete. |
| “Discovery is complete; authorize Business Refinement readiness.” | Completion/lifecycle event; ready_for_refinement, owner retained pending handoff. | Nominate/confirm a PO separately, or leave handoff pending. |

Unknowns can remain visible. There is no fixed question count, automatic completeness
score, or approval implied by stopping questions. Preparation of business.md is a later
explicit request, using the pinned scaffold and confirmed evidence.

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
