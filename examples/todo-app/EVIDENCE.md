# Preserved SDLC evidence

Engineering and QA are Verified. This is the completed real interactive acceptance,
not a synthetic approval fixture. All stored baselines and actual human wording remain
unchanged. Historical declared identity is David Krzystek; it is not authenticated RBAC.

## Authoritative request and documents

- [metadata.yaml](project/requirements/REQ-0001-task-due-date-management/metadata.yaml): lifecycle,
  decisions/approval references, track ownership, append-only audit and separate advancements.
- [idea.md](project/requirements/REQ-0001-task-due-date-management/idea.md): original business idea.
- [discovery.yaml](project/requirements/REQ-0001-task-due-date-management/discovery.yaml): sourced
  statements, questions and human decisions.
- [business.md](project/requirements/REQ-0001-task-due-date-management/business.md) and
  [specification.md](project/requirements/REQ-0001-task-due-date-management/specification.md):
  original business/Functional Analysis documents, with their revision histories alongside.

| Artifact | Exact preserved physical file |
|---|---|
| Engineering: Technical Design | [Technical Design (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/engineering-baselines/97e48e3c6e0fcfdcb07373d0a2cb420bbb67f374e9599a588516765206db899d/content.md) |
| Engineering: Engineering Implementation Plan | [Engineering Implementation Plan (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/engineering-baselines/6875a98c313457dd5fa9f3f5dfb567e66380d87e8f531f1ae47b915b48a26f0f/content.md) |
| Engineering: Engineering Code Review | [Engineering Code Review (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/engineering-baselines/e3195b832a823c3b6412752f88b8187e8e91af254b464ad7be881931d6c97e2a/content.md) |
| Engineering: Security Review | [Security Review (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/engineering-baselines/9067cb3166ca29bf04672c5485419443ee7c22192cde209b3d69b221188d643a/content.md) |
| QA: QA Test Strategy | [QA Test Strategy (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/qa-baselines/fe334ee142992548d60ab3e07167002b7cfeff44a0d7fa5f6227daebb3f1bae0/content.md) |
| QA: QA Test Scenarios | [QA Test Scenarios (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/qa-baselines/84c3b21faea541978595102d431b35d76e8dca945cbdedbbd317c7b9a2bb9bd4/content.md) |
| QA: QA Test Automation Review | [QA Test Automation Review (legacy content.md)](project/requirements/REQ-0001-task-due-date-management/qa-baselines/849ac49769433728d8dd75afdc31727ea2c779db00c33619b33a8ccf344e09e5/content.md) |
| Final report | [verification-report.md](project/requirements/REQ-0001-task-due-date-management/engineering-baselines/bc843c4302b96bc0faeba77993e81da5b064dd283c7ed78e7f484407bbba3eba/verification-report.md) |

Legacy content.md files are labelled explicitly. Only the later advancement and final
report use canonical format0.2; earlier approved snapshots retain format0.1 bytes and
hashes. The historical unapproved combined Plan is retained in Engineering history,
not silently treated as the replacement Engineering Plan or QA signoff.

## Tests, defects and remediation

- Accepted Engineering evidence: **41 unit tests passed**, build validation passed.
- First real browser run: **4 passed, 1 failed, 3 not run**. Its focus-restoration failure
  and all screenshots/traces remain; the earlier HTTP run passed six tests.
- QA-F-001: explicit human remediation authorization, source change, improved regression
  reproduction, 41-test rerun, renewed code approval and separate advancement are preserved.
- Accepted final QA runs: **6 HTTP integration tests and 8 real Chrome scenarios passed**,
  then explicit human QA completion. No category label substitutes for actual UI execution.
- [Historical initial QA report](acceptance-evidence/qa-execution-report.md),
  [successful rerun report](acceptance-evidence/qa-focus-rerun-report.md),
  [focus-remediation diff](acceptance-evidence/engineering-focus-remediation.patch) and
  [finalize result](acceptance-evidence/final-verification-finalize-result.json).
- [All original test reports, screenshots and traces](project/requirements/REQ-0001-task-due-date-management/test-evidence/).
  Four official QA executions contain 51 referenced files whose printed SHA-256 values
  are checked locally by `demo.py verify`.

## Security and instruction versions

The Security Review has no open findings within its scoped local PoC assessment.
Its actual [npm advisory response](acceptance-evidence/security-npm-audit.json) and
[execution record](acceptance-evidence/security-npm-audit-execution.json) returned zero
known advisories at that lookup time; this is not a fresh scan or production certification.

Seven distinct historical/current domain instruction pins are recorded by accepted
artifacts. The original1.0.0 packages are preserved in
[the repository's instruction archive](../../orchestrator/domain-skills/versions/), and
active1.1.0 packages remain in [the catalog](../../orchestrator/domain-skills/catalog.yaml).
`verify` checks each recorded version against exact instruction bytes and validates the
current catalog. Original instruction package links assume their original restored layout.

## Relocation and provenance

[Preservation manifest](preservation-manifest.json) hashes every archived file and maps
original temporary roots to the permanent `project/`, `acceptance-evidence/` and
`acceptance-inputs/` locations. All448 copied files were verified against their originals.
Original paths survive only as historical provenance, never as a runtime prerequisite.
No active human profile file, credential store, installed dependencies, caches or generator scripts
are copied; historical declared identity fields in audit/CLI evidence remain unchanged. Original draft inputs, captured before/after code, actual CLI results and
human intent records are retained in the supporting evidence/input folders.

Some captured prose predates later approvals and legitimately says “proposed/not run”.
Read its timestamp/audit context rather than editing it. Final persisted metadata and
current verified baseline/evidence select authority. Past-date behavior and changing or
clearing assigned dates remain open; acknowledgement did not resolve either topic.

## Fresh preparation checks (not historical SDLC evidence)

[Preparation results](preparation-evidence/results.json),
[complete orchestrator test output](preparation-evidence/orchestrator-tests.txt) and
[rehearsal evidence manifest](preparation-evidence/manifest.json) retain actual new
setup/unit/build/HTTP/Chrome results separately. They do not overwrite acceptance records
or authorize another lifecycle transition. Original evidence remains authoritative for
the accepted request.
