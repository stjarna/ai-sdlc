"""Local domain package contracts tested without changing bundled instruction files."""
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import business_refinement as business
import domain_skills
import sdlc


class DomainSkillTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'domain-skills'
        self.root.mkdir()
        self.manifests = {}
        stages = {
            'architecture': ['technical_design'],
            'development': ['implementation_planning', 'development'],
            'testing': ['verification', 'final_verification'],
            'security': ['technical_design', 'security_review'],
        }
        for name, supported in stages.items():
            path = self.root / name
            path.mkdir()
            (path / 'SKILL.md').write_text(
                f'---\nname: sdlc-{name}\ndescription: Fixture domain instructions.\n---\n\nUse the reviewed inputs.\n',
                encoding='utf-8',
            )
            self.manifests[name] = {
                'name': name,
                'description': 'Fixture domain practice',
                'version': '1.0.0',
                'owner': 'Fixture Domain Team',
                'stages': supported,
                'inputs': ['Approved upstream artifact'],
                'outputs': ['Reviewable artifact'],
                'standards': ['Project conventions'],
                'dependencies': {'security': '1.0.0'} if name == 'architecture' else {},
                'orchestrator': '0.9',
            }
        self.publish()

    def publish(self):
        skills = {}
        for name, manifest in self.manifests.items():
            path = self.root / name
            (path / 'manifest.yaml').write_text(yaml.safe_dump(manifest, sort_keys=False), encoding='utf-8')
            skills[name] = {'version': manifest['version'], 'digest': domain_skills.package(path)}
        (self.root / 'catalog.yaml').write_text(
            yaml.safe_dump({'schema_version': '0.1', 'skills': skills}, sort_keys=False), encoding='utf-8'
        )

    def catalog(self):
        return domain_skills.catalog(sdlc.StrictLoader, self.root)

    def pins(self, names, stage):
        original = domain_skills.catalog
        with patch.object(domain_skills, 'catalog', side_effect=lambda loader: original(loader, self.root)):
            return domain_skills.pins(names, stage, sdlc.StrictLoader)

    def reject(self, operation):
        with self.assertRaises(business.BusinessError) as caught:
            operation()
        self.assertEqual(caught.exception.code, 'E_SKILL')

    def test_discovery_loads_version_owner_contract_and_exact_digest(self):
        catalog = self.catalog()
        self.assertEqual(set(catalog), {'architecture', 'development', 'testing', 'security'})
        for name, entry in catalog.items():
            self.assertEqual(entry['version'], '1.0.0')
            self.assertEqual(entry['owner'], 'Fixture Domain Team')
            self.assertEqual(entry['path'], str(self.root / name))
            self.assertEqual(entry['digest'], domain_skills.package(self.root / name))
            self.assertEqual(len(entry['digest']), 64)
            self.assertEqual(entry['inputs'], self.manifests[name]['inputs'])
            self.assertEqual(entry['outputs'], self.manifests[name]['outputs'])

    def test_pins_include_compatible_transitive_dependencies(self):
        pins = self.pins(['architecture'], 'technical_design')
        self.assertEqual(set(pins), {'architecture', 'security'})
        self.assertEqual(pins['architecture']['version'], '1.0.0')
        self.assertEqual(pins['security']['digest'], self.catalog()['security']['digest'])
        self.assertNotIn('path', pins['architecture'])

    def test_unchanged_package_has_stable_digest_independent_of_parent_path(self):
        import shutil
        copied = self.root.parent / 'another-location'
        shutil.copytree(self.root / 'testing', copied)
        self.assertEqual(domain_skills.package(copied), domain_skills.package(self.root / 'testing'))
        self.assertEqual(self.pins(['testing'], 'verification'), self.pins(['testing'], 'verification'))

    def test_modified_instruction_or_reference_rejects_approved_pin(self):
        path = self.root / 'testing' / 'SKILL.md'
        original = path.read_bytes()
        path.write_bytes(original + b'\nChanged instructions.\n')
        self.reject(self.catalog)
        path.write_bytes(original)
        references = self.root / 'testing' / 'references'
        references.mkdir()
        (references / 'practice.md').write_text('New unapproved practice.', encoding='utf-8')
        self.reject(self.catalog)

    def test_modified_manifest_rejects_pin_before_loading_contract(self):
        path = self.root / 'development' / 'manifest.yaml'
        path.write_bytes(path.read_bytes() + b'\n')
        self.reject(self.catalog)

    def test_missing_dependency_rejected(self):
        self.manifests['architecture']['dependencies'] = {'missing-domain': '1.0.0'}
        self.publish()
        self.reject(self.catalog)

    def test_wrong_dependency_version_rejected(self):
        self.manifests['architecture']['dependencies']['security'] = '2.0.0'
        self.publish()
        self.reject(self.catalog)

    def test_cyclic_dependency_rejected(self):
        self.manifests['security']['dependencies'] = {'architecture': '1.0.0'}
        self.publish()
        self.reject(self.catalog)

    def test_self_dependency_rejected(self):
        self.manifests['testing']['dependencies'] = {'testing': '1.0.0'}
        self.publish()
        self.reject(self.catalog)

    def test_skill_stage_and_dependency_stage_are_checked(self):
        self.reject(lambda: self.pins(['testing'], 'development'))
        self.manifests['security']['stages'] = ['security_review']
        self.publish()
        self.reject(lambda: self.pins(['architecture'], 'technical_design'))

    def test_unknown_skill_rejected(self):
        self.reject(lambda: self.pins(['unapproved-skill'], 'verification'))

    def test_unsupported_orchestrator_contract_rejected(self):
        self.manifests['development']['orchestrator'] = '1.0'
        self.publish()
        self.reject(self.catalog)

    def test_invalid_semver_rejected(self):
        for version in ('1.0', '01.0.0', '1.2.3.4', 'latest', 1):
            with self.subTest(version=version):
                self.manifests['development']['version'] = version
                self.publish()
                self.reject(self.catalog)

    def test_missing_metadata_and_invalid_contract_lists_rejected(self):
        original = self.manifests['testing'].copy()
        for key, value in (('owner', ''), ('stages', []), ('inputs', ['same', 'same']), ('standards', [None]), ('dependencies', [])):
            with self.subTest(key=key):
                self.manifests['testing'] = {**original, key: value}
                self.publish()
                self.reject(self.catalog)
        self.manifests['testing'] = {k: v for k, v in original.items() if k != 'outputs'}
        self.publish()
        self.reject(self.catalog)

    def test_missing_required_skill_file_rejected(self):
        (self.root / 'security' / 'SKILL.md').unlink()
        self.reject(self.catalog)

    def test_catalog_and_package_symlinks_rejected(self):
        original = self.root / 'catalog.yaml'
        content = original.read_bytes()
        external = self.root.parent / 'external-catalog.yaml'
        external.write_bytes(content)
        original.unlink()
        original.symlink_to(external)
        self.reject(self.catalog)
        original.unlink()
        original.write_bytes(content)
        (self.root / 'testing' / 'external-link').symlink_to(external)
        self.reject(self.catalog)

    def test_malformed_catalog_and_duplicate_keys_rejected(self):
        path = self.root / 'catalog.yaml'
        for text in ('!!map [hello]', '!!map hello', 'schema_version: "0.1"\nschema_version: "0.1"\nskills: {}\n', '[]'):
            with self.subTest(text=text):
                path.write_text(text, encoding='utf-8')
                self.reject(self.catalog)
