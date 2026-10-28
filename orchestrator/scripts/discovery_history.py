"""Typed Discovery history and reference rules; no business interpretation or I/O."""

from __future__ import annotations

from copy import deepcopy
import re


SCHEMA_VERSION = "0.1"
KINDS = ("user_statement", "ai_assumption", "question", "human_decision")
ACTIONS = ("decide", "answer", "defer", "unknown", "reopen", "confirm", "reject", "correct")


class HistoryError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def require(condition, message, code="E_DISCOVERY_HISTORY"):
    if not condition:
        raise HistoryError(code, message)


def text(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        value.encode("utf-8")
    except UnicodeError:
        return False
    return True


def valid_operation_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value))


def valid_revision(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def empty(epic_id):
    return {"schema_version": SCHEMA_VERSION, "request_id": epic_id, "operations": []}


def validate_record(record, expected_id):
    code = "E_DISCOVERY_RECORD"
    require(isinstance(record, dict), "Discovery records must be mappings.", code)
    require(record.get("id") == expected_id, f"Expected sequential record ID {expected_id}.", code)
    kind = record.get("kind")
    require(kind in KINDS, "Unsupported Discovery record kind.", code)
    fields = {"id", "kind", "topic", "text", "source"}
    allowed = fields.copy()
    if kind == "user_statement":
        allowed.add("answers")
    if kind == "human_decision":
        fields.add("action")
        allowed.update(("action", "target", "revisit"))
    require(fields <= set(record) <= allowed, "Missing or unknown Discovery record fields.", code)
    require(text(record["topic"]) and text(record["text"]), "Record topic and text must be nonempty UTF-8 strings.", code)
    source = record["source"]
    provenance = "E_DISCOVERY_PROVENANCE"
    require(isinstance(source, dict), "A source mapping is required.", provenance)
    actor = source.get("actor")
    require(actor in ("user", "ai"), "Source actor must be user or ai.", provenance)
    if actor == "user":
        require(set(source) == {"actor", "quote"} and text(source.get("quote")),
                "User records require a supporting nonempty UTF-8 user quotation.", provenance)
    else:
        require(set(source) == {"actor"}, "AI source contains unknown fields.", provenance)
    if kind in ("user_statement", "human_decision"):
        require(actor == "user", "Statements and human decisions require user provenance.", provenance)
    if kind == "ai_assumption":
        require(actor == "ai", "An AI assumption must retain AI provenance.", provenance)
    if "answers" in record:
        require(text(record["answers"]), "answers must reference a question ID.", code)
    if kind == "human_decision":
        action = record["action"]
        require(action in ACTIONS, "Unsupported human decision action.", code)
        if action == "decide":
            require("target" not in record, "A standalone decision has no target.", code)
        else:
            require(text(record.get("target")), "This decision requires a target record ID.", code)
        if "revisit" in record:
            require(action in ("defer", "unknown") and text(record["revisit"]),
                    "revisit is optional text for deferred or unknown answers only.", code)


def project(history, epic_id):
    """Validate the append-only ledger and derive mechanical resolution states."""
    require(isinstance(history, dict) and set(history) == {"schema_version", "request_id", "operations"},
            "History must contain schema_version, request_id and operations.")
    require(history["schema_version"] == SCHEMA_VERSION, "Unsupported Discovery schema version.", "E_DISCOVERY_VERSION")
    require(history["request_id"] == epic_id, "Discovery request_id does not match the Epic.")
    require(isinstance(history["operations"], list), "History operations must be a list.")
    seen, operation_ids, questions, assumptions, superseded = {}, set(), {}, {}, {}
    for operation in history["operations"]:
        require(isinstance(operation, dict) and set(operation) == {"id", "base_revision", "records"},
                "Each operation requires id, base_revision and records.")
        operation_id = operation["id"]
        require(valid_operation_id(operation_id), "Invalid operation ID.")
        require(operation_id not in operation_ids, "Duplicate operation ID.")
        operation_ids.add(operation_id)
        require(valid_revision(operation["base_revision"]), "Invalid base revision.")
        require(isinstance(operation["records"], list), "Operation records must be a list.")
        for record in operation["records"]:
            record_id = f"D-{len(seen) + 1:04d}"
            validate_record(record, record_id)
            kind = record["kind"]
            reference_code = "E_DISCOVERY_REFERENCE"
            if kind == "question":
                questions[record_id] = {"id": record_id, "status": "open", "resolution_id": None, "revisit": None}
            elif kind == "ai_assumption":
                assumptions[record_id] = {"id": record_id, "status": "proposed", "resolution_id": None}
            if kind == "user_statement" and "answers" in record:
                target = record["answers"]
                require(target in questions, "answers must reference an earlier question.", reference_code)
                require(questions[target]["status"] != "answered", "Correct the existing answer instead of overwriting it.", reference_code)
                questions[target].update(status="answered", resolution_id=record_id, revisit=None)
            if kind == "human_decision" and record["action"] != "decide":
                action, target = record["action"], record["target"]
                require(target in seen, "Decision target must reference an earlier record.", reference_code)
                if action in ("answer", "defer", "unknown", "reopen"):
                    require(target in questions, "This decision must target a question.", reference_code)
                    status = questions[target]["status"]
                    if action == "reopen":
                        require(status != "open", "The question is already open.", reference_code)
                    else:
                        require(status != "answered", "Reopen the question or correct its existing answer.", reference_code)
                    state = {"answer": "answered", "defer": "deferred", "unknown": "unknown", "reopen": "open"}[action]
                    questions[target].update(status=state, resolution_id=record_id, revisit=record.get("revisit"))
                elif action in ("confirm", "reject"):
                    require(target in assumptions, "Confirmation/rejection must target an AI assumption.", reference_code)
                    allowed = ("proposed",) if action == "confirm" else ("proposed", "confirmed")
                    require(assumptions[target]["status"] in allowed, "Assumption already resolved; create a new proposal if needed.", reference_code)
                    assumptions[target].update(status="confirmed" if action == "confirm" else "rejected", resolution_id=record_id)
                elif action == "correct":
                    earlier = seen[target]
                    correctable = earlier["kind"] == "user_statement" or (
                        earlier["kind"] == "human_decision" and earlier["action"] in ("decide", "answer", "correct")
                    )
                    require(correctable and target not in superseded, "Corrections must target a current user statement or substantive decision.", reference_code)
                    superseded[target] = record_id
            seen[record_id] = record
    for question in questions.values():
        if question["status"] == "answered":
            while question["resolution_id"] in superseded:
                question["resolution_id"] = superseded[question["resolution_id"]]
    return {"questions": list(questions.values()), "assumptions": list(assumptions.values()), "superseded_by": superseded}


def append(history, epic_id, operation_id, revision, records):
    """Return a validated candidate; never mutate the supplied history or records."""
    project(history, epic_id)
    candidate = deepcopy(history)
    require(isinstance(records, list), "Update records must be a list.", "E_UPDATE_INPUT")
    count = sum(len(operation["records"]) for operation in history["operations"])
    added = []
    for index, record in enumerate(records, count + 1):
        require(isinstance(record, dict) and "id" not in record, "Record IDs are assigned by the operation.", "E_UPDATE_INPUT")
        added.append({"id": f"D-{index:04d}", **deepcopy(record)})
    operation = {"id": operation_id, "base_revision": revision, "records": added}
    candidate["operations"].append(operation)
    project(candidate, epic_id)
    return candidate, operation


def requested_records(operation):
    return [{key: value for key, value in record.items() if key != "id"} for record in operation["records"]]
