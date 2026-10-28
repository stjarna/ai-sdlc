"""Procedural business decisions and immutable Epic-local input baselines."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

import yaml

import business_refinement as business
import discovery_history as discovery


BASELINE_FILES = ("metadata.yaml", "idea.md", "discovery.yaml", "business.md", "business-history.yaml")
DECISION_FIELDS = {"id", "operation_id", "action", "actor", "reason", "decision", "timestamp", "review_revision", "business_revision", "business_operation_id", "source_revision", "discovery_completion_id", "acknowledged_open_items", "baseline_id"}
MANIFEST_FIELDS = {"schema_version", "request_id", "business_revision", "business_operation_id", "source_revision", "discovery_completion_id", "idea_reference", "files"}


def require(condition, message, code="E_BUSINESS_DECISIONS", filename="metadata.yaml"):
    business.require(condition, code, message, filename)


def valid_timestamp(value):
    try:
        return isinstance(value, str) and value.endswith("Z") and datetime.fromisoformat(value[:-1] + "+00:00").utcoffset().total_seconds() == 0
    except (ValueError, TypeError, AttributeError):
        return False


def completion_id(metadata):
    return next((event["id"] for event in reversed(metadata.get("lifecycle", [])) if event["action"] == "complete"), None)


def context(metadata, draft):
    return {"business_revision": draft["revision"], "business_operation_id": draft["history"][-1]["operation_id"], "source_revision": draft["source_revision"], "discovery_completion_id": completion_id(metadata)}


def open_items(draft):
    if draft is None:
        return []
    return [{"id": match[1], "sources": [ref.strip() for ref in match[2].split(",")], "text": match[3]} for line in draft["content"].splitlines() if (match := business.ITEM.fullmatch(line)) and match[1].startswith(("U-", "P-"))]


def validate_decisions(metadata):
    entries = metadata.get("business_decisions")
    require(isinstance(entries, list), "business_decisions must be an append-only list.")
    operations, decisions = set(), {}
    completions = {event["id"] for event in metadata["lifecycle"] if event["action"] == "complete"}
    for index, entry in enumerate(entries, 1):
        require(isinstance(entry, dict) and set(entry) == DECISION_FIELDS, "Invalid business decision fields.")
        require(entry["id"] == f"BD-{index:04d}", "Business decision IDs must be sequential.")
        require(discovery.valid_operation_id(entry["operation_id"]) and entry["operation_id"] not in operations, "Invalid or duplicate decision operation ID.")
        require(entry["action"] in ("approve", "request_changes"), "Unsupported business decision action.")
        require(all(business.valid_person(entry[key]) for key in ("actor", "reason", "decision")) and valid_timestamp(entry["timestamp"]), "Decision requires declared identity, reason, explicit text and UTC timestamp.")
        require(all(discovery.valid_revision(entry[key]) for key in ("review_revision", "business_revision", "source_revision")), "Invalid decision revision.")
        require(discovery.valid_operation_id(entry["business_operation_id"]) and entry["discovery_completion_id"] in completions, "Invalid business revision or Discovery completion reference.")
        acknowledged = entry["acknowledged_open_items"]
        require(isinstance(acknowledged, list) and all(isinstance(value, str) and re.fullmatch(r"[UP]-[0-9]{3,}", value) for value in acknowledged) and len(set(acknowledged)) == len(acknowledged), "Invalid unresolved-item acknowledgements.")
        if entry["action"] == "approve":
            require(discovery.valid_revision(entry["baseline_id"]), "An approval requires an immutable baseline ID.")
        else:
            require(entry["baseline_id"] is None and not acknowledged, "Request changes cannot create a baseline or acknowledge approval risks.")
        operations.add(entry["operation_id"])
        decisions[entry["id"]] = entry
    for event in metadata["lifecycle"]:
        if event["action"] == "advance":
            require(event["id"] not in operations, "Gate operation ID was reused by advancement.")
            operations.add(event["id"])
            selected = decisions.get(event["approval_id"])
            require(selected is not None and selected["action"] == "approve" and selected["baseline_id"] == event["baseline_id"] and selected["business_revision"] == event["business_revision"], "Advancement must reference its approval and baseline.")


def read_snapshot(directory: Path, metadata):
    """Fixed artifact roles; the original idea may have a different local path."""
    files = {}
    for name in BASELINE_FILES:
        path = directory / (metadata["artifacts"]["idea"] if name == "idea.md" else name)
        files[name] = path.read_bytes() if path.exists() else None
    return files


def review_revision(files):
    fingerprints = [business.digest(files[name]) if files[name] is not None else None for name in BASELINE_FILES]
    return business.digest(json.dumps(fingerprints).encode("utf-8"))


def manifest_for(metadata, draft, files):
    require(all(files.get(name) is not None for name in BASELINE_FILES), "Approval requires all supporting artifacts.", "E_BASELINE_CONTEXT")
    return {"schema_version": "0.1", "request_id": metadata["id"], **context(metadata, draft), "idea_reference": metadata["artifacts"]["idea"], "files": {name: business.digest(files[name]) for name in BASELINE_FILES}}


def canonical_manifest(manifest):
    return json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def validate_bundle(manifest, files, loader):
    require(isinstance(manifest, dict) and set(manifest) == MANIFEST_FIELDS and manifest["schema_version"] == "0.1", "Invalid baseline manifest.", "E_BASELINE_INTEGRITY")
    require(isinstance(manifest["files"], dict) and set(manifest["files"]) == set(BASELINE_FILES) and set(files) == set(BASELINE_FILES), "Unexpected baseline artifact set.", "E_BASELINE_INTEGRITY")
    require(all(discovery.valid_revision(value) for value in manifest["files"].values()), "Invalid baseline file digest.", "E_BASELINE_INTEGRITY")
    require(all(business.digest(files[name]) == expected for name, expected in manifest["files"].items()), "Baseline file hash mismatch.", "E_BASELINE_INTEGRITY")
    try:
        metadata = yaml.load(files["metadata.yaml"].decode("utf-8"), Loader=loader)
        document = yaml.load(files["discovery.yaml"].decode("utf-8"), Loader=loader)
        history = yaml.load(files["business-history.yaml"].decode("utf-8"), Loader=loader)
        require(isinstance(metadata, dict) and metadata.get("id") == manifest["request_id"] and metadata.get("status") == "business_refinement" and metadata.get("schema_version") in ("0.2", "0.3"), "Frozen metadata does not identify a refinement snapshot.", "E_BASELINE_CONTEXT")
        require(metadata.get("artifacts") == {"idea": manifest["idea_reference"]}, "Frozen idea reference mismatch.", "E_BASELINE_CONTEXT")
        business.validate_lifecycle(metadata["lifecycle"], metadata["status"], allow_advance=metadata["schema_version"] == "0.3")
        if metadata["schema_version"] == "0.3":
            validate_decisions(metadata)
        state = discovery.project(document, manifest["request_id"])
        business.validate_history(history, manifest["request_id"])
        latest = history["revisions"][-1]
        require(business.decode_revision(latest) == files["business.md"], "Frozen business history differs from the approved document.", "E_BASELINE_CONTEXT")
        source = business.digest(json.dumps([business.digest(files["idea.md"]), business.digest(files["discovery.yaml"])]).encode())
        require(source == manifest["source_revision"] == latest["source_revision"] and business.digest(files["business.md"]) == manifest["business_revision"] == latest["digest"] and latest["operation_id"] == manifest["business_operation_id"] and completion_id(metadata) == manifest["discovery_completion_id"], "Frozen business/source context mismatch.", "E_BASELINE_CONTEXT")
        business.validate_markdown(files["business.md"], manifest["request_id"], source, document, state)
    except (KeyError, TypeError, ValueError, UnicodeError, yaml.YAMLError, RecursionError, discovery.HistoryError, business.BusinessError) as exc:
        raise business.BusinessError("E_BASELINE_CONTEXT", f"Invalid frozen supporting context: {exc}") from exc


def read_baseline(directory: Path, baseline_id, loader):
    require(discovery.valid_revision(baseline_id), "Invalid baseline ID.", "E_BASELINE_INTEGRITY")
    root = directory / "business-baselines"
    path = root / baseline_id
    require(not root.is_symlink() and (not root.exists() or root.is_dir()), "Unsafe baseline root.", "E_BASELINE_INTEGRITY", "business-baselines")
    require(path.exists(), "Approved baseline is missing; restore it from a known-good copy.", "E_BASELINE_MISSING", f"business-baselines/{baseline_id}")
    require(path.is_dir() and not path.is_symlink(), "Baseline must be a nonsymlink directory.", "E_BASELINE_INTEGRITY", f"business-baselines/{baseline_id}")
    try:
        require({p.name for p in path.iterdir()} == set(BASELINE_FILES) | {"manifest.json"}, "Unexpected or missing baseline files.", "E_BASELINE_INTEGRITY")
        contents = {}
        for name in (*BASELINE_FILES, "manifest.json"):
            item = path / name
            require(item.is_file() and not item.is_symlink(), "Baseline files must be regular and nonsymlink.", "E_BASELINE_INTEGRITY", f"business-baselines/{baseline_id}/{name}")
            contents[name] = item.read_bytes()
        manifest = json.loads(contents.pop("manifest.json").decode("utf-8"))
        require(canonical_manifest(manifest) == (path / "manifest.json").read_bytes() and business.digest(canonical_manifest(manifest)) == baseline_id, "Baseline manifest identity mismatch.", "E_BASELINE_INTEGRITY")
        validate_bundle(manifest, contents, loader)
        return manifest, contents
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, business.BusinessError) as exc:
        if isinstance(exc, business.BusinessError) and exc.filename.startswith("business-baselines/"):
            raise
        code = exc.code if isinstance(exc, business.BusinessError) else "E_BASELINE_INTEGRITY"
        raise business.BusinessError(code, str(exc), f"business-baselines/{baseline_id}") from exc


def check_baselines(directory, metadata, draft, loader):
    errors = []
    revisions = {item["operation_id"]: item for item in draft["history"]} if draft else {}
    for index, entry in enumerate(metadata.get("business_decisions", [])):
        revision = revisions.get(entry["business_operation_id"])
        require(revision is not None and revision["digest"] == entry["business_revision"] and revision["source_revision"] == entry["source_revision"], "Decision no longer matches retained business history.")
        if entry["action"] != "approve":
            continue
        try:
            manifest, files = read_baseline(directory, entry["baseline_id"], loader)
            require(manifest["request_id"] == metadata["id"] and all(manifest[key] == entry[key] for key in ("business_revision", "business_operation_id", "source_revision", "discovery_completion_id")), "Approval does not match its baseline.", "E_BASELINE_CONTEXT")
            require(review_revision(files) == entry["review_revision"], "Approval review revision does not match its frozen context.", "E_BASELINE_CONTEXT")
            frozen_metadata = yaml.load(files["metadata.yaml"].decode("utf-8"), Loader=loader)
            require(frozen_metadata.get("business_decisions", []) == metadata["business_decisions"][:index] and frozen_metadata["lifecycle"] == metadata["lifecycle"][:len(frozen_metadata["lifecycle"])], "Retained audit history differs from the approved snapshot.", "E_BASELINE_CONTEXT")
            frozen_draft = {"content": files["business.md"].decode("utf-8")}
            require(set(entry["acknowledged_open_items"]) == {item["id"] for item in open_items(frozen_draft)}, "Approval acknowledgements do not match frozen unresolved items.", "E_BASELINE_CONTEXT")
        except business.BusinessError as exc:
            if not exc.filename.startswith("business-baselines"):
                exc.filename = f"business-baselines/{entry['baseline_id']}"
            errors.append(exc)
    return errors


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_baseline(directory, metadata, draft, files, loader):
    manifest = manifest_for(metadata, draft, files)
    validate_bundle(manifest, files, loader)
    encoded = canonical_manifest(manifest)
    baseline_id = business.digest(encoded)
    root = directory / "business-baselines"
    require(not root.is_symlink() and (not root.exists() or root.is_dir()), "Unsafe baseline root.", "E_BASELINE_INTEGRITY", root.name)
    temporary = None
    try:
        if not root.exists():
            root.mkdir(mode=0o700)
            fsync_directory(directory)
        final = root / baseline_id
        if final.exists() or final.is_symlink():
            read_baseline(directory, baseline_id, loader)
            # A retained orphan may come from a prior directory-fsync failure.
            fsync_directory(root)
            fsync_directory(directory)
            return baseline_id
        temporary = Path(tempfile.mkdtemp(prefix=".pending-", dir=root))
        for name, content in {**files, "manifest.json": encoded}.items():
            with (temporary / name).open("xb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        fsync_directory(temporary)
        os.rename(temporary, final)
        fsync_directory(root)
        fsync_directory(directory)
        read_baseline(directory, baseline_id, loader)
        return baseline_id
    except OSError as exc:
        raise business.BusinessError("E_BASELINE_WRITE", "Baseline preparation failed; no approval was published. Inspect retained temporary/orphan baselines and retry the same operation.", root.name) from exc
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def evaluate(metadata, draft, source_revision, integrity_errors):
    decisions = metadata.get("business_decisions", [])
    latest = decisions[-1] if decisions else None
    reasons = []
    if latest is None:
        reasons.append("no_approval")
    elif latest["action"] != "approve":
        reasons.append("changes_requested")
    else:
        if draft is None or latest["business_revision"] != draft["revision"] or latest["business_operation_id"] != draft["history"][-1]["operation_id"]:
            reasons.append("business_revision_changed")
        if latest["source_revision"] != source_revision or draft is None or draft["source_revision"] != source_revision:
            reasons.append("source_revision_changed")
        if latest["discovery_completion_id"] != completion_id(metadata):
            reasons.append("discovery_completion_changed")
        if metadata["status"] not in ("business_refinement", "ready_for_analysis"):
            reasons.append("discovery_requires_reconciliation")
    if integrity_errors:
        reasons.append("baseline_integrity_failure")
    valid = latest is not None and latest["action"] == "approve" and not reasons
    status = "valid" if valid else "invalid" if integrity_errors else "none" if latest is None else "changes_requested" if latest["action"] == "request_changes" else "stale"
    advanced = next((event for event in reversed(metadata.get("lifecycle", [])) if event["action"] == "advance"), None) if metadata["status"] == "ready_for_analysis" else None
    if advanced and (latest is None or latest["id"] != advanced["approval_id"]):
        reasons.append("advancement_approval_mismatch")
        valid, status = False, "invalid"
    return {"status": status, "valid": valid, "reasons": reasons, "latest_decision": latest, "can_advance": valid and metadata["status"] == "business_refinement", "analysis_input": {"approval_id": advanced["approval_id"], "baseline_id": advanced["baseline_id"]} if advanced else None}
