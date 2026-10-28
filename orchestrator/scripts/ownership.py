"""Epic-local accountability and explicit responsibility transfer; no authorization policy."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from engineering_contract import ROLES
import business_refinement as business
import discovery_history as discovery

STAGES = {
    "discovery": ("discovery", "Requester / Business Stakeholder"),
    "ready_for_refinement": ("business_refinement", "Product Owner"),
    "business_refinement": ("business_refinement", "Product Owner"),
    "ready_for_analysis": ("functional_analysis", "Business Analyst"),
    "functional_analysis": ("functional_analysis", "Business Analyst"),
    "ready_for_technical_design": ("technical_design", "Engineering Lead / Architect"),
}
STAGES.update(ROLES)
STATE_FIELDS = {"owner", "assignee", "required_role", "assignment_status", "target_stage", "since"}
EVENT_FIELDS = {"operation_id", "action", "actor", "identity_source", "timestamp", "expected_revision", "from_owner", "to_owner", "assignee", "required_role", "assignment_status", "target_stage", "lifecycle_id", "decision"}


def require(condition, message, code="E_OWNERSHIP"):
    business.require(condition, code, message, "metadata.yaml")


def text(value):
    return discovery.text(value) and all(ord(c) >= 32 or c in "\n\r\t" for c in value)


def timestamp_valid(value):
    try:
        return isinstance(value, str) and value.endswith("Z") and datetime.fromisoformat(value[:-1] + "+00:00").utcoffset().total_seconds() == 0
    except (ValueError, TypeError, AttributeError):
        return False


def responsibility(status):
    require(status in STAGES, "No assignment activity is available in this lifecycle state.", "E_STATUS")
    return STAGES[status]


def state(event):
    return {"owner": event["to_owner"], **{k: event[k] for k in ("assignee", "required_role", "assignment_status", "target_stage")}, "since": event["timestamp"]}


def needs_handoff(event):
    return event["action"] in ("complete", "advance", "analysis_advance", "reopen") or (event["action"] == "engineer" and responsibility(event["from"]) != responsibility(event["to"]))


def validate(metadata):
    if "ownership" not in metadata:
        return
    value = metadata["ownership"]
    require(isinstance(value, dict) and set(value) == STATE_FIELDS | {"history"}, "Invalid ownership fields.")
    history = value["history"]
    require(isinstance(history, list) and bool(history), "Ownership requires retained history.")
    previous, operations = None, set()
    lifecycle = {e["id"]: e for e in metadata.get("lifecycle", [])}
    handoffs = []
    for index, event in enumerate(history):
        require(isinstance(event, dict) and set(event) == EVENT_FIELDS, "Invalid assignment event fields.")
        require(discovery.valid_operation_id(event["operation_id"]) and event["operation_id"] not in operations, "Invalid or duplicate assignment operation ID.")
        require(event["action"] in ("initialize", "assign", "handoff"), "Unknown assignment event action.")
        require(business.valid_person(event["actor"]) and business.valid_person(event["to_owner"]) and text(event["decision"]) and timestamp_valid(event["timestamp"]), "Invalid assignment attribution or decision.")
        require(event["identity_source"] in ("local_profile", "declared"), "Unsupported assignment identity source.")
        require((event["expected_revision"] is None or discovery.valid_revision(event["expected_revision"])) if index == 0 else discovery.valid_revision(event["expected_revision"]), "Invalid assignment revision binding.")
        require(event["from_owner"] == (previous["owner"] if previous else None), "Broken ownership history chain.")
        require((event["target_stage"], event["required_role"]) in list(STAGES.values()), "Unknown target stage or required role.")
        require(event["assignment_status"] in ("assigned", "awaiting_assignment"), "Invalid assignment status.")
        if event["assignment_status"] == "assigned":
            require(event["assignee"] == event["to_owner"], "Assigned work must have its accountable owner as assignee.")
        else:
            require(event["assignee"] is None, "Awaiting handoff cannot claim an assignee.")
        if index == 0:
            require(event["action"] == "initialize" and event["lifecycle_id"] is None, "Ownership must start with initialization.")
        elif event["action"] == "handoff":
            linked = lifecycle.get(event["lifecycle_id"]) if isinstance(event["lifecycle_id"], str) else None
            require(linked is not None and linked["id"] == event["operation_id"] and linked["action"] in ("complete", "advance", "analysis_advance", "reopen", "engineer"), "Handoff must reference its lifecycle advancement/reopening.")
            require((event["target_stage"], event["required_role"]) == responsibility(linked["to"]) and event["to_owner"] == previous["owner"] and event["assignment_status"] == "awaiting_assignment", "Handoff must retain its owner and await the next role.")
            require(event["timestamp"] == linked["timestamp"] and event["actor"] == linked["actor"], "Handoff attribution differs from lifecycle evidence.")
            handoffs.append(linked["id"])
        else:
            require(event["action"] == "assign" and event["lifecycle_id"] is None and event["assignment_status"] == "assigned" and event["target_stage"] == previous["target_stage"] and event["required_role"] == previous["required_role"], "Assignment cannot change lifecycle or responsibility stage.")
        operations.add(event["operation_id"])
        previous = state(event)
    require({k: value[k] for k in STATE_FIELDS} == previous, "Current ownership differs from its history.")
    if metadata["status"] != "cancelled":
        require((value["target_stage"], value["required_role"]) == responsibility(metadata["status"]), "Ownership responsibility differs from current lifecycle.")
    # All handoffs after ownership was introduced must remain represented in order.
    if handoffs:
        lifecycle_handoffs = [e["id"] for e in metadata.get("lifecycle", []) if needs_handoff(e)]
        require(handoffs == lifecycle_handoffs[lifecycle_handoffs.index(handoffs[0]):], "Ownership is missing a later lifecycle handoff.")


def event_for(action, current, status, actor, source, operation_id, expected_revision, decision, *, owner=None, lifecycle=None, timestamp=None):
    stage, role = responsibility(status)
    next_owner = owner if owner is not None else current["owner"]
    assigned = action != "handoff" and (action == "assign" or status == "discovery")
    return {"operation_id": operation_id, "action": action, "actor": actor, "identity_source": source or "declared", "timestamp": timestamp or business.timestamp(),
            "expected_revision": expected_revision, "from_owner": current["owner"] if current else None, "to_owner": next_owner,
            "assignee": next_owner if assigned else None, "required_role": role,
            "assignment_status": "assigned" if assigned else "awaiting_assignment", "target_stage": stage,
            "lifecycle_id": lifecycle["id"] if lifecycle else None, "decision": decision}


def initialized(status, owner, actor, source, operation_id, decision, timestamp=None):
    event = event_for("initialize", None, status, actor, source, operation_id, None, decision, owner=owner, timestamp=timestamp)
    return {**state(event), "history": [event]}


def append(value, event):
    return {**state(event), "history": [*value["history"], event]}


def legacy_requester(metadata):
    names = {e["actor"] for e in metadata.get("lifecycle", []) if e["action"] in ("complete", "reopen")}
    return next(iter(names)) if len(names) == 1 else None


def view(metadata):
    if "ownership" in metadata:
        return {**metadata["ownership"], "persisted": True, "initialization_required": False}
    owner = legacy_requester(metadata)
    stage, role = STAGES.get(metadata["status"], ("cancelled", None))
    boundaries = [e for e in metadata.get("lifecycle", []) if needs_handoff(e)]
    return {"owner": owner, "assignee": owner if metadata["status"] == "discovery" else None,
            "required_role": role, "target_stage": stage,
            "assignment_status": "owner_declaration_required" if owner is None else "assigned" if metadata["status"] == "discovery" else "awaiting_assignment",
            "since": boundaries[-1]["timestamp"] if boundaries else None, "history": [], "persisted": False,
            "initialization_required": owner is None}


def materialize(metadata, actor, source, *, initial_owner=None, timestamp=None):
    if "ownership" in metadata:
        return metadata["ownership"]
    owner = legacy_requester(metadata) or initial_owner
    require(business.valid_person(owner), "No unambiguous recorded Requester; explicitly declare the initial accountable owner.", "E_OWNER_REQUIRED")
    digest = hashlib.sha256(json.dumps([metadata, owner], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return initialized(metadata["status"], owner, actor, source,
                       "owner-init-" + digest, "Initialize accountability from recorded Requester." if legacy_requester(metadata) else "Explicit initial-owner declaration.", timestamp=timestamp)


def handoff(before, candidate, actor, source):
    linked = candidate["lifecycle"][-1]
    current = materialize(before, actor, source, timestamp=linked["timestamp"])
    event = event_for("handoff", current, candidate["status"], actor, source, linked["id"], linked["base_revision"], linked["decision"], lifecycle=linked, timestamp=linked["timestamp"])
    candidate["ownership"] = append(current, event)
    validate(candidate)


def preserve_prefix(before, after):
    if "ownership" in before:
        old = before["ownership"]["history"]
        require("ownership" in after and after["ownership"]["history"][:len(old)] == old, "Historical assignment events must remain unchanged.", "E_OWNERSHIP_AUDIT")


def row(epic, now=None):
    value = view(epic.metadata)
    since = value["since"]
    elapsed = None
    if value["assignment_status"] == "awaiting_assignment" and timestamp_valid(since):
        elapsed = max(0, int(((now or datetime.now(timezone.utc)) - datetime.fromisoformat(since[:-1] + "+00:00")).total_seconds()))
    if value["assignment_status"] == "awaiting_assignment":
        next_action = "Nominate " + value["required_role"]
    elif value["owner"] is None:
        next_action = "Declare the initial accountable owner"
    elif value["target_stage"] == "technical_design":
        next_action = "Review the approved Analysis handoff; start Technical Design only when explicitly requested"
    else:
        next_action = "Review the current stage and carry out the assigned activity only when explicitly requested"
    return {"id": epic.metadata["id"], "title": epic.metadata["title"], "lifecycle": epic.metadata["status"],
            **{k: value[k] for k in STATE_FIELDS}, "time_awaiting_seconds": elapsed,
            "responsibility": "Accountable owner awaiting handoff" if value["assignment_status"] == "awaiting_assignment" else "Current assignee" if value["assignee"] else "Initial owner declaration required",
            "recommended_next_action": next_action}
