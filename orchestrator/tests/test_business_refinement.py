"""Increment 3 acceptance tests against isolated local Epics."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sdlc
import business_refinement as business


SCRIPT = Path(sdlc.__file__).resolve()


def record(kind, text, topic="scope"):
    return {"kind": kind, "topic": topic, "text": text, "source": {"actor": "ai"} if kind in ("question", "ai_assumption") else {"actor": "user", "quote": text}}


class BusinessRefinementTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name)
        self.created = sdlc.new_epic(self.project, "Task due dates", "Users need due dates on tasks.")["epic"]
        self.directory = Path(self.created["directory"])
        self.docfile = self.project / "draft-input.md"
        self.counter = 0

    def cli(self, *args):
        run = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *args], capture_output=True, text=True)
        self.assertEqual(run.stderr, "", run.stderr)
        output = json.loads(run.stdout)
        self.assertEqual(run.returncode, 0 if output["ok"] else 1)
        return output

    def opened(self):
        return self.cli("open", "REQ-0001")["epic"]

    def update(self, records):
        self.counter += 1
        return sdlc.discovery_update(self.project, "REQ-0001", self.opened()["revision"], f"discover-{self.counter}", records)

    def complete(self, op="complete-1", revision=None):
        return sdlc.lifecycle_change(self.project, "REQ-0001", revision or self.opened()["revision"], op, "Requester David", "I confirm Discovery is complete for refinement.", "complete")

    def draft(self, source, confirmed="- **B-001** [D-0001] Users need due dates on tasks.", unresolved="None recorded.", proposals="None recorded."):
        return f"# Business Refinement — REQ-0001\n\nSource revision: {source}\n\n## Confirmed information\n### Business value\n{confirmed}\n\n## Unresolved issues\n{unresolved}\n\n## Unconfirmed proposals\n{proposals}\n"

    def prepare(self, extra=None):
        self.update([record("user_statement", "Users need due dates on tasks."), *(extra or [])])
        return self.complete()["epic"]

    def write(self, content, mode="generate", op=None, source=None, previous=None, editor="Product Owner", reason="Initial business draft"):
        self.counter += 1
        self.docfile.write_text(content, encoding="utf-8")
        return sdlc.business_write(self.project, "REQ-0001", source or self.opened()["source_revision"], previous, op or f"business-{self.counter}", editor, reason, self.docfile, mode)

    def rejected(self, code, action):
        with self.assertRaises(sdlc.Rejected) as caught:
            action()
        self.assertIn(code, {item.code for item in caught.exception.diagnostics})

    def test_completion_requires_explicit_identity_decision_history_and_exact_revision(self):
        initial = self.opened()
        self.rejected("E_DISCOVERY_HISTORY", lambda: self.complete())
        self.update([record("user_statement", "Users need due dates on tasks.")])
        self.rejected("E_UPDATE_INPUT", lambda: sdlc.lifecycle_change(self.project, "REQ-0001", self.opened()["revision"], "bad", "", "Yes", "complete"))
        self.rejected("E_UPDATE_INPUT", lambda: sdlc.lifecycle_change(self.project, "REQ-0001", self.opened()["revision"], "bad-action", "David", "Yes", "approve"))
        self.rejected("E_REVISION_CONFLICT", lambda: self.complete(revision=initial["revision"]))
        base = self.opened()["revision"]
        output = self.complete(revision=base)
        self.assertEqual(output["epic"]["metadata"]["status"], "ready_for_refinement")
        self.assertEqual(output["epic"]["metadata"]["lifecycle"][0]["actor"], "Requester David")
        self.assertFalse(output["replayed"])
        self.assertTrue(self.complete(revision=base)["replayed"])
        self.rejected("E_IDEMPOTENCY", lambda: sdlc.lifecycle_change(self.project, "REQ-0001", base, "complete-1", "Other", "Yes", "complete"))
        self.rejected("E_STATUS", lambda: self.complete(op="complete-again"))
        self.assertFalse((self.directory / "business.md").exists())

    def test_completion_reports_open_unknown_and_proposed_without_treating_them_as_approved(self):
        self.update([record("user_statement", "Users need due dates on tasks."), record("question", "Allow past dates?"), record("ai_assumption", "Dates are optional.")])
        output = self.complete()
        state = output["unresolved"]
        self.assertEqual(state["questions"][0]["status"], "open")
        self.assertEqual(state["assumptions"][0]["status"], "proposed")
        self.assertNotIn("approval", output["epic"]["metadata"])
        self.rejected("E_STATUS", lambda: self.update([record("user_statement", "More")]))

    def test_initial_generation_cli_and_read_only_review(self):
        completed = self.prepare()
        content = self.draft(completed["source_revision"])
        self.docfile.write_text(content)
        output = self.cli("business-generate", "REQ-0001", "--expected-source-revision", completed["source_revision"], "--operation-id", "generate-1", "--editor", "PO", "--reason", "Initial draft", "--document-file", str(self.docfile))
        self.assertTrue(output["ok"])
        business_view = output["epic"]["business"]
        self.assertEqual(business_view["revision"], hashlib.sha256(content.encode()).hexdigest())
        self.assertEqual(output["epic"]["metadata"]["status"], "business_refinement")
        self.assertEqual((self.directory / "business.md").read_text(), content)
        before = (self.directory / "business.md").read_bytes()
        review = self.cli("business-review", "REQ-0001")
        self.assertTrue(review["current"])
        self.assertEqual(review["source_records"]["confirmed"], ["D-0001"])
        self.assertEqual((self.directory / "business.md").read_bytes(), before)

    def test_provenance_and_coverage_keep_unresolved_and_ai_assumptions_separate(self):
        completed = self.prepare([record("question", "Allow past dates?"), record("ai_assumption", "Dates are optional.")])
        source = completed["source_revision"]
        good = self.draft(source, unresolved="- **U-001** [D-0002] Past dates need a decision.", proposals="- **P-001** [D-0003] Dates might be optional.")
        self.rejected("E_BUSINESS_PROVENANCE", lambda: self.write(self.draft(source, confirmed="- **B-001** [D-0003] Dates are optional.", unresolved="- **U-001** [D-0002] Decide past dates.", proposals="- **P-001** [D-0003] Proposed optionality.")))
        self.rejected("E_BUSINESS_COVERAGE", lambda: self.write(self.draft(source, unresolved="- **U-001** [D-0002] Decide past dates.", proposals="")))
        self.rejected("E_BUSINESS_PROVENANCE", lambda: self.write(good.replace("[D-0001]", "[D-9999]")))
        self.rejected("E_BUSINESS_DOCUMENT", lambda: self.write(good.replace("Source revision: " + source, "Source revision: " + "0" * 64)))
        self.assertTrue(self.write(good)["ok"])

    def test_confirmed_assumption_and_correction_are_eligible_only_after_sourced_decisions(self):
        self.update([record("user_statement", "Users need dates."), record("ai_assumption", "Dates are optional.")])
        self.update([{"kind": "human_decision", "topic": "scope", "text": "Yes, optional.", "action": "confirm", "target": "D-0002", "source": {"actor": "user", "quote": "Yes, optional."}}])
        completed = self.complete()["epic"]
        doc = self.draft(completed["source_revision"], confirmed="- **B-001** [D-0001] Users need dates.\n- **B-002** [D-0002] Dates are optional.")
        self.assertTrue(self.write(doc)["ok"])

    def test_human_confirmation_can_be_primary_with_or_without_other_valid_sources(self):
        self.update([record("user_statement", "Users need dates."), record("ai_assumption", "Dates are optional.")])
        self.update([{**record("human_decision", "Yes, dates are optional."), "action": "confirm", "target": "D-0002"}])
        completed = self.complete()["epic"]
        source = completed["source_revision"]
        original = self.draft(source, confirmed="- **B-001** [D-0001] Users need dates.\n- **B-002** [D-0002] Dates are optional.")
        previous = self.write(original)["epic"]["business"]["revision"]
        # Existing assumption-only documents remain valid; confirmation-only coverage
        # follows its target, and multiple references retain their declared order.
        for refs in ("D-0003", "D-0003, D-0002", "D-0003, D-0002, D-0001"):
            with self.subTest(refs=refs):
                document = self.draft(source, confirmed=f"- **B-001** [D-0001] Users need dates.\n- **B-002** [{refs}] Dates are optional.")
                output = self.write(document, mode="revise", previous=previous)
                previous = output["epic"]["business"]["revision"]
                self.assertIn(f"[{refs}]", output["epic"]["business"]["content"])
                self.assertEqual(output["epic"]["source_revision"], source)
                review = self.cli("business-review", "REQ-0001")
                self.assertTrue(review["current"])
                self.assertEqual(review["source_records"]["confirmed"], ["D-0001", "D-0002", "D-0003"])

    def test_unconfirmed_assumption_cannot_support_confirmed_business_requirement(self):
        completed = self.prepare([record("ai_assumption", "Dates are optional.")])
        document = self.draft(completed["source_revision"], confirmed="- **B-001** [D-0001] Users need dates.\n- **B-002** [D-0002] Dates are optional.", proposals="- **P-001** [D-0002] Proposed optionality.")
        self.rejected("E_BUSINESS_PROVENANCE", lambda: self.write(document))
        self.assertFalse((self.directory / "business.md").exists())

    def test_rejection_invalidates_assumption_and_its_former_human_confirmation(self):
        self.update([record("user_statement", "Users need dates."), record("ai_assumption", "Dates are optional.")])
        self.update([{**record("human_decision", "Yes, optional."), "action": "confirm", "target": "D-0002"}])
        self.update([{**record("human_decision", "Reject the earlier optionality assumption."), "action": "reject", "target": "D-0002"}])
        source = self.complete()["epic"]["source_revision"]
        for refs in ("D-0002", "D-0003", "D-0003, D-0002"):
            with self.subTest(refs=refs):
                document = self.draft(source, confirmed=f"- **B-001** [D-0001] Users need dates.\n- **B-002** [{refs}] Dates are optional.")
                self.rejected("E_BUSINESS_PROVENANCE", lambda: self.write(document))
        valid = self.write(self.draft(source))["epic"]
        self.assertEqual(self.cli("business-review", "REQ-0001")["source_records"]["confirmed"], ["D-0001"])
        self.assertFalse(valid["business"]["needs_reconciliation"])

    def test_only_latest_correction_can_support_confirmed_business_requirement(self):
        self.update([record("user_statement", "Dates are optional.")])
        self.update([{**record("human_decision", "Dates are required."), "action": "correct", "target": "D-0001"}])
        self.update([{**record("human_decision", "Dates are optional for draft tasks."), "action": "correct", "target": "D-0002"}])
        source = self.complete()["epic"]["source_revision"]
        for refs in ("D-0001", "D-0002", "D-0003, D-0001"):
            with self.subTest(refs=refs):
                document = self.draft(source, confirmed=f"- **B-001** [{refs}] Dates are optional for draft tasks.")
                self.rejected("E_BUSINESS_PROVENANCE", lambda: self.write(document))
        self.assertTrue(self.write(self.draft(source, confirmed="- **B-001** [D-0003] Dates are optional for draft tasks."))["ok"])

    def test_invalid_and_nonexistent_discovery_references_remain_rejected(self):
        source = self.prepare()["source_revision"]
        for refs, code in (("D-9999", "E_BUSINESS_PROVENANCE"), ("D-invalid", "E_BUSINESS_REFERENCE"), ("D-0001, D-0001", "E_BUSINESS_REFERENCE")):
            with self.subTest(refs=refs):
                document = self.draft(source, confirmed=f"- **B-001** [{refs}] Users need dates.")
                self.rejected(code, lambda: self.write(document))
        self.assertFalse((self.directory / "business.md").exists())

    def test_revision_history_contains_exact_recoverable_bytes_and_attribution(self):
        completed = self.prepare()
        first = self.draft(completed["source_revision"])
        one = self.write(first, op="first")["epic"]["business"]["revision"]
        second = first.replace("Users need due dates on tasks.", "Users need visible due dates on tasks.")
        two = self.write(second, mode="revise", op="second", previous=one, editor="David", reason="Clarify display")["epic"]["business"]["revision"]
        ledger = yaml.safe_load((self.directory / "business-history.yaml").read_text())
        self.assertEqual([item["digest"] for item in ledger["revisions"]], [one, two])
        self.assertEqual(ledger["revisions"][1]["previous"], one)
        self.assertEqual(ledger["revisions"][1]["editor"], "David")
        self.assertEqual(ledger["revisions"][1]["reason"], "Clarify display")
        self.assertTrue(ledger["revisions"][1]["timestamp"].endswith("Z"))
        self.assertEqual(business.decode_revision(ledger["revisions"][0]), first.encode())
        self.assertEqual(business.decode_revision(ledger["revisions"][1]), second.encode())

    def test_business_idempotency_and_stale_revision_conflicts(self):
        completed = self.prepare()
        source = completed["source_revision"]
        first = self.draft(source)
        one = self.write(first, op="same", source=source)["epic"]["business"]["revision"]
        self.assertTrue(self.write(first, op="same", source=source)["replayed"])
        self.rejected("E_IDEMPOTENCY", lambda: self.write(first + "\n", op="same", source=source))
        next_doc = first.replace("due dates", "visible due dates")
        self.rejected("E_REVISION_CONFLICT", lambda: self.write(next_doc, mode="revise", previous="0" * 64))
        self.rejected("E_REVISION_CONFLICT", lambda: self.write(next_doc, mode="revise", previous=one, source="0" * 64))
        self.assertTrue(self.write(next_doc, mode="revise", previous=one)["ok"])
        self.assertTrue(self.write(first, op="same", source=source)["replayed"])

    def test_mutated_document_or_history_is_rejected_before_review_or_write(self):
        completed = self.prepare()
        content = self.draft(completed["source_revision"])
        revision = self.write(content)["epic"]["business"]["revision"]
        path = self.directory / "business.md"
        path.write_text(content + "\n")
        review = self.cli("business-review", "REQ-0001")
        self.assertIn("E_BUSINESS_MISMATCH", {item["code"] for item in review["diagnostics"]})
        self.rejected("E_BUSINESS_MISMATCH", lambda: self.write(content, mode="revise", previous=revision, source=completed["source_revision"]))
        path.write_text(content)
        ledger_path = self.directory / "business-history.yaml"
        ledger = yaml.safe_load(ledger_path.read_text())
        ledger["revisions"][0]["reason"] = ""
        ledger_path.write_text(yaml.safe_dump(ledger))
        review = self.cli("business-review", "REQ-0001")
        self.assertIn("E_BUSINESS_HISTORY", {item["code"] for item in review["diagnostics"]})

    def test_two_concurrent_writes_cannot_both_replace_same_revision(self):
        completed = self.prepare()
        first = self.draft(completed["source_revision"])
        one = self.write(first)["epic"]["business"]["revision"]
        def contender(number):
            input_path = self.project / f"input-{number}.md"
            input_path.write_text(first.replace("due dates", f"due dates {number}"))
            try:
                return sdlc.business_write(self.project, "REQ-0001", completed["source_revision"], one, f"parallel-{number}", "PO", "Refine", input_path, "revise")
            except sdlc.Rejected as exc:
                return {"ok": False, "code": exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(contender, (1, 2)))
        self.assertEqual(sum(item["ok"] for item in results), 1)
        self.assertIn(next(item["code"] for item in results if not item["ok"]), ("E_PROJECT_BUSY", "E_REVISION_CONFLICT"))

    def test_interrupted_publication_is_not_presented_and_can_be_rolled_forward(self):
        completed = self.prepare()
        content = self.draft(completed["source_revision"])
        self.docfile.write_text(content)
        real_replace = business.os.replace
        count = 0
        def interrupt(*args):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("injected interruption")
            return real_replace(*args)
        with patch.object(business.os, "replace", side_effect=interrupt):
            self.rejected("E_WRITE_UNCERTAIN", lambda: sdlc.business_write(self.project, "REQ-0001", completed["source_revision"], None, "interrupted", "PO", "Draft", self.docfile, "generate"))
        self.assertTrue((self.directory / ".business-transaction.json").exists())
        self.assertFalse(self.cli("business-review", "REQ-0001")["ok"])
        self.assertTrue(self.cli("business-recover", "REQ-0001")["ok"])
        self.assertTrue(self.cli("business-review", "REQ-0001")["current"])
        self.assertEqual((self.directory / "business.md").read_text(), content)
        self.assertFalse((self.directory / ".business-transaction.json").exists())

    def test_reopen_retains_history_and_requires_explicit_source_reconciliation(self):
        completed = self.prepare()
        first = self.draft(completed["source_revision"])
        first_revision = self.write(first)["epic"]["business"]["revision"]
        reopened = sdlc.lifecycle_change(self.project, "REQ-0001", self.opened()["revision"], "reopen-1", "Requester David", "Need a new scope decision.", "reopen")
        self.assertEqual(reopened["epic"]["metadata"]["status"], "discovery")
        self.assertTrue(reopened["epic"]["business"]["needs_reconciliation"])
        review = self.cli("business-review", "REQ-0001")
        self.assertFalse(review["current"])
        self.assertEqual(review["epic"]["business"]["revision"], first_revision)
        self.rejected("E_STATUS", lambda: self.write(first, mode="revise", previous=first_revision))
        self.update([record("user_statement", "Reminders are out of scope.")])
        completed_again = self.complete(op="complete-2")["epic"]
        self.assertFalse(self.cli("business-review", "REQ-0001")["current"])
        reconciled = self.draft(completed_again["source_revision"], confirmed="- **B-001** [D-0001] Users need due dates on tasks.\n- **B-002** [D-0002] Reminders are out of scope.")
        self.rejected("E_REVISION_CONFLICT", lambda: self.write(reconciled, previous=first_revision, source=completed["source_revision"]))
        result = self.write(reconciled, previous=first_revision, source=completed_again["source_revision"])
        self.assertFalse(result["epic"]["business"]["needs_reconciliation"])
        self.assertEqual(len(result["epic"]["business"]["history"]), 2)
        self.assertEqual(result["epic"]["business"]["history"][1]["previous"], first_revision)

    def test_old_lifecycle_compatibility_and_no_analysis_operations(self):
        self.assertTrue(self.cli("validate")["ok"])
        self.assertEqual(self.opened()["metadata"]["schema_version"], "0.1")
        help_text = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), "--help"], capture_output=True, text=True).stdout
        self.assertIn("business-approve", help_text)
        self.assertNotIn("functional-analysis", help_text)
        self.assertIn("business-advance", help_text)


if __name__ == "__main__":
    unittest.main()
