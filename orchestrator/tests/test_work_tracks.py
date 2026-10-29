"""Engineering/QA fork fixtures. Human identities and decisions are fictional test data.

These tests never mutate the external conversational acceptance scenario or simulate
Product Owner consent for an actual business request.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

import test_analysis_approval as fixtures
import business_refinement as business
import engineering
import local_identity
import sdlc
import work_tracks


class WorkTrackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.AnalysisApprovalTests('test_exact_baseline_binding_and_separate_advancement')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.project, self.directory = self.fixture.project, self.fixture.directory
        self.counter = 0

    def epic(self):
        return sdlc.selected_epic(self.project, 'REQ-0001')

    def fork(self):
        approved = self.fixture.approve()
        advanced = self.fixture.advance()
        return approved, advanced

    def current(self):
        return work_tracks.current(self.epic().metadata)

    def request(self, action='assign', track='engineering', assignee='Fixture Engineering Lead', **changes):
        self.counter += 1
        expected = (engineering.review(self.epic(), self.project)['revision'] if action == 'adopt'
                    else work_tracks.revision(self.epic(), track, self.project))
        return dict(project=self.project, epic_id='REQ-0001', expected_revision=expected,
                    operation_id=f'work-track-fixture-{self.counter}', action=action, track=track,
                    actor='Fixture Requester', decision=f'Fixture: explicitly {action} {track}.',
                    assignee=assignee, **changes)

    def update(self, **request):
        return work_tracks.update(**request)

    def reject(self, code, action):
        try:
            action()
        except business.BusinessError as exc:
            self.assertEqual(exc.code, code, str(exc))
        except sdlc.Rejected as exc:
            self.assertIn(code, {d.code for d in exc.diagnostics})
        else:
            self.fail('Expected ' + code)

    def files(self):
        return {str(p.relative_to(self.project)):p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def legacy(self):
        """Construct a historical pre-fork fixture; no production migration is implied."""
        self.fork()
        path = self.directory/'metadata.yaml'
        metadata = yaml.safe_load(path.read_text())
        metadata.pop('work_tracks')
        path.write_text(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True))
        return self.epic()

    def design_document(self):
        items, unresolved = engineering.analysis_items(self.epic())
        result={'content':'Fixture design from approved Analysis; no extra business behavior.',
                'coverage':{rid:{'disposition':'blocked' if state in ('blocked','proposed') else 'implemented',
                                 'reason':'Preserve approved Analysis disposition.'}
                            for rid,state in items.items()},
                'unresolved':[{'id':item['id'],'text':item['text']} for item in unresolved]}
        if engineering.governed(self.epic()):result['governance']={'schema_version':'0.1','prototype_limitations':[]}
        return result

    def engineering_write(self, action, kind, payload):
        self.counter += 1
        if action=='write' and kind=='plan' and engineering.governed(self.epic()):
            payload=deepcopy(payload);payload.pop('governance',None);payload['limitation_refs']=[]
        return engineering.update(self.project,'REQ-0001',engineering.review(self.epic(),self.project)['revision'],
                                  f'legacy-engineering-fixture-{self.counter}',action,kind,payload,
                                  'Fixture Engineering Lead',f'Fixture: {action} {kind}.')

    def test_no_tracks_before_explicit_analysis_approval_and_advancement(self):
        self.assertNotIn('work_tracks',self.epic().metadata)
        self.reject('E_APPROVAL_REQUIRED',lambda:self.fixture.advance('AD-0001'))
        self.assertNotIn('work_tracks',self.epic().metadata)
        self.fixture.approve()
        self.assertNotIn('work_tracks',self.epic().metadata)
        self.assertEqual(self.epic().metadata['status'],'functional_analysis')

    def test_explicit_advancement_atomically_creates_two_tracks_on_same_baseline(self):
        approved,advanced = self.fork()
        epic = self.epic()
        tracks = self.current()
        self.assertEqual(tracks['id'],epic.metadata['lifecycle'][-1]['id'])
        self.assertEqual(tracks['analysis_baseline'],approved['baseline_id'])
        self.assertEqual(tracks['origin'],'advance')
        self.assertEqual(epic.metadata['status'],'ready_for_technical_design')
        self.assertEqual(tracks['qa']['status'],'ready_for_test_design')
        self.assertEqual(tracks['qa']['history'],[])
        self.assertEqual(epic.metadata.get('engineering_history',[]),[])
        owner = advanced['epic']['ownership']['owner']
        for name,role in [('engineering','Engineering Lead'),('qa','QA Lead / Tester')]:
            value=tracks[name]['ownership']
            self.assertEqual(value['owner'],owner)
            self.assertIsNone(value['assignee'])
            self.assertEqual(value['required_role'],role)
            self.assertEqual(value['assignment_status'],'awaiting_assignment')
        self.assertEqual({p.name for p in self.directory.iterdir()} & {'technical-design.md','implementation-plan.md','test-strategy.md','test-scenarios.md'},set())

    def test_both_pending_roles_are_visible_without_starting_work(self):
        self.fork()
        before=self.files()
        rows=sdlc.ownership_overview(self.project,'pending-assignments')['pending_assignments']
        self.assertEqual(len(rows),2)
        self.assertEqual({r['track'] for r in rows},{'engineering','qa'})
        self.assertEqual({r['required_role'] for r in rows},{'Engineering Lead','QA Lead / Tester'})
        self.assertTrue(all(r['assignee'] is None and r['assignment_status']=='awaiting_assignment' for r in rows))
        self.assertEqual(before,self.files())

    def test_requester_inbox_keeps_both_pending_handoffs(self):
        self.fork()
        owner=self.current()['engineering']['ownership']['owner']
        with tempfile.TemporaryDirectory() as area,patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(Path(area)/'identity.json')}):
            local_identity.save(self.project,owner,['Informational fixture role'])
            inbox=sdlc.ownership_overview(self.project,'inbox')
            self.assertEqual(inbox['assigned_work'],[])
            self.assertEqual({r['track'] for r in inbox['awaiting_handoff']},{'engineering','qa'})

    def test_assignments_transfer_only_selected_track_and_preserve_other_revision(self):
        self.fork()
        qa_before=deepcopy(self.current()['qa'])
        qa_token=work_tracks.revision(self.epic(),'qa',self.project)
        self.update(**self.request())
        current=self.current()
        self.assertEqual(current['engineering']['ownership']['owner'],'Fixture Engineering Lead')
        self.assertEqual(current['qa'],qa_before)
        self.assertEqual(work_tracks.revision(self.epic(),'qa',self.project),qa_token)
        eng_token=work_tracks.revision(self.epic(),'engineering',self.project)
        self.update(**self.request(track='qa',assignee='Fixture QA Lead'))
        current=self.current()
        self.assertEqual(current['qa']['ownership']['owner'],'Fixture QA Lead')
        self.assertEqual(current['engineering']['ownership']['owner'],'Fixture Engineering Lead')
        self.assertEqual(work_tracks.revision(self.epic(),'engineering',self.project),eng_token)
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')
        self.assertEqual(current['qa']['status'],'ready_for_test_design')

    def test_recipient_inbox_and_pending_list_keep_other_track_visible(self):
        self.fork()
        self.update(**self.request(track='qa',assignee='Fixture QA Lead'))
        pending=sdlc.ownership_overview(self.project,'pending-assignments')['pending_assignments']
        self.assertEqual([r['track'] for r in pending],['engineering'])
        with tempfile.TemporaryDirectory() as area,patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(Path(area)/'identity.json')}):
            local_identity.save(self.project,'Fixture QA Lead',['Tester'])
            inbox=sdlc.ownership_overview(self.project,'inbox')
            self.assertEqual([r['track'] for r in inbox['assigned_work']],['qa'])
            self.assertEqual(inbox['awaiting_handoff'],[])

    def test_read_only_status_is_unambiguous_but_actions_require_track_selection(self):
        self.fork()
        before=self.files()
        status=sdlc.command_context(self.project,'status','REQ-0001')
        self.assertTrue(status['ok'])
        for command in ('start','review','approve','advance','assign'):
            self.reject('E_TRACK_AMBIGUOUS',lambda command=command:sdlc.command_context(self.project,command,'REQ-0001'))
        self.assertEqual(before,self.files())

    def test_start_routes_are_track_specific_and_do_not_execute(self):
        self.fork()
        before=self.files()
        engineering_context=sdlc.command_context(self.project,'start','REQ-0001',track='engineering')
        qa_context=sdlc.command_context(self.project,'start','REQ-0001',track='qa')
        self.assertTrue(engineering_context['ok'])
        self.assertTrue(qa_context['ok'])
        self.assertNotEqual(engineering_context['routing']['write_operation'],qa_context['routing']['write_operation'])
        self.assertIsNotNone(engineering_context['routing']['write_operation'])
        self.assertIsNotNone(qa_context['routing']['write_operation'])
        self.assertEqual(before,self.files())
        self.assertEqual(self.current()['qa']['history'],[])

    def test_engineering_design_progression_keeps_qa_state_and_revision_unchanged(self):
        self.fork()
        before=deepcopy(self.current()['qa'])
        token=work_tracks.revision(self.epic(),'qa',self.project)
        self.engineering_write('write','design',self.design_document())
        self.assertEqual(self.epic().metadata['status'],'technical_design')
        self.assertEqual(self.current()['qa'],before)
        self.assertEqual(work_tracks.revision(self.epic(),'qa',self.project),token)

    def test_engineering_plan_approval_does_not_require_qa_scenarios(self):
        self.fork()
        design=self.design_document()
        self.engineering_write('write','design',design)
        self.engineering_write('approve','design',{'acknowledged':[i['id'] for i in design['unresolved']]})
        self.engineering_write('advance','design',{})
        plan=deepcopy(design)
        plan.update(tasks=[{'id':'T-001','description':'Fixture Engineering-only work and unit checks.','requirements':['FR-001','AC-001'],'depends_on':[],'paths':['app.py','unit.py']}],
                    checks=[{'id':kind,'category':kind,'argv':[sys.executable,'-c','pass'],'cwd':'.','timeout':10,'requirements':['AC-001'],'scenario':'Engineering-only fixture check.'} for kind in ('unit','build')])
        self.engineering_write('write','plan',plan)
        self.engineering_write('approve','plan',{'acknowledged':[i['id'] for i in plan['unresolved']]})
        self.assertTrue(engineering.review(self.epic(),self.project)['approvals']['plan']['valid'])
        self.assertEqual(self.current()['qa']['history'],[])
        self.assertEqual(self.current()['qa']['status'],'ready_for_test_design')

    def test_track_assignments_replay_exactly_without_restoring_old_owner(self):
        self.fork()
        request=self.request(track='qa',assignee='Fixture QA One')
        self.update(**request)
        before=self.files()
        self.assertTrue(self.update(**request)['replayed'])
        self.assertEqual(before,self.files())
        self.update(**self.request(track='qa',assignee='Fixture QA Two'))
        self.assertTrue(self.update(**request)['replayed'])
        self.assertEqual(self.current()['qa']['ownership']['owner'],'Fixture QA Two')
        self.reject('E_IDEMPOTENCY',lambda:self.update(**{**request,'assignee':'Fixture QA Three'}))
        self.reject('E_IDEMPOTENCY',lambda:self.update(**{**request,'decision':'Other fixture words.'}))

    def test_pending_assignment_detects_stale_own_track_but_not_other_track_change(self):
        self.fork()
        eng=self.request()
        qa=self.request(track='qa',assignee='Fixture QA Lead')
        self.update(**qa)
        self.assertTrue(self.update(**eng)['ok'])
        stale=self.request(track='qa',assignee='Fixture Stale')
        self.update(**self.request(track='qa',assignee='Fixture Current'))
        self.reject('E_REVISION_CONFLICT',lambda:self.update(**stale))

    def test_same_track_concurrent_assignments_cannot_both_commit(self):
        self.fork()
        first=self.request(track='qa',assignee='Fixture QA One')
        second={**self.request(track='qa',assignee='Fixture QA Two'),'expected_revision':first['expected_revision']}
        def run(request):
            try:return self.update(**request)
            except business.BusinessError as exc:return {'ok':False,'code':exc.code}
            except sdlc.Rejected as exc:return {'ok':False,'code':exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,(first,second)))
        self.assertEqual(sum(r['ok'] for r in results),1)
        self.assertIn(next(r['code'] for r in results if not r['ok']),('E_PROJECT_BUSY','E_REVISION_CONFLICT'))

    def test_interrupted_track_assignment_is_atomic_and_exact_retry_recovers(self):
        self.fork()
        request=self.request(track='qa',assignee='Fixture QA Lead')
        before=self.files()
        with patch.object(sdlc,'atomic_history_write',side_effect=OSError('Fixture precommit failure')):
            with self.assertRaises(OSError):self.update(**request)
        self.assertEqual(before,self.files())
        self.assertTrue(self.update(**request)['ok'])
        self.assertTrue(self.update(**request)['replayed'])

    def test_post_commit_uncertainty_replays_track_assignment_once(self):
        self.fork()
        request=self.request(track='qa',assignee='Fixture QA Lead')
        real=sdlc.atomic_history_write
        def lost_response(*args):
            real(*args)
            raise sdlc.Rejected([sdlc.error('E_WRITE_UNCERTAIN',self.directory/'metadata.yaml','Fixture lost assignment response.')])
        with patch.object(sdlc,'atomic_history_write',side_effect=lost_response):
            self.reject('E_WRITE_UNCERTAIN',lambda:self.update(**request))
        saved=deepcopy(self.current()['qa']['ownership'])
        self.assertTrue(self.update(**request)['replayed'])
        self.assertEqual(self.current()['qa']['ownership'],saved)
        self.assertEqual(len(saved['history']),2)

    def test_assignment_attribution_must_match_its_management_decision(self):
        self.fork()
        self.update(**self.request(track='qa',assignee='Fixture QA Lead'))
        data=deepcopy(self.epic().metadata)
        work_tracks.current(data)['qa']['ownership']['history'][-1]['actor']='Unrecorded fixture actor'
        self.reject('E_WORK_TRACKS',lambda:work_tracks.validate(data))

    def test_automatic_fork_must_match_explicit_analysis_advancement(self):
        self.fork()
        data=deepcopy(self.epic().metadata)
        data['work_tracks']['operations'][0]['actor']='Unrecorded fixture actor'
        self.reject('E_APPROVAL_AUDIT',lambda:work_tracks.validate(data))

    def test_malformed_track_inputs_return_diagnostics_without_partial_changes(self):
        self.fork()
        before=self.files()
        for changes in ({'track':[]},{'assignee':{}},{'actor':''},{'decision':''}):
            request={**self.request(track='qa',assignee='Fixture QA Lead'),**changes}
            self.reject('E_UPDATE_INPUT',lambda request=request:self.update(**request))
        self.assertEqual(before,self.files())

    def test_legacy_reads_do_not_materialize_tracks_and_explicit_adoption_preserves_history(self):
        self.legacy()
        design=self.design_document()
        self.engineering_write('write','design',design)
        self.engineering_write('approve','design',{'acknowledged':[i['id'] for i in design['unresolved']]})
        self.engineering_write('advance','design',{})
        plan=deepcopy(design)
        plan.update(tasks=[{'id':'T-001','description':'Fixture combined plan task.','requirements':['FR-001','AC-001'],'depends_on':[],'paths':['app.py','checks.py']}],
                    checks=[{'id':kind,'category':kind,'argv':[sys.executable,'-c','pass'],'cwd':'.','timeout':10,'requirements':['AC-001'],'scenario':'Fictional combined-plan check.'} for kind in ('unit','build','integration','ui')])
        self.engineering_write('write','plan',plan)
        before=self.epic()
        baseline_files={str(p.relative_to(self.directory)):p.read_bytes() for p in (self.directory/'engineering-baselines').rglob('*') if p.is_file()}
        self.assertNotIn('work_tracks',before.metadata)
        self.assertNotIn('work_tracks',self.epic().metadata)
        self.update(**self.request(action='adopt',track=None,assignee=None))
        after=self.epic()
        self.assertEqual(after.metadata['engineering_history'],before.metadata['engineering_history'])
        self.assertEqual(after.metadata['lifecycle'],before.metadata['lifecycle'])
        self.assertTrue(engineering.review(after,self.project)['approvals']['design']['valid'])
        self.assertEqual(self.current()['origin'],'adopt')
        self.assertEqual(self.current()['qa']['history'],[])
        self.assertEqual(self.current()['qa']['status'],'ready_for_test_design')
        self.assertEqual(baseline_files,{str(p.relative_to(self.directory)):p.read_bytes() for p in (self.directory/'engineering-baselines').rglob('*') if p.is_file()})
        self.reject('E_TRACK_RECONCILIATION',lambda:self.engineering_write('approve','plan',{'acknowledged':[i['id'] for i in plan['unresolved']]}))

    def test_upstream_reopening_retains_track_history_and_deactivates_both(self):
        self.fork()
        self.update(**self.request(track='qa',assignee='Fixture QA Lead'))
        before=deepcopy(self.epic().metadata['work_tracks'])
        self.fixture.business_fixture.reopen()
        after=self.epic()
        self.assertEqual(after.metadata['work_tracks'],before)
        self.reject('E_TRACK_RECONCILIATION',lambda:work_tracks.active(after))
        self.assertEqual(after.metadata['status'],'discovery')

    def test_analysis_advancement_exact_retry_keeps_one_fork(self):
        self.fixture.approve()
        request=self.fixture.request('advance',approval_id=self.fixture.review()['analysis_approval']['latest_decision']['id'])
        first=self.fixture.execute(request)
        before=deepcopy(self.epic().metadata['work_tracks'])
        retry=self.fixture.execute(request)
        self.assertTrue(retry['replayed'])
        self.assertEqual(self.epic().metadata['work_tracks'],before)
        self.assertEqual(len(before['cycles']),1)
        self.assertEqual(first['epic']['metadata']['status'],'ready_for_technical_design')

    def test_interrupted_analysis_advancement_creates_neither_partial_track(self):
        self.fixture.approve()
        request=self.fixture.request('advance',approval_id=self.fixture.review()['analysis_approval']['latest_decision']['id'])
        before=self.files()
        with patch.object(sdlc,'atomic_history_write',side_effect=OSError('Fixture interrupted fork publication')):
            with self.assertRaises(OSError):self.fixture.execute(request)
        self.assertEqual(before,self.files())
        self.assertNotIn('work_tracks',self.epic().metadata)
        self.fixture.execute(request)
        self.assertEqual(self.current()['qa']['status'],'ready_for_test_design')
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')

    def test_new_analysis_cycle_requires_separate_impact_reconciliation_for_both_tracks(self):
        self.fork()
        old=deepcopy(self.current())
        original=self.epic().analysis['content']
        upstream=self.fixture.business_fixture
        upstream.reopen()
        upstream.complete()
        upstream.revise(upstream.initial_document,mode='generate')
        upstream.approve()
        upstream.advance()
        view=self.fixture.review()
        old_baseline=next(line[10:] for line in original.splitlines() if line.startswith('Baseline: '))
        old_approval=next(line[10:] for line in original.splitlines() if line.startswith('Approval: '))
        old_handoff=next(line[9:] for line in original.splitlines() if line.startswith('Handoff: '))
        changed=original.replace('Baseline: '+old_baseline,'Baseline: '+view['input']['baseline_id'])
        changed=changed.replace('Approval: '+old_approval,'Approval: '+view['input']['approval_id'])
        changed=changed.replace('Handoff: '+old_handoff,'Handoff: '+view['input']['handoff_id'])
        self.fixture.revise(changed)
        self.fixture.approve()
        self.fixture.advance()
        metadata=self.epic().metadata
        self.assertEqual(len(metadata['work_tracks']['cycles']),2)
        self.assertEqual(metadata['work_tracks']['cycles'][0],old)
        self.assertNotEqual(self.current()['id'],old['id'])
        for track in ('engineering','qa'):
            self.reject('E_TRACK_RECONCILIATION',lambda track=track:work_tracks.require_reconciled(self.epic(),track))
        self.update(**self.request(action='reconcile',track='engineering',assignee=None))
        work_tracks.require_reconciled(self.epic(),'engineering')
        self.reject('E_TRACK_RECONCILIATION',lambda:work_tracks.require_reconciled(self.epic(),'qa'))
        self.update(**self.request(action='reconcile',track='qa',assignee=None))
        work_tracks.require_reconciled(self.epic(),'qa')
        self.assertEqual(self.current()['qa']['history'],[])
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')
