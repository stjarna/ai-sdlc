---
name: sdlc-security
description: Contribute security-by-design and review implemented changes against their approved design, recording evidence, security findings and verified remediation.
---

# Security domain skill

Use this package during Engineering Technical Design and postimplementation Security
Review after the integrated Engineering/QA verification conditions. Its manifest declares Application Security ownership, version and
compatibility. Resolve and pin the package through the orchestrator; record the
returned version and content digest with every contribution. A pin reproduces
instructions, not deterministic model output.

Follow the [orchestrator workflow](../../skill/SKILL.md) for persistence and decisions.
This skill supplies security expertise. It does not mutate lifecycle metadata, create
approvals, transfer ownership, execute a separate security-development branch or build
its own audit mechanism.

## Document templates and validation

Use `security-review` for Security reviews; contributions to Technical Design use its `technical-design` template.
Resolve each template using `sdlc.py templates <template-id>` before drafting. The
pinned catalog owns document headings, their order and optional sections; use the returned
scaffold rather than creating a second layout here. Domain guidance below supplies
content expertise, not a competing structure. Deterministic writers record the exact
template ID, version and digest. Existing validators remain authoritative for structured
fields and governance; template, skill and CLI versions are independent. Preserve legacy
artifacts and their historical pins instead of adding provenance retrospectively.

## Security-by-design

Read the exact approved Analysis input, Business dependency and proposed technical
design. Identify relevant assets, trust boundaries, sensitive data, dependencies,
permissions and abuse cases. Inspect existing controls rather than assuming them.
Recommend proportionate controls and concrete ways to verify them. Keep new security
requirements visibly proposed until human review accepts them; do not silently expand
business scope, add identity services or decide unresolved product behavior.

Record unresolved risks in the Technical Design and trace each recommendation to the
affected source requirement or component. Design consultation is not approval or a
claim that security verification has run. The Architecture skill remains responsible
for integrating the contribution into the reviewable design.

## Postimplementation review

Read the approved Engineering design/plan and implementation, the independently
approved QA scenarios/automation, current integrated evidence and prior findings. QA
functional expectations come from approved Analysis, not the design. Do not create a
third work track or infer successful QA from missing evidence. Use the [review guidance](references/security-review.md)
to scope inspection. Perform only authorized checks through the documented workflow;
never claim a scanner, dependency lookup or test ran without observing its output.
Keep execution inside the project's approved boundaries and host permissions.

Record a human-readable report and structured findings through the orchestrator.
Use stable `SF-...` identifiers, severity `critical`, `high`, `medium` or `low`, and
status `open` or `resolved`. Include the affected source or dependency, supporting
evidence, security impact, proposed remediation and verification needed. Clearly label
uncertain findings; do not fabricate exploit evidence or represent hypotheses as facts.

Retain prior findings during remediation. Link each resolution to the changed source
and actual rerun or review evidence addressing the original issue. A developer's claim
or a passing unrelated test does not resolve a finding. The orchestrator returns work
to Development for authorized remediation and requires current verification evidence
and a new Security review. Preserve independent QA scenario history while rerunning
source-bound checks or adapting automation as required; do not start automatic agents
or a separate security-development branch.

All open findings block finalization in this PoC, including low severity. Do not silently
suppress, downgrade or mark them resolved to make the gate pass. Risk acceptance and
business uncertainty acknowledgement are different decisions; neither substitutes for
verified remediation under this conservative policy. Material scope changes require
upstream reconciliation through the orchestrator.

## Report limits honestly

Bind the report to the reviewed source revision and list actual inspection/check
coverage, unavailable checks and remaining uncertainty. A clean report means no open
findings within the stated review scope; it is not a security certification. The CLI
checks structure and provenance, not whether prose or security judgments are correct.
Do not infer approval, lifecycle advancement, deployment or permission to run further
checks from a clean result.

## Supporting specialties — roadmap only

These are high-level extensions, not separately installed or executed capabilities:

- Threat Modeling: assets, trust boundaries, abuse cases and mitigations.
- OWASP Secure Coding: relevant input, output, state and error-handling controls.
- Dependency Security: actual inventory, advisories and upgrade verification.
- Secrets Detection: scoped repository inspection and safe evidence redaction.
- Authentication & Authorization Review: existing trust and permission boundaries.
- Security Testing: authorized negative tests and reproducible remediation checks.

No external AI API, authentication provider, remote registry or enterprise security
platform is introduced by this package.
