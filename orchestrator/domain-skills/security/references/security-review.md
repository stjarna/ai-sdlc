# Security review guidance

Use the pinned `security-review` template for document layout. These topics guide
security judgment; they are not additional required sections or a second validation schema.

Select checks from actual architecture, approved Engineering scope and the independent
QA strategy/automation where relevant. Their common approved Analysis baseline remains
functional authority; no domain review may invent missing business rules. Do not turn every small
change into an exhaustive enterprise audit. Inspect data entry/output boundaries,
data ownership, local or remote storage, permissions, dependencies, configuration and
error handling where relevant. Explain why each selected area matters for this change.

Separate source inspection, actual automated execution and external advisory evidence.
Record the tool/version or inspection method, reviewed source, result and limitations.
An unavailable scanner is an unperformed check, not a pass. Public advisory information
must retain a source and retrieval context; do not invent vulnerability versions or
severity ratings. Existing application behavior is evidence, not automatic policy.

Use findings with enough information for another reviewer to reproduce the concern:

- Stable finding ID and concise title.
- Severity and rationale tied to impact and exposure.
- Affected source, interface or dependency and relevant requirement/design reference.
- Actual evidence, with sensitive values redacted without losing the reasoning.
- Remediation recommendation, current status and verification evidence when resolved.

Do not copy credentials or personal data into reports. Describe secrets by location
and type with safe redaction. Do not run destructive, intrusive or externally mutating
checks without the required authorization; report the resulting coverage limitation.

On remediation, preserve the original finding and link its verification to the current
source. Re-run affected checks and relevant regression tests rather than relabeling an
older successful run. Review related controls when the fix changes a trust boundary.
If the original issue remains observable, keep the finding open. The latest source-bound
report must account for earlier findings instead of dropping them from its scope.

Inherited open business questions remain open even after acknowledged Analysis or
Design approval. Report their security impact and affected blocked behavior; do not
implement an assumed answer as a mitigation. If the approved plan cannot remediate an
issue without changing scope or architecture, ask for the corresponding review before
continuing development.

Final report wording should state what was inspected, which checks actually ran and
whether open findings remain. Avoid absolute claims such as “secure” or “no possible
vulnerabilities.” Human approval and release decisions remain separate orchestrator
operations.
