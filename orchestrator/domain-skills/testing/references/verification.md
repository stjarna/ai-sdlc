# Verification guidance

Use the pinned QA templates for document layout and `verification-report` for the
deterministically rendered final report. These topics guide evidence quality; they do
not define a second document structure or replace deterministic validators.

## Scenario and evidence contract

Keep business meaning in the approved Analysis; reference FR/AC IDs instead of copying
and independently maintaining requirement text. A test scenario identifies:

- Its stable scenario ID, referenced acceptance criteria and risk addressed.
- Preconditions and controlled data, action, observable expected result and test level.
- Its implementation/check reference, automation status and unresolved impediments.

Choose positive, negative and boundary cases based on actual behavior and risk rather
than requiring a fixed case count. A scenario is not automatically implemented, and an
implemented test is not automatically executed. Avoid assertions that merely mirror
implementation details or pass without exercising the requirement.

The approved QA automation artifact declares integration/UI checks, argument arrays,
project-relative working directories, timeouts and AC coverage. Engineering owns its
unit/build checks separately. Strategy and scenarios need only the approved Analysis
baseline; later automation can bind approved interface details from Technical Design. The
orchestrator owns format validation and execution evidence. Check captured output as
well as exit status; the CLI cannot determine whether a command genuinely exercises a
particular UI or acceptance criterion. Structural traceability is not semantic coverage.

## Levels and applicability

Unit checks isolate relevant behavior and normally accompany developer changes. Build
checks establish that the declared build command succeeded; they do not replace tests.
Integration checks exercise meaningful component boundaries and failure handling.
UI/E2E checks interact with the actual interface, assert user-observable outcomes and
retain available screenshots, traces or logs with source attribution.

Do not relabel API requests as UI coverage. This vertical slice requires a UI check and has no applicability exception yet. When there is no UI, explain that limitation; do not invent a passing UI run. Missing browser automation is a known gap until actual verification
is performed. Tools such as Playwright are possible project choices, not implicit
installed dependencies of this skill.

Use isolated test data and a reproducible project environment. Follow approved
container/runtime configuration when present. Do not install dependencies, change
shared infrastructure or access production data merely to obtain a green result.
Describe unavailable context and request the necessary project decision.

## Defects and remediation

A useful defect report records severity, affected FR/AC, the exact source revision,
reproduction steps, expected versus observed behavior, and actual failed evidence.
Separate confirmed failures from suspected causes and environmental obstacles.

Report defects to Engineering and route fixes through its approved implementation scope.
Keep the independently owned QA scenarios as expectations; do not edit them merely to
match the defect. QA automation source/dependencies stay under `qa/` in this PoC. Scope/design changes need
reassessment rather than an invented correction to expected behavior. After remediation,
retain original failures and link the new check results to the corrected revision.
Security findings are owned by the Security review; the testing role supplies relevant
regression evidence without silently closing a security finding.

## Final verification review

Summarize the approved Analysis/design/plan references and pinned skill versions, then
the exact reviewed Engineering implementation, QA scenario/automation revisions and
evidence. Check the orchestrator synchronization view for both tracks rather than
assuming missing QA work succeeded. State actual executed results by level,
remaining FR/AC gaps, unresolved requirements, defects, security findings and limitations.
Do not combine results from different source fingerprints into one claim of success.

A concise recommendation should say whether the available evidence supports the next
human decision, and explain any blockers. Do not infer release approval from all checks
passing. The orchestrator retains responsibility for explicit gates, immutable
baselines, audit, ownership and separate lifecycle advancement.

## Future specialist outlines

These are guidance topics and possible independently maintained skills, not executable
capabilities or installed packages:

| Extension | Intended expertise |
|---|---|
| Test Scenario Design | Risk-based positive, negative, boundary and regression cases |
| Integration Testing | Component contracts, persistence and external boundary failures |
| API Testing | Observable contracts, validation and error behavior |
| UI Automation / Playwright | Browser interaction, stable assertions and trace inspection |
| Test Data Management | Isolated fixtures, cleanup and sensitive-data handling |
| Accessibility Testing | Keyboard, assistive-technology and relevant accessibility checks |
| Performance Testing | Workload assumptions, measurements and agreed performance criteria |

An Engineering-only artifact revision does not invalidate unrelated functional scenario
expectations. New Analysis authority requires explicit impact assessment and renewed
reconciliation for both tracks; matching old bytes does not reinstate an old approval.

Version pins reproduce the instructions used for a review, not deterministic LLM
outputs. A later skill version does not retroactively change an approved report.
