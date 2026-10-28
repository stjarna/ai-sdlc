# Canonical artifact filenames and legacy compatibility

New Engineering/QA snapshots use manifest format **0.2** and canonical physical files.
The displayed filename, link label and actual target basename agree. No duplicate files,
symlinks, export aliases or generic document-management layer are introduced.

| Document type | Canonical physical filename |
|---|---|
| Technical Design | `technical-design.md` |
| Engineering Implementation Plan | `implementation-plan.md` |
| Engineering Code Review | `code-review.md` |
| Security Review | `security-review.md` |
| Final Verification Report | `verification-report.md` |
| QA Test Strategy | `test-strategy.md` |
| QA Test Scenarios | `test-scenarios.md` |
| QA Test Automation Review | `test-automation.md` |

`artifact_names.py` owns the fixed catalog and event suffixes. Approval, change-request,
advancement and remediation snapshots use the document stem plus `-approval.md`,
`-change-request.md`, `-advancement.md` or `-remediation.md`. Other event documents use
`development-start.md`, `verification-advancement.md`, `verification-remediation.md`,
`qa-verification-completion.md`, `check-evidence.md` and `qa-check-evidence.md` as applicable.
The structured audit remains authoritative for decisions/results; changing a filename
does not change what was approved or turn event wording into document requirements.

## Inventory and migration decision

Engineering/QA `content.md` files are immutable snapshots, including unapproved drafts,
revisions, approval/advancement decisions, execution evidence and final reports. They
are not mutable working copies. Their filenames participate in manifests and baseline
hashes, and later approvals/audit records bind those identities. Renaming them would
change identities and invalidate history. **Do not migrate, rename or rewrite them.**

Existing Business `business.md`, Analysis `specification.md`, original idea references
and Discovery `discovery.yaml` are already meaningful physical names with established
contracts. Their CLI names now match those actual basenames. Custom original idea
references remain intact. No mutable `content.md` storage convention was found, so no
mutable-file migration is needed. Temporary caller input files are not managed documents.

## Explicit storage formats

Format 0.1 remains exactly `{schema_version, request_id, files}`, with the exact file set
`metadata.yaml`, `artifact.json`, `content.md`, plus `manifest.json`. Its bytes, hashes,
IDs, metadata schemas, historical instruction pins and approval/audit authority remain
unchanged. Reading does not migrate it.

Format 0.2 adds `document`, bound to the canonical filename for the recorded stage,
kind and action. Its exact file set is `metadata.yaml`, `artifact.json`, that document,
and `manifest.json`. The reader selects filenames from a closed catalog, verifies all
file hashes/canonical manifest identity and checks the type/action-to-filename binding.
Unknown formats, traversal names, missing/extra files, symlinks and type mismatches fail
closed. Format 0.1 cannot be silently interpreted as canonical format 0.2.

All new writes, revisions, approvals, evidence and final reports use 0.2. Publication
retains durable temporary-bundle/atomic metadata behavior. Failed publication leaves no
authority; exact retries verify/reuse the canonical orphan where applicable. Committed
legacy retries replay their original decision without republishing or migrating it.
Optimistic concurrency, lifecycle, idempotency and approval policies are unchanged.
Business/Analysis baseline formats are unaffected. Older binaries that only understand
0.1 cannot read 0.2; mixed repositories require this updated reader.

## Discovery, links and presentation

Validated Engineering/QA draft entries and final report views expose a `document`:
`name` equals the actual basename, `canonical_name` identifies the catalog type,
`title` describes the document, `legacy` identifies old generic storage, and `path`/`link`
point to the exact physical file. New links say `security-review.md`, for example.
Legacy links explicitly say **Security Review (legacy content.md)** and target the
existing `content.md`; they never pretend a canonical physical file exists.

Core payloads expose `epic.documents`; aggregate status/details returns
`review.documents.engineering` and `.qa`. Business/Analysis links target current working
documents, so approved consumers must still resolve their verified upstream baselines.
When comparing multiple revisions/requests, include request/revision context. Titles or
filenames never substitute for approval, freshness or integrity checks.

Shared skill guidance applies to both thin host adapters. Historical pinned domain
instructions describing `content.md` refer to format 0.1; the current deterministic
storage contract governs new publication, without rewriting those approved packages.
There is no new export command: links/opening existing files use the exact canonical or
explicit legacy target. Paths are local and refreshed after project relocation; no
custom viewer, service or duplicate human-facing folder is added.
