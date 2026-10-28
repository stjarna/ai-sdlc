"""Portable declared identity preferences. No authentication, credentials or RBAC."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile

import business_refinement as business

SOURCE = "local_profile"
FIELDS = {"schema_version", "display_name", "declared_roles"}
PACKAGE_ROOT = Path(__file__).resolve().parents[2]


class IdentityError(Exception):
    def __init__(self, code, message, path):
        super().__init__(message)
        self.code, self.path = code, Path(path)


def require(condition, code, message, path):
    if not condition:
        raise IdentityError(code, message, path)


def profile_path(project):
    configured = os.environ.get("SDLC_IDENTITY_FILE")
    if configured:
        path = Path(configured).expanduser()
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).expanduser()
        require(base.is_absolute(), "E_IDENTITY_PATH", "XDG_CONFIG_HOME must be absolute.", base)
        path = base / "ai-sdlc" / "identity.json"
    require(path.is_absolute(), "E_IDENTITY_PATH", "SDLC_IDENTITY_FILE must be absolute.", path)
    require(not path.is_symlink(), "E_IDENTITY_PATH", "Identity profile must not be a symlink.", path)
    resolved = path.resolve()
    forbidden = (Path(project).resolve(), PACKAGE_ROOT)
    require(not any(resolved.is_relative_to(root) for root in forbidden), "E_IDENTITY_PATH", "Keep identity outside the target project and implementation checkout.", path)
    require(not any((parent / ".git").exists() for parent in resolved.parents), "E_IDENTITY_PATH", "Keep the identity profile outside Git repositories.", path)
    return resolved


def validate(data, path):
    require(isinstance(data, dict) and set(data) == FIELDS and data["schema_version"] == "0.1", "E_IDENTITY_PROFILE", "Expected schema_version, display_name and declared_roles only; credentials are not supported.", path)
    require(business.valid_person(data["display_name"]), "E_IDENTITY_PROFILE", "Display name must be nonempty single-line text.", path)
    roles = data["declared_roles"]
    require(isinstance(roles, list) and bool(roles) and all(business.valid_person(r) for r in roles) and len(set(roles)) == len(roles), "E_IDENTITY_PROFILE", "Declare one or more unique role labels; roles are informational, not enforced permissions.", path)
    return data


def load(project):
    path = profile_path(project)
    require(path.exists(), "E_IDENTITY_MISSING", "Set up your local display name and declared roles once before recording decisions.", path)
    require(path.is_file(), "E_IDENTITY_PROFILE", "Expected a regular identity profile file.", path)
    def mapping(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("Duplicate identity profile key: " + k)
            result[k] = v
        return result
    try:
        raw = path.read_bytes()
        data = validate(json.loads(raw.decode("utf-8"), object_pairs_hook=mapping), path)
        return {**data, "identity_source": SOURCE, "authenticated": False, "roles_enforced": False,
                "profile_revision": hashlib.sha256(raw).hexdigest(), "file": str(path)}
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise IdentityError("E_IDENTITY_PROFILE", str(exc), path) from exc


@contextmanager
def profile_lock(path):
    lock = path.parent / ".identity.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise IdentityError("E_IDENTITY_BUSY", "Another profile update is in progress; inspect an abandoned lock before retrying.", lock) from exc
    try:
        yield
    finally:
        lock.rmdir()


def save(project, display_name, roles, *, edit=False, expected_revision=None):
    path = profile_path(project)
    require(not edit or expected_revision is not None, "E_IDENTITY_REVISION", "Editing requires the profile revision returned by identity-show.", path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with profile_lock(path):
        if edit:
            previous = load(project)
            require(previous["profile_revision"] == expected_revision, "E_IDENTITY_REVISION", "Profile changed; reload before editing.", path)
            display_name = previous["display_name"] if display_name is None else display_name
            roles = previous["declared_roles"] if roles is None else roles
        else:
            require(not path.exists(), "E_IDENTITY_EXISTS", "Profile already exists; use identity-edit.", path)
        data = validate({"schema_version": "0.1", "display_name": display_name, "declared_roles": roles}, path)
        temporary = None
        published = False
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".identity-", delete=False) as stream:
                temporary = Path(stream.name)
                os.chmod(temporary, 0o600)
                stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
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
            raise IdentityError("E_IDENTITY_WRITE_UNCERTAIN" if published else "E_IDENTITY_WRITE", "Profile save failed; inspect identity-show before retrying.", path) from exc
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return load(project)


def validate_source(entry, code):
    business.require("identity_source" not in entry or entry["identity_source"] == SOURCE, code,
                     "Only an unauthenticated local_profile identity source is supported.", "metadata.yaml")


def attribution(project, explicit, expected_revision=None):
    if explicit is not None:
        require(expected_revision is None, "E_IDENTITY_REVISION", "A profile revision cannot be combined with an explicit legacy actor.", project)
        return explicit, None
    profile = load(project)
    require(expected_revision is None or expected_revision == profile["profile_revision"], "E_IDENTITY_REVISION", "Identity changed since review; reload the profile and confirm the intended attribution.", profile["file"])
    return profile["display_name"], SOURCE
