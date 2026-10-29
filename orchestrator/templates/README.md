# Versioned artifact templates

Templates own human-readable document structure. Domain skills supply content expertise;
existing validators remain authoritative for structured data and governance. The SDLC
orchestrator owns persistence, approvals and lifecycle. A scaffold is a drafting input,
not a requirement, business decision, approval or evidence of execution.

## Packages and ownership

`catalog.yaml` pins every supported template ID to one semantic version and package
SHA-256 digest. Each `versions/<id>/<version>/` package contains exactly:

- `manifest.yaml`: schema version, unique ID, semantic version, responsible domain team,
  artifact type, compatible validation contract, content digest, required and optional sections.
- `document.md`: UTF-8 Markdown scaffold, with each declared `##` section exactly once.

Required headings occur in declared order. Optional headings may be omitted when drafting.
Placeholders describe where to draft content; they must not be interpreted as confirmed
requirements or filled with invented decisions. The package digest binds exact manifest
and document bytes; the content digest binds `document.md` alone. Git text conversion
is disabled for template packages so checkout cannot change their pinned bytes.

Business and Analysis teams own their respective core documents; Architecture,
Engineering Enablement, QA / Quality Engineering and Application Security own their
specialist documents. Domain owners review layout changes together with validator
compatibility and representative generated output. Publish a new package version and
review its catalog pin rather than editing a consumed version. A validator-contract
change requires explicit compatibility review. Template version, domain-skill version,
validation contract and CLI version are independent.

## Resolution and persistence

Read-only catalog inspection needs no project argument:

```sh
.venv/bin/python -B orchestrator/scripts/sdlc.py templates
.venv/bin/python -B orchestrator/scripts/sdlc.py templates technical-design
```

Resolution returns the scaffold, manifest and exact pin. Document-writing operations
select the current catalog entry deterministically. Optional
`--expected-template-digest <package-digest>` rejects a changed selection, complementing
artifact revision checks, locking and operation idempotency. Publication checks the
selected package again before writing. These technical details stay inside the agent
workflow during normal interaction.

New provenance is stored without changing historical storage manifests:

| Artifact | Template provenance |
|---|---|
| `idea.md` | `metadata.yaml` optional `template_provenance` block, schema 0.1 |
| `business.md` | Business revision-history entries, explicit envelope schema 0.2 |
| `specification.md` | Analysis revision-history entries, explicit envelope schema 0.2 |
| Engineering and QA documents | Immutable artifact envelope schema 0.2, `template` pin |

Pins contain template ID, version, package digest, content digest and validation contract.
Canonical physical filenames remain authoritative. Machine histories, approval records
and raw test evidence are not templated. Existing manifest formats, approvals and baseline
hashes remain valid. Legacy artifacts without pins remain readable; never retrospectively
assign provenance or rewrite approved documents. The unversioned `idea.md` file remains
only a legacy compatibility reference, not selection authority for new documents.

Most documents are drafted by the agent from their scaffold. Final Verification uses a
small deterministic exact-slot renderer: its fixed named slots project structured current
evidence into the pinned layout once. It is not an executable template language; inserted
content is never evaluated as another template. Required-section checks complement rather
than replace stage validators. Neither check establishes semantic correctness.

## Focused manual acceptance

1. Inspect the catalog and one template using the read-only commands above.
2. Create an isolated project and a new request; no local identity setup is needed when
   an explicit declared requester is supplied:

   ```sh
   demo_dir=$(mktemp -d)
   .venv/bin/python -B orchestrator/scripts/sdlc.py --project "$demo_dir" new \
     --title 'Template acceptance' --requester 'Acceptance tester' \
     --idea 'A small request used only to inspect template provenance.'
   .venv/bin/python -B orchestrator/scripts/sdlc.py --project "$demo_dir" open REQ-0001
   .venv/bin/python -B orchestrator/scripts/sdlc.py --project "$demo_dir" validate REQ-0001
   ```

3. Inspect `idea.md` and its metadata provenance. Empty business details should remain
   warnings. The request must stay in Discovery.
4. In an independently prepared disposable request at an authorized stage, ask the SDLC
   skill to draft a document using its resolved template. Verify canonical filename,
   required headings and persisted pin. Remove a required heading from a proposed draft
   and confirm deterministic rejection without replacing the existing artifact.
5. Review a newly generated Final Verification report for visible unresolved, blocked,
   excluded and limitation sections. Compare it with structured data; do not infer a
   test pass or create approvals merely to complete this check.

Each approval and advancement still needs a separate explicit human instruction.
Historical demos are read-only compatibility evidence, never acceptance workspaces.
