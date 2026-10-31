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
| `business.md` | Business revision-history entries, envelope 0.2 or 0.3 with domain pins |
| `specification.md` | Analysis revision-history entries, envelope 0.2 or 0.3 with domain pins |
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

## Named placeholders and missing information

`artifact_templates.PLACEHOLDERS` defines the named generation contracts for all eleven
artifact types. Package loading lints names, syntax and exactly-one slot occurrences,
including optional-section slots. The retained Idea 1.0.0 contract has only `problem`;
Idea 1.1.0 has seven slots. No published template was rewritten. Slot names and scaffold
sections are independent: fixed explanatory prose needs no placeholder, and optional
sections may be omitted from an agent's completed draft.

There are two generation paths:

- **Deterministic:** `new` fills Idea 1.1.0 once using `problem` (the original `--idea`)
  and optional `--idea-details-file` section strings: `users`, `expected_value`,
  `initial_scope`, `success_criteria`, `assumptions`, `open_questions`. Missing/null/empty
  values become `Not provided.`. This exact generation sentinel retains Discovery
  completeness warnings; it is not a semantic classifier for `TBD` or contradictions.
  Context keys/types are validated; unknown/unused keys are errors. Original Markdown
  and literal braces in supplied text remain data, not another round of substitution.
- **Agent-drafted:** Business, Analysis and specialist documents use the returned scaffold
  and pinned domain expertise. The writer checks structure and rejects raw `{{...}}` or
  unfinished opening tokens. Fill supported items or remove unused optional blocks using
  the existing format; do not invent business content. Escape a genuinely literal token
  as `\{{example}}` when discussing template syntax in an agent-authored document.
  New approvals also reject unresolved draft slots, including older pending drafts;
  reads and retries of historical approved records are not retrospectively revalidated.

Final Verification projects structured evidence through the same single-pass renderer,
with its fixed named context. Literal evidence containing braces stays escaped as data
and is never evaluated. Rendering verifies that all scaffold slots have supplied values;
those literal values are not mistaken for leftover scaffold variables. Nothing executes
expressions, loops, external code or AI calls.

Unknown is **not** confirmed absence. Supply `Confirmed: none.` only if the person said
so; retain `Unconfirmed proposal: ...` and `Deferred: ...` wording when provided. The
renderer does not decide these meanings. `discovery.yaml` remains the authoritative typed
conversation history, and later updates never rewrite the original idea.

For example, the illustrative inputs `--idea 'Help people understand daily spending.'`
and details `{"users":"Individuals.","initial_scope":"Record personal expenses."}`
produce Problem with the original text, Users with `Individuals.`, Initial scope with
the supplied scope and the other four sections with `Not provided.`. The result contains
no unfilled scaffold tokens, stays in Discovery, and has four completeness warnings.
This is an illustration, not a confirmed product requirement or approval.

New requests select the effective runtime's catalog pin. Existing idea.md files retain
their original bytes and pin. A catalog update in a source checkout affects future
creation only; immutable installed runtimes require explicit update/promotion as described
in the [runtime guide](../../docs/runtime-version-management.md). Older Idea versions are
available via exact package resolution; no migration or replacement API is introduced.
