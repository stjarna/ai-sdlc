# Documentation audit and refresh

**Reviewed:** 2026-10-31. Scope: human-facing documentation only in
[stjarna/ai-sdlc](https://github.com/stjarna/ai-sdlc). The separate Littlelist repository,
source presentation projects, executable code, consumed instruction/template packages,
approved records and historical evidence are outside the edit scope.

## Inventory and authority

The audit used the CLI parser/help and routing code, the shared skill/adapters and
conversation policy, installation/preflight code, ownership/work-track contracts,
domain/template catalogs, and preservation/test evidence. A planning statement or a
presentation caption alone was not treated as an implemented feature.

| Classification | Current finding | Authority / evidence |
|---|---|---|
| Implemented and demonstrated | Local external runtime installation, Codex discovery, read-only adoption, request creation and Discovery through verified Engineering/QA. | [Installer](../orchestrator/scripts/install.py), [shared skill](../orchestrator/skill/SKILL.md), [work tracks](work-tracks.md), isolated installation smoke and existing acceptance evidence. |
| Implemented, deterministic regression protected | Revision-bound approval, immutable baseline/integrity checks, local locking, retries/recovery, ownership, template validation and canonical filenames. | [CLI reference](../orchestrator/scripts/README.md), [tests](../orchestrator/tests/README.md), [artifact storage](artifact-names.md), [template catalog](../orchestrator/templates/catalog.yaml). |
| Implemented, not fully host-validated | Thin Claude Code adapter; cross-host/native IDE behavior depends on the host/version/permissions. | [.claude adapter](../.claude/skills/sdlc/SKILL.md); availability is distinct from runtime acceptance. Codex app-server discovery is not a visual IDE interaction test. |
| Procedural / semantic | Human attribution is a local declaration; Discovery readiness and semantic conformance depend on agent/human judgment. | [Conversation policy](../orchestrator/skill/conversation.md), [identity contract](command-ux.md), [governance](engineering.md#governance-corrections-contract-01). |
| Planned / incomplete | Story/Release execution, automatic Git/PR publication and cross-role sync, enterprise connectors/identity, distributed coordination and production operations. | Current parser has no Story/Release operations; [decision register](decisions/architecture-decisions.md) retains the target design. |
| Outdated / conflicting | Root README led with increment history; ownership and command guides said Technical Design was unavailable; specification tables mixed initial scope/target architecture with current execution. | Corrected current-facing prose; historical decisions and detailed contracts retained with current-status navigation. |
| Missing beginner context | Separate source/runtime/application locations; shell versus agent instructions; meanings of review/approve/advance/start/assign; real versus illustrative examples. | New [getting-started guide](getting-started.md), [workflow guide](workflow.md) and rewritten [README](../README.md). |

## Changelog

- Rewrote the README around purpose, practical value, workflow, setup, commands,
  artifacts, domain skills, demonstration, limitations and documentation navigation.
- Added a progressive setup/user guide with the actual installer, verification and
  read-only preflight arguments. It uses generic application paths and natural-language
  identity/request setup instead of hand-edited YAML or revision flags.
- Added a workflow guide separating shared stages, Engineering, QA, evidence dependencies,
  ownership and revision decisions. Only implemented states are presented as executable.
- Added one editable SVG overview in `docs/assets/`, adapted from the approved workflow's
  stage order, connectors, palette and icons for README readability. Current required-role
  names replace presentation role shorthand; conceptual future skill/integration panels,
  presentation title/navigation and production footers are omitted. The SVG records its
  reference source digest without a personal filesystem path. Its dashed QA connection
  is an evidence prerequisite at Engineering Verification, not a backward transition.
- Updated AGENTS.md with README orientation and actual verification commands; replaced
  the stale “first Codex task” instruction with reusable safeguards. Archive preservation,
  no implicit approvals, human responsibility and no unauthorized Git operations remain.
- Corrected stale status/command descriptions in ownership and command documentation;
  linked the human skill README to the beginner path; clarified historical test counts.
- Added current-implementation notes to the specification/register instead of rewriting
  accepted historical decisions or pretending target Story/Release models were implemented.
- Kept Littlelist and the older in-repository acceptance distinct. No video copied into Git.

### Files changed

Rewritten/updated: `README.md`, `AGENTS.md`, `docs/command-ux.md`,
`docs/ownership.md`, `docs/installation-and-adoption.md`, `docs/specification.md`,
`docs/decisions/architecture-decisions.md`, `orchestrator/skill/README.md` and
`orchestrator/tests/README.md`.

Added: `docs/getting-started.md`, `docs/workflow.md`, `docs/documentation-audit.md`
and `docs/assets/workflow-overview.svg`.

## Validation

The exact current results are recorded below after execution; no conversational or
production acceptance is inferred from automated fixtures.

- Git remote confirmed as `git@github.com:stjarna/ai-sdlc.git`; initial working tree clean.
- CLI help inspected for installation, verification, preflight and lifecycle operations.
  Runtime `skills` inspection needs an explicit project; `templates` is also inspectable
  without one. Four actual domain pins and all 11 template entries resolved successfully.
- The documented installation/verification/preflight behavior was executed using the
  existing isolated smoke, a committed runtime base and temporary path overrides.
  Installation and preflight passed, `baseline_ready` was true, and actual Codex CLI
  **0.165.0** `skills/list` discovered one enabled user-scoped `sdlc` loader. The fixture's
  source/instructions/Git data remained unchanged before normal `new` added only two
  Discovery files. No real user loader/profile changed, no model turn or new human
  approval occurred, and temporary fixtures were removed. Clone/default-home commands
  were syntax/source checked rather than run against the operator's existing setup.
- Read-only archived-demo verification passed: **448 preserved files**, both tracks
  Verified, **7 retained skill pins** and **51 referenced evidence files** validated.
  No archived application tests/evidence were regenerated.
- README rendered locally with Markdown-it and Chromium at an **880 px content width**.
  Inspected the opening, diagram and full document; no page overflow, missing image or
  SVG text clipped outside the canvas. Four tables and the heading structure rendered.
  This approximates GitHub Markdown; it is not a screenshot of an already published README.
- Local Markdown/anchor/image links and public HTTP links were checked; final counts and
  regression-suite result are recorded in the completion block below.

### Completion results

- **Full regression suite:** `python -m unittest discover -s orchestrator/tests -v`
  executed in the project virtual environment: **433 tests, 676.688 seconds, OK**.
  Fixture commits/decisions were isolated test construction, not repository commits
  or human acceptance. No production source/Git mutation was performed.
- **Links:** **24 Markdown files, 189 parsed link/image references**, zero missing
  local targets or anchors. **7 distinct external HTTP URLs returned 200**, including
  both GitHub repositories, the published MP4 (`video/mp4`), and existing host-doc links.
- **Diff/integrity:** `git diff --check` passed; all executable scripts, domain/template
  package bytes and archived-demo files match the pre-edit snapshot. Git HEAD/tags and
  the empty staging index remain unchanged. Only documentation and one SVG are pending.
- **Visuals:** the 1280×800 SVG was inspected at 880 px width inside the rendered README;
  current human roles, separate tracks, decision gates and dashed QA prerequisite are
  legible. No new screenshot gallery or embedded MP4 was added.

Raw test/help/smoke/link/render output was retained only in ignored local scratch space,
not published with machine paths, synthetic profiles or dependencies. The smoke's temporary
external fixture/runtime/home were removed after inspection. No test was claimed passed
unless executed.

## Remaining gaps

1. **No license file:** the public source repository has no LICENSE/LICENCE file.
   A maintainer must choose its reuse terms; this refresh does not invent a license
   or advertise an established open-source license.
2. **Routing inconsistency:** `command_ux.route("advance", "ready_for_development")`
   exposes `development-start`, including the Engineering track projection. The shared
   conversation policy requires a separate explicit start. The user guide documents
   `start engineering`; the inconsistency needs a focused implementation decision,
   not a silent behavioral change in documentation work.
3. **Historical design sections:** the specification/ADR preserve Story/Release models,
   Docker-first planning, initial skill-count sketches and earlier increment boundaries.
   Current-status notices and guides distinguish them from the current executable scope.
   They have not been translated/recast as a new approved architecture.
4. **Host acceptance:** Claude runtime, visual IDE interactions in every current host
   version, native Windows and enterprise environments remain unverified. The new smoke
   establishes local Codex backend discovery, not universal portability.
5. **Governance trust boundary:** procedural identities, informational roles and local
   file protections do not authenticate the decision maker or sandbox an unrestricted
   coding agent. Human/semantic review and host infrastructure remain necessary.
6. **Adoption constraints:** fixed `requirements/` / `qa/` namespaces and conservative
   source fingerprints can conflict with existing projects. Presentation files and
   ignored outputs may stale approval; no blanket exclusions or automatic relocations
   were added.
7. **Distribution:** no automatic registration replacement, package upgrade/uninstaller,
   enterprise registry or release automation. An installed runtime is an execution bundle,
   not the complete contributor checkout; examples/development-test links should be read
   in the source repository.
8. **Independent review:** independent QA input authority/work tracks do not guarantee
   different reviewers or isolated AI execution. The real demonstration used multiple roles;
   semantic completeness and exhaustive security are not established by passing checks.

No implementation defects were fixed in this documentation-only refresh. Preserved
baselines, audit records, domain/template pins and archived evidence remain authoritative.
