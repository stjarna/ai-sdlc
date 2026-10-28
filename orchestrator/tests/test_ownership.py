"""Disposable ownership scenarios; all names and human decisions are explicit test fixtures."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
import test_business_approval as business_fixtures
import test_functional_analysis as analysis_fixtures
import sdlc
import ownership
import local_identity

SCRIPT=Path(sdlc.__file__)


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.area=Path(temporary.name);self.project=self.area/'project';self.project.mkdir()
        self.profile=self.area/'identity.json'
        env=patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(self.profile)})
        env.start();self.addCleanup(env.stop)
        local_identity.save(self.project,'Fixture Alice',['Requester'])
        self.created=sdlc.new_epic(self.project,'Request visibility','People need to track requests.')
        self.directory=Path(self.created['epic']['directory'])
        self.counter=0

    def unique(self):
        self.counter+=1
        return f'ownership-fixture-{self.counter}'

    def opened(self):
        return sdlc.inspect_epics(self.project,'open','REQ-0001')['epic']

    def reject(self,code,action):
        with self.assertRaises(sdlc.Rejected) as caught:action()
        self.assertIn(code,{d.code for d in caught.exception.diagnostics})

    def complete(self):
        epic=self.opened()
        if epic['discovery'] is None:
            sdlc.discovery_update(self.project,'REQ-0001',epic['revision'],self.unique(),[business_fixtures.record('user_statement','People need visibility of requests.')])
        epic=self.opened()
        return sdlc.lifecycle_change(self.project,'REQ-0001',epic['revision'],self.unique(),'Fixture Alice','Fixture: complete Discovery.','complete',identity_source='local_profile')

    def request(self,assignee='Fixture John',**extra):
        return dict(project=self.project,epic_id='REQ-0001',expected_revision=self.opened()['revision'],operation_id=self.unique(),actor='Fixture Alice',decision='Fixture: Yes, assign the request to this named person.',assignee=assignee,identity_source='local_profile',**extra)

    def assign(self,assignee='Fixture John'):
        return sdlc.ownership_change(**self.request(assignee))

    def switch_profile(self,name):
        profile=local_identity.load(self.project)
        local_identity.save(self.project,name,None,edit=True,expected_revision=profile['profile_revision'])

    def snapshot(self):
        return {str(p.relative_to(self.project)):p.read_bytes() for p in self.project.rglob('*') if p.is_file()}

    def test_new_request_owned_by_requester_and_visible_as_assigned_work(self):
        value=self.created['epic']['ownership']
        self.assertEqual(value['owner'],'Fixture Alice')
        self.assertEqual(value['assignee'],'Fixture Alice')
        self.assertEqual(value['required_role'],'Requester / Business Stakeholder')
        self.assertEqual(value['assignment_status'],'assigned')
        self.assertEqual(value['history'][0]['identity_source'],'local_profile')
        inbox=sdlc.ownership_overview(self.project,'inbox')
        self.assertEqual([r['id'] for r in inbox['assigned_work']],['REQ-0001'])
        self.assertEqual(inbox['awaiting_handoff'],[])

    def test_explicit_requester_supported_without_local_profile(self):
        self.profile.unlink()
        created=sdlc.new_epic(self.project,'Another request','Another business idea.',requester='Fixture Requester')
        self.assertEqual(created['epic']['ownership']['owner'],'Fixture Requester')
        self.assertEqual(created['epic']['ownership']['history'][0]['identity_source'],'declared')

    def test_missing_identity_cannot_create_an_unowned_request(self):
        self.profile.unlink();before=self.snapshot()
        with self.assertRaises(local_identity.IdentityError) as caught:sdlc.new_epic(self.project,'New request')
        self.assertEqual(caught.exception.code,'E_IDENTITY_MISSING')
        self.assertEqual(self.snapshot(),before)

    def test_handoff_keeps_owner_while_next_assignee_is_unknown(self):
        completed=self.complete()['epic']
        self.assertEqual(completed['metadata']['status'],'ready_for_refinement')
        value=completed['ownership']
        self.assertEqual(value['owner'],'Fixture Alice')
        self.assertIsNone(value['assignee'])
        self.assertEqual(value['assignment_status'],'awaiting_assignment')
        self.assertEqual(value['target_stage'],'business_refinement')
        self.assertEqual(value['required_role'],'Product Owner')
        self.assertFalse((self.directory/'business.md').exists())
        self.assertEqual(value['history'][-1]['lifecycle_id'],completed['metadata']['lifecycle'][-1]['id'])
        self.assertEqual(value['history'][-1]['timestamp'],completed['metadata']['lifecycle'][-1]['timestamp'])
        self.assertEqual(sdlc.ownership_overview(self.project,'inbox')['assigned_work'],[])
        self.assertEqual(len(sdlc.ownership_overview(self.project,'inbox')['awaiting_handoff']),1)

    def test_successful_assignment_transfers_owner_without_advancing(self):
        self.complete();before=self.opened()
        assigned=self.assign()['epic'];value=assigned['ownership']
        self.assertEqual(value['owner'],'Fixture John')
        self.assertEqual(value['assignee'],'Fixture John')
        self.assertEqual(value['required_role'],'Product Owner')
        self.assertEqual(value['assignment_status'],'assigned')
        self.assertEqual(assigned['metadata']['status'],'ready_for_refinement')
        self.assertEqual(assigned['metadata']['lifecycle'],before['metadata']['lifecycle'])
        self.assertEqual(value['history'][:-1],before['ownership']['history'])
        self.assertEqual(value['history'][-1]['from_owner'],'Fixture Alice')
        self.assertEqual(value['history'][-1]['actor'],'Fixture Alice')
        self.assertEqual(sdlc.ownership_overview(self.project,'pending-assignments')['pending_assignments'],[])
        self.assertEqual(sdlc.ownership_overview(self.project,'inbox')['awaiting_handoff'],[])
        self.switch_profile('Fixture John')
        self.assertEqual(len(sdlc.ownership_overview(self.project,'inbox')['assigned_work']),1)
        self.assertFalse((self.directory/'business.md').exists())

    def test_missing_recipient_and_missing_confirmation_never_transfer_owner(self):
        self.complete();before=self.snapshot()
        for extra in ({'assignee':None},{'assignee':''},{'decision':''}):
            self.reject('E_UPDATE_INPUT',lambda:sdlc.ownership_change(**{**self.request(),**extra}))
        self.assertEqual(before,self.snapshot())
        self.assertEqual(self.opened()['ownership']['owner'],'Fixture Alice')

    def test_reassignment_and_exact_human_wording_preserved(self):
        self.complete();self.assign()
        words='Fixture confirmation:\nYes, assign this request to Fixture Mary as Product Owner.'
        assigned=sdlc.ownership_change(**{**self.request('Fixture Mary'),'decision':words})['epic']
        self.assertEqual(assigned['ownership']['owner'],'Fixture Mary')
        self.assertEqual(assigned['ownership']['history'][-1]['from_owner'],'Fixture John')
        self.assertEqual(assigned['ownership']['history'][-1]['decision'],words)
        self.assertEqual(len(assigned['ownership']['history']),4)

    def test_inbox_and_project_pending_are_read_only_and_filter_by_declared_name(self):
        self.complete()
        other=sdlc.new_epic(self.project,'Other request','Another idea.',requester='Fixture Other')['epic']
        sdlc.discovery_update(self.project,other['metadata']['id'],other['revision'],self.unique(),[business_fixtures.record('user_statement','Other fixture statement.')])
        other=sdlc.inspect_epics(self.project,'open',other['metadata']['id'])['epic']
        sdlc.lifecycle_change(self.project,other['metadata']['id'],other['revision'],self.unique(),'Fixture Other','Fixture: complete Discovery.','complete')
        before=self.snapshot()
        inbox=sdlc.command_context(self.project,'inbox')
        self.assertEqual([r['id'] for r in inbox['awaiting_handoff']],['REQ-0001'])
        pending=sdlc.command_context(self.project,'pending assignments')['pending_assignments']
        self.assertEqual({r['owner'] for r in pending},{'Fixture Alice','Fixture Other'})
        self.assertTrue(all(r['required_role']=='Product Owner' and r['target_stage']=='business_refinement' for r in pending))
        self.assertEqual(before,self.snapshot())

    def test_time_awaiting_is_derived_without_sla_or_state_changes(self):
        with patch.object(sdlc.business,'timestamp',return_value='2026-10-28T12:00:00Z'):self.complete()
        epic=sdlc.selected_epic(self.project,'REQ-0001')
        row=ownership.row(epic,now=datetime(2026,10,28,13,0,tzinfo=timezone.utc))
        self.assertEqual(row['time_awaiting_seconds'],3600)
        self.assertEqual(row['responsibility'],'Accountable owner awaiting handoff')
        self.assertNotIn('sla',row)

    def test_stale_assignment_and_stage_change_rejected(self):
        request=self.request()
        self.complete()
        self.reject('E_REVISION_CONFLICT',lambda:sdlc.ownership_change(**request))
        request=self.request();self.assign('Fixture Other')
        self.reject('E_REVISION_CONFLICT',lambda:sdlc.ownership_change(**request))

    def test_concurrent_assignments_cannot_both_commit(self):
        self.complete();first=self.request();second={**self.request('Fixture Other'),'expected_revision':first['expected_revision']}
        def run(request):
            try:return sdlc.ownership_change(**request)
            except sdlc.Rejected as e:return {'ok':False,'code':e.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,(first,second)))
        self.assertEqual(sum(r['ok'] for r in results),1)
        self.assertIn(next(r['code'] for r in results if not r['ok']),('E_PROJECT_BUSY','E_REVISION_CONFLICT'))
        self.assertEqual(len(self.opened()['ownership']['history']),3)

    def test_idempotent_retries_never_restore_an_older_owner(self):
        self.complete();request=self.request();sdlc.ownership_change(**request)
        before=self.snapshot()
        self.assertTrue(sdlc.ownership_change(**request)['replayed'])
        self.assertEqual(before,self.snapshot())
        self.assign('Fixture Mary')
        replay=sdlc.ownership_change(**request)
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['epic']['ownership']['owner'],'Fixture Mary')
        for field,value in (('assignee','Other'),('decision','Other words'),('actor','Other actor'),('expected_revision','0'*64)):
            self.reject('E_IDEMPOTENCY',lambda:sdlc.ownership_change(**{**request,field:value}))

    def test_assignment_operation_cannot_be_reused_for_discovery_transition(self):
        request=self.request();sdlc.ownership_change(**request)
        epic=self.opened()
        self.reject('E_IDEMPOTENCY',lambda:sdlc.lifecycle_change(self.project,'REQ-0001',epic['revision'],request['operation_id'],'Fixture Alice','Fixture complete','complete'))

    def test_assignment_failure_and_post_commit_uncertainty_are_recoverable(self):
        self.complete();request=self.request();before=self.snapshot()
        with patch.object(sdlc.os,'replace',side_effect=OSError('Fixture precommit failure')):
            with self.assertRaises(OSError):sdlc.ownership_change(**request)
        self.assertEqual(before,self.snapshot())
        real=sdlc.atomic_history_write
        def lost_response(*args):
            real(*args)
            raise sdlc.Rejected([sdlc.error('E_WRITE_UNCERTAIN',self.directory/'metadata.yaml','Fixture lost response')])
        with patch.object(sdlc,'atomic_history_write',side_effect=lost_response):
            self.reject('E_WRITE_UNCERTAIN',lambda:sdlc.ownership_change(**request))
        self.assertTrue(sdlc.ownership_change(**request)['replayed'])
        self.assertEqual(self.opened()['ownership']['owner'],'Fixture John')

    def test_handoff_is_atomic_with_transition_even_if_response_is_lost(self):
        epic=self.opened();sdlc.discovery_update(self.project,'REQ-0001',epic['revision'],self.unique(),[business_fixtures.record('user_statement','Fixture business need.')])
        epic=self.opened();op=self.unique();real=sdlc.atomic_history_write
        def lost_response(*args):
            real(*args)
            raise sdlc.Rejected([sdlc.error('E_WRITE_UNCERTAIN',self.directory/'metadata.yaml','Fixture lost response')])
        args=(self.project,'REQ-0001',epic['revision'],op,'Fixture Alice','Fixture complete Discovery','complete')
        with patch.object(sdlc,'atomic_history_write',side_effect=lost_response):self.reject('E_WRITE_UNCERTAIN',lambda:sdlc.lifecycle_change(*args))
        after=self.opened()
        self.assertEqual(after['metadata']['status'],'ready_for_refinement')
        self.assertEqual(after['ownership']['assignment_status'],'awaiting_assignment')
        self.assertTrue(sdlc.lifecycle_change(*args)['replayed'])
        self.assertEqual(len(self.opened()['ownership']['history']),2)

    def test_history_corruption_and_invalid_node_types_rejected(self):
        self.complete();path=self.directory/'metadata.yaml';original=path.read_bytes()
        for change in ('owner','required_role','history_owner','history_role'):
            data=yaml.safe_load(original)
            if change=='owner':data['ownership']['owner']='Tampered'
            elif change=='required_role':data['ownership']['required_role']='Unknown role'
            elif change=='history_owner':data['ownership']['history'][-1]['from_owner']='Tampered'
            else:data['ownership']['history'][-1]['target_stage']=[]
            path.write_text(yaml.safe_dump(data,sort_keys=False))
            self.reject('E_OWNERSHIP',self.opened)
        path.write_bytes(original)

    def test_assignment_does_not_change_business_or_original_content(self):
        self.complete();before={p.name:p.read_bytes() for p in self.directory.iterdir() if p.is_file() and p.name!='metadata.yaml'}
        self.assign()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.directory.iterdir() if p.is_file() and p.name!='metadata.yaml'})

    def test_fresh_cli_inbox_pending_and_assignment_use_profile(self):
        self.complete()
        def cli(*args):
            p=subprocess.run([sys.executable,str(SCRIPT),'--project',str(self.project),*args],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            return json.loads(p.stdout)
        inbox=cli('inbox');self.assertEqual(len(inbox['awaiting_handoff']),1)
        context=cli('command-context','assign')['review']['epic']
        self.assertEqual(ownership.view(context['metadata'])['required_role'],'Product Owner')
        result=cli('assign','REQ-0001','--expected-revision',context['revision'],'--operation-id','cli-assignment-fixture','--decision','Fixture: Yes, assign to Fixture John.','--assignee','Fixture John')
        self.assertEqual(result['epic']['ownership']['owner'],'Fixture John')
        self.assertEqual(cli('pending-assignments')['pending_assignments'],[])
        self.switch_profile('Fixture John')
        self.assertEqual([r['id'] for r in cli('inbox')['assigned_work']],['REQ-0001'])
        self.assertEqual(cli('open','REQ-0001')['epic']['ownership'],result['epic']['ownership'])


class LegacyOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.fixture=business_fixtures.BusinessApprovalTests('test_approval_freezes_exact_context_and_advancement_is_separate')
        self.addCleanup(self.fixture.doCleanups);self.fixture.setUp()
        self.project,self.directory=self.fixture.project,self.fixture.directory

    def test_recorded_requester_is_reused_without_read_time_migration(self):
        path=self.directory/'metadata.yaml';before=path.read_bytes()
        epic=self.fixture.view()['epic']
        self.assertNotIn('ownership',epic['metadata'])
        self.assertEqual(epic['ownership']['owner'],'Fixture Requester')
        self.assertEqual(epic['ownership']['assignment_status'],'awaiting_assignment')
        self.assertEqual(path.read_bytes(),before)
        assigned=sdlc.ownership_change(self.project,'REQ-0001',epic['revision'],'legacy-assign','Fixture Actor','Fixture: assign John.','Fixture John')['epic']
        self.assertEqual(assigned['ownership']['history'][0]['to_owner'],'Fixture Requester')
        self.assertEqual(assigned['ownership']['history'][0]['identity_source'],'declared')
        self.assertIn('recorded Requester',assigned['ownership']['history'][0]['decision'])
        self.assertEqual(assigned['ownership']['history'][0]['actor'],'Fixture Actor')
        self.assertEqual(assigned['ownership']['owner'],'Fixture John')

    def test_missing_legacy_requester_requires_explicit_initial_owner(self):
        # Preserve a valid 0.1 record with no historical Requester declaration.
        project=self.project/'legacy-project';project.mkdir()
        created=sdlc.new_epic(project,'Legacy idea','Old idea.',requester='Fixture original')['epic']
        path=Path(created['directory'])/'metadata.yaml';data=yaml.safe_load(path.read_text());data.pop('ownership');path.write_text(yaml.safe_dump(data,sort_keys=False))
        epic=sdlc.inspect_epics(project,'open','REQ-0001')['epic']
        self.assertTrue(epic['ownership']['initialization_required'])
        self.assertIsNone(epic['ownership']['owner'])
        self.fixture.rejected('E_OWNER_REQUIRED',lambda:sdlc.ownership_change(project,'REQ-0001',epic['revision'],'missing-owner','Fixture Actor','Fixture assign.','Fixture John'))
        initialized=sdlc.ownership_change(project,'REQ-0001',epic['revision'],'declare-owner','Fixture Actor','Fixture: Alice was the Requester.','Fixture Alice',initialize=True)
        self.assertEqual(initialized['epic']['ownership']['owner'],'Fixture Alice')
        self.assertTrue(sdlc.ownership_change(project,'REQ-0001',epic['revision'],'declare-owner','Fixture Actor','Fixture: Alice was the Requester.','Fixture Alice',initialize=True)['replayed'])

    def test_multiple_recorded_requesters_remain_ambiguous(self):
        metadata=deepcopy(self.fixture.view()['epic']['metadata'])
        metadata['lifecycle'].append({**metadata['lifecycle'][0],'id':'fixture-reopen','action':'reopen','from':'business_refinement','to':'discovery','actor':'Other Fixture'})
        metadata['status']='discovery'
        self.assertIsNone(ownership.legacy_requester(metadata))
        self.assertTrue(ownership.view(metadata)['initialization_required'])

    def test_assignment_preserves_active_business_approval_and_frozen_baseline(self):
        approved=self.fixture.approve()
        baseline=self.directory/'business-baselines'/approved['baseline_id']
        frozen={p.name:p.read_bytes() for p in baseline.iterdir()}
        before=self.fixture.view()['epic']
        assigned=sdlc.ownership_change(self.project,'REQ-0001',before['revision'],'assign-after-business-approval','Fixture Actor','Fixture: Yes, assign John.','Fixture John')['epic']
        self.assertTrue(assigned['approval']['valid'])
        self.assertEqual(assigned['metadata']['business_decisions'],before['metadata']['business_decisions'])
        self.assertEqual(frozen,{p.name:p.read_bytes() for p in baseline.iterdir()})
        advanced=self.fixture.advance()['epic']
        self.assertEqual(advanced['ownership']['owner'],'Fixture John')
        self.assertIsNone(advanced['ownership']['assignee'])
        self.assertEqual(advanced['ownership']['required_role'],'Business Analyst')
        self.assertTrue(advanced['approval']['valid'])

    def test_approval_does_not_transfer_or_defer_ownership(self):
        before=self.fixture.view()['epic']
        assigned=sdlc.ownership_change(self.project,'REQ-0001',before['revision'],'assign-before-approval','Fixture Actor','Fixture: Yes.','Fixture PO')['epic']
        approved=self.fixture.approve()['epic']
        self.assertEqual(assigned['metadata']['ownership'],approved['metadata']['ownership'])
        self.assertEqual(approved['metadata']['status'],'business_refinement')


class AnalysisOwnershipTests(unittest.TestCase):
    def test_assignment_and_technical_design_handoff_preserve_analysis_approval(self):
        fixture=analysis_fixtures.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        self.addCleanup(fixture.doCleanups);fixture.setUp();fixture.generate()
        project,directory=fixture.project,fixture.directory
        view=fixture.review()
        args=dict(project=project,epic_id='REQ-0001',expected_review=view['analysis_review_revision'],expected_analysis=view['epic']['analysis']['revision'],expected_baseline=view['input']['baseline_id'],expected_handoff=view['input']['handoff_id'],operation_id='analysis-ownership-approval',actor='Fixture PO',reason='Fixture approval',decision='Fixture approve all disclosed uncertainties.',action='approve',acknowledged=[v['id'] for v in view['analysis_open_items']])
        approved=sdlc.analysis_gate(**args)
        baseline=directory/'analysis-baselines'/approved['baseline_id'];frozen={p.name:p.read_bytes() for p in baseline.iterdir()}
        before=approved['epic']
        assigned=sdlc.ownership_change(project,'REQ-0001',before['revision'],'analysis-assignment','Fixture Actor','Fixture: assign Analyst.','Fixture Analyst')['epic']
        self.assertTrue(assigned['analysis_approval']['valid'])
        self.assertTrue(assigned['approval']['valid'])
        self.assertEqual(assigned['metadata']['analysis_decisions'],before['metadata']['analysis_decisions'])
        view=fixture.review()
        advance={**args,'expected_review':view['analysis_review_revision'],'operation_id':'advance-analysis-ownership','reason':'Fixture: advance separately.','decision':'Fixture: advance separately.','action':'advance','acknowledged':[],'approval_id':approved['decision_id']}
        advanced=sdlc.analysis_gate(**advance)['epic']
        self.assertEqual(advanced['metadata']['status'],'ready_for_technical_design')
        self.assertEqual(advanced['ownership']['owner'],'Fixture Analyst')
        self.assertEqual(advanced['ownership']['required_role'],'Engineering Lead / Architect')
        self.assertEqual(advanced['ownership']['assignment_status'],'awaiting_assignment')
        self.assertTrue(advanced['analysis_approval']['valid'])
        self.assertEqual(frozen,{p.name:p.read_bytes() for p in baseline.iterdir()})
        assigned=sdlc.ownership_change(project,'REQ-0001',advanced['revision'],'assign-design-readiness','Fixture Actor','Fixture: assign Architect.','Fixture Architect')['epic']
        self.assertTrue(assigned['analysis_approval']['valid'])
        self.assertEqual(assigned['metadata']['status'],'ready_for_technical_design')
        self.assertFalse((directory/'design.md').exists())

    def test_assignment_preserves_current_and_historical_baseline_ownership_prefix(self):
        fixture=business_fixtures.BusinessApprovalTests('test_approval_freezes_exact_context_and_advancement_is_separate')
        self.addCleanup(fixture.doCleanups);fixture.setUp()
        before=fixture.view()['epic']
        assigned=sdlc.ownership_change(fixture.project,'REQ-0001',before['revision'],'owned-before-baseline','Fixture Actor','Fixture: assign PO.','Fixture PO')['epic']
        fixture.approve()
        sdlc.ownership_change(fixture.project,'REQ-0001',fixture.view()['epic']['revision'],'owned-after-baseline','Fixture Actor','Fixture: assign another PO.','Fixture Other PO')
        self.assertTrue(fixture.view()['approval']['valid'])
        path=fixture.directory/'metadata.yaml';data=yaml.safe_load(path.read_text())
        data['ownership']['history'][0]['decision']='Tampered historical initialization reason'
        path.write_text(yaml.safe_dump(data,sort_keys=False))
        fixture.rejected('E_OWNERSHIP_AUDIT',fixture.view)
