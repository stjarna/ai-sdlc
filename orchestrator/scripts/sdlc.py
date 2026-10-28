"""Deterministic, local Discovery operations. No Git or host-agent integration."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

import yaml


SCHEMA_VERSION = "0.1"
ORCHESTRATOR_VERSION = "0.1.0"
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

    def payload(self) -> dict:
        return {
            "directory": str(self.directory), "metadata": self.metadata,
            "idea": self.idea,
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
        data = yaml.load(metadata_path.read_text(encoding="utf-8"), Loader=StrictLoader)
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
    if set(data) != FIELDS:
        epic.diagnostics.append(error(
            "E_METADATA", metadata_path,
            f"Expected exactly these fields: {', '.join(sorted(FIELDS))}.",
        ))
    if data.get("schema_version") != SCHEMA_VERSION:
        epic.diagnostics.append(error(
            "E_SCHEMA_VERSION", metadata_path,
            f"Supported schema_version is the string '{SCHEMA_VERSION}'; no migration was performed.",
        ))
    if not valid_id(data.get("id")):
        epic.diagnostics.append(error("E_EPIC_ID", metadata_path, "Expected REQ-0001 through REQ-9999."))
    if not valid_title(data.get("title")):
        epic.diagnostics.append(error("E_TITLE", metadata_path, "Title must be nonempty, single-line text."))
    # Cancelled records reserve IDs; this CLI provides no cancellation transition.
    if data.get("status") not in ("discovery", "cancelled"):
        epic.diagnostics.append(error(
            "E_STATUS", metadata_path, "Supported record statuses are discovery and cancelled."
        ))
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
            or not idea_path.is_relative_to(directory.resolve())
            or idea_path == metadata_path.resolve()
        ):
            epic.diagnostics.append(error(
                "E_ARTIFACT_PATH", metadata_path, "The idea artifact must stay inside its Epic directory."
            ))
            return epic
        if not idea_path.is_file():
            epic.diagnostics.append(error("E_ARTIFACT_FILE", idea_path, "The idea artifact must be an existing file."))
            return epic
        epic.idea = idea_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        epic.diagnostics.append(error("E_READ", idea_path, str(exc)))
        return epic
    epic.diagnostics.extend(business_warnings(idea_path, epic.idea))
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
def creation_lock(root: Path):
    """Fail closed if another local writer holds the transient lock."""
    lock = root / ".sdlc-discovery.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise Rejected([error("E_PROJECT_BUSY", lock, "Another creation may be running; inspect the lock before retrying.")]) from None
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
    with creation_lock(root):
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
    args = parser.parse_args(argv)
    try:
        if args.operation == "new":
            output = new_epic(args.project, args.title, args.idea)
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
