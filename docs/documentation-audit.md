# Documentation audit and command coverage

[Documentation index](README.md)

**Second pass: 2026-10-31.** Editing baseline: `41256c5f443f4591b30dc42a05c6772049ec607c`,
clean main in `git@github.com:stjarna/ai-sdlc.git`, matching the supplied published baseline.
No unrelated edits were present. Runtime, skill instructions/adapters, domain/template
packages, tests, approved artifacts, the 448-file archive and the Littlelist repository
are outside the edit scope. Maintainers own this audit; domain owners review their contracts.

## Complete docs inventory

Every file under docs/ was inspected, including the SVG. Audience, current/historical
status, overlap and action are recorded below. Contract examples can be historical
without being obsolete validators; current generation also resolves the pinned template.
Stable paths avoid breaking pinned resource links. No file was moved, removed or archived.

| Path under docs/ | Audience | Purpose | Authority/status | Duplication, gap or reference issue | Action |
|---|---|---|---|---|---|
| [README.md](README.md) | All readers | Navigation, audience tasks and maintenance ownership | Current | Root navigation overlaps; index provides depth | Create |
| [command-reference.md](command-reference.md) | Users / POs / analysts / engineers | Complete conversational vocabulary, selectors, gates and examples | Current | Replaces tutorial tables; routing mechanics stay in command-ux | Create |
| [cli-reference.md](cli-reference.md) | Integrators / maintainers | Parser-derived 50-operation coverage and required/optional arguments | Current technical | Links schemas/diagnostics rather than copying them | Create |
| [getting-started.md](getting-started.md) | First-time users | Install, adopt, clarify, decide and troubleshoot | Current | Removed long duplicate command table; keep anchor and worked example | Revise |
| [workflow.md](workflow.md) | All readers | Shared path, roles, separate track states and decision boundaries | Current | SVG overview retained; three focused state models added | Revise |
| [command-ux.md](command-ux.md) | Maintainers / advanced users | Routing, identity/profile and conversational contract | Current technical | Links command manual; retains unique profile/retry semantics | Revise |
| [ownership.md](ownership.md) | Owners / leads / maintainers | Accountability, pending handoffs, assignment schema and recovery | Current technical | Handoff diagram/example; no duplicate command catalog | Revise |
| [artifact-names.md](artifact-names.md) | Readers / maintainers | Artifact discovery, physical names, manifest compatibility and traceability | Current technical | Links workflow purposes and template authority | Revise |
| [installation-and-adoption.md](installation-and-adoption.md) | Operators / integrators | External pinning, registration, read-only preflight and recovery | Current technical | Complements beginner guide; adds boundary diagram | Revise |
| [existing-project-demo.md](existing-project-demo.md) | Presenters / adopters | Reproducible authentic before/after capture procedure | Current procedure | Distinct from preserved old acceptance and Littlelist outcome | Keep; add navigation |
| [interactive-discovery.md](interactive-discovery.md) | Maintainers / evaluators | Typed history, provenance, retries and original acceptance protocol | Current data contract; historical increment scope | Original no-install/no-later-phase exclusions labelled, current installation linked | Revise orientation |
| [business-refinement.md](business-refinement.md) | Analysts / maintainers | Business source/document schema, reconciliation and journal recovery | Current data contract; historical increment scope | Approval and template authority linked; exact schema retained | Revise orientation |
| [business-approval.md](business-approval.md) | POs / maintainers | Business gate, immutable baseline, revision semantics and recovery | Current contract with dated examples | Add decision sequence and worked example; actor/profile detail stays in identity contract | Revise |
| [functional-analysis.md](functional-analysis.md) | Business analysts / maintainers | FR/UC/BR/AC/AQ/AP schema and approved-input drafting | Current data contract; historical increment scope | Historical exclusions labelled; no invention of separate Analysis domain package | Revise orientation |
| [analysis-approval.md](analysis-approval.md) | Reviewers / maintainers | Shared gate, Analysis input binding and separate advancement | Current contract with dated increment examples | Links shared approval example; retains unique baseline schema and acknowledgements | Keep; add navigation |
| [engineering.md](engineering.md) | Maintainers / Engineering leads | Legacy sequential contract plus current Plan recovery and governance addenda | Mixed legacy/current | Prominent status; original combined Plan/QA and old package versions kept; current fork linked | Revise classification |
| [work-tracks.md](work-tracks.md) | Engineering / QA leads / maintainers | Current independent tracks, synchronization, schemas and reconciliation | Current technical plus legacy adoption protocol | Evidence-join diagram and worked example; unique policies retained | Revise |
| [agent-ux-evaluation.md](agent-ux-evaluation.md) | Host evaluators | Original cross-host conversational evaluation protocol | Historical protocol; not current host status matrix | Outdated unimplemented/not-run claims explicitly scoped; current guides linked | Retain and label |
| [demo-finalization.md](demo-finalization.md) | Presenters / auditors | Dated preservation/rehearsal results and original proposed commits | Historical preparation evidence narrative | Old pending-commit and suite-count context labelled; evidence links retained | Retain and label |
| [specification.md](specification.md) | Architecture reviewers | Original accepted decisions, target design and later addenda | Mixed historical/target/current addenda | Story/Release/Docker/old catalogs not executable matrix; current authority linked | Retain and label |
| [decisions/architecture-decisions.md](decisions/architecture-decisions.md) | Architecture reviewers | Append-only rationale and increment scope decisions | Historical decisions plus later accepted extensions | Do not replace with current command manual | Retain; add navigation |
| [decisions/0001-repository-and-poc-scope.md](decisions/0001-repository-and-poc-scope.md) | Architecture reviewers | Original public repository/demo/scope rationale | Historical accepted ADR | Release/Docker/old-demo intent is not current feature status | Retain; add navigation |
| [assets/workflow-overview.svg](assets/workflow-overview.svg) | All readers | Primary full-system visual overview | Current overview asset | Smaller Mermaid diagrams explain distinct behaviors, do not replace it | Keep byte-identical |
| [documentation-audit.md](documentation-audit.md) | Maintainers / reviewers | Complete per-file inventory, coverage, verification and known gaps | Current audit; prior pass results labelled | Prior work remains in Git history; this pass records only executed results | Revise |

## Supporting-source audit

| Source | Inspection and action |
|---|---|
| Root README.md | Retain welcoming entry, short Quick Start, unchanged SVG and compact command cheat sheet; link complete manuals. |
| Root AGENTS.md | Add current documentation/CLI navigation only; retain agent safeguards. |
| Shared SKILL.md, commands.md, conversation.md | Inspect actual intent, consent, source and track rules; unchanged agent execution instructions. |
| Codex / Claude adapters | Inspect native invocation distinctions and resource links; unchanged. No claim of new runtime acceptance. |
| scripts/README.md | Retain schema/diagnostic contract, add complete parser inventory links, result guidance and current routing terminology. |
| sdlc.py, command_ux.py, Engineering/QA/ownership/approval code | Authority for verbs, selectors, argparse flags, lifecycle, writes and failure behavior; no executable edits. |
| install.py / adoption.py | Authority for bootstrap flags, non-overwriting registration and read-only preflight; unchanged. |
| Domain catalog / package and template manifests / validators | Confirm four domain pins, eleven template types, independent versions and canonical names; unchanged consumed bytes. |
| Relevant command/track/approval/Plan recovery/template/install tests | Regression evidence for implemented contracts, not live human authorization. |
| Preserved acceptance / demo manifest | Check 448 original files, stored pins, actual evidence bindings and both Verified states; never regenerate tests or evidence. |

## Coverage, information architecture and consolidation

- Ten conversational routing values from command_ux.COMMANDS, plus skill-guided new
  shorthand, have individual entries covering context, selection, reads/writes, records,
  human actions, approval/lifecycle/ownership effects, blockers and illustrative examples.
- The actual argparse tree yields **50 sdlc.py operations**. Every operation has one
  source-to-documentation coverage row and a complete required/optional argument entry
  in [the CLI inventory](cli-reference.md). Installer install/verify and standalone
  adoption preflight are separately covered, not hidden inside that count.
- CLI syntax is separate from conversational input; parser acceptance is separate from
  semantic gate eligibility. Current shared routing and explicit start policy are both
  documented, including their known inconsistency below.
- A task-oriented index separates introductory use, architecture/governance, advanced
  schemas/recovery and historical intent. Technical contracts retain unique information.
- Removed duplicate detailed command table from Getting started and shortened the root
  cheat sheet. Both link the single human manual; command-ux retains profile/routing
  mechanics. No historical rationale, evidence or acceptance criteria were deleted.
- Early evaluation and preparation documents are explicitly historical. The specification
  remains mixed-status; original decisions and future Story/Release diagrams are not
  silently relabelled implemented. Engineering is mixed legacy/current; its original
  combined QA plan and format0.1 illustration are scoped, current extensions linked.

## New diagrams

The original SVG remains byte-identical and is the primary workflow overview. Eight
focused Mermaid blocks were added, using labels, shapes and prose rather than custom colors:

| Location | Distinct behavior |
|---|---|
| workflow.md | Three stateDiagram-v2 blocks: shared path, Engineering projection, independent QA state. |
| business-approval.md | Exact-revision preparation/review/approval, rejection, unchanged lifecycle and separate advancement. |
| ownership.md | Pending handoff, retained owner, nomination and separate confirmed transfer, no automatic start. |
| work-tracks.md | Independent Analysis inputs, automation interfaces and current QA evidence prerequisite for Engineering verification. |
| artifact-names.md | Revisions → human decision → immutable baseline → current source/checks → scoped report; Git separate. |
| installation-and-adoption.md | External complete runtime, user loader, existing app and project-local management artifacts. |

Illustrative worked examples cover first request, Business refinement/approval, independent
tracks, delayed handoff and stale Plan/failed-check recovery. They are not fabricated
transcripts or new approvals. All stage changes still require their existing human gates.

## Verification for this pass

Actual executed checks for this pass:

- **Full regression suite:** `.venv/bin/python -m unittest discover -s orchestrator/tests -v`:
  **433 tests passed in 687.539 seconds**, exit 0. No new live conversational acceptance,
  application tests or production approval were inferred from these automated fixtures.
- **Command coverage:** all ten routing values plus creation shorthand have manual entries.
  The captured argparse tree contains 50 operations; all 50 have coverage rows, argument
  entries and successfully executed `--help` checks. Required/optional flags were compared
  against the parser, and semantic kind/lifecycle restrictions inspected in source/tests.
- **Links:** 27 Markdown documents, 389 parsed link/image references; zero missing local
  targets or anchors. No files moved or deleted, so inbound paths remain stable. Existing
  external reference URLs were retained; no new external host-documentation validation
  or visual host runtime test is claimed by this pass.
- **Mermaid:** all eight new blocks parsed and rendered using local Mermaid 11.12.0 in
  default/light and dark themes: **16 successful renders**. Inspected rendered diagrams;
  shortened sequence labels and moved crowded recovery paths to explanatory prose.
  This is local compatibility checking, not an already-published GitHub rendering test.
- **Markdown:** rendered root README, documentation index, command manual, CLI inventory
  and audit in Chromium at 880 px content width. No page overflow; long tables scroll
  where necessary. Existing SVG remained unchanged and rendered successfully.
- **Historical integrity:** read-only demo verification passed for **448 preserved files**,
  seven historical domain skill pins, 51 referenced evidence files and both Verified
  states. No archived checks or historical evidence were regenerated.
- **Scope/integrity:** **616 protected tracked files** outside the documentation allowlist
  are SHA-256-identical to the initial snapshot, including executable code, skills,
  templates, tests and demonstration assets. The master SVG is also unchanged. Final
  diff and new guides reviewed; `git diff --check` passed. HEAD remains the supplied
  baseline; staging is empty. No commit/push, runtime update or Littlelist modification.

Scratch outputs are ignored local files, not new authoritative evidence. Earlier-pass
results remain in Git history; no old suite count or smoke result is presented as a
fresh run. The docs tree now contains 23 Markdown files and the retained SVG, all
represented in the inventory above. In total this pass updates 23 existing documentation
files and adds three guides (26 files); no document was removed or relocated.

## Remaining gaps

1. `command_ux.route("advance", "ready_for_development")` suggests development-start,
   including track projection, while conversation policy requires explicit start. The
   user/manual and CLI inventory preserve this known defect; no routing fix was made.
2. Shared Business/Analysis start resolves read context; explicit draft-generation intent
   invokes the existing writer. Do not claim a universal deterministic start mutation.
3. Shared argparse kind choices exceed some operation-specific policies. The CLI inventory
   states valid kinds separately; parser acceptance does not authorize an unsupported action.
4. Historical specification/ADR and legacy contracts retain original language and scope;
   status banners and current navigation prevent treating target commands as implemented.
5. Local profile names/roles and claimed review independence are procedural, unauthenticated
   and bypassable with unrestricted tools. Semantic conformance/completeness remain human/AI
   responsibilities, not deterministic semantic guarantees.
6. Claude runtime, visual IDE parity, Windows and distributed coordination remain unverified.
   Static adapter/link checks and automated fixtures do not establish conversational acceptance.
7. No LICENSE/LICENCE defines reuse terms. Maintainers must decide; no license was invented.
8. Installed runtimes omit contributor tests/examples; source-repository docs are the complete
   reference. New documentation is not installed into an existing pinned runtime automatically.
9. Future Git automation, ticketing, messaging, IAM/RBAC, CI/CD, Story and Release execution
   remain future concepts. Verified is limited to stated evidence/scope, not production readiness.

No runtime defect, domain package, authoritative artifact or historical hash was changed.
