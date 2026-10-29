"""Epic-local business draft validation, immutable revision history and recovery."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import yaml

from engineering_contract import STAGES as ENGINEERING_STAGES, TRANSITIONS
import discovery_history as discovery
import artifact_templates as templates


class BusinessError(Exception):
    def __init__(self, code: str, message: str, filename: str = "business.md"):
        self.code, self.filename = code, filename
        super().__init__(message)


def require(condition, code, message, filename="business.md"):
    if not condition:
        raise BusinessError(code, message, filename)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def valid_person(value):
    return discovery.text(value) and not any(ord(char) < 32 for char in value)


def validate_lifecycle(events, status, allow_advance=False, allow_analysis=False, allow_analysis_approval=False, allow_engineering=False):
    require(isinstance(events, list) and bool(events), "E_LIFECYCLE", "Lifecycle events must be a nonempty list.", "metadata.yaml")
    current, ids = "discovery", set()
    for index, event in enumerate(events):
        if isinstance(event, dict) and event.get("action") == "engineer" and allow_engineering:
            fields = {"id","action","from","to","base_revision","actor","decision","timestamp","baseline_id"}
            require(set(event) - {"identity_source"} == fields and event["from"] == current and event["to"] in TRANSITIONS.get(current, ()), "E_LIFECYCLE", "Invalid sequential engineering transition.", "metadata.yaml")
            require(discovery.valid_operation_id(event["id"]) and event["id"] not in ids and discovery.valid_revision(event["base_revision"]) and discovery.valid_revision(event["baseline_id"]) and all(valid_person(event[k]) for k in ("actor","timestamp")) and discovery.text(event["decision"]) and all(ord(c)>=32 or c in "\n\r\t" for c in event["decision"]), "E_LIFECYCLE", "Invalid engineering transition evidence.", "metadata.yaml")
            from local_identity import validate_source
            validate_source(event,"E_LIFECYCLE")
            ids.add(event["id"]); current=event["to"]
            continue
        fields = {"id", "action", "from", "to", "base_revision", "actor", "decision", "timestamp"}
        if isinstance(event, dict) and event.get("action") in (("advance", "analyze") if allow_analysis else ("advance",)) and allow_advance:
            fields |= {"review_revision", "business_revision", "approval_id", "baseline_id"}
            if event["action"] == "analyze":
                fields |= {"handoff_id"}
        if isinstance(event, dict) and event.get("action") == "analysis_advance" and allow_analysis_approval:
            fields |= {"review_revision", "analysis_revision", "analysis_operation_id", "approval_id", "baseline_id", "business_baseline_id", "business_approval_id", "business_handoff_id"}
        if isinstance(event, dict) and "identity_source" in event:
            from local_identity import validate_source
            validate_source(event, "E_LIFECYCLE")
            fields |= {"identity_source"}
        require(isinstance(event, dict) and set(event) == fields, "E_LIFECYCLE", "Invalid lifecycle event fields.", "metadata.yaml")
        action = event["action"]
        require(action in (("complete", "reopen", "refine", "advance", "analyze", "analysis_advance") if allow_analysis_approval else ("complete", "reopen", "refine", "advance", "analyze") if allow_analysis else ("complete", "reopen", "refine", "advance") if allow_advance else ("complete", "reopen", "refine")), "E_LIFECYCLE", "Unknown lifecycle action.", "metadata.yaml")
        target = {"complete": "ready_for_refinement", "reopen": "discovery", "refine": "business_refinement", "advance": "ready_for_analysis", "analyze": "functional_analysis", "analysis_advance": "ready_for_technical_design"}[action]
        allowed = {"complete": ("discovery",), "reopen": ("ready_for_refinement", "business_refinement", "ready_for_analysis", "functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES) if allow_analysis_approval else ("ready_for_refinement", "business_refinement", "ready_for_analysis", "functional_analysis") if allow_analysis else ("ready_for_refinement", "business_refinement", "ready_for_analysis") if allow_advance else ("ready_for_refinement", "business_refinement"), "refine": ("ready_for_refinement",), "advance": ("business_refinement",), "analyze": ("ready_for_analysis",), "analysis_advance": ("functional_analysis",)}[action]
        if action == "reopen" and allow_engineering:
            allowed = (*allowed, *ENGINEERING_STAGES)
        require(event["from"] == current and current in allowed and event["to"] == target, "E_LIFECYCLE", "Invalid lifecycle transition chain.", "metadata.yaml")
        require(discovery.valid_operation_id(event["id"]) and event["id"] not in ids, "E_LIFECYCLE", "Invalid or duplicate lifecycle operation ID.", "metadata.yaml")
        require(discovery.valid_revision(event["base_revision"]) and valid_person(event["actor"]) and valid_person(event["decision"]) and valid_person(event["timestamp"]), "E_LIFECYCLE", "Invalid lifecycle evidence.", "metadata.yaml")
        if action in ("advance", "analyze"):
            require(all(discovery.valid_revision(event[key]) for key in ("review_revision", "business_revision", "baseline_id")) and isinstance(event["approval_id"], str) and re.fullmatch(r"BD-[0-9]{4,}", event["approval_id"]), "E_LIFECYCLE", "Invalid approval reference in advancement.", "metadata.yaml")
        if action == "analyze":
            require(discovery.valid_operation_id(event["handoff_id"]) and index > 0 and events[index - 1]["id"] == event["handoff_id"] and events[index - 1]["action"] == "advance" and all(events[index - 1][key] == event[key] for key in ("approval_id", "baseline_id", "business_revision")), "E_LIFECYCLE", "Analysis must reference its business handoff.", "metadata.yaml")
        if action == "analysis_advance":
            require(all(discovery.valid_revision(event[k]) for k in ("review_revision", "analysis_revision", "baseline_id", "business_baseline_id")) and all(discovery.valid_operation_id(event[k]) for k in ("analysis_operation_id", "business_handoff_id")) and isinstance(event["approval_id"], str) and re.fullmatch(r"AD-[0-9]{4,}", event["approval_id"]) and isinstance(event["business_approval_id"], str) and re.fullmatch(r"BD-[0-9]{4,}", event["business_approval_id"]), "E_LIFECYCLE", "Invalid Analysis advancement references.", "metadata.yaml")
            handoff = next((e for e in reversed(events[:index]) if e["action"] == "advance"), None)
            require(handoff is not None and handoff["id"] == event["business_handoff_id"] and handoff["baseline_id"] == event["business_baseline_id"] and handoff["approval_id"] == event["business_approval_id"], "E_LIFECYCLE", "Analysis advancement must retain its active business handoff.", "metadata.yaml")
        ids.add(event["id"])
        current = target
    require(current == status, "E_LIFECYCLE", "Lifecycle events do not match current status.", "metadata.yaml")


def confirmation_origins(state):
    """Link only currently effective human confirmations to their AI assumptions."""
    return {item["resolution_id"]: item["id"] for item in state["assumptions"] if item["status"] == "confirmed"}


def source_sets(document, state):
    if document is None or state is None:
        return set(), set(), set()
    records = {r["id"]: r for op in document["operations"] for r in op["records"]}
    superseded = set(state["superseded_by"])
    confirmed = {
        rid for rid, record in records.items()
        if rid not in superseded and (
            record["kind"] == "user_statement"
            or record["kind"] == "human_decision" and record["action"] in ("decide", "answer", "correct")
        )
    }
    confirmations = confirmation_origins(state)
    confirmed.update(confirmations.values())
    confirmed.update(confirmations)
    unresolved = {item["id"] for item in state["questions"] if item["status"] in ("open", "unknown", "deferred")}
    proposed = {item["id"] for item in state["assumptions"] if item["status"] == "proposed"}
    return confirmed, unresolved, proposed


ITEM = re.compile(r"^- \*\*([BUP]-[0-9]{3,})\*\* \[([A-Za-z0-9, -]+)\] (\S.*)$")
REF = re.compile(r"D-[0-9]{4,}\Z")
CATEGORIES = {"Confirmed information": "B", "Unresolved issues": "U", "Unconfirmed proposals": "P"}


def validate_markdown(content: bytes, epic_id: str, source_revision: str, document, state):
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise BusinessError("E_BUSINESS_DOCUMENT", str(exc)) from exc
    require(bool(text.strip()) and "\x00" not in text, "E_BUSINESS_DOCUMENT", "Business document must be nonempty UTF-8 text.")
    lines = text.splitlines()
    require(len(lines) >= 5 and lines[0] == f"# Business Refinement — {epic_id}" and lines[2] == f"Source revision: {source_revision}", "E_BUSINESS_DOCUMENT", "Expected title and exact source revision header.")
    allowed = dict(zip(CATEGORIES.values(), source_sets(document, state)))
    confirmations = confirmation_origins(state) if state is not None else {}
    # A confirmation is alternative evidence for its assumption, not a new
    # requirement that would invalidate existing assumption-only documents.
    required = {**allowed, "B": allowed["B"] - confirmations.keys()}
    seen_categories, seen_ids, covered = [], set(), {"B": set(), "U": set(), "P": set()}
    category = None
    for line in lines[3:]:
        if not line.strip():
            continue
        if line.startswith("## "):
            name = line[3:]
            require(name in CATEGORIES and name not in seen_categories, "E_BUSINESS_DOCUMENT", "Unexpected or duplicate section heading.")
            seen_categories.append(name)
            category = CATEGORIES[name]
        elif line.startswith("### "):
            require(category == "B" and bool(line[4:].strip()), "E_BUSINESS_DOCUMENT", "Subheadings belong under Confirmed information.")
        elif line == "None recorded.":
            require(category in ("U", "P") and not required[category], "E_BUSINESS_DOCUMENT", "None recorded conflicts with source records.")
        else:
            match = ITEM.fullmatch(line)
            require(category is not None and match is not None, "E_BUSINESS_DOCUMENT", "Content must be a sourced ID item, heading or empty-section marker.")
            item_id, refs_text, _ = match.groups()
            require(item_id[0] == category and item_id not in seen_ids, "E_BUSINESS_DOCUMENT", "Duplicate or misplaced business item ID.")
            refs = [value.strip() for value in refs_text.split(",")]
            require(bool(refs) and len(set(refs)) == len(refs) and all(REF.fullmatch(value) for value in refs), "E_BUSINESS_REFERENCE", "Each item needs unique Discovery record IDs.")
            require(set(refs) <= allowed[category], "E_BUSINESS_PROVENANCE", "Item cites a missing, superseded or incorrectly classified Discovery record.")
            seen_ids.add(item_id)
            covered[category].update(refs)
            if category == "B":
                covered[category].update(confirmations[ref] for ref in refs if ref in confirmations)
    require(seen_categories == list(CATEGORIES), "E_BUSINESS_DOCUMENT", "Expected Confirmed information, Unresolved issues and Unconfirmed proposals in order.")
    for key in required:
        require(required[key] <= covered[key], "E_BUSINESS_COVERAGE", f"All current {key} Discovery records must be represented.")
    require(any(value.startswith("B-") for value in seen_ids), "E_BUSINESS_DOCUMENT", "At least one confirmed business item is required.")
    return {"confirmed_ids": sorted(v for v in seen_ids if v.startswith("B-")), "unresolved_ids": sorted(v for v in seen_ids if v.startswith("U-")), "proposal_ids": sorted(v for v in seen_ids if v.startswith("P-"))}


def empty(epic_id):
    return {"schema_version": "0.1", "request_id": epic_id, "revisions": []}


def decode_revision(entry):
    try:
        content = base64.b64decode(entry["content_base64"], validate=True)
    except (KeyError, ValueError, TypeError, binascii.Error) as exc:
        raise BusinessError("E_BUSINESS_HISTORY", "Invalid encoded historical document.", "business-history.yaml") from exc
    require(digest(content) == entry["digest"], "E_BUSINESS_HISTORY", "Historical content does not match its SHA-256 digest.", "business-history.yaml")
    return content


def validate_history(data, epic_id):
    filename = "business-history.yaml"
    require(isinstance(data, dict) and set(data) == {"schema_version", "request_id", "revisions"} and data["schema_version"] in ("0.1","0.2") and data["request_id"] == epic_id and isinstance(data["revisions"], list) and bool(data["revisions"]), "E_BUSINESS_HISTORY", "Invalid business history root.", filename)
    previous, ids = None, set()
    for entry in data["revisions"]:
        fields = {"digest", "previous", "source_revision", "editor", "reason", "timestamp", "operation_id", "base_revision", "content_base64", "mode"}
        if isinstance(entry,dict) and "schema_version" in entry:
            require(data["schema_version"]=="0.2" and entry["schema_version"]=="0.2", "E_BUSINESS_HISTORY", "Invalid revision envelope version.",filename)
            fields |= {"schema_version","template"}
            templates.validate_pin(entry.get("template"),"business")
        require(isinstance(entry, dict) and set(entry) == fields, "E_BUSINESS_HISTORY", "Invalid revision entry fields.", filename)
        require(entry["previous"] == previous and entry["base_revision"] == previous, "E_BUSINESS_HISTORY", "Broken previous revision chain.", filename)
        require(discovery.valid_revision(entry["digest"]) and discovery.valid_revision(entry["source_revision"]), "E_BUSINESS_HISTORY", "Invalid revision digest.", filename)
        require(valid_person(entry["editor"]) and valid_person(entry["reason"]) and valid_person(entry["timestamp"]), "E_BUSINESS_HISTORY", "Missing revision attribution.", filename)
        require(discovery.valid_operation_id(entry["operation_id"]) and entry["operation_id"] not in ids and entry["mode"] in ("generate", "revise"), "E_BUSINESS_HISTORY", "Invalid revision operation.", filename)
        decode_revision(entry)
        ids.add(entry["operation_id"])
        previous = entry["digest"]


def read(directory: Path, metadata, source_document, source_state, source_revision):
    journal = directory / ".business-transaction.json"
    require(not journal.exists() and not journal.is_symlink(), "E_BUSINESS_RECOVERY", "Interrupted business publication; run business-recover after inspecting it.", journal.name)
    path, ledger_path = directory / "business.md", directory / "business-history.yaml"
    for file in (path, ledger_path):
        require(not file.is_symlink() and (not file.exists() or file.is_file()), "E_BUSINESS_FILE", "Expected regular nonsymlink business artifact.", file.name)
    if not path.exists() and not ledger_path.exists():
        require(metadata.get("status") != "business_refinement", "E_BUSINESS_HISTORY", "Business refinement requires a draft and history.", ledger_path.name)
        return None
    require(path.exists() and ledger_path.exists(), "E_BUSINESS_HISTORY", "Business draft and history must both exist.", ledger_path.name)
    try:
        from sdlc import StrictLoader
        data = yaml.load(ledger_path.read_text(encoding="utf-8"), Loader=StrictLoader)
        content = path.read_bytes()
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise BusinessError("E_BUSINESS_HISTORY", str(exc), ledger_path.name) from exc
    validate_history(data, metadata["id"])
    latest = data["revisions"][-1]
    require(content == decode_revision(latest), "E_BUSINESS_MISMATCH", "Current business.md differs from the latest recorded revision.", path.name)
    current = latest["source_revision"] == source_revision and metadata["status"] in ("business_refinement", "ready_for_analysis", "functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES)
    if current:
        validate_markdown(content, metadata["id"], source_revision, source_document, source_state)
    try:
        readable = content.decode("utf-8")
    except UnicodeError as exc:
        raise BusinessError("E_BUSINESS_DOCUMENT", str(exc), path.name) from exc
    return {"content": readable, "revision": latest["digest"], "source_revision": latest["source_revision"], "needs_reconciliation": not current, "history": [{key: value for key, value in item.items() if key != "content_base64"} for item in data["revisions"]]}


def atomic_bytes(path: Path, content: bytes):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}-", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            if path.exists():
                os.fchmod(stream.fileno(), path.stat().st_mode & 0o777)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def publish(directory: Path, files: dict[str, bytes], *, analysis=False):
    """Journal a small Epic-local multi-file write; readers reject an unfinished transaction."""
    journal = directory / (".analysis-transaction.json" if analysis else ".business-transaction.json")
    before = {}
    for name in files:
        path = directory / name
        require(not path.is_symlink() and (not path.exists() or path.is_file()), "E_BUSINESS_FILE", "Refusing to replace a nonregular artifact.", name)
        before[name] = digest(path.read_bytes()) if path.exists() else None
    entry = {"before": before, "after": {name: base64.b64encode(value).decode("ascii") for name, value in files.items()}}
    try:
        with journal.open("x", encoding="utf-8") as stream:
            json.dump(entry, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except BaseException:
        if journal.exists():
            journal.unlink()
        raise
    try:
        recover(directory, analysis=True) if analysis else recover(directory)
    except (OSError, BusinessError) as exc:
        raise BusinessError("E_WRITE_UNCERTAIN", "Publication may be partial; inspect and run " + ("analysis-recover." if analysis else "business-recover."), journal.name) from exc


def recover(directory: Path, *, analysis=False):
    journal = directory / (".analysis-transaction.json" if analysis else ".business-transaction.json")
    recovery_code = "E_ANALYSIS_RECOVERY" if analysis else "E_BUSINESS_RECOVERY"
    allowed_files = {"metadata.yaml", "specification.md", "analysis-history.yaml"} if analysis else {"metadata.yaml", "business.md", "business-history.yaml"}
    require(journal.is_file() and not journal.is_symlink(), recovery_code, "No regular transaction journal found.", journal.name)
    try:
        entry = json.loads(journal.read_text(encoding="utf-8"))
        require(isinstance(entry, dict) and set(entry) == {"before", "after"} and isinstance(entry["before"], dict) and isinstance(entry["after"], dict) and set(entry["before"]) == set(entry["after"]) and bool(entry["after"]) and set(entry["after"]) <= allowed_files, recovery_code, "Malformed transaction journal.", journal.name)
        after = {name: base64.b64decode(value, validate=True) for name, value in entry["after"].items()}
        for name, content in after.items():
            path = directory / name
            require(not path.is_symlink() and (not path.exists() or path.is_file()), recovery_code, "Artifact path changed type.", name)
            current = digest(path.read_bytes()) if path.exists() else None
            require(current in (entry["before"][name], digest(content)), recovery_code, "Artifact changed outside the interrupted transaction.", name)
        for name, content in after.items():
            if not (directory / name).exists() or (directory / name).read_bytes() != content:
                atomic_bytes(directory / name, content)
        journal.unlink()
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, UnicodeError, ValueError, TypeError, binascii.Error) as exc:
        raise BusinessError(recovery_code, str(exc), journal.name) from exc


def append(data, epic_id, content: bytes, source_revision, editor, reason, operation_id, mode, template=None):
    candidate = {"schema_version": data["schema_version"], "request_id": epic_id, "revisions": list(data["revisions"])} if data else empty(epic_id)
    previous = candidate["revisions"][-1]["digest"] if candidate["revisions"] else None
    candidate["revisions"].append({"digest": digest(content), "previous": previous, "source_revision": source_revision, "editor": editor, "reason": reason, "timestamp": timestamp(), "operation_id": operation_id, "base_revision": previous, "content_base64": base64.b64encode(content).decode("ascii"), "mode": mode})
    if template is not None:
        candidate["schema_version"]="0.2"
        candidate["revisions"][-1].update(schema_version="0.2",template=template)
    validate_history(candidate, epic_id)
    return candidate
