# Shared SDLC Commands and Local Declared Identity

The assistant accepts `status`, `review`, `approve`, `changes`, `advance` and `details`
through `$sdlc <command>` in Codex CLI/IDE and `/sdlc <command>` in Claude Code CLI/IDE.
Natural-language requests remain supported. These are conversational commands, not shell
commands. Codex supplies a skill mention plus prompt text; Claude supplies skill arguments.
No common host argument-substitution syntax is assumed. Both adapters load the shared
[command contract](../orchestrator/skill/commands.md) and conversation policy.

## Resolution and routing

The agent selects the target project from explicit conversation/workspace context and
keeps an explicitly selected Epic in the conversation. It reopens artifacts for current
state. It never assumes that the implementation checkout is the target application.
A deterministic read-only helper exposes the existing stage operation without executing it:

```text
sdlc.py --project PROJECT command-context COMMAND [--request TITLE_OR_ID]
```

With no selector, exactly one Epic must exist. IDs take precedence over titles; titles
match exactly, case-insensitively. Missing/ambiguous context returns `E_CONTEXT_MISSING`
or `E_CONTEXT_AMBIGUOUS` without writes. The result includes routing, current stage review
and local identity or a setup diagnostic. `requires_human_decision` is informational,
not authorization. The agent interprets actual human language; Python does not classify
consent, business meaning or acknowledgement text.

`status` summarizes progress and approval state; `review` summarizes current content and
uncertainty; `details` exposes the full document/evidence when requested. All are read-only.
Business and Analysis `approve`/`changes`/`advance` map to existing stage gates. Discovery
`changes` captures sourced records, and `advance` explicitly completes Discovery through
`discovery-complete`. Discovery `approve` explains this distinction without changing state.
Readiness states never silently generate the next draft. Technical Design is not run.
The helper is a small fixed routing table, not a workflow engine.

## Local profile

The default location is `$XDG_CONFIG_HOME/ai-sdlc/identity.json`, or
`~/.config/ai-sdlc/identity.json` when XDG_CONFIG_HOME is unset. `SDLC_IDENTITY_FILE` can
select another absolute external file, useful for portable installations and isolated
tests. Both hosts use this same configuration; no host-specific account integration is
required. Keep the full skill package and its Python environment available to either host.
The file must remain outside the target project, this implementation checkout and any
Git repository. File symlinks and resolved paths into those locations are rejected.

```json
{
  "schema_version": "0.1",
  "display_name": "Example User",
  "declared_roles": ["Requester", "Product Owner"]
}
```

These are informational project-role labels reused across projects, not per-project
access grants. Labels may be edited without rewriting historical decisions. No role
membership authorizes an operation or prevents an otherwise explicit human decision.
The profile contains no credentials/tokens; unknown fields, duplicate keys, malformed
JSON and invalid names/roles are rejected rather than repaired. A profile is a local
preference, not a checkpoint or an alternative authority for business requirements.

Tool-facing operations (the assistant performs these internally):

```text
sdlc.py --project PROJECT identity-show
sdlc.py --project PROJECT identity-setup --display-name NAME --role ROLE [--role ROLE]
sdlc.py --project PROJECT identity-edit --expected-profile-revision REVISION [--display-name NAME] [--role ROLE ...]
```

Setup requires the user's supplied name and roles and never overwrites an existing file.
If missing, the assistant asks once for the necessary information and explicit setup,
then reuses the profile across conversations without repeated identity questions.
A prior name declaration may be suggested, but must not silently create a profile.
Editing replaces only supplied fields; role flags replace the complete role list.
Writes use a profile-local lock, a private temporary file, atomic replacement and fsync;
files are created with mode 0600. Failed edits preserve the previous file before commit.
A post-replacement durability failure returns `E_IDENTITY_WRITE_UNCERTAIN`; inspect
`identity-show` before retrying. Abandoned profile locks require operator inspection.

## Attribution and compatibility

The existing explicit `--requester`, `--reviewer`, `--approver` and `--actor` flags remain
supported. When omitted on Discovery lifecycle, Business gate or Analysis gate commands,
the CLI loads the profile and records `identity_source: local_profile` alongside the
actor in the new audit entry. Existing entries without this optional field remain valid
and are not rewritten. The profile's changing contents are not needed to verify old
approvals. Profile edits neither modify old actors nor invalidate an approved document.

Agents pass the optional `--expected-profile-revision` from the reviewed context for
automatic attribution. A changed profile then produces `E_IDENTITY_REVISION` before a
write. It cannot be combined with an explicit legacy actor. An exact retry after a name
change must preserve the original attribution; do not silently use the new actor or
mint a new operation to bypass an uncertain result. Inspect the saved decision first.

Missing profiles return `E_IDENTITY_MISSING`; malformed/unsafe profiles fail explicitly.
There is no Git/login fallback. Legacy callers supplying an actor do not read the profile
and retain their existing semantics and baseline hashes. New local-profile records use
an additive optional audit field; older binaries with strict field validators may not
read those new records. This release reads existing records and baselines without migration.
Business decision text now accepts actual multiline human messages, matching Analysis;
actor/reason validation and baseline serialization remain unchanged.

Filesystem durability follows the existing local POSIX rename/fsync assumptions.
Windows and network-filesystem runtime behavior has not been verified.

The returned identity states `authenticated: false` and `roles_enforced: false`.
Only `local_profile` is implemented as a new identity-source value; unsupported claims
such as `authenticated_host` or `verified_enterprise` are rejected. Host identity and
enterprise authorization remain separate future integrations. An unrestricted agent or
filesystem editor can impersonate a local profile; this is not a human-only security
boundary, enforced RBAC or protection against coordinated audit rewriting.

## Approval interaction

The agent resolves context, retrieves and presents the current review, summarizes any
unresolved questions/proposals/blocked behavior and obtains an explicit human decision.
Ask for acknowledgement only if missing, grouping records that describe the same business
issue while retaining all required technical IDs internally. Acknowledgement leaves
questions unresolved and assumptions unconfirmed. “Looks good”, silence, tool permission
and conditional approval are insufficient.

An `approve` command after an already presented unchanged review can be the explicit
decision if required acknowledgements are complete. If the review was not presented or
was lost, show it and obtain assent before writing. Preserve actual short commands,
contextual replies and acknowledgement wording without inventing formal quotations.
Revalidate document/review tokens and profile revision; all deterministic gate checks,
locks, baseline integrity and idempotency remain in effect. Approval never advances.
A separate `advance` instruction authorizes only the supported readiness transition.

## Manual acceptance — Codex CLI

Use a disposable copy with an approved/advanced Business baseline and a current
Functional Analysis draft that has not yet been approved. Preserve its provenance and
all human decisions; do not delete an existing approval to construct this starting state. Keep evidence outside the implementation
repository. For an isolated profile, launch Codex with `SDLC_IDENTITY_FILE` pointing to
an absolute external file, then invoke these commands in the interactive composer:

1. `$sdlc status`: confirm the current request and stage; with multiple requests,
   expect one selection question and no mutation.
2. `$sdlc review`: inspect a short business-facing review and unresolved issues.
3. `$sdlc approve`: if the profile is missing, supply the requested display name/roles
   and authorize setup once. No approval may be inferred from identity setup.
4. Say “Looks good”: verify no approval. Then give a real explicit approval with all
   disclosed uncertainty acknowledged. Inspect actual wording, local-profile source,
   exact baseline and unchanged lifecycle through `$sdlc details`.
5. Start a new conversation with the same target project/profile. `$sdlc status` and
   `$sdlc details` must reconstruct state without another name question. Request a
   profile edit naturally and verify older audit entries remain unchanged.
6. `$sdlc advance`: give a separate explicit advancement instruction. Verify readiness
   only; no downstream draft, Technical Design or implementation starts automatically.
7. In another disposable copy before advancement, use `$sdlc changes` with real wording
   feedback. Verify actual feedback is retained and only requested changes are applied.
   Attempting to use an earlier review/approval must fail; fresh approval is required.
8. Separately exercise Discovery: `approve` must not create a fictitious approval;
   `advance` requires explicit Requester completion and clearly reports its meaning.

Automated routing/CLI tests and static adapter validation do not prove model behavior.
Live Codex conversational acceptance remains a human exercise. Claude runtime verification
is outside the PoC acceptance scope; its adapter is validated statically only.

## Ownership extension

The six existing commands retain their meanings. [Ownership and Handoff](ownership.md)
adds `inbox`, `pending assignments` and `assign` in both native hosts. Project-level
views need no active Epic selection. Requests keep an accountable owner while waiting
for the next role; nomination and assignment confirmation remain explicit. Creation
now requires a local profile or declared requester, and legacy requester evidence is
used only for ownership, never to impersonate the current actor.

## Sequential engineering extension

The separately authorized [engineering slice](engineering.md) now consumes the approved Analysis handoff through Technical Design, planning, controlled development, verification, Security review and a final report. Earlier increment scope statements describe their historical boundaries. The extension preserves approval separation, existing audit/baseline formats and declared identity semantics.

For new Analysis advancements, the [Engineering/QA fork](work-tracks.md) now creates two independently owned pending tracks. Existing non-fork records retain their historical contracts; adoption and upstream reconciliation are explicit.
