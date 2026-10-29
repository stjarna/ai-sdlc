"""Sequential engineering acceptance fixtures; all human decisions are fictional.

The named unit/build/integration/ui commands below are actual fixture executions,
not a claim that these tests perform browser UI acceptance or security certification.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_analysis_approval as fixtures
import business_refinement as business
import engineering
import sdlc


class EngineeringTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.AnalysisApprovalTests('test_exact_baseline_binding_and_separate_advancement')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.approve()
        self.fixture.advance()
        # Historical pre-fork fixture: retain legacy sequential regression coverage.
        # Production advancement always forks; tests construct old stored metadata.
        import yaml
        metadata_path=self.fixture.directory/'metadata.yaml'
        metadata=yaml.safe_load(metadata_path.read_text())
        metadata.pop('work_tracks',None)
        metadata_path.write_text(yaml.safe_dump(metadata,sort_keys=False,allow_unicode=True))
        self.project = self.fixture.project
        self.directory = self.fixture.directory
        self.counter = 0
        # All application inputs predate the development snapshot. Only declared
        # paths are modified afterward; no synthetic input files enter the tree.
        (self.project / 'app.py').write_text('value = 0\n')
        (self.project / 'check.py').write_text(
            'import app, sys\nassert app.value == 1, "fixture app value differs"\n'
            'print("Executed fixture check:", sys.argv[1])\n')

    def epic(self):
        return sdlc.selected_epic(self.project, 'REQ-0001')

    def review(self):
        return engineering.review(self.epic(), self.project)

    def request(self, action, kind, payload=None, **extra):
        self.counter += 1
        return dict(project=self.project, epic_id='REQ-0001', expected_revision=self.review()['revision'],
                    operation_id=f'engineering-fixture-{self.counter}', action=action, kind=kind,
                    payload={} if payload is None else payload, actor='Fixture Engineering Lead',
                    decision=f'Fixture human decision: {action} {kind}.', **extra)

    def run_update(self, action, kind, payload=None):
        return engineering.update(**self.request(action, kind, payload))

    def reject(self, code, action):
        try:
            action()
        except business.BusinessError as exc:
            self.assertEqual(exc.code, code)
        except sdlc.Rejected as exc:
            self.assertIn(code, {d.code for d in exc.diagnostics})
        else:
            self.fail('Expected diagnostic ' + code)

    def base_document(self):
        items, unresolved = engineering.analysis_items(self.epic())
        return dict(content='Fixture engineering document. No new business behavior.',
                    coverage={rid: {'disposition': 'blocked' if status in ('blocked', 'proposed') else 'implemented',
                                    'reason': 'Retain unresolved behavior.' if status in ('blocked', 'proposed') else 'Within approved scope.'}
                              for rid, status in items.items()},
                    unresolved=[{'id': item['id'], 'text': item['text']} for item in unresolved])

    def document(self, kind):
        doc = self.base_document()
        if kind == 'plan':
            doc.update(tasks=[dict(id='T-001', description='Implement approved behavior and its checks.',
                                   requirements=['FR-001', 'AC-001'], depends_on=[], paths=['app.py', 'check.py'])],
                       checks=[dict(id=category, category=category,
                                    argv=[sys.executable, '-B', 'check.py', category], cwd='.', timeout=10,
                                    requirements=['AC-001'], scenario='Actual fixture command, not browser acceptance.')
                               for category in ('unit', 'build', 'integration', 'ui')])
        elif kind in ('implementation', 'security'):
            current = self.review()
            doc.update(source_revision=current['source_revision'], plan=current['drafts']['plan']['baseline_id'])
            doc.update(completed_tasks=['T-001']) if kind == 'implementation' else doc.update(findings=[])
        return doc

    def approve(self, kind):
        doc = self.review()['drafts'][kind]['payload']
        return self.run_update('approve', kind, {'acknowledged': [i['id'] for i in doc['unresolved']]})

    def design(self):
        return self.run_update('write', 'design', self.document('design'))

    def plan(self):
        self.design()
        self.approve('design')
        self.run_update('advance', 'design')
        self.run_update('write', 'plan', self.document('plan'))

    def development(self):
        self.plan()
        self.approve('plan')
        self.run_update('advance', 'plan')
        self.run_update('start', 'development')
        (self.project / 'app.py').write_text('value = 1\n')

    def check(self, category):
        return self.run_update('run', 'check', {'check_id': category})

    def implementation(self):
        self.development()
        self.check('unit')
        self.check('build')
        return self.run_update('write', 'implementation', self.document('implementation'))

    def verification(self):
        self.implementation()
        self.approve('implementation')
        self.run_update('advance', 'implementation')
        self.check('integration')
        self.check('ui')

    def security(self):
        self.verification()
        self.run_update('advance', 'verification')

    def test_sequential_end_to_end_preserves_approvals_and_actual_evidence(self):
        subprocess.run(['git','init','-q',str(self.project)],check=True)
        self.security()
        self.run_update('write', 'security', self.document('security'))
        self.run_update('advance', 'security')
        done = self.run_update('finalize', 'final')
        self.assertEqual(done['epic']['metadata']['status'], 'verified')
        self.assertTrue(done['epic']['approval']['valid'])
        self.assertTrue(done['epic']['analysis_approval']['valid'])
        obj, _ = engineering.load_artifact(self.directory, done['baseline_id'])
        self.assertEqual(set(obj['payload']['checks']), {'unit', 'build', 'integration', 'ui'})
        for evidence in obj['payload']['checks'].values():
            self.assertEqual(evidence['status'], 'passed')
            self.assertEqual(evidence['exit_code'], 0)
            self.assertIn('Executed fixture check:', evidence['output'])
        self.assertFalse((self.directory / 'design.md').exists())
        self.assertTrue(sdlc.inspect_epics(self.project, 'validate', 'REQ-0001')['ok'])
        reviewed=self.review()
        self.assertTrue(reviewed['current'])
        self.assertEqual(reviewed['final_report']['baseline_id'],done['baseline_id'])
        (self.project/'app.py').write_text('value = 2\n')
        self.assertFalse(self.review()['current'])
        self.assertFalse(self.review()['approvals']['implementation']['valid'])
        self.assertEqual(subprocess.check_output(['git','-C',str(self.project),'diff','--cached','--name-only']),b'')
        self.assertNotEqual(subprocess.run(['git','-C',str(self.project),'rev-parse','HEAD'],capture_output=True).returncode,0)

    def test_design_binds_exact_analysis_and_pinned_skills(self):
        prior = self.review()
        written = self.design()
        obj, frozen = engineering.load_artifact(self.directory, written['baseline_id'])
        self.assertEqual(obj['analysis_baseline'], prior['analysis_baseline'])
        self.assertEqual(obj['analysis_handoff'], prior['analysis_handoff'])
        self.assertEqual(obj['skills']['architecture']['version'], '1.2.0')
        self.assertEqual(len(obj['skills']['architecture']['digest']), 64)
        self.assertEqual(frozen['status'], 'ready_for_technical_design')
        self.assertEqual(written['epic']['metadata']['status'], 'technical_design')

    def test_approval_does_not_advance_and_unresolved_acknowledgements_required(self):
        self.design()
        self.reject('E_ACKNOWLEDGEMENT', lambda: self.run_update('approve', 'design', {'acknowledged': []}))
        approved = self.approve('design')
        self.assertEqual(approved['epic']['metadata']['status'], 'technical_design')
        self.assertEqual(self.run_update('advance', 'design')['epic']['metadata']['status'], 'ready_for_implementation_planning')

    def test_missing_approval_and_incorrect_stage_reject_progression(self):
        self.design()
        self.reject('E_APPROVAL_REQUIRED', lambda: self.run_update('advance', 'design'))
        self.reject('E_STATUS', lambda: self.run_update('start', 'development'))
        self.reject('E_STATUS', lambda: self.run_update('write', 'plan', self.document('plan')))

    def test_same_content_revision_invalidates_approval_and_stale_context(self):
        self.design()
        self.approve('design')
        pending = self.request('advance', 'design')
        self.design()
        self.reject('E_REVISION_CONFLICT', lambda: engineering.update(**pending))
        self.reject('E_APPROVAL_STALE', lambda: self.run_update('advance', 'design'))

    def test_request_changes_keeps_document_and_supersedes_approval(self):
        self.design()
        self.approve('design')
        before = deepcopy(self.review()['drafts']['design'])
        feedback = self.run_update('request_changes', 'design', {'acknowledged': []})
        self.assertEqual(feedback['epic']['metadata']['status'], 'technical_design')
        self.assertEqual(self.review()['drafts']['design'], before)
        self.reject('E_APPROVAL_REQUIRED', lambda: self.run_update('advance', 'design'))

    def test_idempotent_retries_preserve_actual_decision_and_do_not_duplicate(self):
        request = self.request('write', 'design', self.document('design'))
        request['decision'] = 'Fixture human words:\nPlease record this design.'
        first = engineering.update(**request)
        again = engineering.update(**request)
        self.assertTrue(again['replayed'])
        self.assertEqual(again['epic']['metadata']['engineering_history'], first['epic']['metadata']['engineering_history'])
        self.assertEqual(again['epic']['metadata']['engineering_history'][-1]['decision'], request['decision'])
        self.reject('E_IDEMPOTENCY', lambda: engineering.update(**{**request, 'decision': 'Different fixture wording'}))

    def test_requirement_coverage_and_inherited_uncertainty_are_enforced(self):
        doc = self.document('design')
        doc['coverage'].pop('AC-001')
        self.reject('E_ENGINEERING_TRACE', lambda: self.run_update('write', 'design', doc))
        doc = self.document('design')
        doc['coverage']['FR-002']['disposition'] = 'implemented'
        self.reject('E_ENGINEERING_TRACE', lambda: self.run_update('write', 'design', doc))
        doc = self.document('design')
        doc['unresolved'] = []
        self.reject('E_ENGINEERING_TRACE', lambda: self.run_update('write', 'design', doc))

    def test_plan_requires_safe_paths_dependency_order_and_verification_coverage(self):
        self.design()
        self.approve('design')
        self.run_update('advance', 'design')
        doc = self.document('plan')
        doc['tasks'][0]['paths'] = ['../outside']
        self.reject('E_IMPLEMENTATION_BOUNDARY', lambda: self.run_update('write', 'plan', doc))
        doc = self.document('plan')
        doc['tasks'][0]['depends_on'] = ['T-999']
        self.reject('E_ENGINEERING_PLAN', lambda: self.run_update('write', 'plan', doc))
        doc = self.document('plan')
        doc['checks'] = [c for c in doc['checks'] if c['category'] != 'ui']
        self.reject('E_ENGINEERING_PLAN', lambda: self.run_update('write', 'plan', doc))

    def test_changed_application_requires_replanning_before_start(self):
        self.plan()
        self.assertIn('testing', self.review()['drafts']['plan']['skills'])
        self.approve('plan')
        self.run_update('advance', 'plan')
        (self.project/'app.py').write_text('value = 7\n')
        self.reject('E_APPROVAL_STALE',lambda:self.run_update('start','development'))

    def test_out_of_plan_file_changes_block_check_execution(self):
        self.development()
        (self.project / 'outside.txt').write_text('Not in the approved plan.')
        self.reject('E_IMPLEMENTATION_BOUNDARY', lambda: self.check('unit'))
        self.assertEqual(self.review()['evidence'], [])

    def test_failed_checks_are_persisted_and_never_count_as_passed(self):
        self.development()
        (self.project / 'app.py').write_text('value = 2\n')
        result = self.check('unit')
        evidence = result['engineering']['evidence'][-1]
        self.assertEqual(evidence['status'], 'failed')
        self.assertNotEqual(evidence['exit_code'], 0)
        self.assertIn('fixture app value differs', evidence['output'])
        self.reject('E_VERIFICATION', lambda: self.run_update('write', 'implementation', self.document('implementation')))

    def test_source_changes_invalidate_check_results_and_pending_reviews(self):
        self.implementation()
        pending = self.request('approve', 'implementation', {'acknowledged': [i['id'] for i in self.document('implementation')['unresolved']]})
        (self.project / 'app.py').write_text('value = 1\n# Changed source\n')
        self.reject('E_REVISION_CONFLICT', lambda: engineering.update(**pending))
        self.reject('E_VERIFICATION', lambda: self.approve('implementation'))

    def test_ui_and_integration_do_not_run_during_development(self):
        self.development()
        self.reject('E_STATUS', lambda: self.check('integration'))
        self.reject('E_STATUS', lambda: self.check('ui'))

    def test_security_findings_block_advancement_and_remain_traceable(self):
        self.security()
        doc = self.document('security')
        doc['findings'] = [dict(id='SF-001', severity='high', status='open', requirements=['FR-001'],
                                evidence='Fixture risk at app.py:1.', remediation='')]
        self.run_update('write', 'security', doc)
        self.reject('E_SECURITY_FINDINGS', lambda: self.run_update('advance', 'security'))
        self.reject('E_SECURITY_FINDINGS', lambda: self.run_update('remediate', 'security', {'findings': ['SF-999']}))
        remediated = self.run_update('remediate', 'security', {'findings': ['SF-001']})
        self.assertEqual(remediated['epic']['metadata']['status'], 'development')
        self.assertIn('SF-001', engineering.load_artifact(self.directory, remediated['baseline_id'])[0]['payload']['findings'])
        # Even an authorized no-code remediation starts a fresh review/check cycle.
        # It must not recycle the earlier pass results or code approval merely
        # because the source fingerprint happens to be identical.
        self.reject('E_APPROVAL_STALE', lambda: self.run_update('advance', 'implementation'))
        self.reject('E_VERIFICATION', lambda: self.run_update('write', 'implementation', self.document('implementation')))
        self.check('unit')
        self.check('build')
        self.run_update('write', 'implementation', self.document('implementation'))
        self.approve('implementation')
        self.run_update('advance', 'implementation')
        self.check('integration')
        self.check('ui')
        self.run_update('advance', 'verification')
        resolved = self.document('security')
        resolved['findings'] = [dict(id='SF-001', severity='high', status='resolved', requirements=['FR-001'],
                                     evidence='Fixture review of the same app.py:1.',
                                     remediation='Fixture authorized re-evaluation and fresh named checks support resolution.')]
        self.run_update('write', 'security', resolved)
        # Reopening a previously resolved finding needs new authorization; an old
        # remediation event cannot authorize closing a later report's open finding.
        reopened=deepcopy(resolved)
        reopened['findings'][0]['status']='open'
        reopened['findings'][0]['remediation']=''
        self.run_update('write','security',reopened)
        self.reject('E_SECURITY_FINDINGS',lambda:self.run_update('write','security',resolved))

    def test_malformed_completed_task_nodes_return_structured_diagnostic(self):
        self.development()
        doc = self.document('implementation')
        doc['completed_tasks'] = [{}]
        self.reject('E_ENGINEERING_TRACE', lambda: engineering.validate_document(self.epic(), 'implementation', doc))

    def test_corrupted_baseline_blocks_current_operations(self):
        written = self.design()
        path = Path(self.review()['drafts']['design']['document']['path'])
        path.write_text('Corrupted retained engineering content.')
        self.reject('E_BASELINE_INTEGRITY', lambda: sdlc.inspect_epics(self.project, 'open', 'REQ-0001'))

    def test_interrupted_metadata_publication_leaves_no_decision_and_exact_retry_recovers(self):
        request = self.request('write', 'design', self.document('design'))
        before = (self.directory / 'metadata.yaml').read_bytes()
        with patch.object(sdlc, 'atomic_history_write', side_effect=OSError('Injected fixture precommit failure')):
            with self.assertRaises(OSError):
                engineering.update(**request)
        self.assertEqual((self.directory / 'metadata.yaml').read_bytes(), before)
        self.assertNotIn('engineering_history', self.epic().metadata)
        result = engineering.update(**request)
        self.assertTrue(result['ok'])
        self.assertEqual(len(result['epic']['metadata']['engineering_history']), 1)

    def test_concurrent_writers_cannot_both_publish_one_revision(self):
        first = self.request('write', 'design', self.document('design'))
        second = {**self.request('write', 'design', self.document('design')), 'expected_revision': first['expected_revision']}
        def run(request):
            try:
                return engineering.update(**request)
            except business.BusinessError as exc:
                return {'ok': False, 'code': exc.code}
            except sdlc.Rejected as exc:
                return {'ok': False, 'code': exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, (first, second)))
        self.assertEqual(sum(v['ok'] for v in results), 1)
        self.assertIn(next(v['code'] for v in results if not v['ok']), ('E_PROJECT_BUSY', 'E_REVISION_CONFLICT'))

    def test_upstream_reopening_preserves_engineering_history_but_removes_authority(self):
        self.design()
        history = deepcopy(self.epic().metadata['engineering_history'])
        self.fixture.business_fixture.reopen()
        epic = self.epic()
        self.assertEqual(epic.metadata['schema_version'], '0.6')
        self.assertEqual(epic.metadata['engineering_history'], history)
        self.assertFalse(engineering.review(epic, self.project)['active'])
        with self.assertRaises(business.BusinessError) as caught:
            engineering.cycle(epic)
        self.assertEqual(caught.exception.code, 'E_ENGINEERING_INPUT')


class CheckExecutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name)

    def check(self, argv, timeout=10, cwd='.'):
        return engineering.execute_check(self.project, dict(argv=argv, timeout=timeout, cwd=cwd))

    def test_real_command_exit_and_combined_output_are_captured(self):
        result = self.check([sys.executable, '-c', 'import sys; print("fixture stdout"); print("fixture stderr", file=sys.stderr); sys.exit(3)'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['exit_code'], 3)
        self.assertIn('fixture stdout', result['output'])
        self.assertIn('fixture stderr', result['output'])
        self.assertEqual(len(result['output_sha256']), 64)

    def test_unavailable_executable_is_not_run_never_passed(self):
        result = self.check([str(self.project / 'not-an-executable')])
        self.assertEqual(result['status'], 'not_run')
        self.assertIsNone(result['exit_code'])

    def test_timeout_is_not_reported_as_success(self):
        result = self.check([sys.executable, '-c', 'import time; time.sleep(5)'], timeout=1)
        self.assertEqual(result['status'], 'timeout')
        self.assertIsNone(result['exit_code'])

    def test_output_truncation_retains_digest_of_full_output(self):
        result = self.check([sys.executable, '-c', 'print("x" * 1000001)'])
        self.assertEqual(result['status'], 'passed')
        self.assertTrue(result['output_truncated'])
        self.assertEqual(len(result['output']), 1000000)
        self.assertEqual(result['output_sha256'], business.digest(b'x' * 1000001 + b'\n'))

    def test_working_directory_cannot_escape_project(self):
        with self.assertRaises(business.BusinessError) as caught:
            self.check([sys.executable, '-c', 'pass'], cwd='..')
        self.assertEqual(caught.exception.code, 'E_IMPLEMENTATION_BOUNDARY')
