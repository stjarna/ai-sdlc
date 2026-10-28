---
name: sdlc
description: Create, reopen, or structurally validate local Discovery Epics in an existing project's Git-native requirements directory. Use for managing early business ideas with the AI SDLC Orchestrator.
---

# Discovery management

This increment supports only `new`, `open`, and `validate`. Read the
[operation contract](../scripts/README.md) for setup, arguments, schema, and diagnostics.
Keep this checkout's `orchestrator/` directory together: scripts and templates are
siblings of this skill. This is a checkout-based entrypoint; it does not install
itself into the host's skill catalog.

## Route the request

- Establish the target project from the active workspace or explicit user context.
  If multiple project roots are plausible, ask which one. The orchestrator checkout
  is not automatically the target project.
- For a new business idea, derive a concise title from the user's wording and pass
  their initial description as business content. Ask when the intended idea is
  ambiguous. Users do not need to supply IDs, slugs, or directory names.
- Invoke the deterministic `new` operation to allocate the ID and persist files.
  Never allocate IDs, create Epic directories, or patch metadata with improvised
  shell commands or direct model edits.
- For `open`, resolve the user's reference from known Epic context. If the user
  names an idea without a known ID, `validate` returns local IDs; `open` can then
  retrieve their titles. Ask when multiple Epics match. Never guess an ID.
- For `validate`, explain structural errors and incomplete-content warnings. Neither
  successful validation nor the user's initial idea constitutes approval or readiness.

Run `scripts/sdlc.py` relative to this skill's parent `orchestrator/` directory,
using the Python environment described in the contract. Pass user content as a
literal argument through the host's argument API or correctly shell-quote it;
never interpolate raw user text into executable shell syntax.

## Persist and report

Read the JSON result and actual files. Report the assigned ID, directory, and
warnings; on failure report the diagnostic code and file and ask for missing
information when needed. Do not silently repair structural errors or retry with
invented metadata. `open` and `validate` are read-only.

This increment saves the initial description only. Conversational refinement,
subsequent content persistence, Requester confirmation, and `ready_for_refinement`
transitions are deferred. Do not claim they were performed, create Stories, or
invent business answers, approvals, or test results. No checkpoint file, automatic
Git staging, commit, push, skill installation, or external integrations.
