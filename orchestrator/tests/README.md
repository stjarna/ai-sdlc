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
