# Discovery and Business Refinement tests

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
