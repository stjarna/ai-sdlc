---
name: sdlc-architecture
description: Prepare and review a traceable technical design from an approved Functional Analysis baseline, including architecture trade-offs, interfaces, data and security-by-design.
---

# Architecture domain skill

Use this instruction package for Technical Design in the Engineering track. The package manifest declares its
version, Architecture Team ownership, supported stage and dependencies. Resolve and
pin the complete package through the orchestrator before use; retain the returned
version and content digest with the resulting artifact. Pinning reproduces instructions,
not deterministic model output.

Follow the [orchestrator workflow](../../skill/SKILL.md) for identity, persistence,
approvals and handoff. This skill supplies architecture expertise; it does not own
lifecycle metadata, create approvals, assign people or implement an audit mechanism.

## Document templates and validation

Technical Design uses the `technical-design` template.
Resolve each template using `sdlc.py templates <template-id>` before drafting. The
pinned catalog owns document headings, their order and optional sections; use the returned
scaffold rather than creating a second layout here. Domain guidance below supplies
content expertise, not a competing structure. Deterministic writers record the exact
template ID, version and digest. Existing validators remain authoritative for structured
fields and governance; template, skill and CLI versions are independent. Preserve legacy
artifacts and their historical pins instead of adding provenance retrospectively.

## Establish the approved design input

Read the exact immutable Analysis baseline selected by its explicit advancement,
including the specification, revision operation, approved Business dependency and
unresolved-item acknowledgements. Engineering and QA start from this same immutable
Analysis baseline but have independent owners, states, documents and revisions. Do not substitute a mutable draft or an earlier
approval. Inspect the existing application and its conventions before proposing
changes; distinguish observed behavior from approved requirements.

Keep inherited questions, assumptions and blocked behavior visible. Acceptance of
uncertainty is not its resolution and does not authorize an implementation choice.
When a design decision would select undefined business behavior, ask one focused
question or explain the need for upstream reconciliation instead of deciding it here.

## Prepare and review the design

Use the [design guidance](references/design.md) to select the useful level of detail.
Prefer a small design that explains how the confirmed behavior can be built and
verified. Evaluate plausible alternatives, then explain the recommended trade-offs.
Reuse the project's stack where justified. Label a new stack, dependency, service or
infrastructure choice as a technical proposal until the design is approved.

Consult the pinned Security skill for security-by-design: trust boundaries, data
exposure, abuse cases and proposed controls. Record the security package pin as a
contribution to the artifact; consulting it is not security signoff.

Persist through the orchestrator's documented deterministic operation. Its immutable
revision contains human-readable `technical-design.md` and the structured `artifact.json`
coverage and unresolved-item data. Keep requirement prose authoritative in the frozen
specification; reference its IDs rather than copying a second requirements source.

Present the technical approach, material risks, alternatives and unresolved decisions
concisely. Obtain explicit human Design approval for the exact reviewed revision and
the required uncertainty acknowledgements. Approval does not advance the lifecycle
or authorize coding. Wait for separate advancement before Implementation Planning.
QA may already be designing functional tests from Analysis; neither the existence of
QA documents nor QA approval is a prerequisite for this Engineering design or plan.
Provide interface details to QA when useful, but never replace Analysis expectations
with the design, observed code or a prototype. A design revision may require QA
automation adaptation; it must not silently rewrite unrelated functional scenarios.
If a reviewed revision changes, obtain a fresh decision rather than carrying approval
forward. Domain guidance never overrides CLI checks or host execution permissions.

## Supporting specialties — roadmap only

The current package provides high-level guidance, not separate specialist tooling:

- API Design: contracts, compatibility, validation and error semantics.
- Data Modeling: ownership, invariants, storage changes and recovery implications.
- Architecture Decision Records: context, options, choice and consequences.
- Performance & Scalability: evidence-based budgets and validation plans.
- Integration Architecture: boundaries, failure handling and dependency contracts.
- Threat Modeling: assets, entry points and abuse cases, developed with Security.

Dedicated versions and evaluation scenarios for these supporting skills are future
catalog work. Do not claim them installed, executed or independently reviewed.

## Explicit prototype limitations (governance 0.1)

Prefer clarifying unresolved observable business behavior before proposing an exception.
An unanswered or acknowledged question is not authority to reject an input, select a
default, disable an operation or invent a validation rule. Not implementing a behavior
and explicitly rejecting it are different business effects. Review negative conditions,
defaults, validation restrictions and unsupported-operation responses individually.

For a newly governed cycle, include `governance: {schema_version: "0.1",
prototype_limitations: [...]}` in the Design payload, even when the list is empty.
Each limitation has `id` (LIM-001), affected `requirements`, unresolved `questions`,
`observable_behavior`, `business_impact`, `scope`, and `validity: current_analysis_cycle`.
This is a proposal, not consent. Keep inherited uncertainty and blocked coverage intact.
Explain the exact observable effect and ask for separate explicit authorization within
Design approval. Generic Design approval and uncertainty acknowledgement grant no exception.
A combined decision must explicitly approve the Design and authorize the identified
limitation effects; otherwise ask one concise question at a time. Preserve actual wording.
Permanent product behavior belongs upstream in Business/Analysis, not in a PoC exception.
Refer to the shared governance contract; never edit lifecycle or audit records yourself.
