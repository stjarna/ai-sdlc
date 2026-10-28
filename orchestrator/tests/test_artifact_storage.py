"""Real filesystem/publication tests with fictional approval actors and decisions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import artifact_names
import approval_common as common
import business_refinement as business
import engineering
import sdlc
import test_engineering as legacy
import test_qa_track as fork


def hashes(path):
    return {str(f.relative_to(path)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in path.rglob('*') if f.is_file()}


def old_snapshot(stage, kind, action, request_id, metadata, stored, content):
    """Exact pre-format-0.2 serializer, deliberately generating historical fixtures."""
    files = {'metadata.yaml': metadata, 'artifact.json': common.canonical_manifest(stored), 'content.md': content}
    return {'schema_version': '0.1', 'request_id': request_id,
            'files': {n: business.digest(v) for n, v in files.items()}}, files


class ArtifactStorageTests(unittest.TestCase):
    def fixture(self, cls=legacy.EngineeringTests):
        f = cls(next(n for n in dir(cls) if n.startswith('test_')))
        self.addCleanup(f.doCleanups); f.setUp()
        return f

    def assert_bundle(self, directory, root, event):
        path = directory/root/event['baseline_id']
        manifest = json.loads((path/'manifest.json').read_text())
        stage = 'qa' if root == 'qa-baselines' else 'engineering'
        name = artifact_names.filename(stage, event['kind'], event['action'])
        self.assertEqual(manifest['schema_version'], '0.2')
        self.assertEqual(manifest['document'], name)
        self.assertEqual({p.name for p in path.iterdir()}, {'metadata.yaml', 'artifact.json', name, 'manifest.json'})
        self.assertEqual(business.digest((path/'manifest.json').read_bytes()), event['baseline_id'])
        obj, _ = engineering.load_artifact(directory, event['baseline_id'], root)
        self.assertEqual((path/name).read_text(), obj['payload']['content'])
        return path

    def test_new_engineering_documents_approvals_events_and_final_use_physical_names(self):
        f = self.fixture(); f.security()
        f.run_update('write', 'security', f.document('security'))
        f.run_update('advance', 'security'); f.run_update('finalize', 'final')
        for event in f.epic().metadata['engineering_history']:
            self.assert_bundle(f.directory, 'engineering-baselines', event)
        review = f.review()
        self.assertEqual({v['document']['name'] for v in review['drafts'].values()},
                         {'technical-design.md', 'implementation-plan.md', 'code-review.md', 'security-review.md'})
        self.assertEqual(review['final_report']['document']['name'], 'verification-report.md')
        for draft in list(review['drafts'].values()) + [review['final_report']]:
            self.assertEqual(draft['document']['name'], Path(draft['document']['path']).name)
            self.assertIn('['+draft['document']['name']+']', draft['document']['link'])
        self.assertFalse(list(f.directory.rglob('content.md')))

    def test_qa_initial_revision_approval_and_advancement_use_canonical_files(self):
        f = self.fixture(fork.QATrackTests); f.design_engineering(); f.automation()
        original = f.view()['drafts']['scenarios']['baseline_id']
        changed = f.scenarios(); changed['content'] += '\nFictional revised wording.'
        f.update('write', 'scenarios', changed)
        self.assertNotEqual(f.view()['drafts']['scenarios']['baseline_id'], original)
        for event in __import__('qa_track').history(f.epic()):
            self.assert_bundle(f.directory, 'qa-baselines', event)
        self.assertTrue((f.directory/'qa-baselines'/original/'test-scenarios.md').is_file())
        self.assertFalse(list(f.directory.rglob('content.md')))
        self.assertTrue(sdlc.inspect_epics(f.project, 'validate', 'REQ-0001')['ok'])

    def test_legacy_approved_history_keeps_bytes_hashes_authority_and_explicit_links(self):
        f = self.fixture()
        with patch.object(engineering, 'baseline_snapshot', old_snapshot):
            f.implementation(); f.approve('implementation')
        before = hashes(f.directory)
        view = f.review()
        self.assertTrue(view['approvals']['implementation']['valid'])
        for draft in view['drafts'].values():
            doc = draft['document']
            self.assertTrue(doc['legacy'])
            self.assertEqual(doc['name'], 'content.md')
            self.assertIn('legacy content.md', doc['link'])
            self.assertEqual(Path(doc['path']).name, doc['name'])
        self.assertEqual(before, hashes(f.directory))
        self.assertTrue(sdlc.inspect_epics(f.project, 'validate', 'REQ-0001')['ok'])

    def test_mixed_history_and_legacy_idempotent_retry_do_not_migrate(self):
        f = self.fixture()
        request = f.request('write', 'design', f.document('design'))
        with patch.object(engineering, 'baseline_snapshot', old_snapshot):
            saved = engineering.update(**request)
            f.approve('design'); f.run_update('advance', 'design')
        old = hashes(f.directory/'engineering-baselines')
        self.assertTrue(engineering.update(**request)['replayed'])
        f.run_update('write', 'plan', f.document('plan'))
        for relative, digest in old.items():
            self.assertEqual(hashlib.sha256((f.directory/'engineering-baselines'/relative).read_bytes()).hexdigest(), digest)
        self.assertTrue(f.review()['approvals']['design']['valid'])
        self.assertTrue(f.review()['drafts']['design']['document']['legacy'])
        self.assertEqual(f.review()['drafts']['plan']['document']['name'], 'implementation-plan.md')
        self.assertTrue((f.directory/'engineering-baselines'/saved['baseline_id']/'content.md').is_file())

    def test_interrupted_canonical_publication_and_exact_retry_reuse_orphan(self):
        f = self.fixture(); request = f.request('write', 'design', f.document('design'))
        with patch.object(sdlc, 'atomic_history_write', side_effect=OSError('Injected precommit failure')):
            with self.assertRaises(OSError):
                engineering.update(**request)
        root = f.directory/'engineering-baselines'
        dirs = list(root.iterdir()); self.assertEqual(len(dirs), 1)
        self.assertTrue((dirs[0]/'technical-design.md').is_file())
        result = engineering.update(**request)
        self.assertEqual(result['baseline_id'], dirs[0].name)
        before = hashes(f.directory)
        self.assertTrue(engineering.update(**request)['replayed'])
        self.assertEqual(before, hashes(f.directory))

    def test_qa_interrupted_publication_and_retry_preserve_named_file(self):
        f = self.fixture(fork.QATrackTests); request = f.request('write', 'strategy', f.base())
        import qa_track
        with patch.object(sdlc, 'atomic_history_write', side_effect=OSError('Injected precommit failure')):
            with self.assertRaises(OSError):
                qa_track.update(**request)
        self.assertEqual(len(list(f.directory.glob('qa-baselines/*/test-strategy.md'))), 1)
        result = qa_track.update(**request)
        before = hashes(f.directory)
        self.assertTrue(qa_track.update(**request)['replayed'])
        self.assertEqual(before, hashes(f.directory))
        self.assertTrue((f.directory/'qa-baselines'/result['baseline_id']/'test-strategy.md').is_file())

    def test_format_version_and_type_filename_binding_fail_closed(self):
        f = self.fixture(); result = f.run_update('write', 'design', f.document('design'))
        original = f.directory/'engineering-baselines'/result['baseline_id']
        manifest = json.loads((original/'manifest.json').read_text())
        for version, name in [('0.3', 'technical-design.md'), ('0.2', '../outside.md'), ('0.2', 'security-review.md')]:
            altered = deepcopy(manifest); altered['schema_version'] = version; altered['document'] = name
            if name == 'security-review.md':
                altered['files'][name] = altered['files'].pop('technical-design.md')
            encoded = common.canonical_manifest(altered); target = original.parent/business.digest(encoded)
            target.mkdir(); (target/'manifest.json').write_bytes(encoded)
            for file in ('metadata.yaml', 'artifact.json', 'technical-design.md'):
                destination = 'security-review.md' if name == 'security-review.md' and file == 'technical-design.md' else file
                (target/destination).write_bytes((original/file).read_bytes())
            with self.assertRaises(business.BusinessError):
                engineering.load_artifact(f.directory, target.name)
