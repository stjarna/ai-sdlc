"""Local approval storage and transaction primitives; no stage or business policy."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile

import business_refinement as business
import discovery_history as discovery


def canonical_manifest(manifest):
    # This serialization is part of the original Business baseline identity contract.
    return json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def revision(files, names):
    return business.digest(json.dumps([business.digest(files[n]) if files[n] is not None else None for n in names]).encode("utf-8"))


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_files(manifest, files, names):
    business.require(isinstance(manifest.get("files"), dict) and set(manifest["files"]) == set(names) and set(files) == set(names), "E_BASELINE_INTEGRITY", "Unexpected baseline artifact set.", "metadata.yaml")
    business.require(all(discovery.valid_revision(v) for v in manifest["files"].values()), "E_BASELINE_INTEGRITY", "Invalid baseline file digest.", "metadata.yaml")
    business.require(all(business.digest(files[n]) == expected for n, expected in manifest["files"].items()), "E_BASELINE_INTEGRITY", "Baseline file hash mismatch.", "metadata.yaml")


def read_baseline(directory, baseline_id, root_name, names, validate):
    business.require(discovery.valid_revision(baseline_id), "E_BASELINE_INTEGRITY", "Invalid baseline ID.", "metadata.yaml")
    root, path = directory / root_name, directory / root_name / baseline_id
    business.require(not root.is_symlink() and (not root.exists() or root.is_dir()), "E_BASELINE_INTEGRITY", "Unsafe baseline root.", root_name)
    business.require(path.exists(), "E_BASELINE_MISSING", "Approved baseline is missing; restore it from a known-good copy.", f"{root_name}/{baseline_id}")
    business.require(path.is_dir() and not path.is_symlink(), "E_BASELINE_INTEGRITY", "Baseline must be a nonsymlink directory.", f"{root_name}/{baseline_id}")
    try:
        business.require({p.name for p in path.iterdir()} == set(names) | {"manifest.json"}, "E_BASELINE_INTEGRITY", "Unexpected or missing baseline files.")
        contents = {}
        for name in (*names, "manifest.json"):
            item = path / name
            business.require(item.is_file() and not item.is_symlink(), "E_BASELINE_INTEGRITY", "Baseline files must be regular and nonsymlink.", f"{root_name}/{baseline_id}/{name}")
            contents[name] = item.read_bytes()
        encoded = contents.pop("manifest.json")
        manifest = json.loads(encoded.decode("utf-8"))
        business.require(canonical_manifest(manifest) == encoded and encoded == (path / "manifest.json").read_bytes() and business.digest(encoded) == baseline_id, "E_BASELINE_INTEGRITY", "Baseline manifest identity mismatch.")
        validate(manifest, contents)
        return manifest, contents
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, business.BusinessError) as exc:
        if isinstance(exc, business.BusinessError) and exc.filename.startswith(root_name + "/"):
            raise
        code = exc.code if isinstance(exc, business.BusinessError) else "E_BASELINE_INTEGRITY"
        raise business.BusinessError(code, str(exc), f"{root_name}/{baseline_id}") from exc


def publish_baseline(directory, root_name, manifest, files, validate, read, sync=None):
    sync = fsync_directory if sync is None else sync
    validate(manifest, files)
    encoded = canonical_manifest(manifest)
    baseline_id = business.digest(encoded)
    root = directory / root_name
    business.require(not root.is_symlink() and (not root.exists() or root.is_dir()), "E_BASELINE_INTEGRITY", "Unsafe baseline root.", root.name)
    temporary = None
    try:
        if not root.exists():
            root.mkdir(mode=0o700)
            sync(directory)
        final = root / baseline_id
        if final.exists() or final.is_symlink():
            read(baseline_id)
            # Retained orphans must be verified AND made durable before reuse.
            sync(root)
            sync(directory)
            return baseline_id
        temporary = Path(tempfile.mkdtemp(prefix=".pending-", dir=root))
        for name, content in {**files, "manifest.json": encoded}.items():
            with (temporary / name).open("xb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        sync(temporary)
        os.rename(temporary, final)
        sync(root)
        sync(directory)
        read(baseline_id)
        return baseline_id
    except OSError as exc:
        raise business.BusinessError("E_BASELINE_WRITE", "Baseline preparation failed; no approval was published. Inspect retained temporary/orphan baselines and retry the same operation.", root.name) from exc
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def replay(entries, events, operation_id, decision_inputs, advancement_inputs):
    """Compare exact intent before status/revision checks; never restore authority."""
    for entry, inputs, key in [(e, decision_inputs, "operation_id") for e in entries] + [(e, advancement_inputs, "id") for e in events]:
        if entry[key] == operation_id:
            business.require(inputs is not None and all(entry.get(k) == v for k, v in inputs.items()), "E_IDEMPOTENCY", "Gate operation ID was already used with different inputs.", "metadata.yaml")
            return entry, key == "id"
    return None


def exact_acknowledgements(acknowledged, items, message):
    business.require(set(acknowledged) == {item["id"] for item in items}, "E_ACKNOWLEDGEMENT", message, "metadata.yaml")


def persist_decision(epic, candidate, expected, read, token, validate, write):
    """Caller holds the project lock. Baseline publication precedes this commit point."""
    for name in ("business_decisions", "analysis_decisions", "lifecycle"):
        previous = epic.metadata.get(name, [])
        business.require(candidate.get(name, [])[:len(previous)] == previous, "E_APPROVAL_AUDIT", "Approval persistence must preserve every audit prefix.", "metadata.yaml")
    from ownership import preserve_prefix
    preserve_prefix(epic.metadata, candidate)
    validate(candidate)
    checked = read(epic.directory)
    business.require(token(checked) == expected, "E_REVISION_CONFLICT", "Artifacts changed while preparing the gate operation.", "metadata.yaml")
    write(epic.directory / "metadata.yaml", candidate)
