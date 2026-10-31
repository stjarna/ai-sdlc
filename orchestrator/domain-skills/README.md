# Versioned SDLC domain skills

The Orchestrator coordinates stages, roles, persistence, approvals and separate
advancement. Domain teams own specialist content guidance; versioned templates own
layout; deterministic validators own structural and governance checks. Packages are
bundled resources, not additional native skills or automatically launched agents.

| Package | Current version | Domain owner | Activity / output |
|---|---|---|---|
| Discovery | 1.0.0 | Discovery Team | Adaptive clarification; idea.md context, typed discovery.yaml evidence and review |
| Business Requirements | 1.0.0 | Product / Business Requirements Team | business.md from completed sourced Discovery |
| Functional Analysis | 1.0.0 | Business Analysis Team | specification.md from the handoff-selected approved Business baseline |
| Architecture | 1.3.0 | Architecture Team | technical-design.md; Security dependency retained |
| Development | 1.3.0 | Engineering Enablement | implementation-plan.md, implementation and code-review.md |
| Testing | 1.3.0 | QA / Quality Engineering | test-strategy.md, test-scenarios.md, test-automation.md and verification evidence |
| Security | 1.2.0 | Application Security | Security-by-design and security-review.md |

## Resolve before use

From the effective runtime, use `PYTHON -B orchestrator/scripts/sdlc.py --project APP
skills --stage ACTIVITY`. `skills` without stage retains its catalog result; with stage
it additionally returns exact selected pins, including dependencies. Follow returned
catalog paths to read selected SKILL.md files. Readiness routes to the next activity;
QA is selected independently of Engineering. Resolution does not start work or approve.

The catalog uses schema 0.1, with exact semantic version/content pins. Modern manifests
use schema 0.2 and `sdlc-domain/1`, independent of CLI 0.15.0 and template contracts.
Current packages live at `<name>/`; retained immutable versions live at
`versions/<name>/<version>/`, following existing repository conventions. Do not modify
consumed versions. Publish reviewed changes under a new version/pin and preserve old
snapshots. Local digests detect changes, not publisher identity or content correctness.

## Provenance and compatibility

New idea metadata has a separate `domain_provenance` schema 0.1 envelope. New Discovery
operations use envelope/root 0.2 with `skills`; Business/Analysis revision envelope/root
0.3 adds `skills` beside the existing template pin. Mixed old/new histories are readable:
legacy records retain their bytes/fields and unknown attribution, without backfilling.
Human-readable documents, template pins, approval manifests and canonical filenames are
unchanged. Normal approval baselines freeze these supporting artifacts as before.

Existing writers always resolve and record the relevant domain pin for a new operation;
an exact retry preserves its original entry. Pin validation reads the exact current or
retained package, not today's catalog selection. The normal locks, concurrency tokens,
transaction journals and source-bound decisions remain authoritative. No domain skill
can complete, approve, assign or advance a request independently.

A newly installed runtime includes all seven packages. Old runtimes remain immutable. Default rollback retains the verified resolver manager,
including when an older default has the protocol but lacks the new envelope readers.
An additive catalog/reader extension can support forward promotion after compatibility
inspection and explicit future-scope reconciliation. It does not reopen approved
upstream work. Older readers may not understand new history envelopes: promotion back
to one is blocked if its actual read fails. Integrated verification checks current
selected and current-cycle track evidence runtimes. Historical shared-stage writers
need not read newly created downstream documents; the current reader verifies their
frozen inputs. Incompatible current track evidence still blocks the join.

## Focused acceptance

In a disposable project, record a short idea, one answered question and one deferred
question through normal conversation. Request a review: the skill should stop questioning
and display confirmed information, assumptions and remaining uncertainty. Complete only
on explicit human instruction, then prepare Business and Analysis through their separate
gates. Inspect exact skill/template pins and preserve original IDs and idea text.
Repeat Analysis preparation after an explicitly assessed forward runtime promotion;
compare upstream baseline/audit hashes. Test decisions in automated fixtures are fictional.
Automated checks do not prove identical AI output or replace conversational human acceptance.
