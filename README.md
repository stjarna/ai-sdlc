# AI SDLC Orchestrator

**Agent-native, human-governed software delivery.**

AI SDLC Orchestrator is an experimental skill for guiding a change in an existing
software project from its first business idea to verified implementation. It works
inside a coding agent: the assistant helps clarify requirements, prepare designs,
write code and tests, and collect evidence. People supply intent, resolve important
ambiguities, review outputs and authorize progression.

Software delivery context is often distributed across tickets, documents, source
code, test systems and conversations. This project brings the requirements,
artifacts and decisions for a change into a shared, versionable project context.
It coordinates work alongside Git and existing tools; it does not replace a ticketing
system, continuous integration and delivery (CI/CD), or specialist judgment.

This experimental proof of concept (PoC) explores agent-native, human-governed
software delivery, with Codex as its tested host. It is not a production SDLC platform.

[Get started](#quick-start)
· [User commands](#commands-inside-codex)
· [Technical documentation](#documentation)

## What it provides

- **A guided conversation:** turn an idea into a business specification and testable
  requirements; resume from saved records rather than chat memory.
- **Human decisions at clear gates:** review, approve an exact revision, then authorize
  advancement separately. Request changes without losing earlier decisions.
- **Ownership and handoffs:** keep an accountable owner while the next role is
  unassigned; see pending work and explicitly transfer responsibility.
- **Specialist assistance:** pinned Architecture, Development, Testing and Security
  guidance, with versioned document templates.
- **Two governed work tracks:** Engineering owns implementation; quality assurance
  (QA) derives its expectations from the approved Functional Analysis independently
  of the Technical Design. Verification checks that the current outputs agree.
- **Traceable evidence:** preserve approved baselines, revision history, actual check
  results and final reports alongside the application.

Opt-in [Git-native collaboration](docs/git-native-collaboration.md) publishes existing
SDLC events with explicit path staging, remote revision checks and recoverable receipts.
Feature work stays separate from shared lifecycle authority; protected proposals remain
pending until their exact reviewed integration is verified. Legacy local use is unchanged.

## How the workflow works

[![Implemented SDLC: Discovery, Business Refinement and Functional Analysis feed separate Engineering and QA tracks. Current QA evidence is required at Engineering verification before Security Review and Final Verification. Approval and advancement are separate human decisions.](docs/assets/workflow-overview.svg)](docs/assets/workflow-detailed.svg)

[Expanded workflow with artifact names](docs/assets/workflow-detailed.svg) · [Diagram source and visual verification](docs/workflow-diagram.md)

AI prepares work; humans review and decide. **Review, approval, advancement and work
initiation are separate human decisions.** Assignment transfers responsibility without
approving content or advancing work. Discovery
uses explicit completion rather than artifact approval.

After Functional Analysis is approved and separately advanced, Engineering and QA can
progress independently. This is a division of responsibility, not automatic parallel
agent execution. Current approved QA results and explicit QA completion are prerequisites
for Engineering to proceed through verification. Both tracks finish at **Verified**;
that is not release approval, deployment or security certification.

See the [workflow guide](docs/workflow.md) for the roles, artifacts and exact gates.

## Quick Start

Use an **existing application Git repository** with an initial commit. The example
below uses `~/projects/my-app`; substitute your application's path. The orchestrator
stays in a separate checkout and installs its runtime outside the application.

Prerequisites: macOS or another local POSIX environment, Git, Python **3.10+** with
`venv`/`pip`, and Codex with permission to read the runtime and work in your application.
macOS/Codex is the demonstrated environment; other environments need validation.
Your application's build/test dependencies remain its own responsibility.

**In a terminal — obtain a revision and prepare its Python environment:**

```bash
git clone https://github.com/stjarna/ai-sdlc.git "$HOME/ai-sdlc"
cd "$HOME/ai-sdlc"
SDLC_SOURCE="$PWD"
SDLC_PROJECT="$HOME/projects/my-app"
SDLC_REVISION="$(git rev-parse HEAD)"
SDLC_PYTHON="$HOME/.local/share/ai-sdlc/venv/bin/python"

python3 -m venv "$HOME/.local/share/ai-sdlc/venv"
"$SDLC_PYTHON" -m pip install -r orchestrator/requirements.txt
```

`SDLC_REVISION` pins this checkout's exact commit; record it and review the code before
installation. There is no moving “latest” runtime or automatic upgrade.

**In the same terminal — install the pinned runtime and Codex loader:**

```bash
"$SDLC_PYTHON" -B "$SDLC_SOURCE/orchestrator/scripts/install.py" install \
  --source "$SDLC_SOURCE" --revision "$SDLC_REVISION" \
  --project "$SDLC_PROJECT" --python "$SDLC_PYTHON"
```

The JSON result includes `runtime` and `snapshot_digest`; keep both for verification.
Installation validates dependencies, skill/template pins and resource links. It does
not edit application source, tests, Git history or project instructions. An existing
SDLC registration is never overwritten; if a conflict is reported, inspect it before
choosing an installation. The [step-by-step setup guide](docs/getting-started.md) covers
verification, preflight, directory locations and troubleshooting.

**Open the application in Codex CLI or the Codex IDE integration.** Confirm that the
installed user skill appears in `/skills` (restart/reload if necessary). In the
conversation—not the terminal—enter:

```text
$sdlc status
```

In a fresh application, “no request yet” is an expected result, not an installation
failure. Ask the assistant to run the read-only adoption preflight and show any
blockers before creating your first request. A clean working tree is needed for a
reproducible initial source baseline; the tool never cleans it for you.

Then describe a change:

```text
$sdlc new
Help users export their saved search results as a CSV file.
```

The assistant asks for a local display name and declared roles if no profile exists,
then reuses that profile in later conversations. No credentials are needed. It creates
a stable request ID under `requirements/`, preserves the original idea and asks one
consequential Discovery question at a time. You do not supply YAML, hashes or operation IDs.

To resume later, ask: **“Continue Discovery for REQ-0001.”** For the next decision,
use `$sdlc review`. Nothing is approved or advanced merely by creating or opening a request.

## Where does the skill install?

Codex discovers one user-scoped `$sdlc` loader in `~/.agents/skills/sdlc/`. It points
to an external pinned runtime under `~/.local/share/ai-sdlc/runtimes/`. Discovery, Business Requirements, Functional Analysis, Architecture,
Development, Testing and Security packages live **inside that runtime**; installation
does not register these seven packages as separate native skills. The host agent reads the relevant
guidance as the workflow requires. Existing requests retain their effective runtime;
[explicit updates, rollback and future-stage promotion](docs/runtime-version-management.md)
keep default selection separate from governed execution. Your application keeps its own code/tests and later
stores governed request artifacts under `requirements/`, with QA automation under `qa/`.

[Installation architecture: locations, discovery and domain-skill loading](docs/installation-architecture.md)
explains what gets installed, why user scope is used, and how this differs from adoption
and authorized Development. The installer registers Codex only, not Claude Code.

## Commands inside Codex

These are **conversational instructions**, not shell commands. The assistant resolves
the project, request and stage and invokes deterministic operations internally.
Select a track when needed: `engineering` or `qa`. Missing or ambiguous context prompts
a clarification instead of a guess.

| Example | Purpose |
|---|---|
| `$sdlc new` + idea | Create and clarify a request. |
| `$sdlc status` / `$sdlc details` | See progress or exact records. |
| `$sdlc review` / `$sdlc approve` | Review, then explicitly approve the current eligible revision. |
| `$sdlc advance` | Separately authorize eligible progression. |
| `$sdlc start engineering` / `$sdlc start qa` | Start only the selected eligible activity. |

The [complete command reference](docs/command-reference.md) covers all ten routed verbs,
creation shorthand, changes, assignment, inboxes and stage/track variants. These are
conversational skill invocations; [Python CLI operations](docs/cli-reference.md) are a
separate tool-facing interface. Approval, advancement, assignment and start remain distinct.

## A change from idea to verified behavior

**Illustrative interaction**, not a transcript of historical approvals:

1. **Describe the need:** “Add optional due dates to our existing task app.” The
   assistant asks consequential questions, such as whether past dates are allowed.
2. **Review Discovery:** inspect confirmed decisions, assumptions, scope and open
   questions. Explicitly confirm completion and authorize Business Refinement readiness.
3. **Refine and approve:** the Product Owner reviews `business.md`, requests changes
   if needed, then approves the exact revision. A separate advancement authorizes
   Functional Analysis readiness; ask the assistant to prepare that specification.
4. **Review the analysis:** approve the reviewed requirements and acceptance criteria,
   then separately authorize advancement. Engineering and QA are now ready. Nominate
   and confirm their owners; assignment does not start either track.
5. **Guide Engineering and QA:** start each activity explicitly. Review Design and
   Plan before coding, code before verification, and QA scenarios and automation
   through their own approvals. Revisions and failed checks can require renewed review.
6. **Verify:** run the approved checks, inspect actual results, explicitly complete
   QA and separately advance Engineering through the remaining gates. Review the
   final report and authorize finalization.

An unresolved question stays unresolved. A prototype-only restriction on observable
behavior needs its own explicit authorization within Design approval; acknowledging
uncertainty does not authorize an invented business rule.

## What is saved in your project?

A request is an Epic-level change with a stable ID such as `REQ-0001`; the ID survives
renaming its directory. The application retains its own source layout.

| Document | Purpose |
|---|---|
| `idea.md` | The original business idea. |
| `discovery.yaml` | Append-only statements, questions, assumptions and human decisions. |
| `business.md` | Business intent, scope, value and unresolved items. |
| `specification.md` | Functional requirements, acceptance criteria and source links. |
| `technical-design.md` | Architecture, interfaces, security considerations and authorized limitations. |
| `implementation-plan.md` | Engineering tasks, allowed paths and unit/build checks. |
| `test-strategy.md`, `test-scenarios.md` | QA's Analysis-derived expectations and cases. |
| `test-automation.md` | Approved QA automation and executable check definitions. |
| `code-review.md`, `security-review.md` | Source-bound review evidence and findings. |
| `verification-report.md` | Actual results, scope, exclusions, blocked/unresolved behavior and limitations. |

Documents and management records live under `requirements/REQ-0001-…/`. QA automation
uses the reserved application-level `qa/` directory. Engineering/QA documents are stored
in revision/baseline bundles; use `$sdlc details` for their exact current file links.
They are not all flat files in the request root. Metadata and histories bind the
human-readable documents to revisions, decisions and check evidence.

An **approved baseline** freezes exact document bytes and supporting inputs. Changing
those inputs can make an approval or result stale; new work needs the applicable
reconciliation and review. Old snapshots and decisions are retained.

Existing approval bundles retain their immutable identity. Without opt-in collaboration,
the local CLI does not stage, commit or push. With [Git collaboration](docs/git-native-collaboration.md),
publication also records an immutable repository/commit/path/event reference and verifies
shared authority; a local commit or feature push alone is not published approval. Also keep changing presentation captures
outside the application tree: ignored files can still affect source fingerprints.

Read [artifact storage](docs/artifact-names.md), [approval rules](docs/business-approval.md)
and [verification contracts](docs/work-tracks.md#integrated-verification-and-source-binding)
for the technical details.

## The orchestrator and domain skills

The **Orchestrator Skill** coordinates conversation, lifecycle, ownership, artifacts
and decisions. The **domain skills** supply specialist practices used by the coding
agent. Python scripts persist and validate records; they do not perform AI reasoning
or generate business meaning.

The current [pinned catalog](orchestrator/domain-skills/catalog.yaml) contains:

| Skill | Version | Maintainer | Responsibility |
|---|---|---|---|
| Discovery | 1.1.0 | Discovery Team | Adaptive clarification, evidence and review. |
| Business Requirements | 1.0.0 | Product / Business Requirements Team | Sourced business specification. |
| Functional Analysis | 1.0.0 | Business Analysis Team | Testable behavior and acceptance criteria. |
| Architecture | 1.3.0 | Architecture Team | Technical Design, with Security input. |
| Development | 1.3.0 | Engineering Enablement | Planning, implementation and code review. |
| Testing | 1.3.0 | QA / Quality Engineering | Strategy, scenarios, automation and verification. |
| Security | 1.2.0 | Application Security | Security-by-design and scoped implementation review. |

Organizations can maintain their own versioned specialist guidance. The bundled
packages demonstrate this model locally; there is no enterprise skill registry.
[Domain-team responsibilities and provenance](orchestrator/domain-skills/README.md)
cover all seven packages. The coordinator retains every human gate. [Templates](orchestrator/templates/README.md)
define document structure, while skills provide domain judgment and validators enforce
machine-checkable contracts. Existing approved artifacts retain their original pins.

Agent Skills are also distinct from **Model Context Protocol (MCP)** connectors:
skills supply instructions and expertise; connectors expose external tools and data.
Enterprise connectors are future work here.

## Demonstration and evidence

The practical scenario extends an existing create/read/update/delete (CRUD)
application with optional task due dates.
[Littlelist has its own repository](https://github.com/stjarna/ai-sdlc-demo):
its existing code and tests were preserved during external skill adoption, followed by
requirement clarification, human decisions, Engineering/QA work and actual verification.

There is also an **older, separate in-repository acceptance demonstrator** under
[examples/todo-app](examples/todo-app/README.md). It preserves its original limitations,
failures, remediation, approvals and evidence. Do not apply Littlelist's requirements
to that older example or rewrite either history to make them agree.

**Verified means verified for the stated scope.** It does not mean released,
production-certified, independently audited or reviewed by different people in every role.

## Current status and limits

The PoC implements Discovery through Functional Analysis, approval/ownership management,
external Codex installation, pinned skills/templates and independently governed
Engineering/QA tracks through Verified. Deterministic scripts validate structure,
revisions, integrity, local concurrency and recorded evidence. AI and human review
remain responsible for semantic quality and identifying missing requirements.

Not implemented: Story decomposition, release planning/execution, automatic PR creation/merge
or cross-role synchronization, ticketing/messaging connectors, CI/CD adapters, enterprise
authentication or role-based access control (RBAC), general distributed coordination,
and operational monitoring. Local roles are declarations, not enforced access grants.
Opt-in Git publication uses remote fast-forward checks across clones; local locks alone
protect only one checkout. Named checks run locally; they do
not establish complete semantic coverage or exhaustive security testing.

Claude Code runtime acceptance, native Windows support and broader production hardening
remain open. See the [workflow limitations](docs/workflow.md#boundaries) and
[architecture decisions](docs/decisions/architecture-decisions.md).

## Documentation

**[Start here](docs/getting-started.md) → [Understand the workflow](docs/workflow.md) →
[Explore commands](docs/command-reference.md) → [Advanced CLI/contracts](docs/cli-reference.md).**

The [documentation index](docs/README.md) groups user guides, architecture/governance,
technical contracts and historical decisions. Focused diagrams explain
[approval versus advancement](docs/business-approval.md#approval-and-advancement-sequence),
[handoffs](docs/ownership.md#handoff-without-automatic-work) and
[Engineering/QA synchronization](docs/work-tracks.md#evidence-dependency-between-tracks).

## Contributing

Keep changes small, preserve historical evidence and run the relevant checks. For local
regression tests, from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r orchestrator/requirements.txt
.venv/bin/python -m unittest discover -s orchestrator/tests -v
```

Read [AGENTS.md](AGENTS.md) and the authoritative contracts before changing behavior.
Do not include credentials, proprietary company information or unreviewed external
skills. The demonstration application and its preserved evidence are not scratch space.
