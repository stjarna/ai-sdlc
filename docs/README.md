# Documentation

[Project overview](../README.md)

Start with your task, then open the precise contract when you need implementation detail.
The current endpoint is verified Engineering and QA, not release or deployment. Examples
are illustrative unless a page links preserved execution evidence.

## Getting started

- [Getting started](getting-started.md): install, check adoption, create and clarify a request, troubleshoot.
- [Installation and adoption](installation-and-adoption.md): pinned external runtime, loader, preflight and operator recovery.
- [Existing-project demo runbook](existing-project-demo.md): authentic before/after evidence capture outside governed source.

## Using AI SDLC

- [Complete conversational command reference](command-reference.md): all ten routed commands, creation shorthand, selectors, gates and examples.
- [Workflow](workflow.md): roles, persisted states, separate tracks and evidence dependencies.
- [Business approval](business-approval.md) and [Analysis approval](analysis-approval.md): exact revision decisions, uncertainty and separate advancement.
- [Ownership and handoffs](ownership.md): retained accountability, inboxes, nomination and confirmed assignment.
- [Artifact guide](artifact-names.md): document purposes, physical filenames, history and baseline discovery.

## Architecture and governance

- [Workflow responsibilities](workflow.md#who-does-what): agent judgment, deterministic persistence and human decisions.
- [Governance corrections](engineering.md#governance-corrections-contract-01): prototype limitation consent and source-bound semantic review.
- [Domain package contract](engineering.md#domain-instruction-packages) and [pinned catalog](../orchestrator/domain-skills/catalog.yaml): ownership and immutable instruction versions.
- [Template contract](../orchestrator/templates/README.md): structure, validation compatibility and exact provenance.
- [Artifact traceability](artifact-names.md#how-documents-become-evidence): revisions, approvals, source and actual checks.

## Advanced technical reference

- [Complete CLI inventory](cli-reference.md): 50 parser operations, arguments, routes and contract links; installer/adoption entrypoints separately.
- [Operation contract](../orchestrator/scripts/README.md): JSON diagnostics, schemas and persistence guarantees.
- [Interactive Discovery](interactive-discovery.md), [Business Refinement](business-refinement.md), [Functional Analysis](functional-analysis.md): stage data and source contracts.
- [Command routing and local identity](command-ux.md): profile semantics and trust boundaries.
- [Engineering contract](engineering.md): shared mechanics, retained sequential compatibility and current recovery/governance addenda.
- [Engineering/QA work tracks](work-tracks.md): current fork policy, QA schemas, joined verification and reconciliation.
- [Regression suite](../orchestrator/tests/README.md): automated fixtures and their acceptance limits.

## Historical design and evaluation

These records preserve original intent and evidence; they are not the current command catalog.

- [Working specification](specification.md): mixed historical decisions, future Story/Release models and later implementation addenda.
- [Decision register](decisions/architecture-decisions.md) and [PoC scope ADR](decisions/0001-repository-and-poc-scope.md): original rationale and subsequent extensions.
- [Host UX evaluation](agent-ux-evaluation.md): early cross-host manual protocol, not a current acceptance matrix.
- [Demo preparation record](demo-finalization.md): dated commit proposal and actual original verification results.
- [Preserved acceptance](../examples/todo-app/EVIDENCE.md): authoritative old example, kept distinct from Littlelist.
- [Documentation audit](documentation-audit.md): per-file inventory, coverage, verification and remaining gaps.

## Ownership and maintenance

Repository maintainers own navigation, conversational semantics and runtime contracts.
Business/Analysis, Architecture, Engineering Enablement, QA and Security domain owners
review the documents and template/skill packages in their area; package manifests declare
actual responsible teams. These are maintenance responsibilities, not an implemented
review-assignment or RBAC service. A behavior change should update its authoritative
contract, the relevant command entry and diagrams together. Readers start here; agent
execution instructions remain in AGENTS.md, shared skill guidance and thin host adapters.

Keep historical decisions/evidence and consumed package versions unchanged. New user
explanations link to the existing technical authority instead of copying schemas into
multiple guides. Do not retrospectively assign today's templates to legacy artifacts.
