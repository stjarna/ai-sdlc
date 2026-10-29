"""Procedural gate acceptance tests; all identities/decisions here are test fixtures."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sdlc
import business_refinement as business
import business_approval as approval


SCRIPT = Path(sdlc.__file__).resolve()


def record(kind, text, **extra):
    source = {"actor": "ai"} if kind in ("question", "ai_assumption") else {"actor": "user", "quote": text}
    return {"kind": kind, "topic": "test_fixture", "text": text, "source": source, **extra}


class BusinessApprovalTests(unittest.TestCase):
    def test_legacy_baseline_and_review_hash_golden(self):
        """Captured from Increment 5 before extracting shared approval code."""
        with patch.object(business, "timestamp", return_value="2026-10-28T12:00:00Z"):
            self.setUp(legacy_templates=True)
            before = self.view()
            self.assertEqual(before["review_revision"], "c69b7852b0e6fad5494ba0fca0a09878ac99cb7d2c8dde120229a63649590846")
            approved = self.approve()
            self.assertEqual(approved["baseline_id"], "b8fedd4455ab54f64754bbb81b00fb438fc97a7d35377932a4e75c58e205113c")
            manifest, _ = approval.read_baseline(self.directory, approved["baseline_id"], sdlc.StrictLoader)
            self.assertEqual(manifest["schema_version"], "0.1")
            self.assertEqual(set(manifest["files"]), set(approval.BASELINE_FILES))

    def setUp(self, legacy_templates=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.counter = 0
        self.directory = Path(sdlc.new_epic(self.project, "Task due dates", "People forget commitments.", requester="Fixture Requester")["epic"]["directory"])
        # Deliberately construct a pre-ownership legacy fixture. The golden hashes
        # protect the exact historical schema/bytes, not today's creation defaults.
        metadata_path = self.directory / "metadata.yaml"
        metadata = yaml.safe_load(metadata_path.read_text())
        metadata.pop("ownership")
        if legacy_templates:
            metadata.pop("template_provenance")
        metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True))
        self.append([record("user_statement", "Record deadlines against tasks."), record("question", "Dates or reminders?")])
        self.append([record("user_statement", "Dates only; reminders are excluded.", answers="D-0002"), record("ai_assumption", "Dates are optional.")])
        self.append([record("human_decision", "Yes, optional.", action="confirm", target="D-0004"), record("question", "Allow past dates?")])
        self.append([record("human_decision", "Defer until support discussion.", action="defer", target="D-0006", revisit="After support discussion")])
        # Historical completion evidence predates ownership tracking.
        epic = self.view()["epic"]
        metadata = dict(epic["metadata"])
        metadata.update(schema_version="0.2", status="ready_for_refinement", lifecycle=[{
            "id": self.unique("fixture-complete"), "action": "complete", "from": "discovery", "to": "ready_for_refinement",
            "base_revision": epic["revision"], "actor": "Fixture Requester", "decision": "Test fixture: explicitly complete Discovery.", "timestamp": business.timestamp()}])
        metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True))
        source = self.view()["epic"]["source_revision"]
        self.initial_document = f"# Business Refinement — REQ-0001\n\nSource revision: {source}\n\n## Confirmed information\n### Business value\n- **B-001** [D-0001] Record deadlines against tasks.\n### Scope and exclusions\n- **B-002** [D-0003] Dates only; reminders are excluded.\n- **B-003** [D-0005, D-0004] Dates are optional.\n\n## Unresolved issues\n- **U-001** [D-0006] Past-date rule remains deferred until support discussion (D-0007).\n\n## Unconfirmed proposals\nNone recorded.\n"
        self.revise(self.initial_document, mode="generate")
        if legacy_templates:
            # Reconstruct the captured pre-template fixture, never migrate real history.
            path = self.directory / "business-history.yaml"
            ledger = yaml.safe_load(path.read_text())
            ledger["schema_version"] = "0.1"
            for entry in ledger["revisions"]:
                entry.pop("schema_version", None)
                entry.pop("template", None)
            path.write_text(yaml.safe_dump(ledger, sort_keys=False, allow_unicode=True))

    def unique(self, prefix):
        self.counter += 1
        return f"{prefix}-{self.counter}"

    def view(self):
        return sdlc.business_review(self.project, "REQ-0001")

    def append(self, records):
        epic = sdlc.inspect_epics(self.project, "open", "REQ-0001")["epic"]
        return sdlc.discovery_update(self.project, "REQ-0001", epic["revision"], self.unique("fixture-discovery"), records)

    def complete(self):
        epic = self.view()["epic"]
        return sdlc.lifecycle_change(self.project, "REQ-0001", epic["revision"], self.unique("fixture-complete"), "Fixture Requester", "Test fixture: explicitly complete Discovery.", "complete")

    def reopen(self):
        epic = self.view()["epic"]
        return sdlc.lifecycle_change(self.project, "REQ-0001", epic["revision"], self.unique("fixture-reopen"), "Fixture Requester", "Test fixture: explicitly reopen Discovery.", "reopen")

    def revise(self, content, mode="revise"):
        epic = self.view()["epic"]
        path = self.project / (self.unique("input") + ".md")
        path.write_text(content)
        return sdlc.business_write(self.project, "REQ-0001", epic["source_revision"], epic["business"]["revision"] if epic["business"] else None, self.unique("fixture-business"), "Fixture PO", "Test fixture refinement", path, mode)

    def request(self, action="approve", view=None, op=None, acknowledged=None, selected=None):
        view = self.view() if view is None else view
        return {"project": self.project, "epic_id": "REQ-0001", "expected_review": view["review_revision"], "expected_business": view["epic"]["business"]["revision"], "operation_id": op or self.unique("gate"), "actor": "Fixture PO", "reason": "Explicit test fixture decision", "decision": "Explicit test fixture approval acknowledging U-001." if action == "approve" else "Please clarify the wording." if action == "request_changes" else "Explicit test fixture advancement", "action": action, "acknowledged": (["U-001"] if acknowledged is None else acknowledged) if action == "approve" else [], "approval_id": selected}

    def execute(self, request):
        if request["action"] == "advance":
            request = {**request, "reason": request["decision"]}
        return sdlc.business_gate(**request)

    def approve(self):
        return self.execute(self.request())

    def advance(self, selected=None):
        view = self.view()
        selected = selected or view["approval"]["latest_decision"]["id"]
        return self.execute(self.request("advance", view=view, selected=selected))

    def rejected(self, code, action):
        with self.assertRaises(sdlc.Rejected) as caught:
            action()
        self.assertIn(code, {item.code for item in caught.exception.diagnostics})

    def baseline(self, output):
        return self.directory / "business-baselines" / output["baseline_id"]

    def test_approval_freezes_exact_context_and_advancement_is_separate(self):
        before = self.view()
        files = approval.read_snapshot(self.directory, before["epic"]["metadata"])
        approved = self.approve()
        self.assertEqual(approved["epic"]["metadata"]["status"], "business_refinement")
        self.assertEqual(approved["epic"]["metadata"]["schema_version"], "0.3")
        self.assertTrue(approved["epic"]["approval"]["can_advance"])
        manifest, frozen = approval.read_baseline(self.directory, approved["baseline_id"], sdlc.StrictLoader)
        self.assertEqual(frozen, files)
        self.assertEqual(manifest["source_revision"], before["epic"]["source_revision"])
        self.assertEqual(approved["epic"]["metadata"]["business_decisions"][0]["acknowledged_open_items"], ["U-001"])
        advanced = self.advance()
        self.assertEqual(advanced["epic"]["metadata"]["status"], "ready_for_analysis")
        review = self.view()
        self.assertTrue(review["current"])
        self.assertTrue(review["approval"]["valid"])
        self.assertFalse(review["approval"]["can_advance"])
        self.assertEqual(review["approval"]["analysis_input"], {"approval_id": approved["decision_id"], "baseline_id": approved["baseline_id"]})
        self.assertEqual({p.name for p in self.directory.iterdir()} - {"business-baselines"}, {"metadata.yaml", "idea.md", "discovery.yaml", "business.md", "business-history.yaml"})

    def test_no_advance_without_approval_or_without_explicit_acknowledgement(self):
        metadata = (self.directory / "metadata.yaml").read_bytes()
        self.rejected("E_APPROVAL_REQUIRED", lambda: self.advance("BD-0001"))
        for items, code in (([], "E_ACKNOWLEDGEMENT"), (["U-999"], "E_ACKNOWLEDGEMENT"), (["U-001", "U-001"], "E_UPDATE_INPUT")):
            with self.subTest(items=items):
                self.rejected(code, lambda: self.execute(self.request(acknowledged=items)))
        self.assertEqual((self.directory / "metadata.yaml").read_bytes(), metadata)
        self.assertFalse((self.directory / "business-baselines").exists())

    def test_request_changes_preserves_draft_and_supersedes_approval_then_reapproval(self):
        approved = self.approve()
        old_draft = (self.directory / "business.md").read_bytes()
        feedback = self.execute(self.request("request_changes"))
        self.assertEqual(feedback["epic"]["metadata"]["status"], "business_refinement")
        self.assertEqual((self.directory / "business.md").read_bytes(), old_draft)
        self.assertEqual(self.view()["approval"]["status"], "changes_requested")
        self.rejected("E_APPROVAL_SUPERSEDED", lambda: self.advance(approved["decision_id"]))
        self.revise(self.initial_document.replace("Record deadlines against tasks.", "Record due dates against tasks."))
        again = self.approve()
        self.assertEqual(len(again["epic"]["metadata"]["business_decisions"]), 3)
        self.rejected("E_APPROVAL_SUPERSEDED", lambda: self.advance(approved["decision_id"]))
        self.assertTrue(self.advance(again["decision_id"])["ok"])
        self.assertTrue(self.baseline(approved).is_dir())

    def test_feedback_can_be_first_decision_without_creating_baseline(self):
        output = self.execute(self.request("request_changes"))
        self.assertEqual(output["decision_id"], "BD-0001")
        self.assertIsNone(output["baseline_id"])
        self.assertFalse((self.directory / "business-baselines").exists())
        self.assertEqual(output["epic"]["metadata"]["business_decisions"][0]["decision"], "Please clarify the wording.")
        self.assertTrue(self.approve()["ok"])

    def test_repeated_explicit_approval_supersedes_previous_and_requires_fresh_review(self):
        first_request = self.request()
        first = self.execute(first_request)
        self.rejected("E_REVISION_CONFLICT", lambda: self.execute({**first_request, "operation_id": self.unique("other-approval")}))
        second = self.approve()
        self.assertNotEqual(first["baseline_id"], second["baseline_id"])
        replay = self.execute(first_request)
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["epic"]["approval"]["latest_decision"]["id"], second["decision_id"])
        self.rejected("E_APPROVAL_SUPERSEDED", lambda: self.advance(first["decision_id"]))
        self.assertTrue(self.advance(second["decision_id"])["ok"])

    def test_new_decisions_require_declared_identity_and_explicit_text(self):
        request = self.request()
        for key in ("actor", "decision", "reason"):
            with self.subTest(key=key):
                self.rejected("E_UPDATE_INPUT", lambda: self.execute({**request, key: ""}))
        self.assertFalse((self.directory / "business-baselines").exists())

    def test_stale_review_or_business_revision_is_rejected(self):
        old = self.request()
        self.execute(self.request("request_changes"))
        self.rejected("E_REVISION_CONFLICT", lambda: self.execute(old))
        request = self.request()
        request["expected_business"] = "0" * 64
        self.rejected("E_REVISION_CONFLICT", lambda: self.execute(request))

    def test_business_revisions_including_identical_content_invalidate_approval(self):
        for content in (self.initial_document, self.initial_document.replace("Record deadlines", "Record due dates")):
            with self.subTest(content_changed=content != self.initial_document):
                approved = self.approve()
                self.revise(content)
                self.assertFalse(self.view()["approval"]["valid"])
                self.assertIn("business_revision_changed", self.view()["approval"]["reasons"])
                self.rejected("E_APPROVAL_STALE", lambda: self.advance(approved["decision_id"]))

    def test_returning_to_original_bytes_does_not_reactivate_historical_approval(self):
        approved = self.approve()
        original_digest = approved["epic"]["business"]["revision"]
        self.revise(self.initial_document.replace("Record deadlines", "Record due dates"))
        self.revise(self.initial_document)
        self.assertEqual(self.view()["epic"]["business"]["revision"], original_digest)
        self.assertFalse(self.view()["approval"]["valid"])
        self.rejected("E_APPROVAL_STALE", lambda: self.advance(approved["decision_id"]))

    def check_reopening(self, advanced):
        approved = self.approve()
        decisions = deepcopy(approved["epic"]["metadata"]["business_decisions"])
        source = approved["epic"]["source_revision"]
        baseline_bytes = {p.name: p.read_bytes() for p in self.baseline(approved).iterdir()}
        if advanced:
            self.advance()
        self.reopen()
        self.assertEqual(self.view()["epic"]["metadata"]["schema_version"], "0.3")
        self.assertFalse(self.view()["approval"]["valid"])
        self.assertIsNone(self.view()["approval"]["analysis_input"])
        self.assertEqual(self.view()["epic"]["metadata"]["business_decisions"], decisions)
        self.complete()
        self.assertFalse(self.view()["current"])
        self.revise(self.initial_document, mode="generate")
        self.assertEqual(self.view()["epic"]["source_revision"], source)
        self.assertTrue(self.view()["current"])
        self.rejected("E_APPROVAL_STALE", lambda: self.advance(approved["decision_id"]))
        self.assertEqual({p.name: p.read_bytes() for p in self.baseline(approved).iterdir()}, baseline_bytes)
        self.assertTrue(self.approve()["ok"])
        self.assertTrue(self.advance()["ok"])

    def test_reopen_after_approval_requires_completion_refinement_and_new_approval(self):
        self.check_reopening(False)

    def test_reopen_after_advancement_preserves_history_and_requires_new_approval(self):
        self.check_reopening(True)

    def test_source_byte_change_invalidates_draft_and_approval(self):
        approved = self.approve()
        path = self.directory / "idea.md"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertFalse(self.view()["current"])
        self.assertIn("source_revision_changed", self.view()["approval"]["reasons"])
        self.rejected("E_APPROVAL_STALE", lambda: self.advance(approved["decision_id"]))
        self.rejected("E_APPROVAL_STALE", lambda: self.approve())

    def test_all_unconfirmed_proposals_require_acknowledgement_without_becoming_confirmed(self):
        self.reopen()
        self.append([record("ai_assumption", "Users might want date colours.")])
        self.complete()
        source = self.view()["epic"]["source_revision"]
        document = self.initial_document.replace(self.view()["epic"]["business"]["source_revision"], source).replace("None recorded.", "- **P-001** [D-0008] Proposed date colours.")
        self.revise(document, mode="generate")
        self.rejected("E_ACKNOWLEDGEMENT", lambda: self.approve())
        output = self.execute(self.request(acknowledged=["P-001", "U-001"]))
        self.assertTrue(output["ok"])
        self.assertEqual(output["epic"]["discovery_state"]["assumptions"][-1]["status"], "proposed")

    def test_gate_idempotency_and_conflicting_retries_do_not_restore_old_authority(self):
        request = self.request()
        first = self.execute(request)
        metadata = (self.directory / "metadata.yaml").read_bytes()
        self.assertTrue(self.execute(request)["replayed"])
        self.assertEqual((self.directory / "metadata.yaml").read_bytes(), metadata)
        for key, value in (("actor", "Other fixture PO"), ("reason", "Other reason"), ("decision", "Different words"), ("expected_review", "0" * 64), ("acknowledged", [])):
            with self.subTest(key=key):
                self.rejected("E_IDEMPOTENCY", lambda: self.execute({**request, key: value}))
        self.execute(self.request("request_changes"))
        retried = self.execute(request)
        self.assertTrue(retried["replayed"])
        self.assertEqual(retried["decision_id"], first["decision_id"])
        self.assertFalse(retried["epic"]["approval"]["valid"])
        self.assertEqual(len(retried["epic"]["metadata"]["business_decisions"]), 2)

    def test_feedback_and_advance_retries_preserve_current_state(self):
        feedback = self.request("request_changes")
        self.execute(feedback)
        self.assertTrue(self.execute(feedback)["replayed"])
        self.rejected("E_IDEMPOTENCY", lambda: self.execute({**feedback, "decision": "Other feedback"}))
        approved = self.approve()
        advance = self.request("advance", selected=approved["decision_id"])
        self.execute(advance)
        self.assertTrue(self.execute(advance)["replayed"])
        self.rejected("E_IDEMPOTENCY", lambda: self.execute({**advance, "approval_id": "BD-9999"}))
        self.reopen()
        retry = self.execute(advance)
        self.assertTrue(retry["replayed"])
        self.assertEqual(retry["epic"]["metadata"]["status"], "discovery")
        self.assertFalse(retry["epic"]["approval"]["valid"])

    def competing(self, actions):
        view = self.view()
        requests = [self.request(action, view=view) for action in actions]
        def run(request):
            try:
                return self.execute(request)
            except sdlc.Rejected as exc:
                return {"ok": False, "code": exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, requests))
        self.assertEqual(sum(item["ok"] for item in results), 1)
        self.assertIn(next(item["code"] for item in results if not item["ok"]), ("E_PROJECT_BUSY", "E_REVISION_CONFLICT"))
        self.assertEqual(len(self.view()["epic"]["metadata"]["business_decisions"]), 1)

    def test_concurrent_approvals_cannot_both_commit_same_review(self):
        self.competing(("approve", "approve"))

    def test_concurrent_feedback_and_approval_cannot_both_commit_same_review(self):
        self.competing(("request_changes", "approve"))

    def test_approval_then_revision_is_serialized_and_invalidates_approval(self):
        entered, release = threading.Event(), threading.Event()
        real = approval.publish_baseline
        def pause(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test synchronization timeout")
            return real(*args)
        request = self.request()
        with ThreadPoolExecutor(max_workers=1) as pool, patch.object(approval, "publish_baseline", side_effect=pause):
            future = pool.submit(self.execute, request)
            self.assertTrue(entered.wait(5))
            try:
                self.rejected("E_PROJECT_BUSY", lambda: self.revise(self.initial_document))
            finally:
                release.set()
            future.result(timeout=10)
        self.revise(self.initial_document)
        self.assertFalse(self.view()["approval"]["valid"])

    def test_revision_then_approval_or_advancement_rejects_earlier_review(self):
        approved = self.approve()
        old_approval = self.request()
        old_advance = self.request("advance", selected=approved["decision_id"])
        entered, release = threading.Event(), threading.Event()
        real = business.publish
        def pause(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test synchronization timeout")
            return real(*args)
        with ThreadPoolExecutor(max_workers=1) as pool, patch.object(business, "publish", side_effect=pause):
            future = pool.submit(self.revise, self.initial_document)
            self.assertTrue(entered.wait(5))
            try:
                self.rejected("E_PROJECT_BUSY", lambda: self.execute(old_approval))
                self.rejected("E_PROJECT_BUSY", lambda: self.execute(old_advance))
            finally:
                release.set()
            future.result(timeout=10)
        self.rejected("E_REVISION_CONFLICT", lambda: self.execute(old_approval))
        self.rejected("E_REVISION_CONFLICT", lambda: self.execute(old_advance))

    def test_advancement_then_revision_is_rejected_by_lock_and_lifecycle(self):
        approved = self.approve()
        request = self.request("advance", selected=approved["decision_id"])
        entered, release = threading.Event(), threading.Event()
        real = sdlc.atomic_history_write
        def pause(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test synchronization timeout")
            return real(*args)
        with ThreadPoolExecutor(max_workers=1) as pool, patch.object(sdlc, "atomic_history_write", side_effect=pause):
            future = pool.submit(self.execute, request)
            self.assertTrue(entered.wait(5))
            try:
                self.rejected("E_PROJECT_BUSY", lambda: self.revise(self.initial_document))
            finally:
                release.set()
            future.result(timeout=10)
        self.rejected("E_STATUS", lambda: self.revise(self.initial_document))

    def test_corruption_deletion_symlinks_and_extra_baseline_files_fail_closed(self):
        approved = self.approve()
        root = self.baseline(approved)
        for name in (*approval.BASELINE_FILES, "manifest.json"):
            with self.subTest(file=name):
                path = root / name
                original = path.read_bytes()
                for mutation in ("modify", "delete", "symlink"):
                    with self.subTest(mutation=mutation):
                        if mutation == "modify":
                            path.write_bytes(original + b"\n")
                        else:
                            path.unlink()
                            if mutation == "symlink":
                                outside = self.project / "outside"
                                outside.write_bytes(original)
                                path.symlink_to(outside)
                        review = self.view()
                        self.assertFalse(review["ok"])
                        self.assertFalse(review["approval"]["valid"])
                        self.assertTrue(any(item["code"].startswith("E_BASELINE_") for item in review["diagnostics"]))
                        if path.is_symlink():
                            path.unlink()
                        path.write_bytes(original)
                self.assertTrue(self.view()["approval"]["valid"])
        extra = root / "unexpected"
        extra.write_text("unexpected")
        self.assertFalse(self.view()["approval"]["valid"])
        extra.unlink()
        saved = self.project / "saved-baseline"
        root.rename(saved)
        self.assertIn("E_BASELINE_MISSING", {item["code"] for item in self.view()["diagnostics"]})
        self.rejected("E_BASELINE_MISSING", lambda: self.advance(approved["decision_id"]))
        self.assertFalse(root.exists())
        saved.rename(root)
        self.assertTrue(self.view()["approval"]["valid"])
        retained = self.project / "retained-baseline-root"
        container = root.parent
        container.rename(retained)
        container.symlink_to(retained, target_is_directory=True)
        self.assertFalse(self.view()["approval"]["valid"])
        container.unlink()
        retained.rename(container)
        self.assertTrue(self.view()["approval"]["valid"])

    def test_audit_validation_rejects_malformed_or_dangling_entries_without_repair(self):
        self.approve()
        path = self.directory / "metadata.yaml"
        original = path.read_bytes()
        metadata = yaml.safe_load(original)
        for key, value in (("action", "automatic_approve"), ("discovery_completion_id", "missing"), ("business_operation_id", "missing"), ("timestamp", "not-a-timestamp")):
            with self.subTest(key=key):
                modified = deepcopy(metadata)
                modified["business_decisions"][0][key] = value
                content = yaml.safe_dump(modified).encode()
                path.write_bytes(content)
                self.rejected("E_BUSINESS_DECISIONS", self.view)
                self.assertEqual(path.read_bytes(), content)
                path.write_bytes(original)

    def test_frozen_review_revision_and_prior_audit_cannot_diverge_silently(self):
        self.execute(self.request("request_changes"))
        self.approve()
        path = self.directory / "metadata.yaml"
        original = path.read_bytes()
        data = yaml.safe_load(original)
        for mutate in (lambda d: d["business_decisions"][-1].update(review_revision="0" * 64), lambda d: d["business_decisions"][0].update(decision="Rewritten earlier feedback")):
            modified = deepcopy(data)
            mutate(modified)
            path.write_text(yaml.safe_dump(modified))
            review = self.view()
            self.assertFalse(review["ok"])
            self.assertIn("E_BASELINE_CONTEXT", {item["code"] for item in review["diagnostics"]})
            path.write_bytes(original)
        self.assertTrue(self.view()["approval"]["valid"])

    def test_baseline_write_failures_publish_no_approval_and_exact_retry_recovers(self):
        request = self.request()
        metadata = (self.directory / "metadata.yaml").read_bytes()
        with patch.object(approval.os, "rename", side_effect=OSError("injected rename failure")):
            self.rejected("E_BASELINE_WRITE", lambda: self.execute(request))
        self.assertEqual((self.directory / "metadata.yaml").read_bytes(), metadata)
        self.assertFalse(self.view()["approval"]["valid"])
        self.assertTrue(self.execute(request)["ok"])

    def test_file_fsync_failure_during_baseline_preparation_leaves_no_approval(self):
        request = self.request()
        real = approval.os.fsync
        def fail_file(descriptor):
            if stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("injected file fsync failure")
            return real(descriptor)
        with patch.object(approval.os, "fsync", side_effect=fail_file):
            self.rejected("E_BASELINE_WRITE", lambda: self.execute(request))
        self.assertEqual(self.view()["epic"]["metadata"]["schema_version"], "0.2")
        self.assertTrue(self.execute(request)["ok"])

    def test_directory_durability_failures_before_and_after_baseline_publication_recover(self):
        request = self.request()
        real = approval.fsync_directory
        for stage in ("new_root", "staging", "published_root"):
            with self.subTest(stage=stage):
                root = self.directory / "business-baselines"
                if root.exists():
                    shutil.rmtree(root)
                def fail(path):
                    if (stage == "new_root" and path == self.directory) or (stage == "staging" and path.name.startswith(".pending-")) or (stage == "published_root" and path == root):
                        raise OSError("injected directory durability failure")
                    return real(path)
                with patch.object(approval, "fsync_directory", side_effect=fail):
                    self.rejected("E_BASELINE_WRITE", lambda: self.execute(request))
                self.assertFalse(self.view()["approval"]["valid"])
        # The published orphan must be fsynced again before metadata can refer to it.
        root = self.directory / "business-baselines"
        with patch.object(approval, "fsync_directory", side_effect=OSError("orphan still not durable")):
            self.rejected("E_BASELINE_WRITE", lambda: self.execute(request))
        self.assertFalse(self.view()["approval"]["valid"])
        self.assertTrue(self.execute(request)["ok"])

    def test_observed_source_change_during_preparation_prevents_approval_commit(self):
        request = self.request()
        real = approval.publish_baseline
        def change_after_preparation(*args):
            result = real(*args)
            path = self.directory / "idea.md"
            path.write_bytes(path.read_bytes() + b"\n")
            return result
        with patch.object(approval, "publish_baseline", side_effect=change_after_preparation):
            self.rejected("E_REVISION_CONFLICT", lambda: self.execute(request))
        self.assertFalse(self.view()["approval"]["valid"])
        self.assertNotIn("business_decisions", self.view()["epic"]["metadata"])

    def test_orphan_baseline_before_metadata_commit_has_no_authority_and_is_reused(self):
        request = self.request()
        metadata = (self.directory / "metadata.yaml").read_bytes()
        with patch.object(sdlc, "atomic_history_write", side_effect=OSError("injected pre-commit failure")):
            with self.assertRaises(OSError):
                self.execute(request)
        self.assertEqual((self.directory / "metadata.yaml").read_bytes(), metadata)
        self.assertFalse(self.view()["approval"]["valid"])
        baselines = list((self.directory / "business-baselines").iterdir())
        self.assertEqual(len(baselines), 1)
        frozen = {p.name: p.read_bytes() for p in baselines[0].iterdir()}
        result = self.execute(request)
        self.assertEqual(result["baseline_id"], baselines[0].name)
        self.assertEqual({p.name: p.read_bytes() for p in baselines[0].iterdir()}, frozen)

    def test_metadata_replace_failure_leaves_only_orphan_and_retries_safely(self):
        request = self.request()
        with patch.object(sdlc.os, "replace", side_effect=OSError("injected metadata replace failure")):
            with self.assertRaises(OSError):
                self.execute(request)
        self.assertFalse(self.view()["approval"]["valid"])
        self.assertTrue(self.execute(request)["ok"])

    def uncertain_metadata_write(self, request):
        replaced = False
        real_replace, real_fsync = sdlc.os.replace, sdlc.os.fsync
        def replace(*args):
            nonlocal replaced
            real_replace(*args)
            replaced = True
        def fsync(descriptor):
            if replaced:
                raise OSError("injected post-publication fsync failure")
            return real_fsync(descriptor)
        with patch.object(sdlc.os, "replace", side_effect=replace), patch.object(sdlc.os, "fsync", side_effect=fsync):
            self.rejected("E_WRITE_UNCERTAIN", lambda: self.execute(request))
        return self.execute(request)

    def test_post_commit_uncertainty_replays_approval_without_duplicate_decision(self):
        output = self.uncertain_metadata_write(self.request())
        self.assertTrue(output["replayed"])
        self.assertEqual(len(output["epic"]["metadata"]["business_decisions"]), 1)

    def test_post_commit_uncertainty_replays_advancement_without_duplicate_transition(self):
        approved = self.approve()
        output = self.uncertain_metadata_write(self.request("advance", selected=approved["decision_id"]))
        self.assertTrue(output["replayed"])
        self.assertEqual(output["epic"]["metadata"]["status"], "ready_for_analysis")
        self.assertEqual(len([event for event in output["epic"]["metadata"]["lifecycle"] if event["action"] == "advance"]), 1)

    def test_abrupt_exit_requires_inspected_lock_recovery_but_creates_no_approval(self):
        request = self.request()
        args = {key: str(value) if isinstance(value, Path) else value for key, value in request.items()}
        program = "import os,sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import sdlc,business_approval; args=json.loads(sys.argv[2]); args['project']=Path(args['project']); business_approval.os.rename=lambda *args: os._exit(17); sdlc.business_gate(**args)"
        run = subprocess.run([sys.executable, "-c", program, str(SCRIPT.parent), json.dumps(args)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 17, run.stderr)
        self.assertTrue((self.project / ".sdlc-discovery.lock").is_dir())
        self.assertFalse(self.view()["approval"]["valid"])
        self.rejected("E_PROJECT_BUSY", lambda: self.execute(request))
        # The child has exited: simulate explicit operator inspection and lock recovery.
        (self.project / ".sdlc-discovery.lock").rmdir()
        self.assertTrue(self.execute(request)["ok"])

    def test_review_revision_covers_metadata_history_and_source_bytes(self):
        initial = self.view()["review_revision"]
        for name in ("metadata.yaml", "business-history.yaml", "idea.md", "discovery.yaml"):
            with self.subTest(file=name):
                path = self.directory / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assertNotEqual(self.view()["review_revision"], initial)
                path.write_bytes(original)
        self.approve()
        current = self.view()["review_revision"]
        renamed = self.directory.with_name("renamed-request")
        self.directory.rename(renamed)
        self.directory = renamed
        self.assertEqual(self.view()["review_revision"], current)
        self.assertTrue(self.view()["approval"]["valid"])

    def test_baseline_freezes_original_idea_from_legacy_nested_artifact_path(self):
        nested = self.directory / "source"
        nested.mkdir()
        (self.directory / "idea.md").rename(nested / "request.md")
        path = self.directory / "metadata.yaml"
        metadata = yaml.safe_load(path.read_text())
        metadata["artifacts"]["idea"] = "source/request.md"
        path.write_text(yaml.safe_dump(metadata))
        output = self.approve()
        manifest, frozen = approval.read_baseline(self.directory, output["baseline_id"], sdlc.StrictLoader)
        self.assertEqual(manifest["idea_reference"], "source/request.md")
        self.assertEqual(frozen["idea.md"], (nested / "request.md").read_bytes())
        self.assertTrue(self.advance()["ok"])

    def test_real_cli_uses_declared_identity_and_separate_operations(self):
        def cli(*args):
            run = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *args], capture_output=True, text=True)
            self.assertEqual(run.stderr, "")
            result = json.loads(run.stdout)
            self.assertEqual(run.returncode, 0 if result["ok"] else 1)
            return result
        view = cli("business-review", "REQ-0001")
        base = ["REQ-0001", "--expected-review-revision", view["review_revision"], "--expected-business-revision", view["epic"]["business"]["revision"]]
        feedback = cli("business-request-changes", *base, "--operation-id", "cli-feedback", "--reviewer", "Fixture CLI PO", "--reason", "Fixture review", "--feedback", "Please clarify wording before approval.")
        self.assertEqual(feedback["epic"]["metadata"]["status"], "business_refinement")
        self.assertEqual(feedback["epic"]["approval"]["status"], "changes_requested")
        view = cli("business-review", "REQ-0001")
        base = ["REQ-0001", "--expected-review-revision", view["review_revision"], "--expected-business-revision", view["epic"]["business"]["revision"]]
        output = cli("business-approve", *base, "--operation-id", "cli-approve", "--approver", "Fixture CLI PO", "--reason", "Fixture ready", "--decision", "Explicit fixture approval, acknowledging U-001.", "--acknowledge-open-item", "U-001")
        self.assertEqual(output["epic"]["metadata"]["status"], "business_refinement")
        view = cli("business-review", "REQ-0001")
        output = cli("business-advance", "REQ-0001", "--expected-review-revision", view["review_revision"], "--expected-business-revision", view["epic"]["business"]["revision"], "--operation-id", "cli-advance", "--approval-id", output["decision_id"], "--actor", "Fixture CLI PO", "--reason", "Explicit fixture advancement")
        self.assertEqual(output["epic"]["metadata"]["status"], "ready_for_analysis")


if __name__ == "__main__":
    unittest.main()
