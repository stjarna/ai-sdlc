---
name: sdlc
description: Guide an informal business idea through Discovery, business specification refinement, explicit Product Owner decisions, and Functional Analysis using the AI SDLC Assistant.
---

# AI SDLC Assistant for Claude Code

Before acting, read and follow the [shared workflow](../../../orchestrator/skill/SKILL.md),
which loads the common conversational policy and CLI contracts. Resolve this link from
this adapter's location, not the working directory; keep the complete package together.

Use the main Claude Code conversation in the CLI or IDE. Natural task descriptions can
select this skill; explicit entry is `/sdlc <command>`, with `status`, `review`, `approve`, `changes`,
`advance`, `details`, `inbox`, `pending assignments` and `assign`. Claude supplies trailing arguments to the skill (automatically
appending them when no placeholder consumes them). Keep it in the current interactive context,
without fork/background execution. Use available native tools under the host's permissions;
if a suitable question control is unavailable, use ordinary text and wait for the reply.
