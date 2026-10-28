# Discovery tests

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
failure recovery, including an abruptly terminated temporary writer. Conversational
question quality and fidelity require the separate
[manual evaluation](../../docs/interactive-discovery.md#manual-conversational-evaluation).
