# Template placeholder audit and correction

[Documentation index](README.md) · [Generation contract](../orchestrator/templates/README.md)

Audit baseline: `68452ea1f700bce5f4e2b3a310932b686a0accaf`.
All eleven registered artifact types and their published Markdown, manifests, generation
paths, domain guidance and validators were inspected. Historical evidence is read-only.

## Findings

1. Idea 1.0.0 has seven headings but only `problem` is a slot. `new` used one literal
   replacement and left six sections empty. That was visible as completeness warnings;
   it did not lose the original idea or infer missing business facts. However, adding
   six Markdown slots alone would leave them unresolved: the old writer did not provide
   a rendering context. Idea 1.1.0 plus context-aware deterministic generation fixes both.
2. Package validation checked content digests/headings but had no named-variable schema.
   Most agent drafts were checked for structure, not raw leftover slot syntax. Generic
   new writes and fresh approvals now reject unresolved opening tokens; published history
   remains readable. Final Verification already checked its own fixed slots; that check
   now uses the shared single-pass renderer, retaining exact structured evidence projection.
3. Other ten layouts have no demonstrated missing slot. Optional sections can be omitted
   in a completed agent draft; their scaffold slot/comment is intentional. Static report
   explanations do not need variables. No other template version was changed.

## Registered template inventory

| Template | Selected version | Named slots | Generation | Assessment |
|---|---|---:|---|---|
| `idea` | 1.1.0 | 7 | Deterministic original/context rendering | Six previously absent slots corrected in 1.1.0; same seven headings. |
| `business` | 1.0.0 | 5 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `specification` | 1.0.0 | 61 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `technical-design` | 1.0.0 | 8 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `implementation-plan` | 1.0.0 | 6 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `test-strategy` | 1.0.0 | 5 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `test-scenarios` | 1.0.0 | 5 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `test-automation` | 1.0.0 | 7 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `code-review` | 1.0.0 | 6 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `security-review` | 1.0.0 | 6 | Agent fills scaffold; stage writer validates | Complete named slots; optional section/comment structure is intentional. |
| `verification-report` | 1.0.0 | 12 | Deterministic structured-evidence projection | Complete named slots; fixed prose is intentional. |

Idea 1.0.0 remains readable/resolvable with its original one-slot contract. No published
version directory is changed. Canonical package hashing calculates the new content and
catalog digest; values are not guessed. Required/optional sections still come from the
existing manifests, while named slot strings are checked against explicit generation
contracts in `artifact_templates.py`. Discovery guidance 1.1.0 explains the new slots;
its retained 1.0.0 package and other domain versions remain unchanged.

## Unknowns, literals and original evidence

Creation accepts the original `--idea` and optional `--idea-details-file` strings/nulls
for six sections. It does no semantic extraction. Missing/empty values become exactly
`Not provided.` and retain warning-only completeness checks. Confirmed absence, proposals
and deferrals require actual supplied wording; the authoritative conversation remains
append-only discovery.yaml. Later answers never rewrite the initial idea.

Literal braces and Markdown in the original idea remain original data. Deterministic
substitution consumes each scaffold slot once, never recursively evaluating inserted text.
Final Verification similarly keeps literal evidence text as data. Agent-authored drafts
must fill/remove unused slots or escape intentionally literal examples. This distinction
prevents both accidental leftovers and corrupting authentic quoted evidence.

## Version and approval compatibility

New requests select the catalog inside the effective runtime and record the exact pin.
Existing requests keep their saved idea/template provenance. Explicit expected-digest
checks reject stale selection; retries reuse their original pins. No template-only
migration, approved-content rewrite or new workflow stage is introduced. Promotion to
this runtime follows existing compatibility and human reconciliation rules; new Discovery
and Idea pins are visible differences. Schema/layout/approval manifests remain unchanged.

Legacy reads and idempotent replays are preserved. A pending draft containing unresolved
slots must be revised before a new approval; an already approved historical artifact is
not retrospectively invalidated. Structural validity and nonempty marker text do not
establish business completeness, correctness or readiness.

## Rehearsal and validation

The template guide includes an illustrative spending-request input/output example.
Generated samples remain outside authoritative requests/history. Tests cover every
registered layout, malformed/unknown/missing/duplicate slots, strict contexts, all seven
Idea sections, original literals, incomplete warnings, legacy selection, rejected writes
and fresh approvals. Final Verification tests compare structured scope/evidence and
literal-safe output. Static/digest, lifecycle and historical-preservation results are
recorded in the completion note after execution. No live AI conversation is simulated.


## Completion evidence — 2026-11-01

- Complete regression run: **475 tests passed** in two isolated module groups (220 in
  830.797s; 255 in 639.590s; 830.934s wall time). All captured implementation/package/test
  files stayed unchanged during the run. One additional missing-resource regression,
  added after discovery started, also passed (0.057s): **476 verified tests in total**.
- Focused checks: eight placeholder/context tests passed; all 16 template tests passed;
  all 12 Final Verification projection tests passed. The original Business review and
  approved-baseline golden hashes passed unchanged. No successful AI conversation or
  deterministic model-output equivalence is claimed.
- Static skill validation, Python compilation, CLI/help coverage, local-link and whitespace
  checks passed. Generated Idea sample was inspected: supplied values remain visible,
  four unprovided fields have explicit markers, and no scaffold tokens remain.
- Read-only archived verification retained all 448 files, seven stored historical skill
  pins and 51 evidence bindings. All 552 pre-existing versioned-template/domain and demo
  files in the protected inventory remain byte-identical. No historical artifact was
  regenerated, reformatted or migrated.

The field-contract checks are syntactic, not business analysis. Unknown markers are valid
in incomplete Discovery. Raw braces supplied as original/evidence text are intentional
data; agent-drafted literal examples require escaping. A human still reviews meaning and
approves exact revisions. Existing installed runtimes and the separate demo repository
are not updated by this source change.
