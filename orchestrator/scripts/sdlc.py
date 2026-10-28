"""Deterministic, local Discovery operations. No Git or host-agent integration."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata

import yaml
import discovery_history as history
import business_refinement as business
import business_approval as approval


SCHEMA_VERSION = "0.1"
ORCHESTRATOR_VERSION = "0.4.0"
EPIC_ID = re.compile(r"REQ-[0-9]{4}\Z")
FIELDS = {"schema_version", "id", "title", "status", "artifacts"}
SECTIONS = (
    "Problem", "Users", "Expected value", "Initial scope", "Success criteria",
    "Assumptions", "Open questions",
)
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "idea.md"


@dataclass
class Diagnostic:
    severity: str
    code: str
    file: str
    message: str
    line: int | None = None


class Rejected(Exception):
    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__("; ".join(item.message for item in diagnostics))


def error(code: str, path: Path, message: str) -> Diagnostic:
    return Diagnostic("error", code, str(path), message)


class StrictLoader(yaml.SafeLoader):
    """Safe YAML with string keys and no duplicate or implicit merge keys."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.events.AliasEvent):
            event = self.peek_event()
            raise yaml.composer.ComposerError(
                None, None, "YAML aliases are not supported in metadata.", event.start_mark
            )
        return super().compose_node(parent, index)

    def construct_object(self, node, deep=False):
        try:
            return super().construct_object(node, deep=deep)
        except (ValueError, TypeError, LookupError, AttributeError, OverflowError) as exc:
            # Explicit scalar tags can raise conversion errors outside YAMLError.
            raise yaml.constructor.ConstructorError(
                None, None, f"Invalid YAML value: {exc}", node.start_mark
            ) from exc

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, f"Expected a mapping node, but found {node.id}.", node.start_mark
            )
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(
                    None, None, "Metadata keys must be strings.", key_node.start_mark
                )
            if key in result:
                raise yaml.constructor.ConstructorError(
                    None, None, f"Duplicate metadata key: {key}", key_node.start_mark
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def valid_id(value) -> bool:
    return isinstance(value, str) and bool(EPIC_ID.fullmatch(value)) and value != "REQ-0000"


def valid_title(value) -> bool:
    return (
        isinstance(value, str) and bool(value.strip())
        and not any(ord(char) < 32 for char in value)
    )


@dataclass
class Epic:
    directory: Path
    metadata: dict = field(default_factory=dict)
    idea: str | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    revision: str | None = None
    discovery: dict | None = None
    discovery_state: dict | None = None
    source_revision: str | None = None
    business: dict | None = None
    review_revision: str | None = None
    approval: dict | None = None
    open_items: list = field(default_factory=list)

    def payload(self) -> dict:
        return {
            "directory": str(self.directory), "metadata": self.metadata,
            "idea": self.idea,
            "revision": self.revision, "discovery": self.discovery,
            "discovery_state": self.discovery_state,
            "source_revision": self.source_revision, "business": self.business,
            "review_revision": self.review_revision, "approval": self.approval,
            "open_items": self.open_items,
        }


def business_warnings(path: Path, content: str) -> list[Diagnostic]:
    """Check template sections mechanically; never judge business readiness."""
    parts = re.split(r"(?m)^##[ \t]+([^\n]+)\n?", content)
    sections = {
        parts[index].strip().casefold(): parts[index + 1].strip()
        for index in range(1, len(parts), 2)
    }
    return [
        Diagnostic(
            "warning", "W_DISCOVERY_INCOMPLETE", str(path),
            f"Discovery section '{name}' is missing or empty; clarification may be needed.",
        )
        for name in SECTIONS if not sections.get(name.casefold())
    ]


def read_epic(directory: Path) -> Epic:
    epic = Epic(directory)
    metadata_path = directory / "metadata.yaml"
    if metadata_path.is_symlink() or not metadata_path.is_file():
        epic.diagnostics.append(error(
            "E_METADATA_FILE", metadata_path, "Expected a regular metadata.yaml file."
        ))
        return epic
    try:
        metadata_bytes = metadata_path.read_bytes()
        data = yaml.load(metadata_bytes.decode("utf-8"), Loader=StrictLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        epic.diagnostics.append(Diagnostic(
            "error", "E_YAML", str(metadata_path),
            getattr(exc, "problem", None) or "Invalid YAML.",
            mark.line + 1 if mark else None,
        ))
        return epic
    except (OSError, UnicodeError) as exc:
        epic.diagnostics.append(error("E_READ", metadata_path, str(exc)))
        return epic
    except RecursionError:
        epic.diagnostics.append(error("E_YAML", metadata_path, "YAML nesting is too deep."))
        return epic
    if not isinstance(data, dict):
        epic.diagnostics.append(error("E_METADATA", metadata_path, "Metadata must be a mapping."))
        return epic
    epic.metadata = data
    version = data.get("schema_version")
    expected_fields = FIELDS if version == SCHEMA_VERSION else FIELDS | {"lifecycle"}
    if version == "0.3":
        expected_fields |= {"business_decisions"}
    if set(data) != expected_fields:
        epic.diagnostics.append(error(
            "E_METADATA", metadata_path,
            f"Expected exactly these fields: {', '.join(sorted(expected_fields))}.",
        ))
    if version not in (SCHEMA_VERSION, "0.2", "0.3"):
        epic.diagnostics.append(error(
            "E_SCHEMA_VERSION", metadata_path,
            "Supported schema_version values are the strings '0.1', '0.2' and '0.3'.",
        ))
    if not valid_id(data.get("id")):
        epic.diagnostics.append(error("E_EPIC_ID", metadata_path, "Expected REQ-0001 through REQ-9999."))
    if not valid_title(data.get("title")):
        epic.diagnostics.append(error("E_TITLE", metadata_path, "Title must be nonempty, single-line text."))
    # Cancelled records reserve IDs; this CLI provides no cancellation transition.
    statuses = ("discovery", "cancelled") if version == SCHEMA_VERSION else ("discovery", "ready_for_refinement", "business_refinement")
    if version == "0.3":
        statuses += ("ready_for_analysis",)
    if data.get("status") not in statuses:
        epic.diagnostics.append(error(
            "E_STATUS", metadata_path, f"Supported record statuses are {', '.join(statuses)}."
        ))
    if version in ("0.2", "0.3"):
        try:
            business.validate_lifecycle(data["lifecycle"], data.get("status"), allow_advance=version == "0.3")
            if version == "0.3":
                approval.validate_decisions(data)
        except (KeyError, business.BusinessError) as exc:
            epic.diagnostics.append(error(exc.code if isinstance(exc, business.BusinessError) else "E_LIFECYCLE", metadata_path, str(exc)))
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != {"idea"}:
        epic.diagnostics.append(error(
            "E_ARTIFACTS", metadata_path, "artifacts must contain exactly one key: idea."
        ))
        return epic
    reference = artifacts["idea"]
    if not isinstance(reference, str) or not reference.strip():
        epic.diagnostics.append(error("E_ARTIFACT_PATH", metadata_path, "idea must be a relative file path."))
        return epic
    relative = Path(reference)
    idea_path = directory / relative
    try:
        idea_path = idea_path.resolve()
        if (
            relative.is_absolute() or ".." in relative.parts
            or "business-baselines" in relative.parts[:1]
            or not idea_path.is_relative_to(directory.resolve())
            or idea_path == metadata_path.resolve()
            or idea_path in {(directory / "discovery.yaml").resolve(), (directory / "business.md").resolve(), (directory / "business-history.yaml").resolve()}
        ):
            epic.diagnostics.append(error(
                "E_ARTIFACT_PATH", metadata_path, "The idea artifact must stay inside its Epic directory."
            ))
            return epic
        if not idea_path.is_file():
            epic.diagnostics.append(error("E_ARTIFACT_FILE", idea_path, "The idea artifact must be an existing file."))
            return epic
        idea_bytes = idea_path.read_bytes()
        epic.idea = idea_bytes.decode("utf-8")
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        epic.diagnostics.append(error("E_READ", idea_path, str(exc)))
        return epic
    epic.diagnostics.extend(business_warnings(idea_path, epic.idea))
    discovery_path = directory / "discovery.yaml"
    discovery_bytes = None
    if discovery_path.is_symlink() or (discovery_path.exists() and not discovery_path.is_file()):
        epic.diagnostics.append(error("E_DISCOVERY_FILE", discovery_path, "Expected a regular nonsymlink Discovery file."))
        return epic
    if discovery_path.exists():
        try:
            discovery_bytes = discovery_path.read_bytes()
            epic.discovery = yaml.load(discovery_bytes.decode("utf-8"), Loader=StrictLoader)
            epic.discovery_state = history.project(epic.discovery, data.get("id"))
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            epic.diagnostics.append(Diagnostic(
                "error", "E_YAML", str(discovery_path), getattr(exc, "problem", None) or "Invalid YAML.",
                mark.line + 1 if mark else None,
            ))
            return epic
        except history.HistoryError as exc:
            epic.diagnostics.append(error(exc.code, discovery_path, str(exc)))
            return epic
        except (OSError, UnicodeError) as exc:
            epic.diagnostics.append(error("E_READ", discovery_path, str(exc)))
            return epic
        except RecursionError:
            epic.diagnostics.append(error("E_YAML", discovery_path, "YAML nesting is too deep."))
            return epic
    # Hash the exact bytes read, including missing history, independently of folder names.
    contents = [metadata_bytes, idea_bytes, discovery_bytes]
    fingerprints = [hashlib.sha256(content).hexdigest() if content is not None else None for content in contents]
    epic.revision = hashlib.sha256(json.dumps(fingerprints).encode()).hexdigest()
    epic.source_revision = hashlib.sha256(json.dumps(fingerprints[1:]).encode()).hexdigest()
    if not any(item.severity == "error" for item in epic.diagnostics):
        try:
            epic.business = business.read(directory, data, epic.discovery, epic.discovery_state, epic.source_revision)
            snapshot = approval.read_snapshot(directory, data)
            if snapshot["metadata.yaml"] != metadata_bytes or snapshot["idea.md"] != idea_bytes or snapshot["discovery.yaml"] != discovery_bytes or (epic.business is not None and (snapshot["business.md"] is None or business.digest(snapshot["business.md"]) != epic.business["revision"])):
                epic.diagnostics.append(error("E_READ_CONFLICT", directory, "Artifacts changed during the read; reopen and retry."))
                return epic
            epic.review_revision = approval.review_revision(snapshot)
            baseline_errors = approval.check_baselines(directory, data, epic.business, StrictLoader)
            epic.diagnostics.extend(error(exc.code, directory / exc.filename, str(exc)) for exc in baseline_errors)
            epic.approval = approval.evaluate(data, epic.business, epic.source_revision, baseline_errors)
            epic.open_items = approval.open_items(epic.business)
            if (metadata_path.read_bytes() != metadata_bytes or idea_path.read_bytes() != idea_bytes
                    or (discovery_path.read_bytes() if discovery_path.exists() else None) != discovery_bytes
                    or approval.read_snapshot(directory, data) != snapshot
                    or (directory / ".business-transaction.json").exists()):
                epic.diagnostics.append(error("E_READ_CONFLICT", directory, "Artifacts changed during the read; reopen and retry."))
        except business.BusinessError as exc:
            epic.diagnostics.append(error(exc.code, directory / exc.filename, str(exc)))
        except OSError as exc:
            epic.diagnostics.append(error("E_READ", directory, str(exc)))
    return epic


def project_path(project: Path) -> Path:
    root = Path(project).resolve()
    if not root.is_dir():
        raise Rejected([error("E_PROJECT", root, "Project root must be an existing directory.")])
    return root


def scan(root: Path) -> tuple[list[Epic], list[Diagnostic]]:
    requirements = root / "requirements"
    if requirements.is_symlink() or (requirements.exists() and not requirements.is_dir()):
        raise Rejected([error("E_REQUIREMENTS", requirements, "Expected a nonsymlink requirements directory.")])
    if not requirements.exists():
        return [], []
    epics, diagnostics, ids = [], [], {}
    for directory in sorted(requirements.iterdir()):
        if directory.is_symlink():
            diagnostics.append(error("E_EPIC_DIRECTORY", directory, "Epic entries cannot be symlinks."))
            continue
        if not directory.is_dir():
            if directory.name.startswith("REQ-"):
                diagnostics.append(error("E_EPIC_DIRECTORY", directory, "Expected an Epic directory."))
            continue
        epic = read_epic(directory)
        epics.append(epic)
        diagnostics.extend(epic.diagnostics)
        epic_id = epic.metadata.get("id")
        if valid_id(epic_id):
            if epic_id in ids:
                diagnostics.append(error(
                    "E_DUPLICATE_ID", directory / "metadata.yaml",
                    f"Duplicate ID {epic_id}; also present in {ids[epic_id]}.",
                ))
            ids[epic_id] = directory / "metadata.yaml"
    return epics, diagnostics


def require_valid(diagnostics: list[Diagnostic]) -> None:
    if any(item.severity == "error" for item in diagnostics):
        raise Rejected(diagnostics)


def result(operation: str, diagnostics: list[Diagnostic], **payload) -> dict:
    return {
        "operation": operation,
        "ok": not any(item.severity == "error" for item in diagnostics),
        "diagnostics": [asdict(item) for item in diagnostics], **payload,
    }


@contextmanager
def project_lock(root: Path):
    """Fail closed if another local writer holds the transient lock."""
    lock = root / ".sdlc-discovery.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise Rejected([error("E_PROJECT_BUSY", lock, "Another write may be running; inspect the lock before retrying.")]) from None
    try:
        yield
    finally:
        lock.rmdir()


def write_new(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def new_epic(project: Path, title: str, idea: str = "") -> dict:
    root = project_path(project)
    if not valid_title(title):
        raise Rejected([error("E_TITLE", root, "Title must be nonempty, single-line text.")])
    with project_lock(root):
        epics, diagnostics = scan(root)
        require_valid(diagnostics)
        next_number = max((int(epic.metadata["id"][4:]) for epic in epics), default=0) + 1
        if next_number > 9999:
            raise Rejected([error("E_ID_EXHAUSTED", root / "requirements", "The four-digit Epic ID range is exhausted.")])
        epic_id = f"REQ-{next_number:04d}"
        normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:64].rstrip("-") or "epic"
        requirements = root / "requirements"
        directory = requirements / f"{epic_id}-{slug}"
        metadata = {
            "schema_version": SCHEMA_VERSION, "id": epic_id,
            "title": title.strip(), "status": "discovery", "artifacts": {"idea": "idea.md"},
        }
        content = TEMPLATE.read_text(encoding="utf-8").replace("{{problem}}", idea.strip())
        made_requirements = False
        made_epic = False
        try:
            if not requirements.exists():
                requirements.mkdir()
                made_requirements = True
            directory.mkdir()  # Exclusive ownership; never replace an existing directory.
            made_epic = True
            write_new(directory / "metadata.yaml", yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True))
            write_new(directory / "idea.md", content)
            created = read_epic(directory)
            require_valid(created.diagnostics)
        except BaseException:
            if made_epic:
                shutil.rmtree(directory)
            if made_requirements:
                requirements.rmdir()
            raise
        return result("new", created.diagnostics, epic=created.payload())


def inspect_epics(project: Path, operation: str, epic_id: str | None = None) -> dict:
    root = project_path(project)
    if epic_id is not None and not valid_id(epic_id):
        raise Rejected([error("E_EPIC_ID", root / "requirements", "Expected REQ-0001 through REQ-9999.")])
    epics, diagnostics = scan(root)
    if operation == "open":
        require_valid(diagnostics)
    if epic_id is not None:
        selected = [epic for epic in epics if epic.metadata.get("id") == epic_id]
        if not selected:
            diagnostics.append(error("E_EPIC_NOT_FOUND", root / "requirements", f"Epic {epic_id} was not found."))
        # Preserve repository-wide errors; report business warnings only for the requested Epic.
        selected_files = {item.file for epic in selected for item in epic.diagnostics}
        diagnostics = [item for item in diagnostics if item.severity == "error" or item.file in selected_files]
    else:
        selected = epics
    if operation == "open":
        require_valid(diagnostics)
        return result(operation, diagnostics, epic=selected[0].payload())
    return result(operation, diagnostics, validated_ids=[
        epic.metadata["id"] for epic in selected if valid_id(epic.metadata.get("id"))
    ])


def atomic_history_write(path: Path, content: str) -> None:
    """Publish a complete history and its idempotency ledger in one replacement."""
    temporary = None
    published = False
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".discovery-", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            if path.exists():
                os.fchmod(stream.fileno(), path.stat().st_mode & 0o777)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        published = True
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        if published:
            raise Rejected([error("E_WRITE_UNCERTAIN", path, "History was published but durability could not be confirmed; retry with the same operation ID and payload.")]) from exc
        raise
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def discovery_update(project: Path, epic_id: str, expected_revision: str, operation_id: str, records: list) -> dict:
    root = project_path(project)
    if not valid_id(epic_id):
        raise Rejected([error("E_EPIC_ID", root / "requirements", "Expected REQ-0001 through REQ-9999.")])
    if not history.valid_revision(expected_revision) or not history.valid_operation_id(operation_id):
        raise Rejected([error("E_UPDATE_INPUT", root, "A SHA-256 revision and an operation ID (1–128 letters, digits, . _ : -) are required.")])
    if not isinstance(records, list):
        raise Rejected([error("E_UPDATE_INPUT", root, "Update records must be a list.")])
    with project_lock(root):
        epics, diagnostics = scan(root)
        require_valid(diagnostics)
        selected = [epic for epic in epics if epic.metadata["id"] == epic_id]
        if not selected:
            raise Rejected([error("E_EPIC_NOT_FOUND", root / "requirements", f"Epic {epic_id} was not found.")])
        epic = selected[0]
        path = epic.directory / "discovery.yaml"
        if epic.metadata["status"] != "discovery":
            raise Rejected([error("E_STATUS", epic.directory / "metadata.yaml", "Only discovery requests can be updated.")])
        document = epic.discovery if epic.discovery is not None else history.empty(epic_id)
        for existing in document["operations"]:
            if existing["id"] == operation_id:
                if existing["base_revision"] != expected_revision or history.requested_records(existing) != records:
                    raise Rejected([error("E_IDEMPOTENCY", path, "Operation ID was already used with different content or a different base revision.")])
                return result("discovery-update", epic.diagnostics, epic=epic.payload(), replayed=True, record_ids=[record["id"] for record in existing["records"]])
        if expected_revision != epic.revision:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Request artifacts changed; reopen and reconcile before sending a new operation.")])
        try:
            candidate, operation = history.append(document, epic_id, operation_id, expected_revision, records)
        except history.HistoryError as exc:
            raise Rejected([error(exc.code, path, str(exc))]) from exc
        content = yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True)
        # Cooperating writers share the lock; catch manual edits observed since the scan.
        checked = read_epic(epic.directory)
        require_valid(checked.diagnostics)
        if checked.revision != expected_revision:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Request artifacts changed while preparing the update.")])
        atomic_history_write(path, content)
        updated = read_epic(epic.directory)
        require_valid(updated.diagnostics)
        return result("discovery-update", updated.diagnostics, epic=updated.payload(), replayed=False, record_ids=[record["id"] for record in operation["records"]])


def selected_epic(root: Path, epic_id: str, allow_baseline_errors=False) -> Epic:
    if not valid_id(epic_id):
        raise Rejected([error("E_EPIC_ID", root / "requirements", "Expected REQ-0001 through REQ-9999.")])
    epics, diagnostics = scan(root)
    require_valid([item for item in diagnostics if not (allow_baseline_errors and item.code.startswith("E_BASELINE_"))])
    selected = [epic for epic in epics if epic.metadata["id"] == epic_id]
    if not selected:
        raise Rejected([error("E_EPIC_NOT_FOUND", root / "requirements", f"Epic {epic_id} was not found.")])
    return selected[0]


def unresolved_discovery(epic: Epic) -> dict:
    state = epic.discovery_state or {"questions": [], "assumptions": []}
    return {"questions": [item for item in state["questions"] if item["status"] != "answered"], "assumptions": [item for item in state["assumptions"] if item["status"] == "proposed"]}


def lifecycle_change(project: Path, epic_id: str, expected_revision: str, operation_id: str, actor: str, decision: str, action: str) -> dict:
    root = project_path(project)
    if action not in ("complete", "reopen") or not history.valid_revision(expected_revision) or not history.valid_operation_id(operation_id) or not business.valid_person(actor) or not business.valid_person(decision):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected a SHA-256 revision, unique operation ID, declared identity and explicit decision.")])
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        events = epic.metadata.get("lifecycle", [])
        for event in events:
            if event["id"] == operation_id:
                if event["base_revision"] != expected_revision or event["actor"] != actor or event["decision"] != decision or event["action"] != action:
                    raise Rejected([error("E_IDEMPOTENCY", path, "Lifecycle operation ID was reused with different inputs.")])
                return result(f"discovery-{action}", epic.diagnostics, epic=epic.payload(), replayed=True, unresolved=unresolved_discovery(epic))
        if epic.revision != expected_revision:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Discovery revision changed; reopen and reconcile.")])
        allowed = "discovery" if action == "complete" else ("ready_for_refinement", "business_refinement", "ready_for_analysis")
        if epic.metadata["status"] not in ((allowed,) if isinstance(allowed, str) else allowed):
            raise Rejected([error("E_STATUS", path, f"Cannot {action} from {epic.metadata['status']}.")])
        if action == "complete" and epic.discovery is None:
            raise Rejected([error("E_DISCOVERY_HISTORY", epic.directory / "discovery.yaml", "Persist Discovery history before completion.")])
        target = "ready_for_refinement" if action == "complete" else "discovery"
        event = {"id": operation_id, "action": action, "from": epic.metadata["status"], "to": target, "base_revision": expected_revision, "actor": actor, "decision": decision, "timestamp": business.timestamp()}
        candidate = dict(epic.metadata)
        candidate.update(schema_version="0.3" if epic.metadata["schema_version"] == "0.3" else "0.2", status=target, lifecycle=[*events, event])
        checked = read_epic(epic.directory)
        require_valid(checked.diagnostics)
        if checked.revision != expected_revision:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Discovery changed during lifecycle preparation.")])
        atomic_history_write(path, yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True))
        updated = read_epic(epic.directory)
        require_valid(updated.diagnostics)
        return result(f"discovery-{action}", updated.diagnostics, epic=updated.payload(), replayed=False, unresolved=unresolved_discovery(updated))


def business_write(project: Path, epic_id: str, expected_source: str, expected_business: str | None, operation_id: str, editor: str, reason: str, document_path: Path, mode: str) -> dict:
    root = project_path(project)
    if not history.valid_revision(expected_source) or not history.valid_operation_id(operation_id) or not business.valid_person(editor) or not business.valid_person(reason) or (expected_business is not None and not history.valid_revision(expected_business)):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected valid source/business revisions, operation ID, editor and reason.")])
    try:
        content = document_path.read_bytes()
    except OSError as exc:
        raise Rejected([error("E_UPDATE_INPUT", document_path, str(exc))]) from exc
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        ledger_path = epic.directory / "business-history.yaml"
        current = epic.business
        ledger = None
        if current is not None:
            try:
                ledger = yaml.load(ledger_path.read_text(encoding="utf-8"), Loader=StrictLoader)
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                raise Rejected([error("E_BUSINESS_HISTORY", ledger_path, str(exc))]) from exc
            for entry in ledger["revisions"]:
                if entry["operation_id"] == operation_id:
                    if entry["digest"] != business.digest(content) or entry["source_revision"] != expected_source or entry["base_revision"] != expected_business or entry["editor"] != editor or entry["reason"] != reason or entry["mode"] != mode:
                        raise Rejected([error("E_IDEMPOTENCY", ledger_path, "Business operation ID was reused with different inputs.")])
                    return result(f"business-{mode}", epic.diagnostics, epic=epic.payload(), replayed=True)
        if epic.metadata["status"] != "ready_for_refinement" and not (mode == "revise" and epic.metadata["status"] == "business_refinement"):
            raise Rejected([error("E_STATUS", epic.directory / "metadata.yaml", "Business writing requires ready_for_refinement or business_refinement.")])
        if mode == "generate" and current is not None and not current["needs_reconciliation"]:
            raise Rejected([error("E_STATUS", ledger_path, "Generate is for the initial or stale draft; use revise for a current draft.")])
        if mode == "revise" and current is None:
            raise Rejected([error("E_BUSINESS_HISTORY", ledger_path, "No business draft exists to revise.")])
        if epic.source_revision != expected_source or (current["revision"] if current else None) != expected_business:
            raise Rejected([error("E_REVISION_CONFLICT", ledger_path, "Source or business draft changed; reopen and reconcile.")])
        try:
            coverage = business.validate_markdown(content, epic_id, expected_source, epic.discovery, epic.discovery_state)
            candidate = business.append(ledger, epic_id, content, expected_source, editor, reason, operation_id, mode)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
        files = {"business.md": content, "business-history.yaml": yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True).encode("utf-8")}
        if epic.metadata["status"] == "ready_for_refinement":
            metadata = dict(epic.metadata)
            metadata["status"] = "business_refinement"
            metadata["lifecycle"] = [*metadata["lifecycle"], {"id": operation_id, "action": "refine", "from": "ready_for_refinement", "to": "business_refinement", "base_revision": epic.revision, "actor": editor, "decision": reason, "timestamp": business.timestamp()}]
            files["metadata.yaml"] = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).encode("utf-8")
        checked = read_epic(epic.directory)
        require_valid(checked.diagnostics)
        if checked.revision != epic.revision or (checked.business["revision"] if checked.business else None) != expected_business:
            raise Rejected([error("E_REVISION_CONFLICT", ledger_path, "Epic changed during business write preparation.")])
        try:
            business.publish(epic.directory, files)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
        updated = read_epic(epic.directory)
        require_valid(updated.diagnostics)
        return result(f"business-{mode}", updated.diagnostics, epic=updated.payload(), replayed=False, coverage=coverage)


def business_review(project: Path, epic_id: str) -> dict:
    root = project_path(project)
    epic = selected_epic(root, epic_id, allow_baseline_errors=True)
    confirmed, unresolved, proposed = business.source_sets(epic.discovery, epic.discovery_state)
    return result("business-review", epic.diagnostics, epic=epic.payload(), current=bool(epic.business and not epic.business["needs_reconciliation"]), review_revision=epic.review_revision, open_items=epic.open_items, approval=epic.approval, source_records={"confirmed": sorted(confirmed), "unresolved": sorted(unresolved), "proposed": sorted(proposed)})


def business_gate(project: Path, epic_id: str, expected_review: str, expected_business: str, operation_id: str, actor: str, reason: str, decision: str, action: str, acknowledged=None, approval_id=None) -> dict:
    """Record procedural PO decisions or separately advance the approved Epic."""
    root = project_path(project)
    acknowledged = [] if acknowledged is None else acknowledged
    if action not in ("approve", "request_changes", "advance") or not all(history.valid_revision(value) for value in (expected_review, expected_business)) or not history.valid_operation_id(operation_id) or not all(business.valid_person(value) for value in (actor, reason, decision)) or (action == "advance" and decision != reason):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected exact review/business revisions, operation ID, declared identity, reason and explicit decision.")])
    if not isinstance(acknowledged, list) or not all(isinstance(value, str) and re.fullmatch(r"[UP]-[0-9]{3,}", value) for value in acknowledged) or len(set(acknowledged)) != len(acknowledged) or (action != "approve" and acknowledged) or (action == "advance" and (not isinstance(approval_id, str) or not re.fullmatch(r"BD-[0-9]{4,}", approval_id))) or (action != "advance" and approval_id is not None):
        raise Rejected([error("E_UPDATE_INPUT", root, "Invalid acknowledgement list or selected approval ID.")])
    acknowledged = sorted(acknowledged)
    command = "business-" + action.replace("_", "-")
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        for entry in epic.metadata.get("business_decisions", []):
            if entry["operation_id"] == operation_id:
                if entry["action"] != action or entry["review_revision"] != expected_review or entry["business_revision"] != expected_business or entry["actor"] != actor or entry["reason"] != reason or entry["decision"] != decision or entry["acknowledged_open_items"] != acknowledged:
                    raise Rejected([error("E_IDEMPOTENCY", path, "Gate operation ID was already used with different inputs.")])
                return result(command, epic.diagnostics, epic=epic.payload(), replayed=True, decision_id=entry["id"], baseline_id=entry["baseline_id"])
        for event in epic.metadata.get("lifecycle", []):
            if event["id"] == operation_id:
                if event["action"] != "advance" or action != "advance" or event["review_revision"] != expected_review or event["business_revision"] != expected_business or event["actor"] != actor or event["decision"] != reason or decision != reason or event["approval_id"] != approval_id:
                    raise Rejected([error("E_IDEMPOTENCY", path, "Lifecycle operation ID was already used with different inputs.")])
                return result(command, epic.diagnostics, epic=epic.payload(), replayed=True, approval_id=event["approval_id"], baseline_id=event["baseline_id"])
        if epic.metadata["status"] != "business_refinement":
            raise Rejected([error("E_STATUS", path, "Business decisions and advancement require business_refinement.")])
        if epic.business is None or epic.business["needs_reconciliation"]:
            raise Rejected([error("E_APPROVAL_STALE", path, "Business draft requires explicit source reconciliation.")])
        if epic.review_revision != expected_review or epic.business["revision"] != expected_business:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Review context or business revision changed; review again.")])
        candidate = dict(epic.metadata)
        candidate.update(schema_version="0.3", business_decisions=list(epic.metadata.get("business_decisions", [])))
        baseline_id, decision_id = None, None
        if action == "advance":
            latest = epic.approval["latest_decision"]
            if latest is None:
                raise Rejected([error("E_APPROVAL_REQUIRED", path, "No Product Owner approval has been recorded.")])
            if latest["id"] != approval_id or latest["action"] != "approve":
                raise Rejected([error("E_APPROVAL_SUPERSEDED", path, "The selected approval is not the latest Product Owner decision.")])
            if not epic.approval["can_advance"]:
                raise Rejected([error("E_APPROVAL_STALE", path, "Approval is stale: " + ", ".join(epic.approval["reasons"]))])
            baseline_id = latest["baseline_id"]
            candidate["status"] = "ready_for_analysis"
            candidate["lifecycle"] = [*candidate["lifecycle"], {"id": operation_id, "action": "advance", "from": "business_refinement", "to": "ready_for_analysis", "base_revision": epic.revision, "actor": actor, "decision": reason, "timestamp": business.timestamp(), "review_revision": expected_review, "business_revision": expected_business, "approval_id": approval_id, "baseline_id": baseline_id}]
        else:
            if action == "approve" and set(acknowledged) != {item["id"] for item in epic.open_items}:
                raise Rejected([error("E_ACKNOWLEDGEMENT", path, "Explicitly acknowledge exactly the unresolved issues and unconfirmed proposals shown by business-review.")])
            if action == "approve":
                snapshot = approval.read_snapshot(epic.directory, epic.metadata)
                if approval.review_revision(snapshot) != expected_review:
                    raise Rejected([error("E_REVISION_CONFLICT", path, "Artifacts changed before baseline preparation.")])
                try:
                    baseline_id = approval.publish_baseline(epic.directory, epic.metadata, epic.business, snapshot, StrictLoader)
                except business.BusinessError as exc:
                    raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
            decision_id = f"BD-{len(candidate['business_decisions']) + 1:04d}"
            candidate["business_decisions"].append({"id": decision_id, "operation_id": operation_id, "action": action, "actor": actor, "reason": reason, "decision": decision, "timestamp": business.timestamp(), "review_revision": expected_review, **approval.context(epic.metadata, epic.business), "acknowledged_open_items": acknowledged, "baseline_id": baseline_id})
        try:
            business.validate_lifecycle(candidate["lifecycle"], candidate["status"], allow_advance=True)
            approval.validate_decisions(candidate)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, path, str(exc))]) from exc
        checked = read_epic(epic.directory)
        require_valid(checked.diagnostics)
        if checked.review_revision != expected_review:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Artifacts changed while preparing the gate operation.")])
        atomic_history_write(path, yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True))
        updated = read_epic(epic.directory)
        require_valid(updated.diagnostics)
        return result(command, updated.diagnostics, epic=updated.payload(), replayed=False, decision_id=decision_id, approval_id=approval_id, baseline_id=baseline_id)


def business_recover(project: Path, epic_id: str) -> dict:
    root = project_path(project)
    with project_lock(root):
        if not valid_id(epic_id):
            raise Rejected([error("E_EPIC_ID", root, "Invalid Epic ID.")])
        matches = []
        for directory in (root / "requirements").iterdir():
            path = directory / "metadata.yaml"
            if directory.is_dir() and not directory.is_symlink() and path.is_file() and not path.is_symlink():
                try:
                    data = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)
                except (OSError, UnicodeError, yaml.YAMLError):
                    continue
                if isinstance(data, dict) and data.get("id") == epic_id:
                    matches.append(directory)
        if len(matches) != 1:
            raise Rejected([error("E_EPIC_NOT_FOUND", root / "requirements", "Expected one matching Epic for recovery.")])
        try:
            business.recover(matches[0])
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, matches[0] / exc.filename, str(exc))]) from exc
        epic = selected_epic(root, epic_id)
        return result("business-recover", epic.diagnostics, epic=epic.payload())


def read_changes(path: Path) -> list:
    def mapping(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=mapping)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise Rejected([Diagnostic("error", "E_UPDATE_INPUT", str(path), str(exc), getattr(exc, "lineno", None))]) from exc
    if not isinstance(data, dict) or set(data) != {"records"} or not isinstance(data["records"], list):
        raise Rejected([error("E_UPDATE_INPUT", path, "Changes must contain exactly one records list.")])
    return data["records"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=ORCHESTRATOR_VERSION)
    parser.add_argument("--project", required=True, type=Path, help="Explicit target project root")
    commands = parser.add_subparsers(dest="operation", required=True)
    create = commands.add_parser("new", help="Create a local Discovery Epic")
    create.add_argument("--title", required=True)
    create.add_argument("--idea", default="", help="Initial business description; stored as content only")
    commands.add_parser("open", help="Read an Epic by stable ID").add_argument("id")
    commands.add_parser("validate", help="Validate one Epic or all local Epics").add_argument("id", nargs="?")
    update = commands.add_parser("discovery-update", help="Atomically append typed Discovery records")
    update.add_argument("id")
    update.add_argument("--expected-revision", required=True)
    update.add_argument("--operation-id", required=True)
    update.add_argument("--changes-file", required=True, type=Path)
    for name, who in (("discovery-complete", "requester"), ("discovery-reopen", "requester")):
        command = commands.add_parser(name, help="Explicitly complete or reopen Discovery")
        command.add_argument("id")
        command.add_argument("--expected-revision", required=True)
        command.add_argument("--operation-id", required=True)
        command.add_argument(f"--{who}", required=True)
        command.add_argument("--decision", required=True)
    for name in ("business-generate", "business-revise"):
        command = commands.add_parser(name, help="Persist an AI-drafted or human-refined business document")
        command.add_argument("id")
        command.add_argument("--expected-source-revision", required=True)
        command.add_argument("--expected-business-revision")
        command.add_argument("--operation-id", required=True)
        command.add_argument("--editor", required=True)
        command.add_argument("--reason", required=True)
        command.add_argument("--document-file", required=True, type=Path)
    commands.add_parser("business-review", help="Read draft, source coverage and reconciliation state").add_argument("id")
    for name, identity in (("business-request-changes", "reviewer"), ("business-approve", "approver"), ("business-advance", "actor")):
        command = commands.add_parser(name, help="Record a procedural PO decision or separately advance")
        command.add_argument("id")
        command.add_argument("--expected-review-revision", required=True)
        command.add_argument("--expected-business-revision", required=True)
        command.add_argument("--operation-id", required=True)
        command.add_argument(f"--{identity}", required=True, dest="gate_actor")
        command.add_argument("--reason", required=True)
        if name == "business-approve":
            command.add_argument("--decision", required=True)
            command.add_argument("--acknowledge-open-item", action="append", default=[])
        elif name == "business-request-changes":
            command.add_argument("--feedback", required=True)
        else:
            command.add_argument("--approval-id", required=True)
    commands.add_parser("business-recover", help="Roll forward an inspected interrupted business publication").add_argument("id")
    args = parser.parse_args(argv)
    try:
        if args.operation == "new":
            output = new_epic(args.project, args.title, args.idea)
        elif args.operation == "discovery-update":
            output = discovery_update(args.project, args.id, args.expected_revision, args.operation_id, read_changes(args.changes_file))
        elif args.operation in ("discovery-complete", "discovery-reopen"):
            output = lifecycle_change(args.project, args.id, args.expected_revision, args.operation_id, args.requester, args.decision, args.operation.removeprefix("discovery-"))
        elif args.operation in ("business-generate", "business-revise"):
            output = business_write(args.project, args.id, args.expected_source_revision, args.expected_business_revision, args.operation_id, args.editor, args.reason, args.document_file, args.operation.removeprefix("business-"))
        elif args.operation == "business-review":
            output = business_review(args.project, args.id)
        elif args.operation in ("business-approve", "business-request-changes", "business-advance"):
            action = args.operation.removeprefix("business-").replace("-", "_")
            text = args.decision if action == "approve" else args.feedback if action == "request_changes" else args.reason
            output = business_gate(args.project, args.id, args.expected_review_revision, args.expected_business_revision, args.operation_id, args.gate_actor, args.reason, text, action, getattr(args, "acknowledge_open_item", []), getattr(args, "approval_id", None))
        elif args.operation == "business-recover":
            output = business_recover(args.project, args.id)
        else:
            output = inspect_epics(args.project, args.operation, args.id)
    except Rejected as exc:
        output = result(args.operation, exc.diagnostics)
    except (OSError, UnicodeError) as exc:
        output = result(args.operation, [error("E_IO", Path(getattr(exc, "filename", None) or args.project), str(exc))])
    print(json.dumps(output, ensure_ascii=False))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
