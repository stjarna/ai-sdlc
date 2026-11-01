# Documentation consistency audit

[Documentation index](README.md) · [Per-file inventory](documentation-inventory.md)

## Baseline and scope

This audit checks published implementation at
`bc6242b33a87aa02d7acd1b5063b1f4e9284f044` on `main`, against `origin/main`.
The checkout was clean and synchronized before editing. Origin is
`git@github.com:stjarna/ai-sdlc.git`. There were no uncommitted or unpublished
implementation increments to describe as pending features.

All 148 existing tracked Markdown documents (15,176 lines), both workflow vectors,
their generator/verifier, relevant parsers, catalogs, manifests and tests were inspected.
The [inventory](documentation-inventory.md) classifies each file and the two new audit
records. This is a documentation correction: no runtime behavior, consumed skill,
template package, immutable baseline or evidence is changed.

Recent published changes already included runtime management (`d5009d8`), early domain
packages (`68452ea`), placeholder contracts (`d02c418`), opt-in Git collaboration
(`370d47d`), neutral public framing (`eaf3216`), removal of the unversioned Idea scaffold
(`7f8dc9f`) and redesigned workflow vectors (`bc6242b`). The audit preserves these
implemented features instead of treating their earlier proposals as current gaps.

## Implementation-to-documentation matrix

Paths below are implementation authority, not additional execution instructions.
Detailed examples and prerequisites remain in the linked guides.

| Capability | Current behavior / boundary | Guide | Implementation and regression coverage |
|---|---|---|---|
| Fresh install | Complete pinned external snapshot; no runtime copied into application source | [Install](installation-and-adoption.md) | `install.py`; `test_installation` |
| Codex discovery | One thin user-scoped loader at `~/.agents/skills/sdlc`; restart/rediscover host when needed | [Locations](installation-architecture.md) | `install.py`; loader fixture checks |
| Snapshot verification | Git revision, resources, Python dependencies, domain and template digests checked | [Runtime](runtime-version-management.md) | `install.py`, `runtime_management.py`; installation/runtime tests |
| Update / rollback | Explicit prepared snapshot and default selection; retains prior runtimes | [Runtime](runtime-version-management.md) | `runtime_management.py`; `test_runtime_management` |
| Existing requests | Effective request/track bindings persist independently of default | [Runtime](runtime-version-management.md) | `runtime_selection.py`; `test_runtime_selection` |
| Future-phase promotion | Explicit compatible future scope; preserves history and compares contracts/pins | [Runtime](runtime-version-management.md) | `runtime_selection.py`; mixed-runtime tests |
| Mixed versions | Reader/contract compatibility and current joined evidence checked, not assumed from version numbers | [Domains](../orchestrator/domain-skills/README.md) | `runtime_selection.py`, `domain_skills.py`; runtime-selection tests |
| Adoption | Read-only preflight reports namespaces, source boundaries and existing instructions | [Start](getting-started.md) | `adoption.py`; `test_installation` |
| Seven domains | Bundled local instruction packages; only the coordinating loader is native | [Domains](../orchestrator/domain-skills/README.md) | `domain_skills.py`; `test_domain_skills`, `test_early_domain_skills` |
| Discovery | Adaptive questions; original idea retained; linked append-only evidence and explicit completion | [Discovery](interactive-discovery.md) | `sdlc.py`, `discovery_history.py`; early-domain and command tests |
| Business | Draft/refine from recorded evidence; approval distinct from advancement | [Business](business-refinement.md), [gate](business-approval.md) | `business_refinement.py`, `business_approval.py`; command/runtime fixtures |
| Functional Analysis | Pinned specialist, approved Business source and separate human gate | [Analysis](functional-analysis.md), [gate](analysis-approval.md) | `functional_analysis.py`, `analysis_approval.py`; early-domain/runtime fixtures |
| Engineering / QA | Independently owned and governed tracks, no automatic parallel agents | [Work tracks](work-tracks.md) | `engineering.py`, `qa_track.py`, `work_tracks.py`; runtime-selection tests |
| Templates | Eleven deterministic catalog selections, exact manifest/content digests | [Templates](../orchestrator/templates/README.md) | `artifact_templates.py`; `test_templates`, `test_template_resources` |
| Placeholder handling | Resolved structural slots, required sections and exact envelope provenance | [Slots](template-placeholder-audit.md) | `artifact_templates.py`; `test_placeholder_contracts` |
| Historical formats | Legacy artifacts remain readable without invented provenance or migration | [Artifacts](artifact-names.md) | Template/resource/runtime/demo regression fixtures |
| Canonical names | Current documents use cataloged physical filenames; legacy immutable `content.md` stays unchanged | [Artifacts](artifact-names.md) | `artifact_names.py`, approval publishers; template/demo tests |
| Git activation | Local-only default; explicit application `.sdlc-git.yaml` enables bridge | [Git](git-native-collaboration.md) | `git_collaboration.py`; `test_git_collaboration` |
| Commit / push | Configured events, validated path scope, commit and non-force push; pending publication is not a handoff | [Git](git-native-collaboration.md) | Bridge `run`, `publish`, `recover`; real Git fixture tests |
| Shared authority | Configured remote/integration branch; feature branches/worktrees do not become authoritative | [Git](git-native-collaboration.md) | Freshness/session checks; Git regression fixtures |
| Synchronization | Fetch and safe fast-forward at explicit boundaries, no reset/stash/implicit conflict resolution | [Git](git-native-collaboration.md) | Bridge `sync`; dirty/diverged/rejected-push tests |
| Source identity | Existing source/package/baseline SHA-256 contracts retained alongside native Git object references | [Git](git-native-collaboration.md) | Source scanner, Git baseline checks; runtime/Git tests |
| Reopening | Supported upstream Discovery reopen invalidates current downstream authority, preserves history; no invented direct Analysis rollback | [Git scenario](git-native-collaboration.md), [tracks](work-tracks.md) | Discovery reopening and track reconciliation; mixed-runtime fixtures |
| Integration | Advisory expected-authority and semantic checks; server-side branch protections remain external | [Git](git-native-collaboration.md) | Bridge `integration-check`; Git tests |
| Recovery | External idempotent publication journal; rejected/uncertain push blocks dependent work | [Git](git-native-collaboration.md) | Bridge recovery/retry/abandon tests |
| Human decisions | Review, approval, advancement, start and assignment remain distinct; declared identities unauthenticated | [Commands](command-reference.md), [identity](command-ux.md) | `command_ux.py`, `local_identity.py`, gates; `test_command_ux` |
| Uncertainty | Acknowledgement does not resolve questions or authorize observable prototype limitations | [Governance](engineering.md#governance-corrections-contract-01) | Existing limitation/semantic contracts unchanged |
| Verification | Current Engineering outputs and current QA evidence join; Verified is not Released | [Workflow](workflow.md), [tracks](work-tracks.md) | Current gate bindings, demo archive checks |
| Diagrams | Shared path, horizontal tracks and evidence prerequisite; compact gates disclose grouped decisions | [Diagrams](workflow-diagram.md) | Runtime-aware generator and browser geometry verifier |

### Current domain catalog

[Catalog](../orchestrator/domain-skills/catalog.yaml) and manifests, not the orchestrator
CLI version, select these packages. Versions have independent ownership and meaning.

| Domain | Selected version | Responsibility |
|---|---|---|
| Discovery | 1.1.0 | Conversational clarification and evidence discipline |
| Business Requirements | 1.0.0 | Business refinement and traceable scope |
| Functional Analysis | 1.0.0 | Functional models and acceptance coverage |
| Architecture | 1.3.0 | Technical Design, observable limitations and decisions |
| Development | 1.3.0 | Plan, controlled implementation and source-bound review |
| Testing | 1.3.0 | Independent scenarios, automation and actual verification |
| Security | 1.2.0 | Security assessment and remediation evidence |

The CLI is `0.17.0`; it is independent of catalog schema `0.1`, modern domain
manifest schema `0.2`, domain validation contract `sdlc-domain/1` and artifact-specific
template `/1` contracts. No additional native Codex registrations,
external AI API or remote package registry is implied. Claude's thin adapter remains
available; Claude runtime acceptance is outside this verified PoC scope.

### Current template catalog

All selections use [the versioned catalog](../orchestrator/templates/catalog.yaml).
New records carry exact ID/version/digest and compatible validation contract. Existing
validators remain authority for structural/governance checks; skills supply semantic
judgment. Layout provenance alone does not prove business correctness.

| Artifact | Selected version |
|---|---|
| `idea.md` | 1.1.0 |
| `business.md` | 1.0.0 |
| `specification.md` | 1.0.0 |
| `technical-design.md` | 1.0.0 |
| `implementation-plan.md` | 1.0.0 |
| `test-strategy.md` | 1.0.0 |
| `test-scenarios.md` | 1.0.0 |
| `test-automation.md` | 1.0.0 |
| `code-review.md` | 1.0.0 |
| `security-review.md` | 1.0.0 |
| `verification-report.md` | 1.0.0 |

Idea 1.0.0 remains published; 1.1.0 is current. The redundant root-level template
was already removed. Project-generated `requirements/REQ-…/idea.md` remains required
and supported. There is no legacy root-file fallback, hardcoded version directory,
retrospective template assignment or digest recalculation in this refresh.

## Corrections made

- README now explains seven implemented domains, independent template pins and opt-in
  Git collaboration without copying internal schemas or duplicating the command table.
- Installation, runtime and artifact guides distinguish local-only defaults and runtime
  administration from configured application Git publication/fetching. Statements that
  no installation, commit or push capability exists were narrowed to their real scope.
- Conversational and advanced references separate ten routed verbs and `new` shorthand
  from 57 core parser operations, nine Git actions and eight installer/admin operations.
  No new conversational verb or implicit permission is introduced.
- Git guidance includes a concrete old-Analysis/new-Analysis Engineering/QA scenario,
  expected-authority checks, explicit reopening and reconciliation. A clean merge does
  not make old QA evidence current or authorize agent execution.
- Early stage guides use current subject titles. Original increment contracts, dated
  test results and design decisions remain historical, with navigation to current scope.
- The domain overview separates CLI, skill and validation-contract versions. Published
  instruction packages and template layouts are unchanged.
- The documentation index points to current findings/inventory and labels earlier audit
  records as history. Both existing vectors and all useful Mermaid diagrams are retained.

## Verification

Executed for this audit, rather than inferred from previous acceptance:

- Relevant existing regression modules: **169 tests passed** in **336.479 seconds**.
  Modules: `test_command_ux`, `test_installation`, `test_runtime_management`,
  `test_runtime_selection`, `test_templates`, `test_template_resources`,
  `test_placeholder_contracts`, `test_domain_skills`, `test_early_domain_skills`,
  `test_git_collaboration`, `test_demo_assets`. This is the focused regression set,
  not a claim that the entire repository suite was rerun.
- **75 successful help executions**: all 57 core operations, eight installer/admin
  operations, nine Git actions and adoption preflight. Core reference sections and
  argument names/choices were compared against actual parser definitions.
- Both SVGs match the committed generator and runtime stage/artifact checks. Actual
  Chrome geometry checks found no issues: 14 stage cards each, 12 compact decision
  checkpoints and 19 expanded individual gates. Native and reduced-width previews
  preserve the committed presentation geometry.
- All **22 Mermaid blocks parsed and rendered in default and dark themes** (44 renders).
  Existing state/sequence diagrams were not replaced or recolored for this audit.
- All 827 links across 150 Markdown files, including local heading anchors, were checked; the only retained broken links
  are the eight immutable historical-wrapper exceptions below. Current navigation and
  current package links resolve. Representative guides were rendered locally in Chrome;
  this is not a claim of remote GitHub UI acceptance on every viewport/theme.
- Five unique external documentation/example URLs returned HTTP 200: two Claude Code
  pages, the example application repository and two linked host documentation pages.
  A successful HTTP request is availability evidence, not a behavioral host guarantee.
- SHA-256 comparison against all 677 starting tracked files confirms only intended editable
  Markdown changed. Published packages, catalogs, templates, runtime/tests, both vectors
  and preserved demonstration evidence remain unchanged; archive manifest verification
  is also part of `test_demo_assets` (448 preserved files).

Reproduction commands (run from a source checkout with the documented Python dependencies):

```bash
PYTHONPATH=orchestrator/tests .venv/bin/python -B -m unittest -v \
  test_command_ux test_installation test_runtime_management test_runtime_selection \
  test_templates test_template_resources test_placeholder_contracts test_domain_skills \
  test_early_domain_skills test_git_collaboration test_demo_assets
python3 docs/assets/generate_workflow.py --check
python3 docs/assets/verify_workflow.py
git diff --check
```

The parser/link/browser audit outputs are disposable local validation, not new historical
SDLC execution evidence. No application test or approval was regenerated.

## Remaining exceptions and implementation findings

### Historical wrapper links

Eight retained `SKILL.md` wrappers link to `../../skill/SKILL.md` using their original
package-root layout. In today's nested `versions/` directory those links do not resolve:
Architecture 1.0.0/1.1.0/1.2.0, Security 1.0.0/1.1.0 and Testing 1.0.0/1.1.0/1.2.0.
Their exact bytes and digests are preserved. Current catalog loading and all current
package resources pass verification. The domain guide explains this browsing limitation;
read the original matching runtime for its original shared-instruction layout.

### Development-start routing

`command_ux.py` still routes an `advance` intention at `ready_for_development` toward
`development-start`. The shared conversational policy and command reference explicitly
require a separate start instruction and a successful start result before edits. This
is a pre-existing implementation inconsistency, not an authorized exception to that
policy. It needs a focused code correction and regression test in a separate task;
this documentation-only audit does not change the router or weaken start controls.

### Public presentation and historical exposure

The example application link remains. The earlier approved public-neutrality cleanup
removed a demonstration video URL whose path included organization-specific framing.
Following explicit authorization, the original video was downloaded unchanged and
published at the neutral repository path
[`docs/assets/ai-sdlc-orchestrator.mp4`](assets/ai-sdlc-orchestrator.mp4).
The README and documentation index now link to the
[browser player](https://stjarna.github.io/ai-sdlc/demo.html), with separate MP4 download
links. Repository file-viewer links do not provide inline playback; raw GitHub URLs
serve the file as `application/octet-stream`.

The minimal player source is [`docs/demo.html`](demo.html). GitHub Pages publishes
`/docs` from `main`, with `.nojekyll` preserving static files without Jekyll processing.
The page uses native video controls, no autoplay, external scripts or tracking. The
published MP4 is served as `video/mp4` and supports byte-range requests. Real Chrome
checks passed for playback, pause, seeking, volume, fullscreen and a 390 px mobile
layout. A download through the live page matched the original 31,318,239 bytes and
SHA-256 `1de10b9a4da41496f3a053524d0df80f7ea5559c7d83f034d9d650b2adf835b9`.
These checks verify browser media behavior, not human auditory acceptance or physical
mobile-device coverage. This changes storage and discoverability, not the recorded
presentation content or historical SDLC evidence.

Read-only object search across accessible Git refs found 46 matching text blobs: eight
current provenance records and 38 historical-only versions. For example, the pre-cleanup
commit `370d47d8fbc09df68a7f6189588c73df683a82ef` retains earlier framing in `README.md`,
`AGENTS.md`, `docs/specification.md` and `docs/decisions/0001-repository-and-poc-scope.md`.
Historical Git commits remain accessible and retain earlier wording and removed links.
The current archived acceptance evidence also contains original machine-specific
workspace paths, including in recorded browser traces. These are preserved provenance,
not current installation instructions; no history, trace or approval is rewritten.
There are no new recruitment-specific descriptions in editable documentation.

### PoC boundaries

Local declared identity is not authentication/RBAC. Discovery completeness and semantic
conformance require AI judgment and human decisions, not deterministic proof. Git branch
protection/integration serialization is external; bridge recovery does not automatically
compose a partially persisted core-operation journal. Parallel tracks are independent
work, not automatic parallel-agent execution. Existing source fingerprints remain
conservative: keep evolving presentation captures outside governed source. Verified
Engineering/QA does not implement release, deployment or production readiness.
