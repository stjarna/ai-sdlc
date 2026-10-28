---
name: sdlc
description: Guide an informal business idea through Discovery, business specification refinement, explicit Product Owner decisions, Functional Analysis and independently owned Engineering/QA work tracks with explicit human gates using the AI SDLC Assistant.
---

# AI SDLC Assistant for Codex

Before acting, read and follow the [shared workflow](../../../orchestrator/skill/SKILL.md),
which loads the common conversational policy and CLI contracts. Resolve this link from
this adapter's location, not the working directory; keep the complete package together.

Use the main Codex conversation in the CLI or IDE. Natural task descriptions can select
this skill; explicit entry is `$sdlc <command>` or the native `/skills` selector. The shared
commands are `status`, `start`, `review`, `approve`, `changes`, `advance`, `details`, `inbox`, `pending assignments` and `assign`; trailing
text is prompt context, not Claude-style argument substitution. Use available
native tools under the host's permissions. If a suitable question control is unavailable,
use ordinary text and wait for the reply; do not change modes merely to obtain a widget.

For Engineering and QA requests, the shared workflow loads version-pinned domain skills.
An optional track selects context: `$sdlc start engineering`, `$sdlc start qa` and `$sdlc review qa`.
Independent logical tracks do not schedule parallel agents or start work automatically.
If the active track is ambiguous, ask one clarification question; do not bypass gates.
