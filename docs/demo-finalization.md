# Final PoC preparation and proposed commits

Preparation date: 2026-10-28. No staging, commits, pushes or new SDLC stages are authorized
by this preparation. The real Task Due Date Management request already completed explicit
human finalization: both Engineering and QA are Verified.

## Permanent demonstration

[examples/todo-app/README.md](../examples/todo-app/README.md) is the runbook.
The preserved project is `examples/todo-app/project`; supporting original evidence and
inputs live alongside it. [EVIDENCE.md](../examples/todo-app/EVIDENCE.md) links actual
requirements, approvals, reviews, defects, test results and the final report.

The preservation manifest covers **448 original files**, including **257 project files**.
Each was compared byte-for-byte and by SHA-256 against the original acceptance session.
The copy excludes installed packages, caches, build outputs, temporary source generators
and implementation-repository-only working-tree inventories. Historical CLI responses may
contain declared identity/path fields; no active identity configuration or credential
store is copied. Pinned active/historical domain instructions remain in the orchestrator.

All copied approvals, baseline IDs, manifests and audit prefixes remain original. No
search/replace, migration, regeneration, approval fabrication or metadata normalization
was performed. Git attributes preserve exact archive and instruction bytes across
newline-converting checkouts. Original immutable artifacts use their original format0.1
`content.md` files; the later advancement/final report retain their real format0.2
canonical files. Verification checks seven stored domain pins and 51 referenced test
report/screenshot/trace hashes, and both current Verified states.

Original `/tmp` and `/private/tmp` session/fixture paths remain historical provenance
inside immutable records. They are not runtime prerequisites: current CLI links resolve
from the permanent copy, and the manifest maps old evidence roots to local files. The
preserved QA source still has its approved macOS Chrome executable path; changing it
would change its approval-bound fingerprint, so it was preserved and documented rather
than silently patched.

## Executed presentation rehearsals

A separate ignored `.run/project` copy was prepared through `demo.py`; the accepted archive
was checked before/after and stayed unchanged. These fresh rehearsals do not extend or
replace historical SDLC evidence, approvals, completion or Security Review.

| Actual command via `demo.py` | Observed result |
|---|---|
| `verify` |448 preservation hashes, seven stored instruction pins, 51 referenced evidence files and both Verified states checked |
| `setup` |Locked npm ci installed two QA packages; scripts/browser downloads disabled; source/lockfile unchanged |
| `unit` |41 passed, zero failed |
| `build` |Passed; seven JS/MJS syntax checks, imports/assets/package scripts |
| `integration` |Six real HTTP tests passed |
| `ui` |Eight actual Chrome scenarios passed |
| `start` |Application launched on an ephemeral loopback port; page returned HTTP200 and task API returned two undated fixtures |

Observed runtime: Python3.13.7, Node25.9.0, npm11.12.1, installed Chrome156.0.8078.74;
Playwright/playwright-core1.64.1 were installed from the existing exact integrity lockfile.
The specific observed port is not configuration; the next run prints its own port.

Fresh setup/check stdout, stderr and exit records plus 30 fresh test evidence files are
retained in [preparation-evidence](../examples/todo-app/preparation-evidence/), explicitly
separate from the unchanged accepted history. Their own manifest records file hashes.
The app process is only a rehearsal; no UI action or test grants further SDLC approval.
The complete orchestrator suite result is recorded below from its actual completed run.

## Pending implementation and safe commit boundaries

HEAD `243d801` already contains Shared Analysis Approval Infrastructure, six-command UX
with local identity, and Ownership/Handoff Management. Do not create duplicate commits
claiming to implement those already-committed increments again. Their pending edits are
compatibility extensions for downstream Engineering/QA states and the work-track model.

The uncommitted domain-skill/Engineering, work-track fork and artifact naming/storage
changes overlap in `sdlc.py`, `engineering.py`, `qa_track.py`, approval/lifecycle validators,
shared skills, tests and architectural docs. Older modules now import the new Engineering
contract. New readers/writers and canonical naming must land together. File-only staging
into separate feature commits would create missing imports or incompatible intermediate
states. No intermediate commit has been fabricated or staged to claim otherwise.

Proposed logical commits, **only after explicit human approval**:

1. **`feat(sdlc): add versioned domain skills, work tracks and canonical artifacts`**
   All pending generic orchestrator implementation/tests (except `test_demo_assets.py`),
   both thin adapters, shared skills, `.gitattributes`, `AGENTS.md` and architectural/CLI
   documentation except this demo-finalization report. This groups the domain workflow,
   independent Engineering/QA fork and format0.1/0.2 naming compatibility because their
   file boundaries overlap. Existing Analysis/identity/ownership code is extended, not
   reimplemented. It preserves a working core without any demo-asset dependency.
2. **`feat(demo): preserve verified acceptance and add reproducible rehearsal`**
   `examples/todo-app/` excluding `.run/`, `.gitignore`, root `README.md`, this report and
   `orchestrator/tests/test_demo_assets.py`. Runner/tests/data arrive together, after the
   reader that can validate their mixed historical formats. Root README's overlapping
   overview changes land here as a complete documentation file; no partial staging is
   needed. Preserved request/business/application bytes are additions, not new approvals.

This is a proposed breakdown, not executed Git work. Do not split already-committed
approval/UX/ownership features or force seven commits with invalid intermediate states.
No feature branch, PR, release, deployment or automatic Git action is introduced.

## Final verification and limits

- Complete orchestrator automated suite: **347 tests passed in 517.193 seconds**, exit0.
  [Full actual test output](../examples/todo-app/preparation-evidence/orchestrator-tests.txt) and
  [machine-readable preparation results](../examples/todo-app/preparation-evidence/results.json) are retained.
  No tests were reported passing without execution.
- Diff review includes tracked changes and new modules, instruction snapshots and demo
  files. `git diff --check` and new mutable source/document whitespace checks passed.
  Historical documents and patch evidence retain original whitespace; archive additions
  may legitimately trigger whitespace warnings when staged later. Do not auto-format
  immutable evidence or change its hashes to silence them.
- No secrets or active host identity/configuration are intended in the versioned assets;
  history retains actual declared actors and original execution context.
- Domain skills remain local/pinned; historical1.0.0 links assume their original restored
  package layout. No package/pin was edited merely to improve this presentation.
- The demo is macOS/installed-Chrome-specific; runtimes are observed, not vendored. Node
  and Chrome binaries/OS are not part of the application source fingerprint. Dependency
  setup requires registry/network availability, but the running app needs no external service.
- Identities are declared, roles informational, and file controls are not an OS sandbox.
  Claude runtime acceptance, enterprise authentication/RBAC, Stories, date-and-time scope,
  release/deployment and production readiness remain outside the demonstrated result.
- Past-date behavior and changing/clearing assigned dates remain acknowledged open topics.
  Their blocked scenarios are not counted as passed or silently resolved.

The read-only preserved project is the acceptance authority. Rehearsal results are fresh
presentation evidence, not permission to revise business content or claim a new signoff.
