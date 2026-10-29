# AI SDLC Assistant in Codex and Claude Code

[SKILL.md](SKILL.md) is the common workflow for both agents.
[conversation.md](conversation.md) defines concise business-facing interaction,
natural-language decisions and optional technical detail. Deterministic operations,
revision/provenance checks and audit contracts stay in the existing CLI.

## Native discovery adapters

| Host | Project entry | Optional explicit entry |
|---|---|---|
| Codex CLI / IDE | [.agents/skills/sdlc/SKILL.md](../../.agents/skills/sdlc/SKILL.md) | `$sdlc` or `/skills` |
| Claude Code CLI / IDE | [.claude/skills/sdlc/SKILL.md](../../.claude/skills/sdlc/SKILL.md) | `/sdlc` |

Natural requests such as "Help me clarify this business idea" can select the skill.
The adapters contain only loading and host instructions; they both read the same
shared workflow and conversation policy. They do not install tools, change execution
permissions or run approval operations during discovery. No optional UI control is
required: plain-text conversation is the common fallback.

Open this complete checkout in the host's CLI or IDE to use the project entries.
They resolve `../../../orchestrator/skill/SKILL.md` from their own directory, not from
the session working directory. Shared links and the CLI then resolve from that
canonical package location. In a new session, confirm that the intended `sdlc` entry
is visible; reload/restart where the host requires it. Avoid registering another
copy of the shared entry under the same name. Personal/managed skills can conflict
with or shadow a project entry; inspect the actual selected skill path during setup.

The orchestrator package and the **target project** are separate. Tell the assistant
which project to operate on; an external disposable target may need explicit host
file access. Do not silently create business artifacts in the orchestration checkout.
Keep `orchestrator/`, supporting documentation and the adapters together at the selected
package revision. Copying only the checkout wrapper into a personal or unrelated project skill
directory breaks its relative resource links. The [external installer](../../docs/installation-and-adoption.md)
now publishes a pinned runtime and a separate user-scoped loader with verified resource
resolution. Native plugin distribution remains outside scope. Do not modify global
host settings or overwrite registrations automatically.

## Contracts and evaluation

- [CLI setup and operation contracts](../scripts/README.md)
- [Discovery evidence and resume](../../docs/interactive-discovery.md)
- [Business Refinement and reconciliation](../../docs/business-refinement.md)
- [Business Approval and immutable baselines](../../docs/business-approval.md)
- [Functional Analysis, revisions and acceptance](../../docs/functional-analysis.md)
- [Manual cross-agent evaluation](../../docs/agent-ux-evaluation.md)

Format/link validation does not establish actual discovery or conversational behavior
in every host. Run the manual guide separately for both CLI and IDE surfaces and
record versions and permission modes. Native command traces may remain visible.
Approval identities are declared and unauthenticated, and execution permission is not
PO approval. Approval and advancement remain separate explicit human decisions.
Functional Analysis approval, Technical Design and Engineering/QA through Verified are
implemented; Story decomposition remains deferred. Claude Code runtime validation is an unverified
portability target, not a PoC acceptance requirement.
