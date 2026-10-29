"""Pinned document layouts and legacy compatibility in disposable projects only."""
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import artifact_templates as templates
import business_refinement as business
import sdlc


class TemplateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / 'project'
        self.project.mkdir()
        self.root = Path(temporary.name) / 'templates'
        shutil.copytree(templates.ROOT, self.root)

    def reject(self, code, action):
        with self.assertRaises(business.BusinessError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def manifest(self, name='technical-design'):
        return self.root / 'versions' / name / '1.0.0' / 'manifest.yaml'

    def rewrite_manifest(self, name, **changes):
        path = self.manifest(name)
        data = yaml.safe_load(path.read_text())
        data.update(changes)
        path.write_text(yaml.safe_dump(data, sort_keys=False))

    def test_catalog_resolves_every_supported_artifact_with_exact_content_pin(self):
        with patch.object(templates, 'ROOT', self.root):
            catalog = templates.catalog()
            self.assertEqual(set(catalog), set(templates.ARTIFACTS))
            for name, item in catalog.items():
                with self.subTest(template=name):
                    self.assertEqual(templates.resolve(name), item)
                    self.assertEqual(item['pin']['content_digest'], hashlib.sha256(item['content'].encode()).hexdigest())
                    self.assertEqual(item['pin']['validation_contract'], templates.ARTIFACTS[name][0] + '/1')
                    self.assertEqual(item['manifest']['version'], '1.0.0')
                    self.assertTrue(item['manifest']['owner'])
                    self.assertEqual(templates.validate_document(item, item['content']), item['pin'])

    def test_foundation_scaffolds_match_existing_validator_fields(self):
        import re
        import functional_analysis as analysis
        self.assertEqual(templates.resolve('idea')['manifest']['required_sections'], list(sdlc.SECTIONS))
        self.assertEqual(templates.resolve('business')['manifest']['required_sections'], list(business.CATEGORIES))
        item = templates.resolve('specification')
        self.assertEqual(item['manifest']['required_sections'], list(analysis.SECTIONS))
        for kind, fields in analysis.FIELDS.items():
            marker = '### {{' + kind.lower() + '_id}}'
            block = item['content'].split(marker, 1)[1]
            block = re.split(r'\n##? ', block, maxsplit=1)[0]
            declared = set(re.findall(r'^([A-Za-z ]+):', block, re.MULTILINE))
            self.assertEqual(declared, fields, kind)

    def test_changed_template_content_rejects_digest_before_use(self):
        document = self.manifest().with_name('document.md')
        document.write_bytes(document.read_bytes() + b'\nUnreviewed layout change.\n')
        self.reject('E_TEMPLATE_INTEGRITY', lambda: templates.package('technical-design', '1.0.0', self.root))

    def test_changed_manifest_rejects_catalog_pin(self):
        self.rewrite_manifest('technical-design', owner='Different declared domain owner')
        self.reject('E_TEMPLATE_INTEGRITY', lambda: templates.catalog(self.root))

    def test_template_validator_contract_mismatch_is_not_cli_version(self):
        self.rewrite_manifest('technical-design', validation_contract='engineering.design/999')
        self.reject('E_TEMPLATE_CONTRACT', lambda: templates.package('technical-design', '1.0.0', self.root))

    def test_missing_duplicate_and_reordered_required_sections_are_rejected(self):
        item = templates.package('technical-design', '1.0.0', self.root)
        sections = item['manifest']['required_sections']
        valid = '\n\n'.join('## ' + heading + '\n\nFixture body.' for heading in sections)
        self.assertEqual(templates.validate_document(item, valid), item['pin'])
        variants = (
            valid.replace('## ' + sections[0], '### ' + sections[0], 1),
            valid + '\n\n## ' + sections[0] + '\n\nDuplicate.',
            '\n\n'.join('## ' + heading + '\n\nFixture body.' for heading in reversed(sections)),
        )
        for content in variants:
            with self.subTest(content=content):
                self.reject('E_TEMPLATE_DOCUMENT', lambda: templates.validate_document(item, content))

    def test_manifest_cannot_silently_change_declared_sections(self):
        item = templates.package('technical-design', '1.0.0', self.root)
        self.rewrite_manifest('technical-design', required_sections=item['manifest']['required_sections'] + ['Undeclared heading'])
        self.reject('E_TEMPLATE_CONTRACT', lambda: templates.package('technical-design', '1.0.0', self.root))

    def test_stale_template_selection_is_rejected(self):
        with patch.object(templates, 'ROOT', self.root):
            selected = templates.resolve('idea')
            self.reject('E_TEMPLATE_STALE', lambda: templates.resolve('idea', '0' * 64))
            changed = deepcopy(selected)
            changed['pin']['digest'] = '0' * 64
            self.reject('E_TEMPLATE_STALE', lambda: templates.assert_current(changed))
            templates.assert_current(selected)

    def test_new_idea_records_exact_pin_and_preserves_original_statement(self):
        idea = 'Fictional users need a simpler way to organize shared requests.'
        with patch.object(templates, 'ROOT', self.root):
            result = sdlc.new_epic(self.project, 'Fixture request', idea, requester='Fixture Requester')
            directory = Path(result['epic']['directory'])
            metadata = yaml.safe_load((directory / 'metadata.yaml').read_text())
            self.assertEqual(metadata['template_provenance'], {'schema_version': '0.1', 'idea': templates.resolve('idea')['pin']})
            self.assertEqual((directory / 'idea.md').read_text(), templates.resolve('idea')['content'].replace('{{problem}}', idea))
            self.assertEqual(metadata['status'], 'discovery')

    def test_legacy_idea_without_provenance_remains_readable_without_retroactive_pin(self):
        sdlc.new_epic(self.project, 'Legacy fixture', 'Existing user idea.', requester='Fixture Requester')
        epic = sdlc.selected_epic(self.project, 'REQ-0001')
        metadata_path = epic.directory / 'metadata.yaml'
        metadata = yaml.safe_load(metadata_path.read_text())
        metadata.pop('template_provenance')
        metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False))
        before = {path.name: path.read_bytes() for path in epic.directory.iterdir() if path.is_file()}
        result = sdlc.inspect_epics(self.project, 'open', 'REQ-0001')
        self.assertTrue(result['ok'])
        self.assertNotIn('template_provenance', result['epic']['metadata'])
        self.assertEqual(before, {path.name: path.read_bytes() for path in epic.directory.iterdir() if path.is_file()})

    def test_template_resolution_is_read_only_and_reproducible(self):
        before = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        with patch.object(templates, 'ROOT', self.root):
            first = templates.resolve('specification')['pin']
            self.assertEqual(templates.resolve('specification')['pin'], first)
        after = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_cli_templates_is_read_only_without_project_context(self):
        import json
        import subprocess
        command = [sys.executable, str(Path(sdlc.__file__).resolve()), 'templates']
        all_items = subprocess.run(command, cwd=self.project, capture_output=True, text=True, check=False)
        self.assertEqual(all_items.returncode, 0, all_items.stderr)
        self.assertEqual(set(json.loads(all_items.stdout)['templates']), set(templates.ARTIFACTS))
        selected = subprocess.run(command + ['technical-design'], cwd=self.project, capture_output=True, text=True, check=False)
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual(json.loads(selected.stdout)['templates']['pin'], templates.resolve('technical-design')['pin'])
        self.assertEqual(list(self.project.iterdir()), [])


class TemplateWorkflowTests(unittest.TestCase):
    def setUp(self):
        import test_qa_track
        self.fixture = test_qa_track.QATrackTests('test_qa_design_does_not_require_technical_design')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    def test_business_analysis_and_engineering_qa_records_pin_templates(self):
        import engineering
        import qa_track
        f = self.fixture
        for filename, name in (('business-history.yaml', 'business'), ('analysis-history.yaml', 'specification')):
            history = yaml.safe_load((f.directory / filename).read_text())
            record = history['revisions'][-1]
            self.assertEqual(record['schema_version'], '0.2')
            self.assertEqual(record['template'], templates.resolve(name)['pin'])
        f.design_engineering()
        f.design_qa()
        for module, stage, kinds in ((engineering, 'engineering', ('design',)), (qa_track, 'qa', ('strategy', 'scenarios'))):
            review = module.review(f.epic(), f.project)
            for kind in kinds:
                draft = review['drafts'][kind]
                obj, _ = engineering.load_artifact(f.directory, draft['baseline_id'], 'qa-baselines' if stage == 'qa' else 'engineering-baselines')
                name = templates.template_for(stage, kind)
                self.assertEqual(obj['schema_version'], '0.2')
                self.assertEqual(obj['template'], templates.resolve(name)['pin'])
                self.assertEqual(draft['template'], obj['template'])
                self.assertEqual(Path(draft['document']['path']).name, templates.ARTIFACTS[name][1])

    def test_missing_sections_reject_write_without_mutating_request(self):
        import engineering
        f = self.fixture
        doc = f.base()
        doc['governance'] = {'schema_version': '0.1', 'prototype_limitations': []}
        before = {str(p.relative_to(f.project)): p.read_bytes() for p in f.project.rglob('*') if p.is_file()}
        with self.assertRaises(business.BusinessError) as caught:
            engineering.update(f.project, 'REQ-0001', engineering.review(f.epic(), f.project)['revision'],
                               'missing-template-sections', 'write', 'design', doc, 'Fixture Lead', 'Fictional draft.')
        self.assertEqual(caught.exception.code, 'E_TEMPLATE_DOCUMENT')
        self.assertEqual(before, {str(p.relative_to(f.project)): p.read_bytes() for p in f.project.rglob('*') if p.is_file()})

    def test_pinned_writes_are_idempotent_and_concurrent_revision_guard_is_preserved(self):
        from concurrent.futures import ThreadPoolExecutor
        import engineering
        from template_fixtures import document_payload
        f = self.fixture
        doc = document_payload('engineering', 'design', f.base())
        doc['governance'] = {'schema_version': '0.1', 'prototype_limitations': []}
        request = dict(project=f.project, epic_id='REQ-0001', expected_revision=engineering.review(f.epic(), f.project)['revision'],
                       operation_id='pinned-design-write', action='write', kind='design', payload=doc,
                       actor='Fixture Engineering Lead', decision='Fictional source-bound draft.',
                       expected_template_digest=templates.resolve('technical-design')['pin']['digest'])
        first = engineering.update(**request)
        self.assertTrue(engineering.update(**request)['replayed'])
        self.assertEqual(engineering.update(**request)['engineering']['drafts']['design']['baseline_id'], first['baseline_id'])
        request['expected_revision'] = engineering.review(f.epic(), f.project)['revision']
        def write(operation_id):
            try:
                return engineering.update(**{**request, 'operation_id': operation_id})
            except business.BusinessError as exc:
                return exc.code
            except sdlc.Rejected as exc:
                return exc.diagnostics[0].code
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(write, ('template-concurrent-one', 'template-concurrent-two')))
        self.assertEqual(sum(isinstance(result, dict) for result in results), 1)
        self.assertEqual(sum(result in ('E_REVISION_CONFLICT', 'E_PROJECT_BUSY') for result in results if isinstance(result,str)), 1)

    def test_exact_retry_survives_catalog_rollforward_but_new_write_rejects_old_pin(self):
        import engineering
        from template_fixtures import document_payload
        f = self.fixture
        doc = document_payload('engineering', 'design', f.base())
        doc['governance'] = {'schema_version': '0.1', 'prototype_limitations': []}
        old_pin = templates.resolve('technical-design')['pin']
        request = dict(project=f.project, epic_id='REQ-0001', expected_revision=engineering.review(f.epic(), f.project)['revision'],
                       operation_id='template-before-rollforward', action='write', kind='design', payload=doc,
                       actor='Fixture Lead', decision='Fictional source-bound draft.', expected_template_digest=old_pin['digest'])
        result = engineering.update(**request)
        with tempfile.TemporaryDirectory() as area:
            root = Path(area) / 'templates'
            shutil.copytree(templates.ROOT, root)
            prior = root / 'versions' / 'technical-design' / '1.0.0'
            updated = prior.with_name('1.0.1')
            shutil.copytree(prior, updated)
            manifest = yaml.safe_load((updated / 'manifest.yaml').read_text())
            manifest['version'] = '1.0.1'
            (updated / 'manifest.yaml').write_text(yaml.safe_dump(manifest, sort_keys=False))
            new_pin = templates.package('technical-design', '1.0.1', root)['pin']
            catalog = yaml.safe_load((root / 'catalog.yaml').read_text())
            catalog['templates']['technical-design'] = {'version': '1.0.1', 'digest': new_pin['digest']}
            (root / 'catalog.yaml').write_text(yaml.safe_dump(catalog, sort_keys=False))
            with patch.object(templates, 'ROOT', root):
                replay = engineering.update(**request)
                self.assertTrue(replay['replayed'])
                draft = replay['engineering']['drafts']['design']
                self.assertEqual(draft['baseline_id'], result['baseline_id'])
                self.assertEqual(draft['template'], old_pin)
                with self.assertRaises(business.BusinessError) as caught:
                    engineering.update(**{**request, 'operation_id': 'template-after-rollforward',
                                          'expected_revision': engineering.review(f.epic(), f.project)['revision']})
                self.assertEqual(caught.exception.code, 'E_TEMPLATE_STALE')
                changed_retry = {**request, 'expected_template_digest': new_pin['digest']}
                with self.assertRaises(business.BusinessError) as caught:
                    engineering.update(**changed_retry)
                self.assertEqual(caught.exception.code, 'E_IDEMPOTENCY')
