# Documentation audit and command coverage

[Documentation index](README.md)

**Second pass: 2026-10-31.** Editing baseline: `41256c5f443f4591b30dc42a05c6772049ec607c`,
clean main in `git@github.com:stjarna/ai-sdlc.git`, matching the supplied published baseline.
No unrelated edits were present. Runtime, skill instructions/adapters, domain/template
packages, tests, approved artifacts, the 448-file archive and the Littlelist repository
are outside the edit scope. Maintainers own this audit; domain owners review their contracts.

> **Latest implementation pass:** early-phase domain extraction extends the verified
> runtime-management foundation. See the final addendum for provenance, compatibility
> and actual test results; earlier scopes and results remain dated historical context.

## Complete docs inventory

Every file under docs/ was inspected, including the SVG. Audience, current/historical
status, overlap and action are recorded below. Contract examples can be historical
without being obsolete validators; current generation also resolves the pinned template.
Stable paths avoid breaking pinned resource links. No file was moved, removed or archived.

| Path under docs/ | Audience | Purpose | Authority/status | Duplication, gap or reference issue | Action |
|---|---|---|---|---|---|
| [README.md](README.md) | All readers | Navigation, audience tasks and maintenance ownership | Current | Root navigation overlaps; index provides depth | Create |
| [runtime-version-management.md](runtime-version-management.md) | Users / operators / maintainers | Default update/rollback, effective authority, explicit promotion, contexts and recovery | Current implementation for review | Owns runtime contracts; CLI inventory owns exact arguments | Create |
| [command-reference.md](command-reference.md) | Users / POs / analysts / engineers | Complete conversational vocabulary, selectors, gates and examples | Current | Replaces tutorial tables; routing mechanics stay in command-ux | Create |
| [cli-reference.md](cli-reference.md) | Integrators / maintainers | Parser-derived 50-operation coverage and required/optional arguments | Current technical | Links schemas/diagnostics rather than copying them | Create |
| [getting-started.md](getting-started.md) | First-time users | Install, adopt, clarify, decide and troubleshoot | Current | Removed long duplicate command table; keep anchor and worked example | Revise |
| [workflow.md](workflow.md) | All readers | Shared path, roles, separate track states and decision boundaries | Current | SVG overview retained; three focused state models added | Revise |
| [command-ux.md](command-ux.md) | Maintainers / advanced users | Routing, identity/profile and conversational contract | Current technical | Links command manual; retains unique profile/retry semantics | Revise |
| [ownership.md](ownership.md) | Owners / leads / maintainers | Accountability, pending handoffs, assignment schema and recovery | Current technical | Handoff diagram/example; no duplicate command catalog | Revise |
| [artifact-names.md](artifact-names.md) | Readers / maintainers | Artifact discovery, physical names, manifest compatibility and traceability | Current technical | Links workflow purposes and template authority | Revise |
| [installation-architecture.md](installation-architecture.md) | Adopters / engineering leads / maintainers | Locations, host discovery, selected domain guidance, templates and project boundaries | Current implementation explanation | Owns explanatory diagrams; installation contract retains exact commands/recovery | Create in clarification pass |
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

## Installation and domain-skill architecture clarification — 2026-10-31

Baseline: `80b6c2e7098210f1cb920c69b8a914e63fd27451`, clean working tree and verified
`git@github.com:stjarna/ai-sdlc.git` remote. This pass changes documentation only.

### Findings and changes

- Added installation-architecture.md to explain one generated user loader, exact
  external payload, explicitly retained interpreter, project selection and later records.
- Verified host discovery against current official OpenAI skills documentation and kept
  it separate from our loader's instructions and Python's verification behavior.
- Explained that the generated pre-operation check omits skill-root: it checks runtime
  and environment; operator verify with skill-root also checks registration bytes.
  This is a procedural agent instruction, not a native security hook.
- Documented current package paths and catalog pins: Architecture/Development/Testing
  1.3.0 and Security 1.2.0; current directories are unversioned by name while the catalog
  binds exact versions/digests. Prior versions remain retained, not silently upgraded.
- Distinguished package hashing/stage/dependency validation from the agent reading
  selected prose, and template structure from content expertise and semantic judgment.
- Clarified the recommended venv is created by setup, not install.py; custom roots are
  external destinations, not automatic host discovery or project-scoped installation.
- Explained multiple retained runtimes versus one selected runtime per registration,
  no automatic per-project dispatcher/upgrade, and Codex-only external registration.
- Added four diagrams: directory topology, Design invocation sequence, expertise/template
  responsibilities, and installation versus read-only adoption versus governed execution.
- Replaced the older overlapping installation boundary diagram with a link to this
  explanation, retaining its existing section anchor. All lifecycle/approval/handoff/
  synchronization diagrams and the master SVG remain unchanged.
- Updated root README, docs/README.md, getting-started.md, installation-and-adoption.md,
  command-reference.md, workflow.md and engineering.md with concise links/context.
  This audit is updated too: eight existing documents plus one new guide. AGENTS.md,
  agent instructions, adapters, catalogs, packages, templates, code and tests are unchanged.
  No documents/evidence were moved or deleted.

### Verification

- Targeted suites executed: installation **27 tests / 15.821 s**, domain skills
  **19 / 0.237 s**, templates **16 / 12.909 s**: **62 tests passed**, all exit 0.
  Tests use disposable fictional fixtures, not new real human approvals. The full
  433-test suite was not rerun for this documentation-only clarification; the previous
  pass's executed result remains above with its own context.
- Executed read-only skills/templates inspection: all four current package pins and
  eleven templates resolved. Checked actual installer parser defaults without invoking
  installation; verified current package paths and Architecture's Security dependency.
- Links: **28 Markdown files, 422 parsed references**, zero broken local targets/anchors.
  Current official OpenAI build-skills documentation was fetched for native Codex scope,
  invocation and progressive instruction loading; those host behaviors are kept separate
  from installer/loader behavior. No new live Codex/Claude discovery or model turn was run.
- Four new Mermaid diagrams parsed and rendered locally with Mermaid 11.12.0 in
  light/default and dark themes: **eight successful renders**. Inspected previews and
  made the seven-participant sequence compact enough for normal reading width. This is
  local compatibility validation, not a newly published GitHub rendering claim.
- Root README and affected setup/architecture/index pages rendered with Chromium at
  880 px content width without page overflow. Existing main SVG remained unchanged.
- **635 protected tracked files** outside the eight-document edit allowlist remain
  SHA-256-identical. All **seven existing lifecycle/approval/handoff/synchronization/
  traceability Mermaid blocks** outside the replaced installation diagram are identical.
- Read-only archive verification: **448 preserved files**, seven stored skill pins,
  51 referenced evidence bindings and both Engineering/QA Verified states passed.
  No archived tests were rerun or historical reports regenerated.
- Complete diff/new guide reviewed and `git diff --check` passed. HEAD/tag references
  are unchanged and the staging index is empty. Validation helpers/results remain
  ignored scratch files, without publishing local paths, fixtures or dependencies.

No installed runtime/profile, Littlelist source/records, immutable artifact, pinned
package/template or historical evidence was modified. No code/tests/agent instruction
files changed; no staging, commit or push was performed.

### Remaining architecture and portability questions

The loader's required verification is not technically enforced by Codex. There is no
per-project runtime selector/catalog policy, automatic registration replacement,
Claude installation path or new Claude runtime verification. Those require explicit
future design/host acceptance; custom directories alone do not implement them.
Python validates declared pins and governance records but cannot prove the model read
instructions or semantic correctness. Domain packages do not automatically appear in
native skills or launch agents. Existing local identity, sandbox, cross-clone and
advance/start routing limitations remain as documented; none was fixed here.

## Runtime management implementation addendum — 2026-10-31

This pass extends the preceding documentation-only task against HEAD
`80b6c2e7098210f1cb920c69b8a914e63fd27451`. Its prior uncommitted documentation was
preserved. Earlier scope statements and unsupported-feature lists above describe those
completed passes; the current runtime contract is [runtime management](runtime-version-management.md).

### Scope and architecture

- Reuse immutable installation manifests and domain/template catalogs. Ordinary install
  remains non-switching; prepare, explicit update/default rollback and inspected recovery
  use owned registration locks and durable switch intent. Old snapshots are retained.
- Separate the default from effective request/Analysis-cycle track selection. Explicit
  future-work binding/promotion appends a runtime sidecar, leaving existing metadata and
  artifact/approval formats unchanged. Actual installed writes enforce the selected
  executable and context receipt, with recoverable runtime/file provenance bookkeeping.
- Candidate read-only validators and contract projections assess compatibility; compatible
  independent Engineering/QA selections are checked at the existing evidence join.
- Preserve source-checkout legacy recovery's existing narrow reader. It must finish a
  partial Business publication before ordinary full-Epic validation can succeed.
- New runtime/CLI guide, updated installation diagrams, human instructions and complete
  CLI reference cover the implemented operations. Native command routing gains no new
  command vocabulary; version management also supports natural-language intentions.

### Verification evidence

- **All 457 tests passed** against the final frozen production code: 211 tests in
  554.858 seconds and 246 tests in 419.619 seconds, run as two isolated complete module
  groups (554.981 seconds wall time). Discovery confirmed all 457 were included, without
  duplicate/missing modules. The 24 new runtime tests are included. Production hashes
  were checked unchanged across the run. Intermediate interrupted runs and the initial
  legacy-recovery regression are not passing acceptance evidence; that regression was
  corrected and passed in the final run. The conventional reproduction command remains
  `.venv/bin/python -m unittest discover -s orchestrator/tests -v`.
- Independent preview installation/preflight and actual Codex CLI 0.165.0 skill discovery
  passed. No model turn/AI API was started. Application and Git hashes were unchanged
  before authorized fixture creation; creation added only idea.md, metadata.yaml and the
  runtime ledger. All installation/context fixtures were disposable and external.
- Python compilation and tracked/new-file whitespace checks passed. Parsed local link
  validation covered **29 Markdown files and 457 references**, with zero broken targets
  or anchors. Complete tracked/new-file diffs were reviewed; the staging index and Git
  HEAD/tag references remain unchanged. No real installed registration/profile, Littlelist
  source/records or presentation project was modified; no staging, commit or push occurred.
- CLI coverage: **57 SDLC operations** and **eight installation operations** had their
  actual help executed successfully and documented flags/coverage checked.
- Local Mermaid 11.12.0 validation: **nine diagrams, 18 successful light/dark renders**.
  Inspected the changed sequence and promotion, mixed-track and provenance diagrams.
  README and affected guides rendered at normal reading width without page overflow.
- Read-only archive verification retained **448 files**, seven stored skill pins and
  51 evidence bindings, with Engineering/QA Verified. Historical reports were not
  regenerated. **624 protected tracked files** outside the current change allowlist
  match the pre-task inventory; domain/template packages and archive bytes are unchanged.

### Remaining trust and acceptance boundaries

Procedural context receipts do not prove a model forgot earlier instructions or
authenticate human/publisher identity. Actual wrong-runtime writes are rejected; fresh
host conversation acceptance remains a manual step. Compatibility projections require
honest maintainer declarations and semantic review, not version-number ordering. Local
POSIX cooperating-writer locks/linked history are not distributed consensus or protection
against coordinated unrestricted edits. Unbound source tooling and old unrestricted
binaries are outside managed runtime-provenance guarantees. Historical missing attribution
stays unknown. Regular active-stage promotion is deferred; no automatic migration,
network updates, Git automation or Claude runtime acceptance is introduced.

## Early-phase domain extraction — 2026-10-31

Baseline: `d5009d8aae78be6bfefe5aac466a03f080599fbd`, including verified runtime
management. Discovery, Business Requirements and Functional Analysis now have separate
1.0.0 packages owned by their domain teams, alongside the unchanged four Engineering/QA
packages. Current and retained package bytes use the existing manifest/catalog contract.

### Responsibility and compatibility review

- Extract adaptive questioning/readiness judgment, business content quality and functional
  behavior/acceptance guidance. The shared coordinator retains source authority, record
  persistence, ownership, explicit human decisions, audit, approvals and separate advancement.
  Conversation policy retains concise presentation and gate semantics.
- Templates retain their exact versions/content digests. No human-readable document layout
  or approval manifest changes. Deterministic early writers record selected domain pins in
  explicitly versioned metadata/history envelopes; old entries and approved snapshots are
  not retrospectively assigned new guidance.
- `skills --stage ACTIVITY` adds read-only deterministic selection without changing the
  unqualified catalog result or adding a new conversational command. CLI 0.15.0 is separate
  from package 1.0.0, domain validation contract 1 and the existing template contracts.
- Runtime comparison permits additive reader/package support, while existing contract
  changes still block. Actual readers remain mandatory. Current selected and current-cycle
  track evidence runtimes are checked at verification; obsolete shared-stage writers need
  not parse newer downstream artifacts. No current track evidence check is omitted.
- A disposable real-process test preserves Business approval/baseline bytes under the
  committed four-package runtime, explicitly reconciles/promotes future Analysis, and
  records new Functional Analysis/domain/template/runtime provenance without upstream
  reapproval. It also rolls the default back to the older protocol-capable runtime,
  retaining the verified manager so the newer request remains resolvable. Decisions in
  this fixture are fictional, not actual user approval.
- The pre-template golden fixture now constructs legacy Discovery envelopes from the outset:
  stripping new provenance after intermediate revision hashes were computed was incorrect.
  Original expected review/baseline hashes remain unchanged and are checked by regression.

### Validation boundaries

The focused ten-test suite covers catalog/stage resolution, retained pins and corruption,
source-projection/content equivalence, mixed history, original-idea preservation, retries,
pin-drift cleanup, additive compatibility, relevant verification readers and actual forward
promotion. It compares representative persisted content and references, not deterministic
AI prose. Static skill checks validate all three new entrypoints. The full-suite result is
recorded in the completion note below.

Local installation smoke testing uses a labelled working-tree preview and disposable
external runtime/registration/application. Actual Codex discovery starts no model turn.
No real installed runtime/profile, Littlelist repository or historical evidence is updated.
Domain instructions still depend on agent execution and human semantic review; pins identify
selected guidance, not proof the model followed it. Older readers may reject new envelopes;
that incompatibility blocks writes instead of migrating evidence or bypassing gates.


### Completion evidence

- Complete suite exercised **467 distinct tests** in two module groups: 218 tests passed
  in 922.489s; the 249-test group had one outdated CLI assertion expecting four packages.
  Only that assertion was corrected to seven; the entire **seven-test CLI module passed**
  in 40.080s. Consolidated latest outcomes are **467 passing tests**, with **474 test
  executions**, retaining the initial failure and retry. The run's blanket file-hash guard
  detected the test-only edit; no production change was made during this final run.
- All ten added tests passed, including actual committed-A/new-B promotion and default
  rollback with the newer request retained. Historical golden review/baseline hashes
  passed unchanged after correcting legacy fixture construction, not expected constants.
- Static skill validation passed for all three new entrypoints. Compilation, all 57 SDLC
  and eight installer operation help checks, tracked/new-file whitespace and final diff
  checks passed. Parsed link validation covered 29 Markdown files/466 references before
  this completion note; no broken local targets/anchors were found.
- Thirteen Mermaid diagrams rendered in light/default and dark themes (26 renders).
  Reviewed the new lifecycle/domain map and normal-width documentation renders.
- Disposable installation smoke and actual Codex CLI discovery passed with the final
  implementation. No model turn was run. Read-only preservation verification passed for
  448 archived files, seven historical skill pins and 51 evidence bindings, with both
  tracks Verified. All pre-existing domain package and template bytes are unchanged.

No new live conversational acceptance is claimed. A focused human rehearsal is described
in domain-skills/README.md. Existing installed runtimes are not updated by this source
change: installation/default update and request promotion remain separate explicit actions.
