"""Pre-development Plan recovery. Every actor/decision is fictional fixture data."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_engineering as fixtures
import test_qa_track as qa_fixtures

import business_refinement as business
import command_ux
import engineering
import sdlc


class PlanRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.EngineeringTests('test_design_binds_exact_analysis_and_pinned_skills')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.project, self.directory = self.f.project, self.f.directory

    def files(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def ready(self):
        self.f.plan()
        self.f.approve('plan')
        self.f.run_update('advance', 'plan')

    def change_capture(self):
        folder = self.project / 'demo' / 'capture'
        folder.mkdir(parents=True)
        (folder / 'event.json').write_text('{"fixture":"presentation"}\n')

    def test_stale_approval_and_advancement_fail_without_writes(self):
        self.f.plan()
        self.change_capture()
        before = self.files()
        self.f.reject('E_APPROVAL_STALE', lambda: self.f.approve('plan'))
        self.assertEqual(self.files(), before)
        self.f.run_update('write', 'plan', self.f.document('plan'))
        self.f.approve('plan')
        (self.project / 'demo/capture/event.json').write_text('changed fixture capture\n')
        before = self.files()
        self.f.reject('E_APPROVAL_STALE', lambda: self.f.run_update('advance', 'plan'))
        self.assertEqual(self.files(), before)
        self.assertEqual(self.f.epic().metadata['status'], 'implementation_planning')

    def test_replanning_preserves_history_and_requires_fresh_gates(self):
        self.ready()
        old = deepcopy(self.f.epic().metadata)
        retained = {p: raw for p, raw in self.files().items() if '/baselines/' in p or '-baselines/' in p}
        original_plan = self.f.review()['drafts']['plan']['baseline_id']
        original_content = self.f.review()['drafts']['plan']['payload']['content']
        self.change_capture()
        feedback = self.f.request('request_changes', 'plan', {'acknowledged': []})
        feedback['decision'] = 'Fixture human: replan for the reviewed input change.'
        changed = engineering.update(**feedback)
        self.assertEqual(changed['epic']['metadata']['status'], 'implementation_planning')
        metadata = self.f.epic().metadata
        self.assertEqual(metadata['engineering_history'][:-1], old['engineering_history'])
        self.assertEqual(metadata['lifecycle'][:-1], old['lifecycle'])
        self.assertEqual(metadata['business_decisions'], old['business_decisions'])
        self.assertEqual(metadata['analysis_decisions'], old['analysis_decisions'])
        self.assertEqual(metadata['engineering_history'][-1]['decision'], feedback['decision'])
        self.assertFalse(self.f.review()['approvals']['plan']['valid'])
        self.assertTrue(self.f.review()['approvals']['design']['valid'])
        self.assertTrue(self.f.epic().approval['valid'])
        self.assertTrue(self.f.epic().analysis_approval['valid'])
        self.f.reject('E_APPROVAL_REQUIRED', lambda: self.f.run_update('advance', 'plan'))
        self.f.run_update('write', 'plan', self.f.document('plan'))
        self.assertNotEqual(self.f.review()['drafts']['plan']['baseline_id'], original_plan)
        self.assertEqual(self.f.review()['drafts']['plan']['payload']['content'], original_content)
        self.f.reject('E_APPROVAL_REQUIRED', lambda: self.f.run_update('advance', 'plan'))
        self.f.approve('plan')
        self.assertEqual(self.f.epic().metadata['status'], 'implementation_planning')
        self.f.reject('E_STATUS', lambda: self.f.run_update('start', 'development'))
        self.f.run_update('advance', 'plan')
        self.assertTrue(self.f.review()['development_start']['eligible'])
        self.f.run_update('start', 'development')
        self.assertEqual(self.f.epic().metadata['status'], 'development')
        for name, raw in retained.items():
            self.assertEqual((self.project / name).read_bytes(), raw)
        # Planned implementation changes must not retroactively invalidate Plan approval.
        (self.project / 'app.py').write_text('value = 1\n')
        self.assertTrue(self.f.review()['approvals']['plan']['valid'])
        self.assertFalse(self.f.review()['development_start']['eligible'])

    def test_review_exposes_stale_start_without_rewriting_approval(self):
        self.ready()
        before_metadata = (self.directory / 'metadata.yaml').read_bytes()
        self.assertTrue(self.f.review()['development_start']['eligible'])
        self.change_capture()
        review = self.f.review()
        self.assertTrue(review['approvals']['plan']['valid'])
        self.assertFalse(review['development_start']['eligible'])
        self.assertEqual(review['development_start']['code'], 'E_APPROVAL_STALE')
        before = self.files()
        self.f.reject('E_APPROVAL_STALE', lambda: self.f.run_update('start', 'development'))
        self.assertEqual(self.files(), before)
        self.assertEqual((self.directory / 'metadata.yaml').read_bytes(), before_metadata)
        self.assertFalse(engineering.events(self.f.epic(), 'start', 'development'))

    def test_scanner_remains_conservative_and_external_capture_is_safe(self):
        self.ready()
        before = self.f.review()['source_revision']
        with tempfile.TemporaryDirectory() as outside:
            Path(outside, 'presentation.json').write_text('fixture capture')
            self.assertEqual(self.f.review()['source_revision'], before)
        (self.project / '.gitignore').write_text('demo/\n')
        self.f.run_update('request_changes', 'plan', {'acknowledged': []})
        self.f.run_update('write', 'plan', self.f.document('plan'))
        self.f.approve('plan'); self.f.run_update('advance', 'plan')
        before = self.f.review()['source_revision']
        self.change_capture()
        self.assertNotEqual(self.f.review()['source_revision'], before)
        self.assertFalse(self.f.review()['development_start']['eligible'])

    def test_only_plan_feedback_before_development_can_return_to_planning(self):
        self.ready()
        self.f.reject('E_STATUS', lambda: self.f.run_update('request_changes', 'design', {'acknowledged': []}))
        self.f.reject('E_STATUS', lambda: self.f.run_update('write', 'plan', self.f.document('plan')))
        self.f.run_update('start', 'development')
        self.f.reject('E_STATUS', lambda: self.f.run_update('request_changes', 'plan', {'acknowledged': []}))
        self.assertEqual(self.f.epic().metadata['status'], 'development')

    def test_prior_start_guard_rejects_replan_even_if_readiness_is_reported(self):
        self.ready()
        request = self.f.request('request_changes', 'plan', {'acknowledged': []})
        original = engineering.events
        def recorded(epic, action=None, kind=None):
            if action == 'start' and kind == 'development':
                return [{'action': 'start', 'kind': 'development'}]
            return original(epic, action, kind)
        before = self.files()
        with patch.object(engineering, 'events', side_effect=recorded):
            self.f.reject('E_STATUS', lambda: engineering.update(**request))
        self.assertEqual(self.files(), before)

    def test_retry_preserves_wording_and_does_not_repeat_transition(self):
        self.ready()
        request = self.f.request('request_changes', 'plan', {'acknowledged': []})
        first = engineering.update(**request)
        self.f.run_update('write', 'plan', self.f.document('plan'))
        self.f.approve('plan'); self.f.run_update('advance', 'plan')
        before = self.files()
        replay = engineering.update(**request)
        self.assertTrue(replay['replayed'])
        self.assertEqual(self.files(), before)
        self.assertEqual(replay['epic']['metadata']['status'], 'ready_for_development')
        self.assertEqual(sum(e['operation_id'] == request['operation_id'] for e in self.f.epic().metadata['engineering_history']), 1)
        self.f.reject('E_IDEMPOTENCY', lambda: engineering.update(**{**request, 'decision': 'Different fixture intent.'}))
        self.assertEqual(first['epic']['metadata']['engineering_history'][-1]['decision'], request['decision'])

    def test_concurrent_feedback_can_publish_only_one_return(self):
        self.ready()
        first = self.f.request('request_changes', 'plan', {'acknowledged': []})
        second = {**first, 'operation_id': 'other-fixture-replan'}
        def run(request):
            try:
                return engineering.update(**request)['ok']
            except business.BusinessError as exc:
                return exc.code
            except sdlc.Rejected as exc:
                return exc.diagnostics[0].code
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(run, (first, second)))
        self.assertEqual(result.count(True), 1)
        self.assertIn(next(v for v in result if v is not True), ('E_PROJECT_BUSY', 'E_REVISION_CONFLICT'))
        self.assertEqual(self.f.epic().metadata['status'], 'implementation_planning')

    def test_interrupted_replan_preserves_metadata_and_exact_retry_recovers(self):
        self.ready()
        request = self.f.request('request_changes', 'plan', {'acknowledged': []})
        metadata = (self.directory / 'metadata.yaml').read_bytes()
        with patch.object(sdlc, 'atomic_history_write', side_effect=OSError('Injected replan publication failure')):
            with self.assertRaises(OSError): engineering.update(**request)
        self.assertEqual((self.directory / 'metadata.yaml').read_bytes(), metadata)
        self.assertEqual(self.f.epic().metadata['status'], 'ready_for_development')
        self.assertTrue(engineering.update(**request)['ok'])
        self.assertEqual(self.f.epic().metadata['status'], 'implementation_planning')

    def test_source_change_during_approval_cannot_publish_a_decision(self):
        self.f.plan()
        request = self.f.request('approve', 'plan', {'acknowledged': [q['id'] for q in self.f.document('plan')['unresolved']]})
        metadata = (self.directory / 'metadata.yaml').read_bytes()
        original = engineering.common.publish_baseline
        def competing_write(*args, **kwargs):
            baseline = original(*args, **kwargs)
            (self.project / 'app.py').write_text('value = 99\n')
            return baseline
        with patch.object(engineering.common, 'publish_baseline', side_effect=competing_write):
            self.f.reject('E_REVISION_CONFLICT', lambda: engineering.update(**request))
        self.assertEqual((self.directory / 'metadata.yaml').read_bytes(), metadata)
        self.assertFalse(self.f.review()['approvals']['plan']['valid'])

    def test_cli_failure_is_structured_and_recovery_keeps_actual_human_words(self):
        self.ready(); self.change_capture()
        def cli(command, **options):
            revision = self.f.review()['revision']
            args = [sys.executable, '-B', str(Path(sdlc.__file__)), '--project', str(self.project), command, 'REQ-0001',
                    '--expected-engineering-revision', revision, '--operation-id', options.pop('operation_id'),
                    '--actor', 'Fixture Engineer', '--decision', options.pop('decision')]
            for key, value in options.items(): args += ['--' + key.replace('_', '-'), value]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.stderr, '')
            return result.returncode, json.loads(result.stdout)
        before = self.files()
        status, failure = cli('development-start', operation_id='fixture-failed-start', decision='Fixture start.')
        self.assertEqual(status, 1); self.assertFalse(failure['ok'])
        self.assertEqual(failure['diagnostics'][0]['code'], 'E_APPROVAL_STALE')
        self.assertEqual(self.files(), before)
        status, changed = cli('engineering-request-changes', kind='plan', operation_id='fixture-cli-replan', decision='Please replan this exact fixture input change.')
        self.assertEqual(status, 0)
        self.assertEqual(changed['epic']['metadata']['status'], 'implementation_planning')
        self.assertEqual(changed['epic']['metadata']['engineering_history'][-1]['decision'], 'Please replan this exact fixture input change.')
        route = command_ux.route('changes', 'ready_for_development')
        self.assertEqual((route['write_operation'], route['kind']), ('engineering-request-changes', 'plan'))


class ForkPlanRecoveryTests(unittest.TestCase):
    def test_fork_recovery_preserves_independent_qa_and_upstream_approvals(self):
        f = qa_fixtures.QATrackTests('test_qa_design_does_not_require_technical_design')
        f.setUp(); self.addCleanup(f.doCleanups)
        f.design_qa(); f.approve_scenarios(); f.design_engineering()
        plan = f.base()
        plan.update(tasks=[{'id':'T-001','description':'Fixture implementation.','requirements':['FR-001','AC-001'],'depends_on':[],'paths':['app.py','check.py']}],
                    checks=[{'id':kind,'category':kind,'argv':[sys.executable,'-B','check.py'],'cwd':'.','timeout':10,'requirements':['AC-001'],'scenario':'Actual fixture check.'} for kind in ('unit','build')])
        f.eng('write', 'plan', plan)
        f.eng('approve', 'plan', {'acknowledged':[q['id'] for q in plan['unresolved']]})
        f.eng('advance', 'plan')
        old = deepcopy(f.epic().metadata)
        frozen = {p:p.read_bytes() for p in f.directory.rglob('*') if p.is_file() and '-baselines' in str(p)}
        (f.project / 'presentation.md').write_text('Fixture source change.')
        f.eng('request_changes', 'plan', {'acknowledged':[]})
        new = f.epic().metadata
        self.assertEqual(new['work_tracks'], old['work_tracks'])
        self.assertEqual(new['business_decisions'], old['business_decisions'])
        self.assertEqual(new['analysis_decisions'], old['analysis_decisions'])
        self.assertTrue(f.view()['approvals']['scenarios']['valid'])
        self.assertTrue(engineering.review(f.epic(), f.project)['approvals']['design']['valid'])
        self.assertTrue(f.epic().approval['valid']); self.assertTrue(f.epic().analysis_approval['valid'])
        for path, raw in frozen.items(): self.assertEqual(path.read_bytes(), raw)
        f.eng('write', 'plan', plan)
        f.eng('approve', 'plan', {'acknowledged':[q['id'] for q in plan['unresolved']]})
        f.eng('advance', 'plan'); f.eng('start', 'development')
        self.assertEqual(f.epic().metadata['status'], 'development')
        self.assertTrue(f.view()['approvals']['scenarios']['valid'])
