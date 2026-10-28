"""Naming is a read-only projection; all decisions below are fictional fixtures."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import artifact_names
import business_refinement as business
import engineering
import sdlc
import test_engineering as legacy
import test_qa_track as fork


def snapshot(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


class ArtifactNamesTests(unittest.TestCase):
    def fixture(self, cls):
        f = cls(next(name for name in dir(cls) if name.startswith('test_')))
        self.addCleanup(f.doCleanups)
        f.setUp()
        return f

    def assert_link(self, doc, expected):
        self.assertEqual(doc['name'], expected)
        self.assertTrue(Path(doc['path']).is_absolute())
        self.assertTrue(Path(doc['path']).is_file())
        self.assertEqual(unquote(doc['link'].split('](<', 1)[1][:-2]), doc['path'])
        self.assertTrue(doc['link'].startswith('[' + expected + ']'))

    def test_types_have_distinct_logical_names_in_a_shared_directory(self):
        with tempfile.TemporaryDirectory() as root:
            descriptors = [artifact_names.document(stage, kind, Path(root)/artifact_names.NAMES[stage, kind][0])
                           for stage, kind in artifact_names.NAMES]
            self.assertEqual(len({d['name'] for d in descriptors}), len(descriptors))
            self.assertEqual(len({str(Path(d['path']).parent) for d in descriptors}), 1)
            self.assertEqual(list(Path(root).iterdir()), [])  # no aliases or copies

    def test_link_escapes_path_characters_without_changing_the_target(self):
        path = Path('/tmp/project [draft] (review) #1% > č/technical-design.md')
        doc = artifact_names.document('engineering', 'design', path)
        self.assertEqual(unquote(doc['link'].split('](<')[1][:-2]), str(path.resolve()))
        self.assertNotIn(' ', doc['link'])
        self.assertIn('%23', doc['link'])
        self.assertIn('%3E', doc['link'])

    def test_unknown_type_does_not_fall_back_to_generic_content(self):
        with self.assertRaises(KeyError):
            artifact_names.document('engineering', 'unknown', '/tmp/content.md')

    def test_discovery_and_legacy_missing_history_are_discoverable_without_writes(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory/'original.md').write_text('Original idea')
            epic = sdlc.Epic(directory, metadata={'artifacts': {'idea': 'original.md'}}, idea='Original idea')
            before = snapshot(directory)
            docs = epic.payload()['documents']
            self.assertEqual(set(docs), {'idea'})
            self.assert_link(docs['idea'], 'original.md')
            self.assertEqual(Path(docs['idea']['path']).name, 'original.md')
            self.assertEqual(before, snapshot(directory))

    def test_legacy_all_engineering_types_and_final_report_preserve_exact_baselines(self):
        f = self.fixture(legacy.EngineeringTests)
        f.security()
        f.run_update('write', 'security', f.document('security'))
        f.run_update('advance', 'security')
        f.run_update('finalize', 'final')
        before, revision = snapshot(f.directory), f.review()['revision']
        view = f.review()
        for kind, name in [('design', 'technical-design.md'), ('plan', 'implementation-plan.md'),
                           ('implementation', 'code-review.md'), ('security', 'security-review.md')]:
            draft = view['drafts'][kind]
            self.assert_link(draft['document'], name)
            self.assertEqual(Path(draft['document']['path']).parent.name, draft['baseline_id'])
            obj, files = engineering.load_artifact(f.directory, draft['baseline_id'])
            self.assertNotIn('document', obj)
            self.assertNotIn('document', obj['payload'])
            self.assertEqual({p.name for p in Path(draft['document']['path']).parent.iterdir()}, {'metadata.yaml', 'artifact.json', name, 'manifest.json'})
            self.assertEqual(Path(draft['document']['path']).read_text(), draft['payload']['content'])
        self.assert_link(view['final_report']['document'], 'verification-report.md')
        self.assertEqual(artifact_names.documents(view)['final'], view['final_report']['document'])
        self.assertEqual(f.review()['revision'], revision)
        self.assertEqual(before, snapshot(f.directory))
        self.assertTrue(sdlc.inspect_epics(f.project, 'validate', 'REQ-0001')['ok'])

    def test_qa_status_details_and_cli_review_expose_exact_named_links(self):
        f = self.fixture(fork.QATrackTests)
        f.design_engineering()
        f.automation()
        before = snapshot(f.directory)
        qa = f.view()
        for kind, name in [('strategy', 'test-strategy.md'), ('scenarios', 'test-scenarios.md'), ('automation', 'test-automation.md')]:
            self.assert_link(qa['drafts'][kind]['document'], name)
        for command in ['status', 'details']:
            context = sdlc.command_context(f.project, command, 'REQ-0001')
            docs = context['review']['documents']
            self.assertEqual(docs['qa'], artifact_names.documents(qa))
            self.assert_link(docs['engineering']['design'], 'technical-design.md')
        result = subprocess.run([sys.executable, str(Path(sdlc.__file__)), '--project', str(f.project),
                                 'command-context', 'review', '--request', 'REQ-0001', '--track', 'qa'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        import json
        self.assertEqual(json.loads(result.stdout)['review']['drafts']['scenarios']['document'], qa['drafts']['scenarios']['document'])
        self.assertEqual(before, snapshot(f.directory))

    def test_business_and_analysis_links_available_through_open_payload(self):
        f = self.fixture(legacy.EngineeringTests)
        docs = f.epic().payload()['documents']
        for kind, name in [('business', 'business.md'), ('analysis', 'specification.md'), ('history', 'discovery.yaml')]:
            self.assert_link(docs[kind], name)

    def test_directory_rename_relocates_links_without_rewriting_baseline(self):
        f = self.fixture(legacy.EngineeringTests)
        f.run_update('write', 'design', f.document('design'))
        before = snapshot(f.directory)
        baseline = f.review()['drafts']['design']['baseline_id']
        renamed = f.directory.with_name('renamed epic [review]')
        f.directory.rename(renamed)
        f.directory = renamed
        view = f.review()['drafts']['design']
        self.assertEqual(view['baseline_id'], baseline)
        self.assert_link(view['document'], 'technical-design.md')
        self.assertTrue(Path(view['document']['path']).is_relative_to(renamed.resolve()))
        self.assertEqual(before, snapshot(renamed))

    def test_naming_does_not_mask_legacy_baseline_corruption(self):
        f = self.fixture(legacy.EngineeringTests)
        f.run_update('write', 'design', f.document('design'))
        path = Path(f.review()['drafts']['design']['document']['path'])
        path.write_text('corrupted')
        with self.assertRaises(sdlc.Rejected) as caught:
            f.review()
        self.assertIn('E_BASELINE_INTEGRITY', {d.code for d in caught.exception.diagnostics})
