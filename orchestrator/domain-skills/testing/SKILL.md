---
name: sdlc-testing
description: Prepare independent QA strategy and functional scenarios from approved Analysis, then review automation and report actual integration or UI evidence for an SDLC change.
---

# Testing and Verification

Use this package for the QA track coordinated by the
[SDLC orchestrator](../../skill/SKILL.md). Its manifest identifies QA / Quality Engineering
ownership, version, compatible stages and inputs. Only orchestrator operations mutate
lifecycle, persist records or transfer ownership. Do not create another approval/audit
mechanism or launch automatic parallel agents.

Legacy requests retain their recorded workflow and instruction pins. Do not reinterpret
an old combined plan as independent QA approval or rewrite an approved artifact; use
the orchestrator's explicit compatibility/reconciliation path when authorized.

## Document templates and validation

Use `test-strategy`, `test-scenarios` and `test-automation` for QA documents. Final Verification uses `verification-report`; the deterministic renderer supplies its content.
Resolve each template using `sdlc.py templates <template-id>` before drafting. The
pinned catalog owns document headings, their order and optional sections; use the returned
scaffold rather than creating a second layout here. Domain guidance below supplies
content expertise, not a competing structure. Deterministic writers record the exact
template ID, version and digest. Existing validators remain authoritative for structured
fields and governance; template, skill and CLI versions are independent. Preserve legacy
artifacts and their historical pins instead of adding provenance retrospectively.

## Start QA from approved Analysis

Read the exact approved Functional Analysis baseline selected by explicit advancement,
including its Business dependency, acceptance criteria and acknowledged unresolved items.
QA strategy and functional scenarios do **not** require Technical Design, an Engineering
plan or implemented code. Do not wait for them before proposing useful tests. Resolve the
QA track internally and ask one clarification question only when the intended track is
ambiguous. A newly created or assigned track does not itself authorize work.

Prepare independently revisioned Test Strategy and Test Scenarios through the documented
QA operations. Reference FR/AC IDs instead of duplicating authoritative requirements.
Derive observable expected outcomes from Analysis, not a prototype, design decision or
observed implementation. Preserve deferred questions and blocked behavior. An acknowledged
uncertainty is not an answer or permission to invent an assertion.

Present strategy and scenarios for one explicit human QA scenario approval bound to their
exact revisions. This is independent of Engineering plan approval. Approval leaves the
QA stage unchanged; obtain separate advancement before automation. A strategy revision
or changed scenario expectation requires renewed relevant review, not copied signoff.
An unrelated Engineering revision must not invalidate functional scenario approval.

## Prepare and review automation

After scenario approval and separate advancement, inspect available approved Technical
Design interfaces and project conventions to prepare executable automation. These are
implementation information; approved Analysis remains the source of functional
expectations. If required interfaces are missing, report that automation is waiting
without invalidating useful QA strategy/scenarios.

For forked requests, put QA runner source and dependencies under the reserved `qa/`
namespace. Declare paths, named integration/UI checks, literal argument arrays, working
directory, timeout and requirement links through QA artifacts. Do not edit Engineering
source, developer unit tests or its approved plan. A source fix belongs to Engineering
under explicit remediation authorization. Prepare automation only within declared paths,
then record its actual source fingerprint and interface binding for human review.

Obtain separate explicit human automation approval; scenario signoff does not approve
generated test code. Wait for separate advancement to verification readiness. Unit
tests remain with Development; reviewing their coverage does not create a second
unit-test implementation stream. Do not claim automation passed merely because it exists.

## Execute and synchronize

Before integration/UI execution, verify current Engineering code approval, available
implementation outputs and current QA scenario/automation approvals. Both tracks must
reference the same approved Analysis cycle. Use only approved named checks through the
orchestrator; record actual command, exit status, output, requirement links and source
contract. An incomplete, failed, stale or unexecuted QA track is not successful integrated
verification. Complete QA explicitly; Engineering advancement remains a separate decision.

A passing exit code is execution evidence, not assertion quality or semantic coverage.
A UI/E2E claim needs real interface interaction and observable assertions; HTTP-only
checks are integration/API evidence. Missing tools/environments remain blocked or not run.
See [verification guidance](references/verification.md) for evidence and remediation.

Preserve failed results and report defects with FR/AC links. Engineering changes may
invalidate execution evidence or require automation adaptation, but do not silently
rewrite unrelated functional scenarios. Authoritative Analysis changes require explicit
impact assessment and reconciliation of **both** tracks; retain older decisions and
baselines. Do not automatically migrate or approve a legacy combined plan.

For final verification, bind the report to current Engineering and QA outputs, actual
checks, uncertainty and Security review. No recommendation authorizes release or deployment.

## Supporting skill roadmap

Scenario Design, Integration Testing, API Testing, UI Automation / Playwright, Test
Data Management, Accessibility Testing and Performance Testing remain high-level future
specialties, not separately installed tools or runtime integrations. Version pins
reproduce instructions, not deterministic LLM outputs. Historical 1.0.0 instruction
snapshots remain in the package archive for legacy audit reproduction.

## Authorized limitations and complete disclosure (governance 0.1)

Derive product cases from approved Analysis, independently of Design. Do not derive a
negative expected outcome from a positive example or treat acknowledged uncertainty as
resolved. Unimplemented behavior and explicit runtime rejection require separate review.

QA automation includes `limitation_checks` (empty if none). These supplemental checks
have the normal named-check fields, plus `limitations` referencing explicitly authorized
Design limitation IDs instead of `cases`. Link affected requirements while preserving
their blocked/excluded dispositions. Test every authorized limitation separately;
supplemental passes never count as product scenario or acceptance-criterion coverage.
Preserve independent product cases unchanged and use fresh source-bound actual evidence.

Final Verification Markdown is rendered deterministically from structured current
sources. Inspect verified scenarios and named checks, blocked requirements, every
unresolved item, scope exclusions and their authority, authorized limitations and
remaining risks. Distinguish scenario outcomes from the aggregate passing commands.
Partial or limited verification must visibly say “Verified for the stated scope”.
An exclusion does not itself authorize an application to reject that behavior.
Do not rewrite historical reports; old cycles remain legacy governance and retain pins.
