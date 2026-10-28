# ADR-0001 — Repository and PoC scope

**Date:** 2026-10-28  
**Status:** Accepted

## Context

We need a version-controlled specification and a reusable AI SDLC orchestration proof of concept suitable for a short Head of Engineering case-study presentation. We want to demonstrate workflow orchestration rather than generate an elaborate application from scratch.

## Decision

- Start a **public** `AI-SDLC` repository now, before detailed implementation.
- Store approved design decisions and living specification as Markdown in Git.
- Keep `orchestrator/` separate from `examples/todo-app/` as ordinary folders, not Git submodules. The deliverable is a **generic orchestration skill**, not the demonstration application's code.
- Use an **existing minimal JavaScript/Node.js To-Do application** with in-memory storage; extend it with **Due Date Management**.
- Use a subsequent date-only → date-and-time requirements change to demonstrate impact analysis across specification, design, tasks and tests.
- Keep enterprise specialist skills (security, architecture, coding, QA) external and version referenced; enterprise governance/distribution can be represented architecturally in the PoC.
- Complete Epics (`ready_for_release`) are the only candidates for Release Planning in the PoC.
- Do not design greenfield bootstrap, Jira/Teams integration or full production deployment into the initial PoC.

## Consequences

This reduces demo complexity while preserving the core skills of analysis, approvals, implementation, testing, traceability and release readiness. The To-Do app must not leak assumptions into the orchestrator.

## Open implementation details

Actual skill commands, directory layout beyond the repository scaffold, YAML schema, platform-specific integration and enforcement mechanisms are still to be designed.
