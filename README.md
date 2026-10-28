# AI-SDLC

**Status:** design / pre-implementation PoC. This repository is not yet an operational SDLC skill.

A reusable, Git-native AI SDLC orchestration capability for existing software projects. The orchestrator will manage Epic/Story/Release workflows, artifacts, human approvals, contextual handoffs and versioned references to approved specialist skills. It does **not** replace project management tools or own all specialist engineering standards.

## Start here

- [Consolidated specification](docs/specification.md) — main source of design decisions, with `[D]` confirmed, `[P]` PoC, `[T]` target architecture and `[O]` open.
- [Initial architecture decision](docs/decisions/0001-repository-and-poc-scope.md) — repository scope and demonstration scenario.
- `orchestrator/skill/` — future orchestrator skill; **not implemented yet**.
- `orchestrator/templates/`, `orchestrator/scripts/`, `orchestrator/tests/` — future reusable skill assets.
- `examples/todo-app/` — future small existing To-Do application used *only* to demonstrate the orchestration flow.

## PoC scenario

Extend an existing small Node.js/JavaScript To-Do app (in-memory data) with **Task Due Date Management**. Demonstrate change impact analysis when a date-only deadline is extended to a date **and time**. Keep the orchestrator generic: no hard-coded Node.js, To-Do, or due-date assumptions in its core.

## Initial Git setup

Create a **public empty** GitHub repository named `AI-SDLC` (do not initialize it with README/license/.gitignore), then from this directory:

```bash
git init -b main
git add .
git commit -m "docs: initialize AI SDLC orchestrator specification"
git remote add origin git@github.com:YOUR-ACCOUNT/AI-SDLC.git
git push -u origin main
```

If you use HTTPS rather than SSH, replace the remote URL accordingly. No remote repository has been created or pushed by this scaffold.

## Next steps

1. Agree on orchestrator directory structure, commands, YAML schema and approval transitions.
2. Add the actual `orchestrator/skill/SKILL.md` and deterministic management scripts.
3. Prepare the To-Do example independently of the generic skill.
4. Verify an end-to-end SDLC walkthrough and release-readiness evidence.
