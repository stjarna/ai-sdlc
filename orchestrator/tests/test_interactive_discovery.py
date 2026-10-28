"""Deterministic persistence tests; conversational judgment is evaluated manually."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sdlc
import discovery_history as history


SCRIPT = Path(sdlc.__file__).resolve()


def source(quote):
    return {"actor": "user", "quote": quote}


def statement(text="Customers call to ask who owns a request.", **extra):
    return {"kind": "user_statement", "topic": "problem", "text": text, "source": source(text), **extra}


def question(text="Who should see the owner?"):
    return {"kind": "question", "topic": "access", "text": text, "source": {"actor": "ai"}}


def assumption():
    return {"kind": "ai_assumption", "topic": "scope", "text": "Ownership is visible only for the user's own requests.", "source": {"actor": "ai"}}


def decision(action, target, text="Confirmed by the user.", **extra):
    return {"kind": "human_decision", "topic": "scope", "text": text, "action": action, "target": target, "source": source(text), **extra}


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file() and not path.is_symlink()}


class InteractiveDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.area = Path(self.temp.name).resolve()
        self.project = self.area / "project"
        self.project.mkdir()
        self.original_idea = "Customers repeatedly call about request ownership. We do not yet know the access rules or target reduction in calls."
        self.created = sdlc.new_epic(self.project, "Request ownership visibility", self.original_idea, requester="Fixture Requester")
        self.epic = Path(self.created["epic"]["directory"])
        self.metadata_bytes = (self.epic / "metadata.yaml").read_bytes()
        self.idea_bytes = (self.epic / "idea.md").read_bytes()
        self.path = self.epic / "discovery.yaml"
        self.number = 0

    def cli(self, *args, env=None):
        if args and args[0] == "new":
            args = (*args, "--requester", "Fixture Requester")
        run = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *args], capture_output=True, text=True, env=env)
        self.assertEqual(run.stderr, "", run.stderr)
        output = json.loads(run.stdout)
        self.assertEqual(run.returncode, 0 if output["ok"] else 1)
        return output

    def opened(self):
        result = self.cli("open", "REQ-0001")
        self.assertTrue(result["ok"])
        return result["epic"]

    def update(self, records, operation_id=None, revision=None):
        self.number += 1
        return sdlc.discovery_update(self.project, "REQ-0001", revision or self.opened()["revision"], operation_id or f"operation-{self.number}", records)

    def cli_update(self, records, operation_id, revision):
        changes = self.area / f"changes-{operation_id}.json"
        changes.write_text(json.dumps({"records": records}))
        return self.cli("discovery-update", "REQ-0001", "--operation-id", operation_id, "--expected-revision", revision, "--changes-file", str(changes))

    def assert_rejected(self, code, records, **kwargs):
        before = snapshot(self.project)
        with self.assertRaises(sdlc.Rejected) as caught:
            self.update(records, **kwargs)
        self.assertIn(code, {item.code for item in caught.exception.diagnostics})
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_existing_requests_remain_valid_without_history_and_reads_do_not_initialize_it(self):
        before = snapshot(self.project)
        opened = self.opened()
        self.assertIsNone(opened["discovery"])
        self.assertIsNone(opened["discovery_state"])
        self.assertRegex(opened["revision"], r"^[0-9a-f]{64}$")
        self.assertTrue(self.cli("validate")["ok"])
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse(self.path.exists())

    def test_empty_initialization_creates_separate_versioned_history_without_changing_originals(self):
        result = self.update([])
        self.assertTrue(result["ok"])
        data = yaml.safe_load(self.path.read_text())
        self.assertEqual(data["schema_version"], "0.1")
        self.assertEqual(data["request_id"], "REQ-0001")
        self.assertEqual(data["operations"][0]["records"], [])
        self.assertEqual((self.epic / "metadata.yaml").read_bytes(), self.metadata_bytes)
        self.assertEqual((self.epic / "idea.md").read_bytes(), self.idea_bytes)
        self.assertTrue(self.cli("validate", "REQ-0001")["ok"])

    def test_start_capture_and_resume_via_fresh_cli_processes(self):
        records = [statement(self.original_idea), question()]
        result = self.cli_update(records, "initial-capture", self.opened()["revision"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["record_ids"], ["D-0001", "D-0002"])
        resumed = self.opened()
        self.assertEqual(resumed["discovery"]["operations"][0]["records"][0]["source"]["quote"], self.original_idea)
        self.assertEqual(resumed["discovery_state"]["questions"][0]["status"], "open")
        response = statement("Only the customer who submitted the request.", answers="D-0002")
        self.assertTrue(self.cli_update([response], "answer-access", resumed["revision"])["ok"])
        resumed = self.opened()
        self.assertEqual(resumed["discovery_state"]["questions"][0]["status"], "answered")
        self.assertEqual(resumed["metadata"]["status"], "discovery")
        self.assertEqual((self.epic / "metadata.yaml").read_bytes(), self.metadata_bytes)
        self.assertEqual((self.epic / "idea.md").read_bytes(), self.idea_bytes)

    def test_append_preserves_prior_records_and_does_not_mutate_input(self):
        records = [statement(), question()]
        original = deepcopy(records)
        first = self.update(records)["epic"]["discovery"]
        second = self.update([assumption()])["epic"]["discovery"]
        self.assertEqual(second["operations"][:1], first["operations"])
        self.assertEqual(records, original)
        self.assertEqual(second["operations"][1]["records"][0]["id"], "D-0003")

    def test_ai_assumption_cannot_be_recorded_as_user_fact_or_decision(self):
        for record in (
            {**statement(), "source": {"actor": "ai"}},
            {**statement(), "source": {"actor": "user"}},
            {**assumption(), "source": source("Proposed by AI, not the user")},
            {"kind": "human_decision", "action": "decide", "topic": "scope", "text": "Do this", "source": {"actor": "ai"}},
        ):
            with self.subTest(record=record):
                self.assert_rejected("E_DISCOVERY_PROVENANCE", [record])

    def test_confirmation_preserves_assumption_type_and_requires_user_evidence(self):
        self.update([assumption()])
        self.assert_rejected("E_DISCOVERY_PROVENANCE", [{**decision("confirm", "D-0001"), "source": {"actor": "user", "quote": ""}}])
        result = self.update([decision("confirm", "D-0001", "Yes, only their own requests.")])
        self.assertEqual(result["epic"]["discovery"]["operations"][0]["records"][0]["kind"], "ai_assumption")
        self.assertEqual(result["epic"]["discovery_state"]["assumptions"][0]["status"], "confirmed")
        self.assertEqual(result["epic"]["discovery"]["operations"][1]["records"][0]["source"]["quote"], "Yes, only their own requests.")

    def test_rejection_is_linked_and_does_not_delete_the_assumption(self):
        self.update([assumption()])
        result = self.update([decision("reject", "D-0001", "Company administrators also need access.")])
        self.assertEqual(result["epic"]["discovery_state"]["assumptions"][0]["status"], "rejected")
        self.assertEqual(len(result["epic"]["discovery"]["operations"]), 2)

    def test_corrections_require_provenance_preserve_history_and_resolve_to_latest_answer(self):
        self.update([question()])
        self.update([statement("Only the requester.", answers="D-0001")])
        before = self.opened()["discovery"]["operations"]
        self.assert_rejected("E_DISCOVERY_PROVENANCE", [{**decision("correct", "D-0002"), "source": {"actor": "ai"}}])
        result = self.update([decision("correct", "D-0002", "The requester and designated company administrators.")])
        self.assertEqual(result["epic"]["discovery"]["operations"][:2], before)
        state = result["epic"]["discovery_state"]
        self.assertEqual(state["superseded_by"], {"D-0002": "D-0003"})
        self.assertEqual(state["questions"][0]["resolution_id"], "D-0003")
        self.assert_rejected("E_DISCOVERY_REFERENCE", [decision("correct", "D-0002")])
        self.assert_rejected("E_DISCOVERY_REFERENCE", [statement("Different answer", answers="D-0001")])

    def test_open_unknown_and_deferred_questions_remain_distinct_on_resume(self):
        self.update([question(), question("What is the target reduction in calls?"), question("Who owns this decision?")])
        self.update([decision("defer", "D-0001", "Defer access rules until the owner joins.", revisit="When the product owner joins")])
        self.update([decision("unknown", "D-0002", "I do not know yet.")])
        questions = self.opened()["discovery_state"]["questions"]
        self.assertEqual([item["status"] for item in questions], ["deferred", "unknown", "open"])
        self.assertEqual(questions[0]["revisit"], "When the product owner joins")
        self.update([decision("reopen", "D-0001", "The product owner is here now.")])
        self.assertEqual(self.opened()["discovery_state"]["questions"][0]["status"], "open")

    def test_invalid_links_and_client_assigned_ids_are_rejected(self):
        self.update([statement(), question()])
        for record in (statement(answers="D-9999"), decision("confirm", "D-0001"), decision("answer", "D-0001")):
            with self.subTest(record=record):
                self.assert_rejected("E_DISCOVERY_REFERENCE", [record])
        self.assert_rejected("E_UPDATE_INPUT", [{"id": "D-0003", **statement()}])

    def test_idempotent_retry_after_later_updates_does_not_duplicate_or_rewrite_history(self):
        revision = self.opened()["revision"]
        first = self.update([statement()], "stable-operation", revision)
        self.update([question()])
        before = snapshot(self.project)
        retry = self.cli_update([statement()], "stable-operation", revision)
        self.assertTrue(retry["ok"])
        self.assertTrue(retry["replayed"])
        self.assertEqual(retry["record_ids"], first["record_ids"])
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(len(retry["epic"]["discovery"]["operations"]), 2)

    def test_reusing_operation_id_with_changed_payload_or_base_revision_is_rejected(self):
        revision = self.opened()["revision"]
        self.update([statement()], "stable", revision)
        self.assert_rejected("E_IDEMPOTENCY", [question()], operation_id="stable", revision=revision)
        self.assert_rejected("E_IDEMPOTENCY", [statement()], operation_id="stable", revision=self.opened()["revision"])

    def test_revision_covers_metadata_original_idea_and_discovery_history(self):
        revision = self.opened()["revision"]
        for path in (self.epic / "metadata.yaml", self.epic / "idea.md"):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assert_rejected("E_REVISION_CONFLICT", [statement()], revision=revision)
                path.write_bytes(original)
        self.update([])
        self.assert_rejected("E_REVISION_CONFLICT", [statement()], revision=revision)
        revision = self.opened()["revision"]
        self.path.write_bytes(self.path.read_bytes() + b"\n")
        self.assert_rejected("E_REVISION_CONFLICT", [statement()], revision=revision)

    def test_revision_and_id_lookup_survive_directory_rename(self):
        revision = self.opened()["revision"]
        self.epic.rename(self.epic.with_name("arbitrary-name"))
        self.epic = self.epic.with_name("arbitrary-name")
        self.path = self.epic / "discovery.yaml"
        self.assertEqual(self.opened()["revision"], revision)
        self.assertTrue(self.update([statement()], revision=revision)["ok"])

    def test_real_concurrent_updates_cannot_both_apply_the_same_revision(self):
        revision = self.opened()["revision"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.cli_update, [statement(f"Answer {index}")], f"parallel-{index}", revision) for index in range(2)]
            results = [future.result(timeout=10) for future in futures]
        self.assertEqual(sum(item["ok"] for item in results), 1)
        loser = next(item for item in results if not item["ok"])
        self.assertIn(loser["diagnostics"][0]["code"], ("E_PROJECT_BUSY", "E_REVISION_CONFLICT"))
        self.assertEqual(len(self.opened()["discovery"]["operations"]), 1)

    def test_lock_covers_revision_check_until_atomic_publication(self):
        ready, release = threading.Event(), threading.Event()
        original_write = sdlc.atomic_history_write
        revision = self.opened()["revision"]

        def wait_before_publish(path, content):
            ready.set()
            if not release.wait(10):
                raise RuntimeError("Test writer was not released")
            original_write(path, content)

        with ThreadPoolExecutor(max_workers=1) as pool:
            with patch.object(sdlc, "atomic_history_write", side_effect=wait_before_publish):
                writer = pool.submit(sdlc.discovery_update, self.project, "REQ-0001", revision, "held-writer", [statement()])
                try:
                    self.assertTrue(ready.wait(5))
                    other = self.cli_update([question()], "competing-writer", revision)
                    self.assertFalse(other["ok"])
                    self.assertEqual(other["diagnostics"][0]["code"], "E_PROJECT_BUSY")
                finally:
                    release.set()
                self.assertTrue(writer.result(timeout=5)["ok"])
        stale = self.cli_update([question()], "competing-writer", revision)
        self.assertEqual(stale["diagnostics"][0]["code"], "E_REVISION_CONFLICT")

    def test_partial_temporary_write_failure_preserves_original_and_allows_retry(self):
        self.update([statement()])
        before = snapshot(self.project)
        revision = self.opened()["revision"]
        factory = sdlc.tempfile.NamedTemporaryFile

        def partial_file(**kwargs):
            stream = factory(**kwargs)
            write = stream.write

            def fail(content):
                write(content[:len(content) // 2])
                raise OSError("Injected partial-write failure")

            stream.write = fail
            return stream

        with patch.object(sdlc.tempfile, "NamedTemporaryFile", side_effect=partial_file):
            with self.assertRaises(OSError):
                self.update([question()], "retry-partial", revision)
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse((self.project / ".sdlc-discovery.lock").exists())
        self.assertTrue(self.update([question()], "retry-partial", revision)["ok"])

    def test_failed_initialization_leaves_no_partial_history_or_temporary_file(self):
        before = snapshot(self.project)
        with patch.object(sdlc.os, "replace", side_effect=OSError("Injected publication failure")):
            with self.assertRaises(OSError):
                self.update([])
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse(self.path.exists())
        self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_replace_and_file_fsync_failures_preserve_committed_history(self):
        self.update([statement()])
        before = snapshot(self.project)
        for name in ("replace", "fsync"):
            with self.subTest(failure=name):
                with patch.object(sdlc.os, name, side_effect=OSError("Injected failure")):
                    with self.assertRaises(OSError):
                        self.update([question()])
                self.assertEqual(snapshot(self.project), before)
                self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_post_publication_durability_failure_is_recoverable_by_idempotent_retry(self):
        revision = self.opened()["revision"]
        fsync = sdlc.os.fsync
        calls = 0

        def fail_directory_sync(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("Injected directory-sync failure")
            fsync(descriptor)

        with patch.object(sdlc.os, "fsync", side_effect=fail_directory_sync):
            with self.assertRaises(sdlc.Rejected) as caught:
                self.update([statement()], "uncertain-result", revision)
        self.assertEqual(caught.exception.diagnostics[0].code, "E_WRITE_UNCERTAIN")
        retry = self.update([statement()], "uncertain-result", revision)
        self.assertTrue(retry["replayed"])
        self.assertEqual(len(retry["epic"]["discovery"]["operations"]), 1)
        self.assertFalse(list(self.epic.glob(".discovery-*.tmp")))

    def test_malformed_or_unsupported_history_has_structured_diagnostics_and_is_not_repaired(self):
        valid = history.empty("REQ-0001")
        for content, code in (
            ("!!map [hello]\n", "E_YAML"),
            ("schema_version: [unterminated\n", "E_YAML"),
            (yaml.safe_dump({**valid, "schema_version": "99"}), "E_DISCOVERY_VERSION"),
            (yaml.safe_dump({**valid, "request_id": "REQ-0002"}), "E_DISCOVERY_HISTORY"),
            (yaml.safe_dump({**valid, "operations": None}), "E_DISCOVERY_HISTORY"),
        ):
            with self.subTest(content=content):
                self.path.write_text(content)
                before = snapshot(self.project)
                for args in (("open", "REQ-0001"), ("validate", "REQ-0001"), ("new", "--title", "Another")):
                    output = self.cli(*args)
                    self.assertFalse(output["ok"])
                    self.assertIn(code, {item["code"] for item in output["diagnostics"]})
                    self.assertTrue(any(item["file"] == str(self.path) for item in output["diagnostics"]))
                update = self.cli_update([], "invalid-history", "0" * 64)
                self.assertFalse(update["ok"])
                self.assertEqual(snapshot(self.project), before)

    def test_persisted_duplicate_operations_records_and_invalid_provenance_are_rejected(self):
        self.update([statement()])
        valid = yaml.safe_load(self.path.read_text())
        duplicate_operation = deepcopy(valid)
        duplicate_operation["operations"].append(deepcopy(valid["operations"][0]))
        duplicate_record = deepcopy(valid)
        duplicate_record["operations"][0]["records"].append(deepcopy(valid["operations"][0]["records"][0]))
        wrong_source = deepcopy(valid)
        wrong_source["operations"][0]["records"][0]["source"] = {"actor": "ai"}
        for data, code in ((duplicate_operation, "E_DISCOVERY_HISTORY"), (duplicate_record, "E_DISCOVERY_RECORD"), (wrong_source, "E_DISCOVERY_PROVENANCE")):
            with self.subTest(code=code):
                self.path.write_text(yaml.safe_dump(data))
                result = self.cli("validate")
                self.assertFalse(result["ok"])
                self.assertIn(code, {item["code"] for item in result["diagnostics"]})

    def test_history_symlinks_and_directories_are_rejected(self):
        outside = self.area / "outside.yaml"
        outside.write_text(yaml.safe_dump(history.empty("REQ-0001")))
        self.path.symlink_to(outside)
        self.assertIn("E_DISCOVERY_FILE", {item["code"] for item in self.cli("validate")["diagnostics"]})
        self.path.unlink()
        self.path.mkdir()
        self.assertIn("E_DISCOVERY_FILE", {item["code"] for item in self.cli("validate")["diagnostics"]})

    def test_non_utf8_history_and_missing_changes_file_report_the_actual_file(self):
        revision = self.opened()["revision"]
        self.path.write_bytes(b"\xff\xfe")
        result = self.cli("validate")
        issue = next(item for item in result["diagnostics"] if item["code"] == "E_READ")
        self.assertEqual(issue["file"], str(self.path))
        missing = self.area / "missing.json"
        result = self.cli("discovery-update", "REQ-0001", "--operation-id", "missing-input", "--expected-revision", revision, "--changes-file", str(missing))
        self.assertEqual(result["diagnostics"][0]["file"], str(missing))
        self.assertEqual(result["diagnostics"][0]["code"], "E_UPDATE_INPUT")

    def test_original_idea_cannot_alias_the_reserved_history_artifact(self):
        self.path.write_text(yaml.safe_dump(history.empty("REQ-0001")))
        metadata = yaml.safe_load(self.metadata_bytes)
        metadata["artifacts"]["idea"] = "discovery.yaml"
        (self.epic / "metadata.yaml").write_text(yaml.safe_dump(metadata))
        self.assertIn("E_ARTIFACT_PATH", {item["code"] for item in self.cli("validate")["diagnostics"]})

    def test_deleted_history_invalidates_the_previously_opened_revision(self):
        self.update([statement()])
        revision = self.opened()["revision"]
        self.path.unlink()
        self.assert_rejected("E_REVISION_CONFLICT", [question()], revision=revision)
        # A fresh open cannot distinguish deletion from a legacy request; documented limit.
        self.assertIsNone(self.opened()["discovery"])

    def test_abrupt_exit_before_publication_preserves_history_and_requires_inspected_lock_recovery(self):
        self.update([statement()])
        revision = self.opened()["revision"]
        before = self.path.read_bytes()
        program = (
            "import os,sys; from pathlib import Path; "
            "sys.path.insert(0,sys.argv[1]); import sdlc; "
            "sdlc.os.replace=lambda *args: os._exit(17); "
            "sdlc.discovery_update(Path(sys.argv[2]), 'REQ-0001', sys.argv[3], 'interrupted', [])"
        )
        run = subprocess.run([sys.executable, "-c", program, str(SCRIPT.parent), str(self.project), revision], capture_output=True, text=True)
        self.assertEqual(run.returncode, 17)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertTrue(self.cli("open", "REQ-0001")["ok"])
        result = self.cli_update([], "interrupted", revision)
        self.assertEqual(result["diagnostics"][0]["code"], "E_PROJECT_BUSY")
        # The child is known to have exited; simulate an operator inspecting and recovering.
        for path in self.epic.glob(".discovery-*.tmp"):
            path.unlink()
        (self.project / ".sdlc-discovery.lock").rmdir()
        self.assertTrue(self.update([], "interrupted", revision)["ok"])

    def test_missing_original_artifact_blocks_updates_and_cancelled_requests_stay_read_only(self):
        path = self.epic / "idea.md"
        revision = self.opened()["revision"]
        path.unlink()
        self.assert_rejected("E_ARTIFACT_FILE", [statement()], revision=revision)
        path.write_bytes(self.idea_bytes)
        metadata = yaml.safe_load(self.metadata_bytes)
        metadata["status"] = "cancelled"
        (self.epic / "metadata.yaml").write_text(yaml.safe_dump(metadata))
        self.assert_rejected("E_STATUS", [statement()])

    def test_invalid_changes_json_and_unknown_record_fields_are_structured_errors(self):
        revision = self.opened()["revision"]
        changes = self.area / "invalid.json"
        for content in ('{"records": [', '{"records": [], "records": []}', '{"records": [], "extra": true}'):
            with self.subTest(content=content):
                changes.write_text(content)
                result = self.cli("discovery-update", "REQ-0001", "--expected-revision", revision, "--operation-id", "bad-input", "--changes-file", str(changes))
                self.assertFalse(result["ok"])
                self.assertEqual(result["diagnostics"][0]["code"], "E_UPDATE_INPUT")
                self.assertEqual(result["diagnostics"][0]["file"], str(changes))
        self.assert_rejected("E_DISCOVERY_RECORD", [{**statement(), "surprise": True}])

    def test_invalid_unicode_is_rejected_before_publication_but_valid_unicode_is_preserved(self):
        revision = self.opened()["revision"]
        before = snapshot(self.project)
        for field in ("text", "topic", "quote"):
            record = statement()
            if field == "quote":
                record["source"]["quote"] = "\ud800"
            else:
                record[field] = "\ud800"
            with self.subTest(field=field):
                result = self.cli_update([record], f"invalid-unicode-{field}", revision)
                self.assertFalse(result["ok"])
                self.assertEqual(result["diagnostics"][0]["code"], "E_DISCOVERY_PROVENANCE" if field == "quote" else "E_DISCOVERY_RECORD")
                self.assertEqual(snapshot(self.project), before)
        original = "Uživatel potřebuje přehled požadavků 📋."
        result = self.cli_update([statement(original)], "valid-unicode", revision)
        self.assertTrue(result["ok"])
        self.assertEqual(self.opened()["discovery"]["operations"][0]["records"][0]["source"]["quote"], original)

    def test_updates_do_not_run_git_or_change_git_data(self):
        git = shutil.which("git")
        self.assertIsNotNone(git)
        subprocess.run([git, "init", "-q", str(self.project)], capture_output=True, check=True)
        before = snapshot(self.project / ".git")
        trap = self.area / "git"
        marker = self.area / "git-called"
        trap.write_text('#!/bin/sh\necho called > "$DISCOVERY_GIT_MARKER"\nexit 99\n')
        trap.chmod(0o755)
        env = dict(os.environ, PATH=str(self.area) + os.pathsep + os.environ.get("PATH", ""), DISCOVERY_GIT_MARKER=str(marker))
        changes = self.area / "records.json"
        changes.write_text(json.dumps({"records": [statement()]}))
        result = self.cli("discovery-update", "REQ-0001", "--expected-revision", self.opened()["revision"], "--operation-id", "no-git", "--changes-file", str(changes), env=env)
        self.assertTrue(result["ok"])
        self.assertFalse(marker.exists())
        self.assertEqual(snapshot(self.project / ".git"), before)


if __name__ == "__main__":
    unittest.main()
