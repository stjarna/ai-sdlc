"""Preservation/rehearsal checks; never rewrite the real acceptance history."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2]/'examples/todo-app/demo.py'
spec = importlib.util.spec_from_file_location('presentation_demo', SCRIPT)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class DemoAssetsTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        for folder in ['project', 'acceptance-evidence', 'acceptance-inputs']:
            (base/folder).mkdir()
        (base/'project/source.txt').write_text('preserved')
        manifest = {'files': {'project/source.txt': hashlib.sha256(b'preserved').hexdigest()},
                    'historical_roots': {'project': ['/old/session/project']}}
        (base/'preservation-manifest.json').write_text(json.dumps(manifest))
        return base, manifest

    def test_actual_demo_archive_matches_every_preserved_hash(self):
        manifest = demo.check_archive()
        self.assertGreater(len(manifest['files']), 400)
        self.assertFalse((demo.BASE/'project/qa/node_modules').exists())
        report = list((demo.BASE/'project/requirements').glob('*/engineering-baselines/*/verification-report.md'))
        self.assertEqual(len(report), 1)

    def test_changed_or_unexpected_archive_files_are_rejected(self):
        base, _ = self.fixture()
        (base/'project/source.txt').write_text('changed')
        with self.assertRaises(ValueError): demo.check_archive(base)
        (base/'project/source.txt').write_text('preserved')
        (base/'project/extra.txt').write_text('untracked')
        with self.assertRaises(ValueError): demo.check_archive(base)

    def test_rehearsal_copy_is_separate_and_never_silently_overwritten(self):
        base, _ = self.fixture()
        target = demo.workspace(base)
        self.assertNotEqual(target, base/'project')
        (target/'source.txt').write_text('local work')
        with self.assertRaises(ValueError): demo.workspace(base)
        self.assertEqual((target/'source.txt').read_text(), 'local work')
        self.assertEqual((base/'project/source.txt').read_text(), 'preserved')

    def test_historical_paths_resolve_locally_and_cannot_escape_archive(self):
        base, manifest = self.fixture()
        path = demo.original_path('/old/session/project/source.txt', manifest, base)
        self.assertEqual(path.read_text(), 'preserved')
        with self.assertRaises(ValueError):
            demo.original_path('/old/session/project/../../outside.txt', manifest, base)
