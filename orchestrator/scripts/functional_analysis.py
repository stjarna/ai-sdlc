"""Epic-local functional specification contracts; semantic drafting belongs to the skill."""
from __future__ import annotations

import base64
import binascii
import json
import re

import yaml

from engineering_contract import STAGES as ENGINEERING_STAGES
import business_refinement as business
import business_approval as approval
import discovery_history as discovery
import artifact_templates as templates

FILES = ("specification.md", "analysis-history.yaml")
JOURNAL = ".analysis-transaction.json"
SECTIONS = {"Functional requirements": "FR", "Use cases": "UC", "Business rules": "BR", "Acceptance criteria": "AC", "Business coverage": "coverage", "Inherited unresolved items": "inherited", "Analysis questions": "AQ", "Analysis proposals": "AP"}
COMMON = {"Business sources", "Discovery evidence", "Status"}
FIELDS = {
    "FR": COMMON | {"Questions", "Statement"},
    "BR": COMMON | {"Requirements", "Questions", "Statement"},
    "UC": COMMON | {"Requirements", "Questions", "Actor", "Preconditions", "Trigger", "Main flow", "Alternative flows", "Outcome"},
    "AC": COMMON | {"Requirements", "Questions", "Given", "When", "Then"},
    "AQ": COMMON | {"Affected items", "Statement"},
    "AP": COMMON | {"Affected items", "Statement"},
}
IDENTIFIER = re.compile(r"(?:FR|UC|BR|AC|AQ|AP)-[0-9]{3,}\Z")
HEADING = re.compile(r"### ((?:FR|UC|BR|AC|AQ|AP)-[0-9]{3,}) — (\S.*)\Z")
COVERAGE = re.compile(r"- \*\*(B-[0-9]{3,})\*\* \[(elaborated|contextual|excluded|unresolved)\] ([A-Z0-9, -]+) \| (\S.*)\Z")


def require(condition, message, code="E_ANALYSIS_DOCUMENT", filename="specification.md"):
    business.require(condition, code, message, filename)


def references(text):
    if text == "-":
        return []
    values = text.split(", ")
    require(len(values) == len(set(values)) and all(re.fullmatch(r"(?:B|D|FR|UC|BR|AC|AQ|AP)-[0-9]{3,}", v) for v in values), "References must be unique comma-space separated IDs or '-'.", "E_ANALYSIS_REFERENCE")
    return values


def handoff(metadata):
    if metadata["status"] not in ("ready_for_analysis", "functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES):
        return None
    return next((event for event in reversed(metadata["lifecycle"]) if event["action"] == "advance"), None)


def binding(event):
    return {"baseline_id": event["baseline_id"], "approval_id": event["approval_id"], "handoff_id": event["id"]}


def approved_input(epic, loader):
    event = handoff(epic.metadata)
    require(event is not None and epic.approval and epic.approval["valid"], "A current approved business advancement is required.", "E_ANALYSIS_INPUT")
    manifest, files = approval.read_baseline(epic.directory, event["baseline_id"], loader)
    require(manifest["business_revision"] == event["business_revision"], "Business handoff differs from its baseline.", "E_ANALYSIS_INPUT")
    return {**binding(event), "manifest": manifest, "business": files["business.md"].decode("utf-8"), "discovery": yaml.load(files["discovery.yaml"].decode("utf-8"), Loader=loader)}


def baseline_items(source):
    return {m[1]: {"refs": [ref.strip() for ref in m[2].split(",")], "text": m[3], "line": line} for line in source["business"].splitlines() if (m := business.ITEM.fullmatch(line))}


def validate_document(content, epic_id, source):
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise business.BusinessError("E_ANALYSIS_DOCUMENT", str(exc), FILES[0]) from exc
    require("\x00" not in text, "NUL is not allowed.")
    lines = text.splitlines()
    header = [f"# Functional Analysis — {epic_id}", "", f"Baseline: {source['baseline_id']}", f"Approval: {source['approval_id']}", f"Handoff: {source['handoff_id']}"]
    require(lines[:5] == header, "Expected exact request, baseline, approval and handoff header.", "E_ANALYSIS_INPUT")
    items, coverage, inherited, sections = {}, {}, [], []
    section, item, field = None, None, None
    empty_sections = set()
    for line in lines[5:]:
        if not line.strip():
            continue
        if line.startswith("## "):
            name = line[3:]
            require(name in SECTIONS and name not in sections, "Unknown or duplicate section.")
            sections.append(name)
            section, item, field = SECTIONS[name], None, None
        elif (m := HEADING.fullmatch(line)):
            rid, title = m.groups()
            require(rid.split('-')[0] == section and rid not in items and section not in empty_sections, "Duplicate or misplaced item ID.")
            item = {"id": rid, "title": title, "fields": {}}
            items[rid], field = item, None
        elif line == "None recorded.":
            require(section in ("BR", "AQ", "AP", "inherited") and item is None and section not in empty_sections and not (section == "inherited" and inherited), "Unexpected empty-section marker.")
            empty_sections.add(section)
        elif section == "coverage":
            m = COVERAGE.fullmatch(line)
            require(m is not None and m[1] not in coverage, "Expected one coverage disposition per business item.", "E_ANALYSIS_COVERAGE")
            coverage[m[1]] = {"disposition": m[2], "items": references(m[3]), "reason": m[4]}
        elif section == "inherited":
            require(section not in empty_sections and business.ITEM.fullmatch(line) is not None, "Expected exact inherited business issue/proposal.", "E_ANALYSIS_UNRESOLVED")
            inherited.append(line)
        elif line.startswith("  "):
            require(item is not None and field is not None, "Unexpected field continuation.")
            item["fields"][field] += "\n" + line[2:]
        else:
            key, separator, value = line.partition(": ")
            require(item is not None and separator and key in FIELDS[section] and key not in item["fields"] and bool(value.strip()), "Unknown, duplicate or empty item field.")
            item["fields"][key], field = value, key
    require(sections == list(SECTIONS), "Expected all specification sections in order.")
    frozen = baseline_items(source)
    bitems = {k: v for k, v in frozen.items() if k.startswith("B-")}
    require(set(coverage) == set(bitems), "Every approved business item requires an explicit coverage disposition.", "E_ANALYSIS_COVERAGE")
    expected_inherited = [v["line"] for k, v in frozen.items() if not k.startswith("B-")]
    require(len(inherited) == len(expected_inherited) and set(inherited) == set(expected_inherited), "Inherited unresolved issues and proposals must remain unchanged.", "E_ANALYSIS_UNRESOLVED")
    discovery_ids = {r["id"] for op in source["discovery"]["operations"] for r in op["records"]}
    state = discovery.project(source["discovery"], epic_id)
    origins = business.confirmation_origins(state)
    unresolved_questions = {q["id"]: q["status"] for q in state["questions"] if q["status"] != "answered"}
    normative = {"FR", "UC", "BR", "AC"}
    for rid, item in items.items():
        kind, f = rid.split('-')[0], item["fields"]
        require(set(f) == FIELDS[kind], f"Missing fields for {rid}.")
        statuses = ("open", "unknown", "deferred", "retired") if kind == "AQ" else ("proposed", "rejected", "retired") if kind == "AP" else ("specified", "blocked", "proposed", "retired")
        require(f["Status"] in statuses, f"Invalid status for {rid}.")
        bs, ds = references(f["Business sources"]), references(f["Discovery evidence"])
        require(set(bs) <= set(bitems) and set(ds) <= discovery_ids, f"Unknown frozen business/Discovery source for {rid}.", "E_ANALYSIS_REFERENCE")
        if kind == "AQ":
            inherited_states = {unresolved_questions[d] for d in ds if d in unresolved_questions}
            require(not inherited_states or f["Status"] != "retired", "An inherited business question cannot be retired in Analysis.", "E_ANALYSIS_UNRESOLVED")
            require("deferred" not in inherited_states or f["Status"] == "deferred", "Inherited deferred business questions remain deferred.", "E_ANALYSIS_UNRESOLVED")
        if kind in normative and f["Status"] != "retired":
            supported = set().union(*(set(bitems[b]["refs"]) for b in bs))
            for confirmation, origin in origins.items():
                if confirmation in supported or origin in supported:
                    supported.update((confirmation, origin))
            require(bool(bs) and bool(ds) and set(ds) <= supported, f"{rid} must trace through its approved business sources.", "E_ANALYSIS_PROVENANCE")
        for key in ("Requirements", "Questions", "Affected items"):
            if key not in f:
                continue
            refs = references(f[key])
            require(set(refs) <= set(items), f"Dangling {key} reference in {rid}.", "E_ANALYSIS_REFERENCE")
            if key == "Requirements":
                require(all(r.startswith("FR-") for r in refs) and (bool(refs) or f["Status"] == "retired"), f"{rid} requires FR references.", "E_ANALYSIS_REFERENCE")
                if f["Status"] == "specified":
                    require(all(items[r]["fields"].get("Status") == "specified" for r in refs), "Specified items cannot depend on blocked/proposed requirements.", "E_ANALYSIS_UNRESOLVED")
            if key == "Requirements" and f["Status"] == "specified":
                parent_sources = set().union(*(set(references(items[r]["fields"].get("Business sources", "-"))) for r in refs))
                require(set(bs) <= parent_sources, "Requirement-dependent items must preserve supporting business traceability.", "E_ANALYSIS_PROVENANCE")
            if key == "Questions":
                require(all(r.startswith("AQ-") for r in refs), "Questions must reference AQ items.", "E_ANALYSIS_REFERENCE")
                active = [r for r in refs if items[r]["fields"].get("Status") != "retired"]
                require(f["Status"] != "specified" or not active, "An item with unresolved dependencies cannot be specified.", "E_ANALYSIS_UNRESOLVED")
                require(f["Status"] != "blocked" or bool(active), "Blocked items must identify an unresolved analysis question.", "E_ANALYSIS_UNRESOLVED")
        if kind == "UC":
            steps = f["Main flow"].splitlines()
            require(all(step.startswith(f"{n}. ") and bool(step[len(str(n))+2:].strip()) for n, step in enumerate(steps, 1)), "Main flow requires consecutively numbered steps.")
    require(any(k.startswith("FR-") for k in items) and any(k.startswith("UC-") for k in items), "A specification requires functional requirements and a use case.")
    for rid, item in items.items():
        if rid.startswith("FR-") and item["fields"]["Status"] == "specified":
            require(any(k.startswith("AC-") and v["fields"]["Status"] == "specified" and rid in references(v["fields"]["Requirements"]) for k, v in items.items()), f"{rid} lacks a specified acceptance criterion.", "E_ANALYSIS_COVERAGE")
    for bid, value in coverage.items():
        targets = value["items"]
        require(set(targets) <= set(items), "Coverage references an unknown item.", "E_ANALYSIS_REFERENCE")
        if value["disposition"] in ("contextual", "excluded"):
            require(not targets, "Context and exclusion coverage do not create functional coverage.", "E_ANALYSIS_COVERAGE")
        else:
            status = "specified" if value["disposition"] == "elaborated" else "blocked"
            require(bool(targets) and all(t.startswith(("FR-", "UC-", "BR-")) and items[t]["fields"]["Status"] == status and bid in references(items[t]["fields"]["Business sources"]) for t in targets), "Coverage must reference supported specified or blocked behavior; proposals cannot count.", "E_ANALYSIS_COVERAGE")
    return {"items": items, "coverage": coverage, "inherited": inherited}


def stable_items(previous, current):
    require(set(previous) <= set(current), "Retire removed items; assigned IDs cannot disappear.", "E_ANALYSIS_HISTORY")
    require(all(current[rid]["fields"]["Status"] == "retired" for rid, value in previous.items() if value["fields"]["Status"] == "retired"), "Retired IDs cannot be reused.", "E_ANALYSIS_HISTORY")


def review_revision(epic):
    fingerprints = [epic.review_revision]
    for name in FILES:
        path = epic.directory / name
        require(not path.is_symlink() and (not path.exists() or path.is_file()), "Expected regular nonsymlink analysis artifacts.", "E_ANALYSIS_FILE", name)
        fingerprints.append(business.digest(path.read_bytes()) if path.exists() else None)
    return business.digest(json.dumps(fingerprints).encode())


def read_history(directory, epic_id, loader):
    path = directory / FILES[1]
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=loader)
        return validate_history(data, epic_id, directory, loader)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, TypeError, KeyError, binascii.Error, RecursionError) as exc:
        raise business.BusinessError("E_ANALYSIS_HISTORY", str(exc), path.name) from exc


def validate_history(data, epic_id, directory, loader):
    try:
        require(isinstance(data, dict) and set(data) == {"schema_version", "request_id", "revisions"} and data["schema_version"] in ("0.1","0.2") and data["request_id"] == epic_id and isinstance(data["revisions"], list) and bool(data["revisions"]), "Invalid analysis history.", "E_ANALYSIS_HISTORY", FILES[1])
        previous, operations, retained, retired = None, set(), set(), set()
        for entry in data["revisions"]:
            keys = {"digest", "previous", "content_base64", "baseline_id", "approval_id", "handoff_id", "editor", "reason", "timestamp", "operation_id", "expected_review", "mode", "feedback"}
            if isinstance(entry,dict) and "schema_version" in entry:
                require(data["schema_version"]=="0.2" and entry["schema_version"]=="0.2", "Invalid Analysis revision envelope.","E_ANALYSIS_HISTORY",FILES[1])
                keys|={"schema_version","template"}
                templates.validate_pin(entry.get("template"),"specification")
            require(isinstance(entry, dict) and set(entry) == keys, "Invalid revision fields.", "E_ANALYSIS_HISTORY", FILES[1])
            require(entry["previous"] == previous and discovery.valid_revision(entry["digest"]) and discovery.valid_revision(entry["baseline_id"]) and discovery.valid_revision(entry["expected_review"]), "Broken revision chain.", "E_ANALYSIS_HISTORY", FILES[1])
            require(discovery.valid_operation_id(entry["operation_id"]) and entry["operation_id"] not in operations and discovery.valid_operation_id(entry["handoff_id"]) and isinstance(entry["approval_id"], str) and re.fullmatch(r"BD-[0-9]{4,}", entry["approval_id"]), "Invalid revision identity.", "E_ANALYSIS_HISTORY", FILES[1])
            require(all(business.valid_person(entry[k]) for k in ("editor", "reason")) and approval.valid_timestamp(entry["timestamp"]) and entry["mode"] in ("generate", "revise") and (entry["feedback"] is None or isinstance(entry["feedback"], dict)), "Invalid revision attribution.", "E_ANALYSIS_HISTORY", FILES[1])
            content = base64.b64decode(entry["content_base64"], validate=True)
            require(business.digest(content) == entry["digest"], "Historical bytes do not match digest.", "E_ANALYSIS_HISTORY", FILES[1])
            _, files = approval.read_baseline(directory, entry["baseline_id"], loader)
            parsed = validate_document(content, epic_id, {**entry, "business": files["business.md"].decode("utf-8"), "discovery": yaml.load(files["discovery.yaml"].decode("utf-8"), Loader=loader)})
            require(retained <= set(parsed["items"]), "Previously assigned IDs must be preserved, retiring removed items.", "E_ANALYSIS_HISTORY", FILES[1])
            require(all(parsed["items"][rid]["fields"]["Status"] == "retired" for rid in retired), "Retired IDs cannot be reactivated for new content.", "E_ANALYSIS_HISTORY", FILES[1])
            retired.update(rid for rid, value in parsed["items"].items() if value["fields"]["Status"] == "retired")
            if entry["feedback"] is not None:
                validate_feedback(entry["feedback"])
                require(set(entry["feedback"]["items"]) <= set(parsed["items"]), "Feedback has dangling references.", "E_ANALYSIS_HISTORY", FILES[1])
            retained.update(parsed["items"])
            previous = entry["digest"]
            operations.add(entry["operation_id"])
        return data
    except (UnicodeError, yaml.YAMLError, ValueError, TypeError, KeyError, binascii.Error, RecursionError) as exc:
        raise business.BusinessError("E_ANALYSIS_HISTORY", str(exc), FILES[1]) from exc


def read(epic, loader):
    journal = epic.directory / JOURNAL
    require(not journal.exists() and not journal.is_symlink(), "Interrupted Analysis publication; inspect and run analysis-recover.", "E_ANALYSIS_RECOVERY", JOURNAL)
    token = review_revision(epic)
    paths = [epic.directory / name for name in FILES]
    if not any(p.exists() for p in paths):
        require(epic.metadata["status"] not in ("functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES), "Analysis state requires specification and history.", "E_ANALYSIS_HISTORY", FILES[1])
        return None, token
    require(all(p.exists() for p in paths), "Specification and history must both exist.", "E_ANALYSIS_HISTORY", FILES[1])
    data = read_history(epic.directory, epic.metadata["id"], loader)
    latest = data["revisions"][-1]
    content = paths[0].read_bytes()
    require(business.digest(content) == latest["digest"], "Specification differs from recorded history.", "E_ANALYSIS_MISMATCH")
    events = {e["id"]: e for e in epic.metadata["lifecycle"] if e["action"] == "advance"}
    for entry in data["revisions"]:
        require(entry["handoff_id"] in events and binding(events[entry["handoff_id"]]) == {k: entry[k] for k in ("baseline_id", "approval_id", "handoff_id")}, "Revision references an unknown business handoff.", "E_ANALYSIS_HISTORY", FILES[1])
    event = handoff(epic.metadata)
    current = bool(event and epic.approval["valid"] and all(latest[k] == v for k, v in binding(event).items()))
    # Capture exact bytes across history/document reads, independent of folder name.
    require(review_revision(epic) == token, "Analysis artifacts changed while reading.", "E_READ_CONFLICT")
    return {"content": content.decode("utf-8"), "revision": latest["digest"], **{k: latest[k] for k in ("baseline_id", "approval_id", "handoff_id")}, "needs_reconciliation": not current, "history": [{k: v for k, v in e.items() if k != "content_base64"} for e in data["revisions"]]}, token


def validate_feedback(value):
    require(isinstance(value, dict) and set(value) == {"actor", "text", "items"} and business.valid_person(value["actor"]) and isinstance(value["text"], str) and bool(value["text"].strip()) and isinstance(value["items"], list) and bool(value["items"]) and all(isinstance(v, str) and IDENTIFIER.fullmatch(v) for v in value["items"]) and len(set(value["items"])) == len(value["items"]), "Feedback requires declared actor, actual text and affected IDs.", "E_UPDATE_INPUT")


def feedback_data(path, loader):
    if path is None:
        return None
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=loader)
        validate_feedback(value)
        return value
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise business.BusinessError("E_UPDATE_INPUT", str(exc), str(path)) from exc
