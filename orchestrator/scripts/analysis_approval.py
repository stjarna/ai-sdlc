"""Functional Analysis approval policy over shared local approval infrastructure."""
from __future__ import annotations
from engineering_contract import STAGES as ENGINEERING_STAGES

import json
import re

import yaml

import approval_common as common
import business_approval as business_gate
import business_refinement as business
import discovery_history as discovery
import functional_analysis as analysis
import local_identity
import ownership

BASELINE_FILES = ("metadata.yaml", "specification.md", "analysis-history.yaml")
CONTEXT_FIELDS = ("analysis_revision", "analysis_operation_id", "business_baseline_id", "business_approval_id", "business_handoff_id")
DECISION_FIELDS = {"id", "operation_id", "action", "actor", "reason", "decision", "timestamp", "review_revision", "acknowledged_open_items", "baseline_id", *CONTEXT_FIELDS}
MANIFEST_FIELDS = {"schema_version", "request_id", "files", "acknowledged_open_items", *CONTEXT_FIELDS}
ITEM_ID = re.compile(r"(?:U|P|FR|UC|BR|AC|AQ|AP)-[0-9]{3,}\Z")


def require(condition, message, code="E_ANALYSIS_DECISIONS", filename="metadata.yaml"):
    business.require(condition, code, message, filename)


def valid_decision_text(value):
    return discovery.text(value) and all(ord(c) >= 32 or c in "\n\r\t" for c in value)


def context(draft):
    return dict(analysis_revision=draft["revision"], analysis_operation_id=draft["history"][-1]["operation_id"],
                business_baseline_id=draft["baseline_id"], business_approval_id=draft["approval_id"], business_handoff_id=draft["handoff_id"])


def validate_decisions(metadata):
    entries = metadata.get("analysis_decisions")
    require(isinstance(entries, list), "analysis_decisions must be an append-only list.")
    operations = {e["operation_id"] for e in metadata.get("business_decisions", [])}
    decisions = {}
    handoffs = {e["id"]: e for e in metadata["lifecycle"] if e["action"] == "advance"}
    lifecycle_ids = {e["id"] for e in metadata["lifecycle"]}
    for index, entry in enumerate(entries, 1):
        require(isinstance(entry, dict) and set(entry) - {"identity_source"} == DECISION_FIELDS, "Invalid Analysis decision fields.")
        local_identity.validate_source(entry, "E_ANALYSIS_DECISIONS")
        require(entry["id"] == f"AD-{index:04d}", "Analysis decision IDs must be sequential.")
        require(discovery.valid_operation_id(entry["operation_id"]) and entry["operation_id"] not in operations | lifecycle_ids, "Invalid or reused Analysis decision operation ID.")
        require(entry["action"] in ("approve", "request_changes"), "Unsupported Analysis decision action.")
        require(all(business.valid_person(entry[k]) for k in ("actor", "reason")) and valid_decision_text(entry["decision"]) and business_gate.valid_timestamp(entry["timestamp"]), "Decision requires declared identity, reason, actual wording and UTC timestamp.")
        require(all(discovery.valid_revision(entry[k]) for k in ("review_revision", "analysis_revision", "business_baseline_id")) and discovery.valid_operation_id(entry["analysis_operation_id"]), "Invalid Analysis decision revision.")
        handoff = handoffs.get(entry["business_handoff_id"]) if isinstance(entry["business_handoff_id"], str) else None
        require(handoff is not None and handoff["baseline_id"] == entry["business_baseline_id"] and handoff["approval_id"] == entry["business_approval_id"], "Decision references an unknown business handoff.")
        items = entry["acknowledged_open_items"]
        require(isinstance(items, list) and all(isinstance(v, str) and ITEM_ID.fullmatch(v) for v in items) and len(set(items)) == len(items), "Invalid Analysis acknowledgements.")
        require(discovery.valid_revision(entry["baseline_id"]) if entry["action"] == "approve" else entry["baseline_id"] is None and not items, "Invalid decision baseline or acknowledgements.")
        operations.add(entry["operation_id"])
        decisions[entry["id"]] = entry
    for event in metadata["lifecycle"]:
        if event["action"] == "analysis_advance":
            selected = decisions.get(event["approval_id"])
            require(selected is not None and selected["action"] == "approve" and selected["baseline_id"] == event["baseline_id"] and all(selected[k] == event[k] for k in CONTEXT_FIELDS), "Analysis advancement differs from its approval.")


def details_for(directory, epic_id, draft, loader):
    _, frozen = business_gate.read_baseline(directory, draft["baseline_id"], loader)
    return analysis.validate_document(draft["content"].encode("utf-8"), epic_id,
        {**draft, "business": frozen["business.md"].decode("utf-8"), "discovery": yaml.load(frozen["discovery.yaml"].decode("utf-8"), Loader=loader)})


def open_items(details):
    if details is None:
        return []
    result = [{"id": business.ITEM.fullmatch(line)[1], "status": "inherited_unresolved", "text": business.ITEM.fullmatch(line)[3]} for line in details["inherited"]]
    for rid, item in details["items"].items():
        status = item["fields"]["Status"]
        if (rid.startswith("AQ-") and status in ("open", "unknown", "deferred")) or status in ("blocked", "proposed"):
            result.append({"id": rid, "status": status, "text": item["title"]})
    return sorted(result, key=lambda v: v["id"])


def read_snapshot(directory):
    files = {}
    for name in BASELINE_FILES:
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "Approval requires regular Analysis supporting artifacts.", "E_BASELINE_CONTEXT", name)
        files[name] = path.read_bytes()
    return files


def frozen_review(files, business_files):
    # Preserve the Increment 5 complete review algorithm. Business content is reused
    # from its immutable dependency; the gate-time live metadata is frozen here.
    upstream = {**business_files, "metadata.yaml": files["metadata.yaml"]}
    fingerprints = [business_gate.review_revision(upstream), *(business.digest(files[n]) for n in analysis.FILES)]
    return business.digest(json.dumps(fingerprints).encode())


def validate_bundle(directory, manifest, files, loader):
    require(isinstance(manifest, dict) and set(manifest) == MANIFEST_FIELDS and manifest["schema_version"] == "0.1", "Invalid Analysis baseline manifest.", "E_BASELINE_INTEGRITY")
    common.validate_files(manifest, files, BASELINE_FILES)
    try:
        metadata = yaml.load(files["metadata.yaml"].decode("utf-8"), Loader=loader)
        require(isinstance(metadata, dict) and metadata.get("schema_version") in ("0.4", "0.5", "0.6") and metadata.get("status") == "functional_analysis" and metadata.get("id") == manifest["request_id"], "Invalid frozen Analysis metadata.", "E_BASELINE_CONTEXT")
        business.validate_lifecycle(metadata["lifecycle"], metadata["status"], True, True, metadata["schema_version"] in ("0.5", "0.6"), metadata["schema_version"] == "0.6")
        ownership.validate(metadata)
        business_gate.validate_decisions(metadata)
        if metadata["schema_version"] in ("0.5", "0.6"):
            validate_decisions(metadata)
        ledger = yaml.load(files["analysis-history.yaml"].decode("utf-8"), Loader=loader)
        analysis.validate_history(ledger, metadata["id"], directory, loader)
        latest = ledger["revisions"][-1]
        require(business.digest(files["specification.md"]) == latest["digest"] and {k: manifest[k] for k in CONTEXT_FIELDS} == context({"revision": latest["digest"], "history": [latest], **latest}), "Analysis baseline differs from its retained revision.", "E_BASELINE_CONTEXT")
        event = analysis.handoff(metadata)
        require(event is not None and event["id"] == manifest["business_handoff_id"] and event["baseline_id"] == manifest["business_baseline_id"] and event["approval_id"] == manifest["business_approval_id"], "Frozen Analysis handoff mismatch.", "E_BASELINE_CONTEXT")
        bm, bf = business_gate.read_baseline(directory, manifest["business_baseline_id"], loader)
        draft = {"revision": bm["business_revision"], "history": [{"operation_id": bm["business_operation_id"]}], "source_revision": bm["source_revision"]}
        require(business_gate.evaluate(metadata, draft, bm["source_revision"], [])["valid"], "Frozen upstream approval is stale.", "E_BASELINE_CONTEXT")
        details = analysis.validate_document(files["specification.md"], metadata["id"], {**latest, "business": bf["business.md"].decode(), "discovery": yaml.load(bf["discovery.yaml"].decode(), Loader=loader)})
        require(manifest["acknowledged_open_items"] == [v["id"] for v in open_items(details)], "Frozen uncertainty acknowledgement mismatch.", "E_BASELINE_CONTEXT")
    except (KeyError, TypeError, ValueError, UnicodeError, yaml.YAMLError, RecursionError, business.BusinessError) as exc:
        raise business.BusinessError("E_BASELINE_CONTEXT", f"Invalid frozen Analysis context: {exc}") from exc


def read_baseline(directory, baseline_id, loader):
    return common.read_baseline(directory, baseline_id, "analysis-baselines", BASELINE_FILES,
                                lambda manifest, files: validate_bundle(directory, manifest, files, loader))


def publish_baseline(directory, metadata, draft, files, acknowledged, loader):
    manifest = {"schema_version": "0.1", "request_id": metadata["id"], **context(draft), "acknowledged_open_items": acknowledged,
                "files": {n: business.digest(files[n]) for n in BASELINE_FILES}}
    return common.publish_baseline(directory, "analysis-baselines", manifest, files,
        lambda m, f: validate_bundle(directory, m, f, loader), lambda value: read_baseline(directory, value, loader))


def check_baselines(directory, metadata, draft, loader):
    errors = []
    revisions = {v["operation_id"]: v for v in draft["history"]} if draft else {}
    for index, entry in enumerate(metadata.get("analysis_decisions", [])):
        revision = revisions.get(entry["analysis_operation_id"])
        require(revision is not None and revision["digest"] == entry["analysis_revision"] and all(revision[k] == entry[v] for k, v in (("baseline_id", "business_baseline_id"), ("approval_id", "business_approval_id"), ("handoff_id", "business_handoff_id"))), "Analysis decision no longer matches retained history.")
        if entry["action"] != "approve":
            continue
        try:
            manifest, files = read_baseline(directory, entry["baseline_id"], loader)
            require(manifest["request_id"] == metadata["id"] and all(manifest[k] == entry[k] for k in (*CONTEXT_FIELDS, "acknowledged_open_items")), "Approval differs from frozen Analysis context.", "E_BASELINE_CONTEXT")
            _, business_files = business_gate.read_baseline(directory, entry["business_baseline_id"], loader)
            require(frozen_review(files, business_files) == entry["review_revision"], "Analysis approval review differs from frozen inputs.", "E_BASELINE_CONTEXT")
            frozen_ledger = yaml.load(files["analysis-history.yaml"].decode(), Loader=loader)
            retained = [{k: v for k, v in e.items() if k != "content_base64"} for e in frozen_ledger["revisions"]]
            require(retained == draft["history"][:len(retained)], "Retained Analysis history differs from the approved snapshot.", "E_BASELINE_CONTEXT")
            frozen = yaml.load(files["metadata.yaml"].decode(), Loader=loader)
            ownership.preserve_prefix(frozen, metadata)
            require(frozen.get("analysis_decisions", []) == metadata["analysis_decisions"][:index] and frozen["lifecycle"] == metadata["lifecycle"][:len(frozen["lifecycle"])] and frozen["business_decisions"] == metadata["business_decisions"][:len(frozen["business_decisions"])], "Retained audit differs from the approved Analysis snapshot.", "E_BASELINE_CONTEXT")
        except business.BusinessError as exc:
            if not exc.filename.startswith("analysis-baselines"):
                exc.filename = f"analysis-baselines/{entry['baseline_id']}"
            errors.append(exc)
    return errors


def current_inputs_match(epic, loader, frozen_analysis=None):
    if epic.analysis is None:
        return False
    _, upstream = business_gate.read_baseline(epic.directory, epic.analysis["baseline_id"], loader)
    live = business_gate.read_snapshot(epic.directory, epic.metadata)
    if any(live[n] != upstream[n] for n in business_gate.BASELINE_FILES if n != "metadata.yaml"):
        return False
    return frozen_analysis is None or all((epic.directory / n).read_bytes() == frozen_analysis[n] for n in analysis.FILES)


def evaluate(epic, integrity_errors, loader):
    entries = epic.metadata.get("analysis_decisions", [])
    latest = entries[-1] if entries else None
    reasons = []
    if latest is None:
        reasons.append("no_approval")
    elif latest["action"] != "approve":
        reasons.append("changes_requested")
    else:
        if epic.analysis is None or any(latest[k] != v for k, v in context(epic.analysis).items()):
            reasons.append("analysis_revision_or_handoff_changed")
        if epic.analysis is None or epic.analysis["needs_reconciliation"] or not epic.approval["valid"] or epic.metadata["status"] not in ("functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES):
            reasons.append("upstream_requires_reconciliation")
    if latest and latest["action"] == "approve" and not integrity_errors and epic.analysis is not None:
        _, frozen = read_baseline(epic.directory, latest["baseline_id"], loader)
        if not current_inputs_match(epic, loader, frozen):
            reasons.append("supporting_artifacts_changed")
    if integrity_errors:
        reasons.append("baseline_integrity_failure")
    advanced = next((e for e in reversed(epic.metadata.get("lifecycle", [])) if e["action"] == "analysis_advance"), None) if epic.metadata["status"] in ("ready_for_technical_design", *ENGINEERING_STAGES) else None
    if advanced and (latest is None or latest["id"] != advanced["approval_id"]):
        reasons.append("advancement_approval_mismatch")
    valid = latest is not None and latest["action"] == "approve" and not reasons
    return {"status": "valid" if valid else "invalid" if integrity_errors else "none" if latest is None else "changes_requested" if latest["action"] == "request_changes" else "stale",
            "valid": valid, "reasons": reasons, "latest_decision": latest,
            "can_advance": valid and epic.metadata["status"] == "functional_analysis",
            "technical_design_input": {"approval_id": advanced["approval_id"], "baseline_id": advanced["baseline_id"]} if advanced else None}
