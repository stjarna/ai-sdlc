"""Deterministic local SDLC artifact operations. No AI, Git or host-agent integration."""

from __future__ import annotations

import argparse
import base64
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
import functional_analysis as analysis
import analysis_approval as analysis_gate_policy
import approval_common as approval_common
import local_identity
import artifact_names
import command_ux
import ownership
import engineering
import domain_skills
import work_tracks
from engineering_contract import STAGES as ENGINEERING_STAGES


SCHEMA_VERSION = "0.1"
ORCHESTRATOR_VERSION = "0.10.0"
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
    analysis: dict | None = None
    analysis_review_revision: str | None = None
    analysis_approval: dict | None = None
    analysis_open_items: list = field(default_factory=list)

    def payload(self) -> dict:
        return {
            "directory": str(self.directory), "metadata": self.metadata,
            "documents": artifact_names.epic_documents(self),
            "idea": self.idea,
            "revision": self.revision, "discovery": self.discovery,
            "discovery_state": self.discovery_state,
            "source_revision": self.source_revision, "business": self.business,
            "review_revision": self.review_revision, "approval": self.approval,
            "open_items": self.open_items, "analysis": self.analysis,
            "analysis_review_revision": self.analysis_review_revision,
            "analysis_approval": self.analysis_approval, "analysis_open_items": self.analysis_open_items,
            "ownership": ownership.view(self.metadata) if self.metadata.get("status") in (*ownership.STAGES, "cancelled") else None,
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
    expected_fields = set(FIELDS) if version == SCHEMA_VERSION else FIELDS | {"lifecycle"}
    if version in ("0.3", "0.4", "0.5", "0.6"):
        expected_fields |= {"business_decisions"}
    if version in ("0.5", "0.6"):
        expected_fields |= {"analysis_decisions"}
    if version == "0.6":
        expected_fields |= {"engineering_history"}
    if "work_tracks" in data:
        expected_fields |= {"work_tracks"}
    if "ownership" in data:
        expected_fields |= {"ownership"}
    if set(data) != expected_fields:
        epic.diagnostics.append(error(
            "E_METADATA", metadata_path,
            f"Expected exactly these fields: {', '.join(sorted(expected_fields))}.",
        ))
    if version not in (SCHEMA_VERSION, "0.2", "0.3", "0.4", "0.5", "0.6"):
        epic.diagnostics.append(error(
            "E_SCHEMA_VERSION", metadata_path,
            "Supported schema_version values are the strings '0.1', '0.2', '0.3', '0.4', '0.5' and '0.6'.",
        ))
    if not valid_id(data.get("id")):
        epic.diagnostics.append(error("E_EPIC_ID", metadata_path, "Expected REQ-0001 through REQ-9999."))
    if not valid_title(data.get("title")):
        epic.diagnostics.append(error("E_TITLE", metadata_path, "Title must be nonempty, single-line text."))
    # Cancelled records reserve IDs; this CLI provides no cancellation transition.
    statuses = ("discovery", "cancelled") if version == SCHEMA_VERSION else ("discovery", "ready_for_refinement", "business_refinement")
    if version in ("0.3", "0.4", "0.5", "0.6"):
        statuses += ("ready_for_analysis",)
    if version in ("0.4", "0.5", "0.6"):
        statuses += ("functional_analysis",)
    if version in ("0.5", "0.6"):
        statuses += ("ready_for_technical_design",)
    if version == "0.6":
        statuses += ENGINEERING_STAGES
    if data.get("status") not in statuses:
        epic.diagnostics.append(error(
            "E_STATUS", metadata_path, f"Supported record statuses are {', '.join(statuses)}."
        ))
    if version in ("0.2", "0.3", "0.4", "0.5", "0.6"):
        try:
            business.validate_lifecycle(data["lifecycle"], data.get("status"), allow_advance=version in ("0.3", "0.4", "0.5", "0.6"), allow_analysis=version in ("0.4", "0.5", "0.6"), allow_analysis_approval=version in ("0.5", "0.6"), allow_engineering=version == "0.6")
            if version in ("0.3", "0.4", "0.5", "0.6"):
                approval.validate_decisions(data)
            if version in ("0.5", "0.6"):
                analysis_gate_policy.validate_decisions(data)
        except (KeyError, business.BusinessError) as exc:
            epic.diagnostics.append(error(exc.code if isinstance(exc, business.BusinessError) else "E_LIFECYCLE", metadata_path, str(exc)))
    if not any(item.severity == "error" for item in epic.diagnostics):
        try:
            ownership.validate(data)
            work_tracks.validate(data)
        except business.BusinessError as exc:
            epic.diagnostics.append(error(exc.code, metadata_path, str(exc)))
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
            or any(name in relative.parts[:1] for name in ("business-baselines", "analysis-baselines", "engineering-baselines"))
            or relative.as_posix() in ("specification.md", "analysis-history.yaml", ".analysis-transaction.json")
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
            epic.analysis, epic.analysis_review_revision = analysis.read(epic, StrictLoader)
            analysis_errors = analysis_gate_policy.check_baselines(directory, data, epic.analysis, StrictLoader)
            epic.diagnostics.extend(error(exc.code, directory / exc.filename, str(exc)) for exc in analysis_errors)
            epic.analysis_approval = analysis_gate_policy.evaluate(epic, analysis_errors, StrictLoader)
            if epic.analysis:
                epic.analysis_open_items = analysis_gate_policy.open_items(analysis_gate_policy.details_for(directory, data["id"], epic.analysis, StrictLoader))
            if version == "0.6":
                engineering.validate_history(epic)
            if data.get("work_tracks"):
                import qa_track
                qa_track.validate_history(epic)
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


def new_epic(project: Path, title: str, idea: str = "", requester: str | None = None) -> dict:
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
        requester, source = local_identity.attribution(root, requester)
        if not business.valid_person(requester):
            raise Rejected([error("E_UPDATE_INPUT", root, "Declare the requester or set up the local identity profile before creating a request.")])
        metadata["ownership"] = ownership.initialized("discovery", requester, requester, source,
            "ownership-created", "Initial accountability belongs to the declared requester.")
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
        reject_analysis_decision_reuse(epic, operation_id)
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


def lifecycle_change(project: Path, epic_id: str, expected_revision: str, operation_id: str, actor: str, decision: str, action: str, identity_source=None) -> dict:
    root = project_path(project)
    source_fields = attribution_fields(identity_source, root)
    if action not in ("complete", "reopen") or not history.valid_revision(expected_revision) or not history.valid_operation_id(operation_id) or not business.valid_person(actor) or not business.valid_person(decision):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected a SHA-256 revision, unique operation ID, declared identity and explicit decision.")])
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        events = epic.metadata.get("lifecycle", [])
        for event in events:
            if event["id"] == operation_id:
                if event["base_revision"] != expected_revision or event["actor"] != actor or event["decision"] != decision or event["action"] != action or event.get("identity_source") != identity_source:
                    raise Rejected([error("E_IDEMPOTENCY", path, "Lifecycle operation ID was reused with different inputs.")])
                return result(f"discovery-{action}", epic.diagnostics, epic=epic.payload(), replayed=True, unresolved=unresolved_discovery(epic))
        reject_analysis_decision_reuse(epic, operation_id)
        if epic.revision != expected_revision:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Discovery revision changed; reopen and reconcile.")])
        allowed = "discovery" if action == "complete" else ("ready_for_refinement", "business_refinement", "ready_for_analysis", "functional_analysis", "ready_for_technical_design", *ENGINEERING_STAGES)
        if epic.metadata["status"] not in ((allowed,) if isinstance(allowed, str) else allowed):
            raise Rejected([error("E_STATUS", path, f"Cannot {action} from {epic.metadata['status']}.")])
        if action == "complete" and epic.discovery is None:
            raise Rejected([error("E_DISCOVERY_HISTORY", epic.directory / "discovery.yaml", "Persist Discovery history before completion.")])
        target = "ready_for_refinement" if action == "complete" else "discovery"
        event = {"id": operation_id, "action": action, "from": epic.metadata["status"], "to": target, "base_revision": expected_revision, "actor": actor, "decision": decision, "timestamp": business.timestamp(), **source_fields}
        candidate = dict(epic.metadata)
        candidate.update(schema_version=epic.metadata["schema_version"] if epic.metadata["schema_version"] in ("0.3", "0.4", "0.5", "0.6") else "0.2", status=target, lifecycle=[*events, event])
        try:
            ownership.handoff(epic.metadata, candidate, actor, identity_source)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, path, str(exc))]) from exc
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
        reject_analysis_decision_reuse(epic, operation_id)
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


def attribution_fields(source, path):
    if source is None:
        return {}
    if source != local_identity.SOURCE:
        raise Rejected([error("E_UPDATE_INPUT", path, "Only unauthenticated local_profile attribution is supported.")])
    return {"identity_source": source}


def validate_gate_metadata(candidate):
    version = candidate["schema_version"]
    business.validate_lifecycle(candidate["lifecycle"], candidate["status"], allow_advance=True,
        allow_analysis=version in ("0.4", "0.5", "0.6"), allow_analysis_approval=version in ("0.5", "0.6"), allow_engineering=version == "0.6")
    approval.validate_decisions(candidate)
    ownership.validate(candidate)
    work_tracks.validate(candidate)
    if version in ("0.5", "0.6"):
        analysis_gate_policy.validate_decisions(candidate)


def commit_gate(epic, candidate, expected, token):
    def checked_read(directory):
        checked = read_epic(directory)
        require_valid(checked.diagnostics)
        return checked
    try:
        if candidate["status"] != epic.metadata["status"]:
            ownership.handoff(epic.metadata, candidate, candidate["lifecycle"][-1]["actor"], candidate["lifecycle"][-1].get("identity_source"))
        if candidate["lifecycle"][-1]["action"] == "analysis_advance" and candidate["status"] != epic.metadata["status"]:
            work_tracks.fork(epic.metadata,candidate,candidate["lifecycle"][-1]["actor"],candidate["lifecycle"][-1].get("identity_source"))
        approval_common.persist_decision(epic, candidate, expected, checked_read, token, validate_gate_metadata,
            lambda path, value: atomic_history_write(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True)))
    except business.BusinessError as exc:
        raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc


def reject_analysis_decision_reuse(epic, operation_id):
    if operation_id in work_tracks.operation_ids(epic.metadata):
        raise Rejected([error("E_IDEMPOTENCY",epic.directory/"metadata.yaml","Operation ID belongs to a work-track event.")])
    if any(e["operation_id"] == operation_id for e in epic.metadata.get("engineering_history", [])):
        raise Rejected([error("E_IDEMPOTENCY", epic.directory / "metadata.yaml", "Operation ID belongs to engineering history.")])
    if any(e["operation_id"] == operation_id for e in epic.metadata.get("ownership", {}).get("history", [])):
        raise Rejected([error("E_IDEMPOTENCY", epic.directory / "metadata.yaml", "Operation ID already belongs to an ownership event.")])
    if any(e["operation_id"] == operation_id for e in epic.metadata.get("analysis_decisions", [])):
        raise Rejected([error("E_IDEMPOTENCY", epic.directory / "metadata.yaml", "Operation ID already belongs to an Analysis decision.")])


def reject_gate_operation_reuse(epic, operation_id):
    ids = {e["operation_id"] for name in ("business_decisions", "analysis_decisions", "engineering_history") for e in epic.metadata.get(name, [])}
    ids.update(work_tracks.operation_ids(epic.metadata))
    ids.update(e["id"] for e in epic.metadata.get("lifecycle", []))
    ids.update(e["operation_id"] for e in epic.metadata.get("ownership", {}).get("history", []))
    for draft in (epic.business, epic.analysis):
        if draft:
            ids.update(e["operation_id"] for e in draft["history"])
    business.require(operation_id not in ids, "E_IDEMPOTENCY", "Operation ID already belongs to another operation.", "metadata.yaml")


def analysis_gate(project: Path, epic_id: str, expected_review: str, expected_analysis: str, expected_baseline: str,
                  expected_handoff: str, operation_id: str, actor: str, reason: str, decision: str,
                  action: str, acknowledged=None, approval_id=None, identity_source=None) -> dict:
    root = project_path(project)
    source_fields = attribution_fields(identity_source, root)
    acknowledged = [] if acknowledged is None else acknowledged
    if action not in ("approve", "request_changes", "advance") or not all(history.valid_revision(v) for v in (expected_review, expected_analysis, expected_baseline)) or not all(history.valid_operation_id(v) for v in (expected_handoff, operation_id)) or not all(business.valid_person(v) for v in (actor, reason)) or not analysis_gate_policy.valid_decision_text(decision) or (action == "advance" and decision != reason):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected exact Analysis context, operation ID, declared identity, reason and explicit decision.")])
    if not isinstance(acknowledged, list) or not all(isinstance(v, str) and analysis_gate_policy.ITEM_ID.fullmatch(v) for v in acknowledged) or len(set(acknowledged)) != len(acknowledged) or (action != "approve" and acknowledged) or (action == "advance" and (not isinstance(approval_id, str) or not re.fullmatch(r"AD-[0-9]{4,}", approval_id))) or (action != "advance" and approval_id is not None):
        raise Rejected([error("E_UPDATE_INPUT", root, "Invalid Analysis acknowledgements or selected approval ID.")])
    acknowledged = sorted(acknowledged)
    command = "analysis-" + action.replace("_", "-")
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        inputs = {"review_revision": expected_review, "analysis_revision": expected_analysis,
                  "business_baseline_id": expected_baseline, "business_handoff_id": expected_handoff, "actor": actor}
        try:
            replay = approval_common.replay(epic.metadata.get("analysis_decisions", []), epic.metadata.get("lifecycle", []), operation_id,
                {**inputs, "identity_source": identity_source, "action": action, "reason": reason, "decision": decision, "acknowledged_open_items": acknowledged} if action != "advance" else None,
                {**inputs, "identity_source": identity_source, "action": "analysis_advance", "decision": reason, "approval_id": approval_id} if action == "advance" else None)
            if replay:
                entry, advancement = replay
                fields = {"approval_id": entry["approval_id"]} if advancement else {"decision_id": entry["id"]}
                return result(command, epic.diagnostics, epic=epic.payload(), replayed=True, baseline_id=entry["baseline_id"], **fields)
            reject_gate_operation_reuse(epic, operation_id)
            analysis_gate_policy.require(epic.metadata["status"] == "functional_analysis", "Analysis decisions and advancement require functional_analysis.", "E_STATUS")
            analysis_gate_policy.require(epic.analysis is not None and not epic.analysis["needs_reconciliation"] and epic.approval["valid"], "Analysis or upstream Business approval requires reconciliation.", "E_APPROVAL_STALE")
            analysis_gate_policy.require(epic.analysis["baseline_id"] == expected_baseline and epic.analysis["handoff_id"] == expected_handoff, "Active business handoff changed.", "E_ANALYSIS_INPUT")
            analysis_gate_policy.require(epic.analysis_review_revision == expected_review and epic.analysis["revision"] == expected_analysis, "Analysis context changed; review again.", "E_REVISION_CONFLICT")
            candidate = {**epic.metadata, "schema_version": "0.6" if epic.metadata["schema_version"] == "0.6" else "0.5", "analysis_decisions": list(epic.metadata.get("analysis_decisions", []))}
            baseline_id, decision_id = None, None
            if action == "advance":
                latest = epic.analysis_approval["latest_decision"]
                analysis_gate_policy.require(latest is not None, "No Analysis approval has been recorded.", "E_APPROVAL_REQUIRED")
                analysis_gate_policy.require(latest["id"] == approval_id and latest["action"] == "approve", "Selected approval is not the latest Analysis decision.", "E_APPROVAL_SUPERSEDED")
                analysis_gate_policy.require(epic.analysis_approval["can_advance"], "Analysis approval is stale: " + ", ".join(epic.analysis_approval["reasons"]), "E_APPROVAL_STALE")
                baseline_id = latest["baseline_id"]
                candidate["status"] = "ready_for_technical_design"
                candidate["lifecycle"] = [*candidate["lifecycle"], {"id": operation_id, "action": "analysis_advance", "from": "functional_analysis", "to": "ready_for_technical_design", "base_revision": epic.revision, "actor": actor, "decision": reason, "timestamp": business.timestamp(), **source_fields, "review_revision": expected_review, **analysis_gate_policy.context(epic.analysis), "approval_id": approval_id, "baseline_id": baseline_id}]
            else:
                if action == "approve":
                    approval_common.exact_acknowledgements(acknowledged, epic.analysis_open_items, "Explicitly acknowledge exactly all unresolved items shown by analysis-review; acknowledgement does not resolve them.")
                    analysis_gate_policy.require(analysis_gate_policy.current_inputs_match(epic, StrictLoader), "Live supporting artifacts differ from the approved Business baseline; explicitly reconcile upstream before approval.", "E_APPROVAL_STALE")
                    snapshot = analysis_gate_policy.read_snapshot(epic.directory)
                    analysis_gate_policy.require(analysis.review_revision(epic) == expected_review, "Artifacts changed before baseline preparation.", "E_REVISION_CONFLICT")
                    baseline_id = analysis_gate_policy.publish_baseline(epic.directory, epic.metadata, epic.analysis, snapshot, acknowledged, StrictLoader)
                decision_id = f"AD-{len(candidate['analysis_decisions']) + 1:04d}"
                candidate["analysis_decisions"].append({"id": decision_id, "operation_id": operation_id, "action": action, "actor": actor, "reason": reason, "decision": decision, "timestamp": business.timestamp(), **source_fields, "review_revision": expected_review, **analysis_gate_policy.context(epic.analysis), "acknowledged_open_items": acknowledged, "baseline_id": baseline_id})
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
        commit_gate(epic, candidate, expected_review, lambda e: e.analysis_review_revision)
        updated = selected_epic(root, epic_id)
        return result(command, updated.diagnostics, epic=updated.payload(), replayed=False, decision_id=decision_id, approval_id=approval_id, baseline_id=baseline_id)


def business_gate(project: Path, epic_id: str, expected_review: str, expected_business: str, operation_id: str, actor: str, reason: str, decision: str, action: str, acknowledged=None, approval_id=None, identity_source=None) -> dict:
    """Record procedural PO decisions or separately advance the approved Epic."""
    root = project_path(project)
    source_fields = attribution_fields(identity_source, root)
    acknowledged = [] if acknowledged is None else acknowledged
    if action not in ("approve", "request_changes", "advance") or not all(history.valid_revision(value) for value in (expected_review, expected_business)) or not history.valid_operation_id(operation_id) or not all(business.valid_person(value) for value in (actor, reason)) or not analysis_gate_policy.valid_decision_text(decision) or (action == "advance" and decision != reason):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected exact review/business revisions, operation ID, declared identity, reason and explicit decision.")])
    if not isinstance(acknowledged, list) or not all(isinstance(value, str) and re.fullmatch(r"[UP]-[0-9]{3,}", value) for value in acknowledged) or len(set(acknowledged)) != len(acknowledged) or (action != "approve" and acknowledged) or (action == "advance" and (not isinstance(approval_id, str) or not re.fullmatch(r"BD-[0-9]{4,}", approval_id))) or (action != "advance" and approval_id is not None):
        raise Rejected([error("E_UPDATE_INPUT", root, "Invalid acknowledgement list or selected approval ID.")])
    acknowledged = sorted(acknowledged)
    command = "business-" + action.replace("_", "-")
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        try:
            replay = approval_common.replay(epic.metadata.get("business_decisions", []), epic.metadata.get("lifecycle", []), operation_id,
                {"identity_source": identity_source, "action": action, "review_revision": expected_review, "business_revision": expected_business, "actor": actor, "reason": reason, "decision": decision, "acknowledged_open_items": acknowledged} if action != "advance" else None,
                {"identity_source": identity_source, "action": "advance", "review_revision": expected_review, "business_revision": expected_business, "actor": actor, "decision": reason, "approval_id": approval_id} if action == "advance" else None)
            if replay:
                entry, advancement = replay
                fields = {"approval_id": entry["approval_id"]} if advancement else {"decision_id": entry["id"]}
                return result(command, epic.diagnostics, epic=epic.payload(), replayed=True, baseline_id=entry["baseline_id"], **fields)
            reject_analysis_decision_reuse(epic, operation_id)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
        if epic.metadata["status"] != "business_refinement":
            raise Rejected([error("E_STATUS", path, "Business decisions and advancement require business_refinement.")])
        if epic.business is None or epic.business["needs_reconciliation"]:
            raise Rejected([error("E_APPROVAL_STALE", path, "Business draft requires explicit source reconciliation.")])
        if epic.review_revision != expected_review or epic.business["revision"] != expected_business:
            raise Rejected([error("E_REVISION_CONFLICT", path, "Review context or business revision changed; review again.")])
        candidate = dict(epic.metadata)
        candidate.update(schema_version=epic.metadata["schema_version"] if epic.metadata["schema_version"] in ("0.4", "0.5", "0.6") else "0.3", business_decisions=list(epic.metadata.get("business_decisions", [])))
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
            candidate["lifecycle"] = [*candidate["lifecycle"], {"id": operation_id, "action": "advance", "from": "business_refinement", "to": "ready_for_analysis", "base_revision": epic.revision, "actor": actor, "decision": reason, "timestamp": business.timestamp(), **source_fields, "review_revision": expected_review, "business_revision": expected_business, "approval_id": approval_id, "baseline_id": baseline_id}]
        else:
            if action == "approve":
                try:
                    approval_common.exact_acknowledgements(acknowledged, epic.open_items, "Explicitly acknowledge exactly the unresolved issues and unconfirmed proposals shown by business-review.")
                except business.BusinessError as exc:
                    raise Rejected([error(exc.code, path, str(exc))]) from exc
            if action == "approve":
                snapshot = approval.read_snapshot(epic.directory, epic.metadata)
                if approval.review_revision(snapshot) != expected_review:
                    raise Rejected([error("E_REVISION_CONFLICT", path, "Artifacts changed before baseline preparation.")])
                try:
                    baseline_id = approval.publish_baseline(epic.directory, epic.metadata, epic.business, snapshot, StrictLoader)
                except business.BusinessError as exc:
                    raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
            decision_id = f"BD-{len(candidate['business_decisions']) + 1:04d}"
            candidate["business_decisions"].append({"id": decision_id, "operation_id": operation_id, "action": action, "actor": actor, "reason": reason, "decision": decision, "timestamp": business.timestamp(), **source_fields, "review_revision": expected_review, **approval.context(epic.metadata, epic.business), "acknowledged_open_items": acknowledged, "baseline_id": baseline_id})
        commit_gate(epic, candidate, expected_review, lambda e: e.review_revision)
        updated = read_epic(epic.directory)
        require_valid(updated.diagnostics)
        return result(command, updated.diagnostics, epic=updated.payload(), replayed=False, decision_id=decision_id, approval_id=approval_id, baseline_id=baseline_id)


def analysis_review(project: Path, epic_id: str) -> dict:
    epic = selected_epic(project_path(project), epic_id, allow_baseline_errors=True)
    source, details = None, None
    try:
        if analysis.handoff(epic.metadata) is not None:
            source = analysis.approved_input(epic, StrictLoader)
        if epic.analysis:
            _, frozen = approval.read_baseline(epic.directory, epic.analysis["baseline_id"], StrictLoader)
            details = analysis.validate_document(epic.analysis["content"].encode("utf-8"), epic_id, {**epic.analysis, "business": frozen["business.md"].decode("utf-8"), "discovery": yaml.load(frozen["discovery.yaml"].decode("utf-8"), Loader=StrictLoader)})
    except business.BusinessError as exc:
        epic.diagnostics.append(error(exc.code, epic.directory / exc.filename, str(exc)))
    can_approve = bool(epic.analysis and not epic.analysis["needs_reconciliation"]
        and epic.metadata["status"] == "functional_analysis"
        and not any(d.severity == "error" for d in epic.diagnostics)
        and analysis_gate_policy.current_inputs_match(epic, StrictLoader))
    return result("analysis-review", epic.diagnostics, epic=epic.payload(), input=source,
        current=bool(epic.analysis and not epic.analysis["needs_reconciliation"]),
        analysis_review_revision=epic.analysis_review_revision, details=details,
        approval_implemented=True, analysis_approval=epic.analysis_approval,
        analysis_open_items=epic.analysis_open_items, can_approve=can_approve,
        semantic_assessment="not_performed_by_cli")


def analysis_write(project: Path, epic_id: str, expected_review: str, expected_analysis: str | None, expected_baseline: str, expected_handoff: str, operation_id: str, editor: str, reason: str, document_path: Path, mode: str, feedback_path: Path | None = None) -> dict:
    root = project_path(project)
    if mode not in ("generate", "revise") or not all(history.valid_revision(v) for v in (expected_review, expected_baseline)) or not all(history.valid_operation_id(v) for v in (expected_handoff, operation_id)) or not all(business.valid_person(v) for v in (editor, reason)) or (expected_analysis is not None and not history.valid_revision(expected_analysis)):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected exact Analysis review/input revisions, operation ID, editor and reason.")])
    try:
        content = document_path.read_bytes()
        feedback = analysis.feedback_data(feedback_path, StrictLoader)
    except business.BusinessError as exc:
        raise Rejected([error(exc.code, root, str(exc))]) from exc
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        ledger = analysis.read_history(epic.directory, epic_id, StrictLoader) if epic.analysis else {"schema_version": "0.1", "request_id": epic_id, "revisions": []}
        for entry in ledger["revisions"]:
            if entry["operation_id"] == operation_id:
                if any(entry[k] != v for k, v in {"digest": business.digest(content), "previous": expected_analysis, "baseline_id": expected_baseline, "handoff_id": expected_handoff, "expected_review": expected_review, "editor": editor, "reason": reason, "mode": mode, "feedback": feedback}.items()):
                    raise Rejected([error("E_IDEMPOTENCY", epic.directory / analysis.FILES[1], "Analysis operation ID was reused with different inputs.")])
                return result("analysis-" + mode, epic.diagnostics, epic=epic.payload(), replayed=True)
        # A new write cannot reuse another lifecycle or business decision operation.
        if any(e["id"] == operation_id for e in epic.metadata.get("lifecycle", [])) or any(e["operation_id"] == operation_id for e in epic.metadata.get("business_decisions", []) + epic.metadata.get("analysis_decisions", [])):
            raise Rejected([error("E_IDEMPOTENCY", epic.directory, "Operation ID already belongs to another operation.")])
        try:
            analysis.require(epic.metadata["status"] not in ("ready_for_technical_design", *ENGINEERING_STAGES), "Analysis is frozen after advancement; explicitly reopen upstream Discovery for a new cycle.", "E_STATUS")
            source = analysis.approved_input(epic, StrictLoader)
            analysis.require(source["baseline_id"] == expected_baseline and source["handoff_id"] == expected_handoff, "The active business handoff changed.", "E_ANALYSIS_INPUT")
            analysis.require(epic.analysis_review_revision == expected_review and (epic.analysis["revision"] if epic.analysis else None) == expected_analysis, "Analysis review context changed; review again.", "E_REVISION_CONFLICT")
            analysis.require(mode != "revise" or epic.analysis is not None, "No Analysis draft exists to revise.", "E_STATUS")
            analysis.require(mode != "generate" or epic.analysis is None or epic.analysis["needs_reconciliation"], "Use analysis-revise for the current draft.", "E_STATUS")
            details = analysis.validate_document(content, epic_id, source)
            if epic.analysis:
                _, old_files = approval.read_baseline(epic.directory, epic.analysis["baseline_id"], StrictLoader)
                old = analysis.validate_document(epic.analysis["content"].encode(), epic_id, {**epic.analysis, "business": old_files["business.md"].decode(), "discovery": yaml.load(old_files["discovery.yaml"].decode(), Loader=StrictLoader)})
                analysis.stable_items(old["items"], details["items"])
            if feedback:
                analysis.require(set(feedback["items"]) <= set(details["items"]), "Feedback references unknown Analysis items.", "E_ANALYSIS_REFERENCE")
            entry = {"digest": business.digest(content), "previous": expected_analysis, "content_base64": base64.b64encode(content).decode("ascii"), **{k: source[k] for k in ("baseline_id", "approval_id", "handoff_id")}, "editor": editor, "reason": reason, "timestamp": business.timestamp(), "operation_id": operation_id, "expected_review": expected_review, "mode": mode, "feedback": feedback}
            ledger["revisions"].append(entry)
            files = {"specification.md": content, "analysis-history.yaml": yaml.safe_dump(ledger, sort_keys=False, allow_unicode=True).encode("utf-8")}
            if epic.metadata["status"] == "ready_for_analysis":
                metadata = dict(epic.metadata)
                metadata.update(schema_version=metadata["schema_version"] if metadata["schema_version"] in ("0.5", "0.6") else "0.4", status="functional_analysis", lifecycle=[*metadata["lifecycle"], {"id": operation_id, "action": "analyze", "from": "ready_for_analysis", "to": "functional_analysis", "base_revision": epic.revision, "actor": editor, "decision": reason, "timestamp": entry["timestamp"], "review_revision": epic.review_revision, "business_revision": epic.business["revision"], **{k: source[k] for k in ("baseline_id", "approval_id", "handoff_id")}}])
                files["metadata.yaml"] = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).encode("utf-8")
            checked = read_epic(epic.directory)
            require_valid(checked.diagnostics)
            analysis.require(checked.analysis_review_revision == expected_review, "Artifacts changed during Analysis preparation.", "E_REVISION_CONFLICT")
            business.publish(epic.directory, files, analysis=True)
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, epic.directory / exc.filename, str(exc))]) from exc
        updated = selected_epic(root, epic_id)
        return result("analysis-" + mode, updated.diagnostics, epic=updated.payload(), replayed=False, details=details)


def business_recover(project: Path, epic_id: str, *, recover_analysis=False) -> dict:
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
            business.recover(matches[0], analysis=True) if recover_analysis else business.recover(matches[0])
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, matches[0] / exc.filename, str(exc))]) from exc
        epic = selected_epic(root, epic_id)
        return result("analysis-recover" if recover_analysis else "business-recover", epic.diagnostics, epic=epic.payload())


def ownership_change(project: Path, epic_id: str, expected_revision: str, operation_id: str,
                     actor: str, decision: str, assignee: str, *, initialize=False, identity_source=None, track=None) -> dict:
    root = project_path(project)
    selected=selected_epic(root,epic_id)
    if selected.metadata.get("work_tracks") and selected.metadata["status"] in __import__("engineering_contract").DOWNSTREAM and not initialize:
        if track not in work_tracks.NAMES:
            raise Rejected([error("E_TRACK_AMBIGUOUS",root,"Which track should be assigned: Engineering or QA?")])
        return work_tracks.update(root,epic_id,expected_revision,operation_id,"assign",track,actor,decision,assignee,identity_source)
    if track is not None:
        raise Rejected([error("E_TRACK_REQUIRED",root,"This legacy request has no work tracks.")])
    attribution_fields(identity_source, root)
    if not history.valid_revision(expected_revision) or not history.valid_operation_id(operation_id) or not all(business.valid_person(v) for v in (actor, assignee)) or not ownership.text(decision):
        raise Rejected([error("E_UPDATE_INPUT", root, "Expected reviewed revision, operation ID, declared actor, assignee and actual explicit confirmation.")])
    action = "initialize" if initialize else "assign"
    command = "ownership-initialize" if initialize else "assign"
    with project_lock(root):
        epic = selected_epic(root, epic_id)
        path = epic.directory / "metadata.yaml"
        try:
            for event in epic.metadata.get("ownership", {}).get("history", []):
                if event["operation_id"] == operation_id:
                    ownership.require(all(event[k] == v for k, v in {"action": action, "expected_revision": expected_revision, "actor": actor, "decision": decision, "to_owner": assignee, "identity_source": identity_source or "declared"}.items()), "Assignment operation ID was reused with different inputs.", "E_IDEMPOTENCY")
                    return result(command, epic.diagnostics, epic=epic.payload(), replayed=True)
            reject_gate_operation_reuse(epic, operation_id)
            ownership.responsibility(epic.metadata["status"])
            ownership.require(epic.revision == expected_revision, "Ownership or lifecycle changed; reload before assigning.", "E_REVISION_CONFLICT")
            candidate = dict(epic.metadata)
            if initialize:
                ownership.require("ownership" not in epic.metadata, "Ownership is already initialized; use assign to transfer it.", "E_OWNERSHIP_INITIALIZED")
                known = ownership.legacy_requester(epic.metadata)
                ownership.require(known is None or known == assignee, "A recorded Requester already identifies the initial owner; use assignment for a transfer.", "E_OWNER_CONFLICT")
                candidate["ownership"] = ownership.initialized(epic.metadata["status"], assignee, actor, identity_source, operation_id, decision)
                candidate["ownership"]["history"][0]["expected_revision"] = expected_revision
            else:
                current = ownership.materialize(epic.metadata, actor, identity_source)
                event = ownership.event_for("assign", current, epic.metadata["status"], actor, identity_source, operation_id, expected_revision, decision, owner=assignee)
                candidate["ownership"] = ownership.append(current, event)
            def validate(value):
                ownership.require({k: v for k, v in value.items() if k != "ownership"} == {k: v for k, v in epic.metadata.items() if k != "ownership"}, "Assignment may change ownership metadata only.", "E_OWNERSHIP_AUDIT")
                ownership.validate(value)
            def read(directory):
                checked = read_epic(directory)
                require_valid(checked.diagnostics)
                return checked
            approval_common.persist_decision(epic, candidate, expected_revision, read, lambda e: e.revision, validate,
                lambda file, value: atomic_history_write(file, yaml.safe_dump(value, sort_keys=False, allow_unicode=True)))
        except business.BusinessError as exc:
            raise Rejected([error(exc.code, path, str(exc))]) from exc
        updated = selected_epic(root, epic_id)
        return result(command, updated.diagnostics, epic=updated.payload(), replayed=False)


def ownership_overview(project: Path, operation: str) -> dict:
    root = project_path(project)
    epics, diagnostics = scan(root)
    require_valid(diagnostics)
    rows = []
    for epic in epics:
        if epic.metadata["status"] == "cancelled":continue
        if epic.metadata.get("work_tracks") and epic.metadata["status"] in __import__("engineering_contract").DOWNSTREAM:
            view=work_tracks.review(epic,root)
            for name, item in view["tracks"].items():
                row={"id":epic.metadata["id"],"title":epic.metadata["title"],"track":name,"lifecycle":item["status"],"owner":item["owner"],"assignee":item["assignee"],"required_role":item["required_role"],"assignment_status":item["assignment_status"],"target_stage":name,"since":item["since"],"responsibility":"Accountable owner awaiting handoff" if item["assignee"] is None else "Current assignee","recommended_next_action":item["next_action"],"needs_reconciliation":item["needs_reconciliation"],"time_awaiting_seconds":None}
                rows.append(row)
        else:rows.append(ownership.row(epic))
    pending = [row for row in rows if row["assignment_status"] in ("awaiting_assignment", "owner_declaration_required")]
    pending.sort(key=lambda row: (row["since"] or "", row["id"]))
    if operation == "pending-assignments":
        return result(operation, diagnostics, pending_assignments=pending)
    profile = local_identity.load(root)
    same = lambda name: isinstance(name, str) and name.strip().casefold() == profile["display_name"].strip().casefold()
    return result("inbox", diagnostics, identity=profile,
        assigned_work=[row for row in rows if row["assignment_status"] == "assigned" and same(row["assignee"])],
        awaiting_handoff=[row for row in pending if same(row["owner"])])


def command_context(project: Path, command: str, selector: str | None = None, track=None) -> dict:
    root = project_path(project)
    if command not in command_ux.COMMANDS:
        raise Rejected([error("E_COMMAND", root, "Expected a supported SDLC command: " + ", ".join(command_ux.COMMANDS) + ".")])
    if command in ("inbox", "pending assignments"):
        return ownership_overview(root, "inbox" if command == "inbox" else "pending-assignments")
    epics, diagnostics = scan(root)
    require_valid(diagnostics)
    if selector is None:
        matches = epics
    elif valid_id(selector):
        matches = [e for e in epics if e.metadata["id"] == selector]
    else:
        matches = [e for e in epics if e.metadata["title"].casefold() == selector.casefold()]
    if len(matches) != 1:
        code = "E_CONTEXT_AMBIGUOUS" if len(matches) > 1 else "E_CONTEXT_MISSING"
        raise Rejected([error(code, root, "Select one request by title or ID." if matches else "No matching request; select an existing project/request or start Discovery.")])
    epic = matches[0]
    if epic.metadata.get("work_tracks") and epic.metadata["status"] in __import__("engineering_contract").DOWNSTREAM:
        return track_command_context(root,epic,command,track)
    if track is not None:
        raise Rejected([error("E_TRACK_REQUIRED",root,"This legacy request has no work tracks; use explicit adoption if appropriate.")])
    routing = command_ux.route(command, epic.metadata["status"])
    if epic.metadata["status"] in ENGINEERING_STAGES:
        if command == "assign":
            routing["required_role"] = ownership.view(epic.metadata)["required_role"]
            routing["initialization_required"] = ownership.view(epic.metadata)["initialization_required"]
        try:
            profile, profile_error = local_identity.load(root), None
        except local_identity.IdentityError as exc:
            profile, profile_error = None, {"code":exc.code,"file":str(exc.path),"message":str(exc)}
        engineering_view = engineering.review(epic, root)
        if command == "approve" and engineering_view["approvals"].get(routing["kind"], {}).get("valid"):
            routing.update(write_operation=None, requires_human_decision=False,
                explanation="The current engineering revision is already approved; report it without duplicating the decision.")
        return result("command-context", epic.diagnostics, routing=routing, review=engineering_view, identity=profile, identity_diagnostic=profile_error, ownership=ownership.view(epic.metadata))
    view = business_review(root, epic.metadata["id"]) if routing["review_operation"] == "business-review" else analysis_review(root, epic.metadata["id"]) if routing["review_operation"] == "analysis-review" else result("open", epic.diagnostics, epic=epic.payload())
    if command == "assign":
        routing["required_role"] = ownership.view(epic.metadata)["required_role"]
        routing["initialization_required"] = ownership.view(epic.metadata)["initialization_required"]
    active_approval = epic.analysis_approval if epic.metadata["status"] == "functional_analysis" else epic.approval if epic.metadata["status"] == "business_refinement" else None
    if command == "approve" and active_approval and active_approval["valid"]:
        routing.update(write_operation=None, requires_human_decision=False,
                       explanation="The current revision is already approved; report it without recording a duplicate decision.")
    try:
        identity, identity_error = local_identity.load(root), None
    except local_identity.IdentityError as exc:
        identity, identity_error = None, {"code": exc.code, "file": str(exc.path), "message": str(exc)}
    return result("command-context", epic.diagnostics, routing=routing, review=view, identity=identity, identity_diagnostic=identity_error)


def track_command_context(root,epic,command,track):
    import qa_track
    summary=work_tracks.review(epic,root)
    try: profile,profile_error=local_identity.load(root),None
    except local_identity.IdentityError as exc:
        profile,profile_error=None,{"code":exc.code,"file":str(exc.path),"message":str(exc)}
    if track is None and command in ("status","details"):
        summary["documents"] = {
            "engineering": artifact_names.documents(engineering.review(epic, root)),
            "qa": artifact_names.documents(qa_track.review(epic, root)),
        }
        return result("command-context",epic.diagnostics,routing={"command":command,"read_only":True,"write_operation":None,"requires_human_decision":False},review=summary,identity=profile,identity_diagnostic=profile_error,integration=qa_track.integration_readiness(epic,root))
    if track not in work_tracks.NAMES:
        raise Rejected([error("E_TRACK_AMBIGUOUS",epic.directory/"metadata.yaml","Which track do you intend: Engineering or QA?")])
    own=summary["tracks"][track]
    if track=="engineering":
        view=engineering.review(epic,root)
        routing=command_ux.route(command,epic.metadata["status"])
        routing["review_operation"]="engineering-review"
    else:
        view=qa_track.review(epic,root)
        stage=work_tracks.current(epic.metadata)["qa"]["status"]
        kind="automation" if stage=="test_automation" else "scenarios" if stage=="test_design" else None
        op=None
        if command=="assign":op="assign"
        elif command=="start":
            if stage in ("ready_for_test_design","test_design"):
                kind="scenarios" if "strategy" in view.get("drafts",{}) else "strategy";op="qa-write"
            elif stage=="test_automation":kind="automation";op="qa-write"
            elif stage in ("ready_for_verification","verified"):kind="check";op="qa-check-run"
        elif command=="approve" and kind:op="qa-approve"
        elif command=="changes":kind=kind or "scenarios";op="qa-request-changes"
        elif command=="advance":
            kind="verification" if stage in ("ready_for_verification","verified") else kind
            if kind:op="qa-advance"
        routing={"command":command,"stage":stage,"kind":kind,"review_operation":"qa-review","write_operation":op,"read_only":True,"requires_human_decision":op is not None}
    routing.update(track=track,required_role=own["required_role"],initialization_required=False)
    if command=="approve" and view.get("approvals",{}).get(routing.get("kind"),{}).get("valid"):
        routing.update(write_operation=None,requires_human_decision=False,explanation="This exact track revision is already approved.")
    return result("command-context",epic.diagnostics,routing=routing,review=view,ownership=own,identity=profile,identity_diagnostic=profile_error)


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
    context = commands.add_parser("command-context", help="Read-only resolution/routing for a conversational SDLC command")
    context.add_argument("command", choices=command_ux.COMMANDS)
    context.add_argument("--request", dest="selector")
    context.add_argument("--track", choices=work_tracks.NAMES)
    commands.add_parser("identity-show", help="Read the local unauthenticated identity profile")
    for name in ("identity-setup", "identity-edit"):
        profile = commands.add_parser(name, help="Explicitly create or edit local identity preferences outside repositories")
        profile.add_argument("--display-name", required=name == "identity-setup")
        profile.add_argument("--role", action="append", required=name == "identity-setup")
        if name == "identity-edit":
            profile.add_argument("--expected-profile-revision", required=True)
    commands.add_parser("inbox", help="Read work assigned to the local declared user and owned pending handoffs")
    commands.add_parser("pending-assignments", help="Read all project requests awaiting assignment")
    for name in ("assign", "ownership-initialize"):
        assignment = commands.add_parser(name, help="Explicitly confirm responsibility transfer or declare a missing legacy owner")
        assignment.add_argument("id")
        assignment.add_argument("--expected-revision", required=True)
        assignment.add_argument("--operation-id", required=True)
        assignment.add_argument("--decision", required=True)
        assignment.add_argument("--actor")
        assignment.add_argument("--track", choices=work_tracks.NAMES)
        assignment.add_argument("--expected-profile-revision")
        assignment.add_argument("--owner" if name == "ownership-initialize" else "--assignee", dest="assignee", required=True)
    for name in ("track-review", "qa-review"):
        commands.add_parser(name,help="Read independent Analysis work tracks").add_argument("id")
    for name in ("tracks-adopt", "track-reconcile"):
        item=commands.add_parser(name,help="Explicitly reconcile a legacy request or changed Analysis track")
        item.add_argument("id")
        item.add_argument("--expected-track-revision",required=True)
        item.add_argument("--operation-id",required=True)
        item.add_argument("--decision",required=True)
        item.add_argument("--actor")
        item.add_argument("--expected-profile-revision")
        if name=="track-reconcile":item.add_argument("--track",choices=work_tracks.NAMES,required=True)
    for name in ("qa-write","qa-approve","qa-request-changes","qa-advance","qa-check-run"):
        item=commands.add_parser(name,help="Independent QA design, review, automation or execution")
        item.add_argument("id")
        item.add_argument("--expected-qa-revision",required=True)
        item.add_argument("--operation-id",required=True)
        item.add_argument("--decision",required=True)
        item.add_argument("--actor")
        item.add_argument("--expected-profile-revision")
        item.add_argument("--expected-source-revision")
        if name=="qa-write":item.add_argument("--input-file",type=Path,required=True)
        if name!="qa-check-run":item.add_argument("--kind",choices=("strategy","scenarios","automation","verification"),required=True)
        else:item.add_argument("--check-id",required=True)
        if name=="qa-approve":item.add_argument("--acknowledge-open-item",action="append",default=[])
    commands.add_parser("skills", help="Read approved local domain skill catalog")
    commands.add_parser("engineering-review", help="Read the sequential engineering state").add_argument("id")
    for name in ("engineering-write", "engineering-approve", "engineering-request-changes", "engineering-advance", "development-start", "check-run", "security-remediate", "verification-remediate", "engineering-finalize"):
        eng = commands.add_parser(name, help="Revision-bound sequential engineering operation")
        eng.add_argument("id")
        eng.add_argument("--expected-engineering-revision", required=True)
        eng.add_argument("--operation-id", required=True)
        eng.add_argument("--actor")
        eng.add_argument("--expected-profile-revision")
        eng.add_argument("--decision", required=True)
        if name.startswith("engineering-") and name != "engineering-finalize":
            eng.add_argument("--kind", required=True, choices=engineering.KINDS if name != "engineering-advance" else (*engineering.KINDS, "verification"))
        if name == "engineering-write": eng.add_argument("--input-file", required=True, type=Path)
        if name == "engineering-approve": eng.add_argument("--acknowledge-open-item", action="append", default=[])
        if name == "check-run": eng.add_argument("--check-id", required=True)
        if name == "verification-remediate": eng.add_argument("--check-id", action="append", required=True)
        if name == "security-remediate": eng.add_argument("--finding", action="append", required=True)
    create = commands.add_parser("new", help="Create a local Discovery Epic")
    create.add_argument("--title", required=True)
    create.add_argument("--requester", help="Explicit initial requester; otherwise use the local declared identity profile")
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
        command.add_argument(f"--{who}")
        command.add_argument("--expected-profile-revision")
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
        command.add_argument(f"--{identity}", dest="gate_actor")
        command.add_argument("--expected-profile-revision")
        command.add_argument("--reason", required=True)
        if name == "business-approve":
            command.add_argument("--decision", required=True)
            command.add_argument("--acknowledge-open-item", action="append", default=[])
        elif name == "business-request-changes":
            command.add_argument("--feedback", required=True)
        else:
            command.add_argument("--approval-id", required=True)
    for name, identity in (("analysis-request-changes", "reviewer"), ("analysis-approve", "approver"), ("analysis-advance", "actor")):
        command = commands.add_parser(name, help="Record an Analysis decision or separately advance to Technical Design readiness")
        command.add_argument("id")
        for flag in ("expected-analysis-review-revision", "expected-analysis-revision", "expected-baseline-id", "expected-handoff-id", "operation-id", "reason"):
            command.add_argument("--" + flag, required=True)
        command.add_argument("--" + identity, dest="gate_actor")
        command.add_argument("--expected-profile-revision")
        if name == "analysis-approve":
            command.add_argument("--decision", required=True)
            command.add_argument("--acknowledge-open-item", action="append", default=[])
        elif name == "analysis-request-changes":
            command.add_argument("--feedback", required=True)
        else:
            command.add_argument("--approval-id", required=True)
    commands.add_parser("analysis-review", help="Read functional specification and approved input").add_argument("id")
    commands.add_parser("analysis-recover", help="Recover an inspected Analysis transaction").add_argument("id")
    for name in ("analysis-generate", "analysis-revise"):
        command = commands.add_parser(name, help="Persist an AI-drafted or human-refined functional specification")
        command.add_argument("id")
        command.add_argument("--expected-analysis-review-revision", required=True)
        command.add_argument("--expected-analysis-revision")
        command.add_argument("--expected-baseline-id", required=True)
        command.add_argument("--expected-handoff-id", required=True)
        command.add_argument("--operation-id", required=True)
        command.add_argument("--editor", required=True)
        command.add_argument("--reason", required=True)
        command.add_argument("--document-file", required=True, type=Path)
        command.add_argument("--feedback-file", type=Path)
    commands.add_parser("business-recover", help="Roll forward an inspected interrupted business publication").add_argument("id")
    args = parser.parse_args(argv)
    diagnostic_base = args.project
    try:
        if args.operation in ("track-review","qa-review"):
            import qa_track
            selected=selected_epic(project_path(args.project),args.id)
            view=work_tracks.review(selected,project_path(args.project)) if args.operation=="track-review" else qa_track.review(selected,project_path(args.project))
            output=result(args.operation,selected.diagnostics,epic=selected.payload(),review=view)
        elif args.operation in ("tracks-adopt","track-reconcile"):
            actor,source=local_identity.attribution(args.project,args.actor,args.expected_profile_revision)
            diagnostic_base=selected_epic(project_path(args.project),args.id).directory
            output=work_tracks.update(project_path(args.project),args.id,args.expected_track_revision,args.operation_id,"adopt" if args.operation=="tracks-adopt" else "reconcile",getattr(args,"track",None),actor,args.decision,identity_source=source)
        elif args.operation in ("qa-write","qa-approve","qa-request-changes","qa-advance","qa-check-run"):
            import qa_track
            actor,source=local_identity.attribution(args.project,args.actor,args.expected_profile_revision)
            diagnostic_base=selected_epic(project_path(args.project),args.id).directory
            action={"qa-check-run":"run","qa-request-changes":"request_changes"}.get(args.operation,args.operation.removeprefix("qa-"))
            kind=getattr(args,"kind","check")
            payload={}
            if action=="write":
                try:payload=yaml.load(args.input_file.read_text(encoding="utf-8"),Loader=StrictLoader)
                except (yaml.YAMLError,RecursionError) as exc:
                    raise Rejected([error("E_QA_DOCUMENT",args.input_file,str(exc))]) from exc
                if not isinstance(payload,dict):raise Rejected([error("E_QA_DOCUMENT",args.input_file,"Expected a QA artifact object.")])
            elif action in ("approve","request_changes"):
                payload={"acknowledged":getattr(args,"acknowledge_open_item",[])}
                if kind=="automation" and action=="approve":payload["source_revision"]=args.expected_source_revision
            elif action=="run":payload={"check_id":args.check_id,"source_revision":args.expected_source_revision}
            output=qa_track.update(project_path(args.project),args.id,args.expected_qa_revision,args.operation_id,action,kind,payload,actor,args.decision,source)
        elif args.operation == "skills":
            output = result("skills", [], skills=domain_skills.catalog(StrictLoader))
        elif args.operation == "engineering-review":
            epic = selected_epic(project_path(args.project), args.id)
            output = result("engineering-review", epic.diagnostics, epic=epic.payload(), engineering=engineering.review(epic, project_path(args.project)))
        elif args.operation in ("engineering-write", "engineering-approve", "engineering-request-changes", "engineering-advance", "development-start", "check-run", "security-remediate", "verification-remediate", "engineering-finalize"):
            actor, source = local_identity.attribution(args.project, args.actor, args.expected_profile_revision)
            action = {"development-start":"start", "check-run":"run", "security-remediate":"remediate", "verification-remediate":"remediate", "engineering-finalize":"finalize"}.get(args.operation, args.operation.removeprefix("engineering-").replace("-", "_"))
            kind = getattr(args, "kind", {"development-start":"development", "check-run":"check", "security-remediate":"security", "verification-remediate":"verification", "engineering-finalize":"final"}.get(args.operation))
            payload = {}
            if args.operation == "engineering-write":
                try:
                    payload = yaml.load(args.input_file.read_text(encoding="utf-8"), Loader=StrictLoader)
                except (yaml.YAMLError, RecursionError) as exc:
                    mark = getattr(exc,"problem_mark",None)
                    raise Rejected([Diagnostic("error","E_ENGINEERING_DOCUMENT",str(args.input_file),str(exc),mark.line+1 if mark else None)]) from exc
                if not isinstance(payload,dict):
                    raise Rejected([error("E_ENGINEERING_DOCUMENT",args.input_file,"Expected an artifact object.")])
            elif action in ("approve", "request_changes"): payload = {"acknowledged":getattr(args,"acknowledge_open_item",[])}
            elif action == "run": payload = {"check_id":args.check_id}
            elif args.operation == "verification-remediate": payload = {"checks":args.check_id}
            elif action == "remediate": payload = {"findings":args.finding}
            diagnostic_base = selected_epic(project_path(args.project), args.id).directory
            output = engineering.update(project_path(args.project), args.id, args.expected_engineering_revision, args.operation_id, action, kind, payload, actor, args.decision, source)
        elif args.operation == "command-context":
            output = command_context(args.project, args.command, args.selector, args.track)
        elif args.operation in ("inbox", "pending-assignments"):
            output = ownership_overview(args.project, args.operation)
        elif args.operation in ("assign", "ownership-initialize"):
            actor, source = local_identity.attribution(args.project, args.actor, args.expected_profile_revision)
            output = ownership_change(args.project, args.id, args.expected_revision, args.operation_id, actor, args.decision, args.assignee, initialize=args.operation == "ownership-initialize", identity_source=source, track=args.track)
        elif args.operation == "identity-show":
            output = result(args.operation, [], identity=local_identity.load(args.project))
        elif args.operation in ("identity-setup", "identity-edit"):
            output = result(args.operation, [], identity=local_identity.save(args.project, args.display_name, args.role, edit=args.operation == "identity-edit", expected_revision=getattr(args, "expected_profile_revision", None)))
        elif args.operation == "new":
            output = new_epic(args.project, args.title, args.idea, requester=args.requester)
        elif args.operation == "discovery-update":
            output = discovery_update(args.project, args.id, args.expected_revision, args.operation_id, read_changes(args.changes_file))
        elif args.operation in ("discovery-complete", "discovery-reopen"):
            actor, source = local_identity.attribution(args.project, args.requester, args.expected_profile_revision)
            output = lifecycle_change(args.project, args.id, args.expected_revision, args.operation_id, actor, args.decision, args.operation.removeprefix("discovery-"), identity_source=source)
        elif args.operation in ("business-generate", "business-revise"):
            output = business_write(args.project, args.id, args.expected_source_revision, args.expected_business_revision, args.operation_id, args.editor, args.reason, args.document_file, args.operation.removeprefix("business-"))
        elif args.operation == "business-review":
            output = business_review(args.project, args.id)
        elif args.operation in ("business-approve", "business-request-changes", "business-advance"):
            action = args.operation.removeprefix("business-").replace("-", "_")
            text = args.decision if action == "approve" else args.feedback if action == "request_changes" else args.reason
            actor, source = local_identity.attribution(args.project, args.gate_actor, args.expected_profile_revision)
            output = business_gate(args.project, args.id, args.expected_review_revision, args.expected_business_revision, args.operation_id, actor, args.reason, text, action, getattr(args, "acknowledge_open_item", []), getattr(args, "approval_id", None), identity_source=source)
        elif args.operation in ("analysis-approve", "analysis-request-changes", "analysis-advance"):
            action = args.operation.removeprefix("analysis-").replace("-", "_")
            text = args.decision if action == "approve" else args.feedback if action == "request_changes" else args.reason
            actor, source = local_identity.attribution(args.project, args.gate_actor, args.expected_profile_revision)
            output = analysis_gate(args.project, args.id, args.expected_analysis_review_revision, args.expected_analysis_revision, args.expected_baseline_id, args.expected_handoff_id, args.operation_id, actor, args.reason, text, action, getattr(args, "acknowledge_open_item", []), getattr(args, "approval_id", None), identity_source=source)
        elif args.operation == "analysis-review":
            output = analysis_review(args.project, args.id)
        elif args.operation in ("analysis-generate", "analysis-revise"):
            output = analysis_write(args.project, args.id, args.expected_analysis_review_revision, args.expected_analysis_revision, args.expected_baseline_id, args.expected_handoff_id, args.operation_id, args.editor, args.reason, args.document_file, args.operation.removeprefix("analysis-"), args.feedback_file)
        elif args.operation == "analysis-recover":
            output = business_recover(args.project, args.id, recover_analysis=True)
        elif args.operation == "business-recover":
            output = business_recover(args.project, args.id)
        else:
            output = inspect_epics(args.project, args.operation, args.id)
    except business.BusinessError as exc:
        output = result(args.operation, [error(exc.code, (args.input_file if hasattr(args,"input_file") and exc.code in ("E_ENGINEERING_DOCUMENT","E_ENGINEERING_TRACE","E_ENGINEERING_PLAN","E_QA_DOCUMENT","E_QA_TRACE") else domain_skills.ROOT / exc.filename if exc.code == "E_SKILL" else diagnostic_base / exc.filename), str(exc))])
    except local_identity.IdentityError as exc:
        output = result(args.operation, [error(exc.code, exc.path, str(exc))])
    except Rejected as exc:
        output = result(args.operation, exc.diagnostics)
    except (OSError, UnicodeError) as exc:
        output = result(args.operation, [error("E_IO", Path(getattr(exc, "filename", None) or args.project), str(exc))])
    print(json.dumps(output, ensure_ascii=False))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    # Engineering callbacks reuse this CLI module, including its exception types.
    sys.modules.setdefault("sdlc", sys.modules[__name__])
    sys.exit(main())
