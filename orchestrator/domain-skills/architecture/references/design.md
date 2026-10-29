# Technical Design guidance

Use the pinned `technical-design` template for layout. The following topics guide
architecture judgment; they are not additional required document sections. Existing
validators own structured fields. Do not invent complexity or requirements to fill headings.

## Context and authority

Identify the approved Analysis input and its upstream Business baseline. Summarize
the change's purpose, existing system constraints and exclusions. Reference source
requirement and acceptance-criterion IDs. Record inspected code paths as observations,
separately from human-confirmed requirements.

## Proposed solution and decisions

Explain the smallest useful component and data changes. State responsibilities,
interfaces, input validation, error paths and externally observable behavior.
Describe persistence, compatibility and migration only when the change requires them.
Name significant dependencies and the reason for each choice. Capture material
alternatives and their costs; do not produce a list of unrelated technologies.

For each consequential decision, distinguish an inherited constraint, a human decision
and an AI technical proposal. Explain what the human Design review is being asked to
accept. A diagram is useful when it clarifies boundaries or an interaction; it is not
mandatory for a small local change.

## Quality and security

Carry approved non-functional requirements into the design. If measurable budgets
are absent, state that limitation; propose targets explicitly instead of inventing
confirmed latency, availability or scale commitments.

With the Security skill, identify relevant assets, trust boundaries, permissions,
sensitive data, attack surfaces and failure modes. Describe controls and how to verify
them. Do not add authentication, external services or data collection merely because
they are common architectural patterns. Retain unresolved security risks and their
owners when actually declared; a review recommendation is not risk acceptance.

## Coverage, uncertainty and handoff

Ensure every active functional requirement and acceptance criterion has a traceable
design disposition. Explain exclusions and blocked items. An acknowledged open rule
must not acquire an implied implementation in prose, example data or an interface.
Keep all inherited uncertainty, new questions and AI assumptions explicitly typed.

Explain the implementation impact, test seams, integration/UI verification needs and
security checks so the approved design can inform a subsequent Engineering implementation
plan and later QA automation. QA strategy/scenarios are independently derived from
approved Analysis and must not wait for this design. Describe newly exposed interface
risks as additional information, not replacement functional requirements.
Do not decompose Stories, start application edits, or treat structural validation as
design correctness. Semantic consistency remains the skill's and human reviewer's
responsibility.
