# Discovery, Business Refinement and Approval tests

From the repository root, after the setup in [the operation contract](../scripts/README.md):

```bash
.venv/bin/python -m unittest discover -s orchestrator/tests -v
```

Tests use temporary projects, exercise the real CLI and operation functions, inject
filesystem failures, and check that existing content and Git data remain unchanged.
They do not require an application, Docker, network, or host skill installation.

`test_discovery.py` preserves Increment 1 coverage. `test_interactive_discovery.py`
tests history initialization, typed append-only records, sourced confirmations and
corrections, resume, idempotency, stale revisions, competing writers and atomic-write
failure recovery, including an abruptly terminated temporary writer.
`test_business_refinement.py` tests explicit completion, provenance separation,
document revisions, concurrency, interrupted multi-file publication, reopening and
reconciliation. Conversational question quality and semantic fidelity require the
separate [Discovery manual evaluation](../../docs/interactive-discovery.md#manual-conversational-evaluation)
and [Business Refinement manual acceptance](../../docs/business-refinement.md#manual-acceptance-task-due-date-management).

`test_business_approval.py` uses fictional identities and decisions to exercise
approval versus advancement, feedback/reapproval, exact frozen context, acknowledgements,
stale/reverted revisions, reopening after advancement, concurrent writers, baseline
corruption/deletion, abrupt exits and idempotent recovery. These fixtures do not
constitute human approval of a real Epic. The original 76 tests remain; the obsolete
Increment 3 assertion that approval commands must be absent is updated for Increment 4,
while preserving the absence of Functional Analysis.

The [manual approval acceptance scenario](../../docs/business-approval.md#manual-acceptance-with-the-established-to-do-example)
requires actual separate human approval and advancement instructions. Automated tests
do not establish semantic correctness or authenticated human identity.

`test_functional_analysis.py` exercises the real approved-handoff fixtures and CLI,
source/coverage/Given-When-Then validation, inherited deferrals, resumable revision
history, feedback, stale tokens, competing writes, reopened/new business cycles,
idempotent replay and interrupted publication/recovery. Earlier 111 tests remain
unchanged. [Functional Analysis manual acceptance](../../docs/functional-analysis.md#manual-acceptance-established-to-do-baseline)
checks meaning, observable outcomes and missing/contradictory behavior, which structural
tests cannot establish. Claude Code runtime validation is not required for PoC acceptance.

## Sequential engineering tests

`test_domain_skills.py` validates local approved instruction pins, versions, manifests,
dependencies/cycles and stage compatibility. `test_engineering.py` exercises the fixed
sequence, exact Analysis authority, source/plan/task/test links, actual named-command
results, separate human fixture gates, stale revisions, path boundaries, Security
remediation, audit integrity and interrupted publication/retries. `test_engineering_cli.py`
adds fresh-process CLI JSON diagnostics, local-profile attribution, read-only routing,
failed-verification remediation and process-group timeout cleanup.

Every human decision in automated fixtures is explicitly fictional. Named fixture commands
execute real Python code, but their category labels do not claim browser interaction or
security certification. Real UI behavior, skill semantics and actual human decisions use
the [manual engineering acceptance](../../docs/engineering.md#manual-end-to-end-acceptance).
No demonstration application or browser dependency is silently installed by these tests.
The pre-engineering 231-test regression coverage, including legacy golden baseline hashes,
remains part of the complete suite. An old unsupported-stage routing assertion now uses
an actually unsupported Release stage. Claude runtime acceptance remains excluded.

## Engineering/QA fork tests

`test_work_tracks.py` exercises automatic atomic forks, common Analysis authority,
independent ownership/revisions, pending rows, track-aware ambiguity/start, explicit legacy
adoption, per-track reconciliation and management audit/concurrency/recovery.
`test_qa_track.py` exercises scenario drafting before Design, independent review gates,
case/check coverage, automation source/interface bindings, actual fixture execution,
complete/stale joins and QA audit/retries. `test_fork_integration.py` covers joined
Verification/Security/finalization, QA-failure remediation, reopened Discovery assignment,
fresh CLI processes and schema0.6 renewal.

Pre-fork Engineering and scalar-ownership tests explicitly construct historical stored
metadata without the new optional mapping. Production advancement always creates tracks;
these fixtures preserve the original legacy contract rather than bypassing the new fork.
Current bundled-skill assertions use1.1.0; exact1.0.0 instruction snapshots are retained
under `domain-skills/versions` for historical pins. Synthetic decisions and category-labelled
commands remain fixtures, not real Product Owner approval or browser acceptance.

## Artifact naming regressions

`test_artifact_names.py` covers typed names, escaped exact-file links, core and missing-history discovery, legacy Engineering/final report bytes and hashes, QA status/details and fresh CLI output, directory relocation and corruption detection. No aliases or physical renames are created. Existing golden approval baseline tests remain in the complete suite.

`test_artifact_storage.py` exercises canonical physical files for documents, approval/event snapshots, revisions, final reports, mixed legacy/new histories, old approvals and exact retries, interrupted Engineering/QA publication and schema/name integrity rejection. Storage0.2 is explicit; legacy0.1 baselines remain unchanged.
