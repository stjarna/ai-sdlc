# Discovery tests

From the repository root, after the setup in [the operation contract](../scripts/README.md):

```bash
.venv/bin/python -m unittest discover -s orchestrator/tests -v
```

Tests use temporary projects, exercise the real CLI and operation functions, inject
filesystem failures, and check that existing content and Git data remain unchanged.
They do not require an application, Docker, network, or host skill installation.
