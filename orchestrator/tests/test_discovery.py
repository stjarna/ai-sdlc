"""Behavioral tests against isolated local projects; no application stack needed."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sdlc


SCRIPT = Path(sdlc.__file__).resolve()


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    }


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()

    def cli(self, *args, env=None):
        if args and args[0] == "new":
            args = (*args, "--requester", "Fixture Requester")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(self.project), *args],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(completed.stderr, "", completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0 if output["ok"] else 1)
        return output

    def create(self, title="Example", idea="People cannot see their request status."):
        return sdlc.new_epic(self.project, title, idea, requester="Fixture Requester")

    def metadata_path(self, output):
        return Path(output["epic"]["directory"]) / "metadata.yaml"

    def change_metadata(self, output, **changes):
        path = self.metadata_path(output)
        data = yaml.safe_load(path.read_text())
        data.update(changes)
        path.write_text(yaml.safe_dump(data))

    def codes(self, output):
        return {item["code"] for item in output["diagnostics"]}

    def test_successful_creation_keeps_metadata_and_business_content_separate(self):
        description = "Potřebujeme lepší přehled o požadavcích."
        output = self.cli("new", "--title", "Přehled požadavků", "--idea", description)
        self.assertTrue(output["ok"])
        directory = Path(output["epic"]["directory"])
        self.assertEqual(directory.name, "REQ-0001-prehled-pozadavku")
        self.assertEqual({path.name for path in directory.iterdir()}, {"metadata.yaml", "idea.md"})
        data = yaml.safe_load((directory / "metadata.yaml").read_text())
        self.assertEqual(data.pop("ownership")["owner"], "Fixture Requester")
        self.assertEqual(data, {
            "schema_version": "0.1", "id": "REQ-0001", "title": "Přehled požadavků",
            "status": "discovery", "artifacts": {"idea": "idea.md"},
        })
        self.assertIn(description, (directory / "idea.md").read_text())
        self.assertNotIn(description, (directory / "metadata.yaml").read_text())
        self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_sequential_allocation_includes_cancelled_records_and_does_not_fill_gaps(self):
        first = self.create()
        second = self.create()
        self.assertEqual(second["epic"]["metadata"]["id"], "REQ-0002")
        self.change_metadata(second, id="REQ-0008", status="cancelled")
        third = self.create()
        self.assertEqual(third["epic"]["metadata"]["id"], "REQ-0009")
        self.assertEqual(yaml.safe_load(self.metadata_path(first).read_text())["id"], "REQ-0001")

    def test_open_uses_metadata_id_after_arbitrary_directory_rename(self):
        created = self.create()
        directory = Path(created["epic"]["directory"])
        renamed = directory.with_name("renamed-business-idea")
        directory.rename(renamed)
        before = snapshot(self.project)
        output = self.cli("open", "REQ-0001")
        self.assertTrue(output["ok"])
        self.assertEqual(output["epic"]["directory"], str(renamed))
        self.assertEqual(output["epic"]["metadata"]["id"], "REQ-0001")
        self.assertIn("People cannot see", output["epic"]["idea"])
        self.assertEqual(snapshot(self.project), before)

    def test_valid_metadata_and_complete_content_have_no_diagnostics(self):
        created = self.create()
        idea_path = Path(created["epic"]["directory"]) / "idea.md"
        idea_path.write_text("\n\n".join(f"## {name}\n\nKnown answer." for name in sdlc.SECTIONS))
        before = snapshot(self.project)
        output = self.cli("validate", "REQ-0001")
        self.assertTrue(output["ok"])
        self.assertEqual(output["diagnostics"], [])
        self.assertEqual(output["validated_ids"], ["REQ-0001"])
        self.assertEqual(snapshot(self.project), before)

    def test_incomplete_business_content_warns_without_blocking_new_open_validate(self):
        created = self.cli("new", "--title", "Unexplored idea")
        for output in (created, self.cli("open", "REQ-0001"), self.cli("validate")):
            with self.subTest(operation=output["operation"]):
                self.assertTrue(output["ok"])
                self.assertEqual(len(output["diagnostics"]), 7)
                self.assertEqual(self.codes(output), {"W_DISCOVERY_INCOMPLETE"})
                self.assertTrue(all(item["severity"] == "warning" for item in output["diagnostics"]))
        self.assertEqual(created["epic"]["metadata"]["status"], "discovery")

    def test_malformed_yaml_blocks_validation_open_and_new_without_modification(self):
        created = self.create()
        self.metadata_path(created).write_text("id: [unterminated\n")
        before = snapshot(self.project)
        for args in (("validate",), ("open", "REQ-0001"), ("new", "--title", "Another")):
            output = self.cli(*args)
            self.assertFalse(output["ok"])
            self.assertIn("E_YAML", self.codes(output))
            issue = next(item for item in output["diagnostics"] if item["code"] == "E_YAML")
            self.assertEqual(issue["file"], str(self.metadata_path(created)))
            self.assertIsInstance(issue["line"], int)
        self.assertEqual(snapshot(self.project), before)

    def test_duplicate_yaml_keys_are_rejected_at_root_and_nested_levels(self):
        created = self.create()
        path = self.metadata_path(created)
        original = path.read_text()
        for text in (original + "id: REQ-0002\n", original.replace("  idea: idea.md", "  idea: idea.md\n  idea: other.md")):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertIn("E_YAML", self.codes(self.cli("validate")))

    def assert_yaml_rejected_by_all_operations(self, created, content, line):
        path = self.metadata_path(created)
        path.write_text(content)
        before = snapshot(self.project)
        for args in (("validate", "REQ-0001"), ("open", "REQ-0001"), ("new", "--title", "Another")):
            with self.subTest(args=args):
                output = self.cli(*args)
                self.assertFalse(output["ok"])
                issue = next(item for item in output["diagnostics"] if item["code"] == "E_YAML")
                self.assertEqual(issue["file"], str(path))
                self.assertEqual(issue["line"], line)
                self.assertTrue(issue["message"])
                self.assertEqual(snapshot(self.project), before)
                self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_unexpected_yaml_mapping_nodes_return_structured_errors_for_all_operations(self):
        created = self.create()
        original = self.metadata_path(created).read_text()
        for content, line in (
            ("!!map [hello]\n", 1),
            ("!!map hello\n", 1),
            (original.replace("artifacts:\n  idea: idea.md", "artifacts: !!map [hello]"), 5),
            (original.replace("  idea: idea.md", "  idea: !!map hello"), 6),
        ):
            with self.subTest(content=content):
                self.assert_yaml_rejected_by_all_operations(created, content, line)

    def test_invalid_explicit_yaml_scalar_values_return_structured_errors(self):
        created = self.create()
        original = self.metadata_path(created).read_text()
        for tagged_value in (
            "!!bool maybe", "!!int hello", "!!int ''", "!!float hello",
            "!!timestamp hello", "!!timestamp 2026-99-99",
        ):
            with self.subTest(tagged_value=tagged_value):
                content = original.replace("title: Example", "title: " + tagged_value)
                self.assert_yaml_rejected_by_all_operations(created, content, 3)

    def test_yaml_aliases_nonstring_keys_and_unsafe_tags_are_rejected(self):
        created = self.create()
        path = self.metadata_path(created)
        for content in (
            "id: &identity [*identity]\n",
            "false: value\n",
            "!!python/object/apply:os.system ['touch intruder']\n",
            "defaults: &base {id: REQ-0001}\n<<: *base\n",
        ):
            with self.subTest(content=content):
                path.write_text(content)
                self.assertIn("E_YAML", self.codes(self.cli("validate")))
        self.assertFalse((self.project / "intruder").exists())

    def test_duplicate_ids_are_rejected_even_when_directories_have_different_names(self):
        created = self.create()
        shutil.copytree(Path(created["epic"]["directory"]), self.project / "requirements" / "another-name")
        before = snapshot(self.project)
        for args in (("validate",), ("open", "REQ-0001"), ("new", "--title", "Another")):
            output = self.cli(*args)
            self.assertFalse(output["ok"])
            self.assertIn("E_DUPLICATE_ID", self.codes(output))
        self.assertEqual(snapshot(self.project), before)

    def test_invalid_metadata_values_and_unknown_fields_are_rejected(self):
        created = self.create()
        path = self.metadata_path(created)
        original = path.read_text()
        cases = (
            ({"title": " "}, "E_TITLE"), ({"title": ["Title"]}, "E_TITLE"),
            ({"title": "Line\nbreak"}, "E_TITLE"), ({"status": "ready_for_refinement"}, "E_STATUS"),
            ({"unexpected": True}, "E_METADATA"), ({"artifacts": []}, "E_ARTIFACTS"),
            ({"artifacts": {"idea": "idea.md", "extra": "extra.md"}}, "E_ARTIFACTS"),
        )
        for changes, code in cases:
            with self.subTest(changes=changes):
                path.write_text(original)
                self.change_metadata(created, **changes)
                self.assertIn(code, self.codes(self.cli("validate")))

    def test_missing_fields_and_nonmapping_metadata_are_rejected(self):
        created = self.create()
        path = self.metadata_path(created)
        data = yaml.safe_load(path.read_text())
        for value in (None, [], "text", {key: val for key, val in data.items() if key != "title"}):
            with self.subTest(value=value):
                path.write_text(yaml.safe_dump(value))
                self.assertIn("E_METADATA", self.codes(self.cli("validate")))

    def test_unsupported_schema_versions_are_rejected_without_migration(self):
        created = self.create()
        for version in ("99.0", 0.1, None):
            with self.subTest(version=version):
                self.change_metadata(created, schema_version=version)
                before = snapshot(self.project)
                self.assertIn("E_SCHEMA_VERSION", self.codes(self.cli("validate")))
                self.assertIn("E_SCHEMA_VERSION", self.codes(self.cli("new", "--title", "Another")))
                self.assertEqual(snapshot(self.project), before)

    def test_invalid_record_and_lookup_ids_are_rejected(self):
        created = self.create()
        for epic_id in ("REQ-0000", "REQ-1", "REQ-00001", "REQ-0001/S01", "req-0001", "REQ-１２３４", "../REQ-0001"):
            with self.subTest(epic_id=epic_id):
                self.change_metadata(created, id=epic_id)
                self.assertIn("E_EPIC_ID", self.codes(self.cli("validate")))
                self.assertIn("E_EPIC_ID", self.codes(self.cli("open", epic_id)))

    def test_missing_epic_and_missing_artifact_have_distinct_errors(self):
        self.assertIn("E_EPIC_NOT_FOUND", self.codes(self.cli("open", "REQ-0001")))
        created = self.create()
        (Path(created["epic"]["directory"]) / "idea.md").unlink()
        self.assertIn("E_ARTIFACT_FILE", self.codes(self.cli("validate")))

    def test_nested_artifact_within_epic_is_readable_and_non_utf8_is_reported(self):
        created = self.create()
        directory = Path(created["epic"]["directory"])
        (directory / "notes").mkdir()
        (directory / "idea.md").rename(directory / "notes" / "idea.md")
        self.change_metadata(created, artifacts={"idea": "notes/idea.md"})
        self.assertTrue(self.cli("open", "REQ-0001")["ok"])
        (directory / "notes" / "idea.md").write_bytes(b"\xff\xfe")
        output = self.cli("validate")
        issue = next(item for item in output["diagnostics"] if item["code"] == "E_READ")
        self.assertEqual(issue["file"], str(directory / "notes" / "idea.md"))

    def test_non_utf8_idea_reports_actual_artifact_for_all_operations(self):
        created = self.create()
        idea_path = Path(created["epic"]["directory"]) / "idea.md"
        idea_path.write_bytes(b"\xff\xfe")
        before = snapshot(self.project)
        for args in (("validate", "REQ-0001"), ("open", "REQ-0001"), ("new", "--title", "Another")):
            with self.subTest(args=args):
                output = self.cli(*args)
                self.assertFalse(output["ok"])
                issue = next(item for item in output["diagnostics"] if item["code"] == "E_READ")
                self.assertEqual(issue["file"], str(idea_path))
                self.assertEqual(snapshot(self.project), before)
                self.assertFalse((self.project / ".sdlc-discovery.lock").exists())

    def test_invalid_metadata_elsewhere_blocks_open_and_new(self):
        self.create()
        second = self.create("Second")
        self.change_metadata(second, id="invalid")
        for args in (("open", "REQ-0001"), ("new", "--title", "Third")):
            output = self.cli(*args)
            self.assertFalse(output["ok"])
            self.assertIn("E_EPIC_ID", self.codes(output))

    def test_artifact_traversal_absolute_path_and_symlink_escape_are_rejected(self):
        created = self.create()
        directory = Path(created["epic"]["directory"])
        outside = self.project / "private.md"
        outside.write_text("Private material must not be returned.")
        (directory / "escape.md").symlink_to(outside)
        for reference in ("../../private.md", str(outside), "escape.md", "metadata.yaml"):
            with self.subTest(reference=reference):
                self.change_metadata(created, artifacts={"idea": reference})
                output = self.cli("validate")
                self.assertIn("E_ARTIFACT_PATH", self.codes(output))
                self.assertNotIn(outside.read_text(), json.dumps(output))

    def test_requirements_and_epic_symlinks_are_rejected(self):
        created = self.create()
        directory = Path(created["epic"]["directory"])
        (directory.parent / "alias").symlink_to(directory, target_is_directory=True)
        self.assertIn("E_EPIC_DIRECTORY", self.codes(self.cli("validate")))
        (directory.parent / "alias").unlink()
        moved = self.project / "moved"
        directory.parent.rename(moved)
        (self.project / "requirements").symlink_to(moved, target_is_directory=True)
        self.assertIn("E_REQUIREMENTS", self.codes(self.cli("new", "--title", "Another")))

    def test_preexisting_content_and_incomplete_directories_are_never_overwritten(self):
        directory = self.project / "requirements" / "REQ-0001-example"
        directory.mkdir(parents=True)
        (directory / "idea.md").write_text("Existing, unfinished user work.")
        before = snapshot(self.project)
        output = self.cli("new", "--title", "Example")
        self.assertFalse(output["ok"])
        self.assertIn("E_METADATA_FILE", self.codes(output))
        self.assertEqual(snapshot(self.project), before)

    def test_creation_failure_cleans_up_new_files_directory_and_lock(self):
        original_write = sdlc.write_new

        def fail_on_idea(path, content):
            if path.name == "idea.md":
                path.write_text("partial write")
                raise OSError("Injected disk failure")
            original_write(path, content)

        for existing_requirements in (False, True):
            with self.subTest(existing_requirements=existing_requirements):
                if existing_requirements:
                    (self.project / "requirements").mkdir()
                with patch.object(sdlc, "write_new", side_effect=fail_on_idea):
                    with self.assertRaises(OSError):
                        self.create()
                self.assertFalse((self.project / ".sdlc-discovery.lock").exists())
                self.assertEqual(list((self.project / "requirements").iterdir()) if existing_requirements else list(self.project.iterdir()), [])
                if existing_requirements:
                    (self.project / "requirements").rmdir()

    def test_failed_second_creation_preserves_existing_epic(self):
        first = self.create()
        before = snapshot(self.project)
        with patch.object(sdlc, "write_new", side_effect=OSError("Injected failure")):
            with self.assertRaises(OSError):
                self.create("Second")
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(self.cli("open", "REQ-0001")["epic"]["metadata"], first["epic"]["metadata"])

    def test_local_creation_lock_fails_closed_without_removing_another_writers_lock(self):
        lock = self.project / ".sdlc-discovery.lock"
        lock.mkdir()
        output = self.cli("new", "--title", "Example")
        self.assertIn("E_PROJECT_BUSY", self.codes(output))
        self.assertTrue(lock.is_dir())
        self.assertFalse((self.project / "requirements").exists())

    def test_id_exhaustion_does_not_wrap_or_change_existing_records(self):
        created = self.create()
        self.change_metadata(created, id="REQ-9999")
        before = snapshot(self.project)
        self.assertIn("E_ID_EXHAUSTED", self.codes(self.cli("new", "--title", "Another")))
        self.assertEqual(snapshot(self.project), before)

    def test_title_cannot_control_directory_path_or_execute_shell_text(self):
        output = self.cli("new", "--title", "../../ $(touch intruder) `whoami`", "--idea", "$(touch other)")
        directory = Path(output["epic"]["directory"])
        self.assertEqual(directory.parent, self.project / "requirements")
        self.assertIn("$(touch other)", output["epic"]["idea"])
        self.assertFalse((self.project / "intruder").exists())
        self.assertFalse((self.project / "other").exists())

    def test_no_automatic_git_operations_or_git_data_changes(self):
        git = shutil.which("git")
        self.assertIsNotNone(git)
        subprocess.run([git, "init", "-q", str(self.project)], check=True, capture_output=True)
        before = snapshot(self.project / ".git")
        with tempfile.TemporaryDirectory() as trap_dir:
            trap = Path(trap_dir) / "git"
            marker = Path(trap_dir) / "called"
            trap.write_text('#!/bin/sh\necho called >> "$SDLC_TEST_GIT_MARKER"\nexit 99\n')
            trap.chmod(0o755)
            env = dict(os.environ, PATH=trap_dir + os.pathsep + os.environ.get("PATH", ""), SDLC_TEST_GIT_MARKER=str(marker))
            for args in (("new", "--title", "Example"), ("open", "REQ-0001"), ("validate",)):
                self.assertTrue(self.cli(*args, env=env)["ok"])
            self.assertFalse(marker.exists(), "An operation attempted to invoke Git")
        self.assertEqual(snapshot(self.project / ".git"), before)
        self.assertEqual({path.name for path in (self.project / "requirements" / "REQ-0001-example").iterdir()}, {"metadata.yaml", "idea.md"})


if __name__ == "__main__":
    unittest.main()
