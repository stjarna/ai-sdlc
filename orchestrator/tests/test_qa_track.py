"""Independent QA fixtures. Every actor and decision is explicitly fictional.

Integration/UI categories execute real tiny fixture commands; they are not claims
of browser acceptance or security certification.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_analysis_approval as fixtures
import business_refinement as business
import engineering
from template_fixtures import document_payload
import qa_track
import sdlc
import work_tracks


class QATrackTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.AnalysisApprovalTests('test_exact_baseline_binding_and_separate_advancement')
        self.addCleanup(self.fixture.doCleanups);self.fixture.setUp()
        self.fixture.approve();self.fixture.advance()
        self.project,self.directory=self.fixture.project,self.fixture.directory
        self.counter=0
        (self.project/'app.py').write_text('value = 0\n')
        (self.project/'check.py').write_text('import app\nassert app.value==1\nprint("fixture engineering check")\n')

    def epic(self):return sdlc.selected_epic(self.project,'REQ-0001')
    def view(self):return qa_track.review(self.epic(),self.project)
    def unique(self):
        self.counter+=1;return 'qa-fixture-'+str(self.counter)
    def request(self,action,kind,payload=None):
        if action=='write':payload=document_payload('qa',kind,payload)
        return dict(project=self.project,epic_id='REQ-0001',expected_revision=self.view()['revision'],operation_id=self.unique(),action=action,kind=kind,payload={} if payload is None else payload,actor='Fixture QA Lead',decision='Fictional QA decision: '+action+' '+kind)
    def update(self,action,kind,payload=None):
        return qa_track.update(**self.request(action,kind,payload))
    def eng(self,action,kind,payload=None):
        if action=='write':payload=document_payload('engineering',kind,payload)
        if action=='write' and engineering.governed(self.epic()):
            # Current-contract fixtures declare no prototype exceptions. These
            # tiny programs have no product validation/default/rejection policy.
            payload=deepcopy(payload)
            if kind=='design':payload.setdefault('governance',{'schema_version':'0.1','prototype_limitations':[]})
            else:payload.setdefault('limitation_refs',[])
            if kind=='implementation':payload.setdefault('conformance',self.conformance())
        return engineering.update(self.project,'REQ-0001',engineering.review(self.epic(),self.project)['revision'],self.unique(),action,kind,{} if payload is None else payload,'Fixture Engineering Lead','Fictional Engineering decision: '+action+' '+kind)
    def conformance(self):
        return {'reviewer':'Fixture Code Reviewer','independence':'author_review',
                'summary':'Fictional fixture assessment: value assignment only; no material product restrictions.',
                'reviewed_categories':['negative_condition','default','validation','unsupported_operation'],'behaviors':[]}
    def reject(self,code,run):
        try:run()
        except business.BusinessError as exc:self.assertEqual(exc.code,code)
        except sdlc.Rejected as exc:self.assertIn(code,{d.code for d in exc.diagnostics})
        else:self.fail('Expected '+code)
    def base(self):
        items,questions=engineering.analysis_items(self.epic())
        return {'content':'Fictional QA design derived only from approved Analysis.',
            'coverage':{rid:{'disposition':'blocked' if status in ('blocked','proposed') else 'implemented','reason':'Keep source disposition.'} for rid,status in items.items()},
            'unresolved':[{'id':q['id'],'text':q['text']} for q in questions]}
    def scenarios(self):
        doc=self.base()
        doc['cases']=[{'id':'TC-001','requirements':['FR-001','AC-001'],'preconditions':'Fixture task exists.','action':'Exercise the approved behavior.','expected':'Observe its approved acceptance outcome.','status':'specified'}]
        return doc
    def design_qa(self):
        self.update('write','strategy',self.base());return self.update('write','scenarios',self.scenarios())
    def approve_scenarios(self):
        return self.update('approve','scenarios',{'acknowledged':[q['id'] for q in self.base()['unresolved']]})
    def prepare_qa(self):
        self.design_qa();self.approve_scenarios();self.update('advance','scenarios')
    def design_engineering(self):
        self.eng('write','design',self.base())
        self.eng('approve','design',{'acknowledged':[q['id'] for q in self.base()['unresolved']]})
        self.eng('advance','design')
    def development(self):
        self.design_engineering()
        plan=self.base();plan.update(tasks=[{'id':'T-001','description':'Implement fixture behavior and unit checks.','requirements':['FR-001','AC-001'],'depends_on':[],'paths':['app.py','check.py']}],checks=[{'id':category,'category':category,'argv':[sys.executable,'-B','check.py'],'cwd':'.','timeout':10,'requirements':['AC-001'],'scenario':'Fictional actual command check.'} for category in ('unit','build')])
        self.eng('write','plan',plan);self.eng('approve','plan',{'acknowledged':[q['id'] for q in plan['unresolved']]});self.eng('advance','plan');self.eng('start','development')
        (self.project/'app.py').write_text('value = 1\n')
    def automation_doc(self):
        doc=self.base();doc.update(paths=['qa/'],source_revision=qa_track.qa_source(self.project),checks=[{'id':'QA-'+category,'category':category,'argv':[sys.executable,'-B','qa/check.py',category],'cwd':'.','timeout':10,'requirements':['AC-001'],'cases':['TC-001'],'scenario':'Actual fixture command, not browser acceptance.'} for category in ('integration','ui')]);
        if engineering.governed(self.epic()):doc['limitation_checks']=[]
        return doc
    def automation(self):
        self.prepare_qa()
        folder=self.project/'qa';folder.mkdir(exist_ok=True)
        (folder/'check.py').write_text('import sys\nprint("Executed QA fixture",sys.argv[1])\n')
        self.update('write','automation',self.automation_doc())
        self.update('approve','automation',{'acknowledged':[q['id'] for q in self.base()['unresolved']],'source_revision':qa_track.qa_source(self.project)})
        self.update('advance','automation')
    def reviewed_implementation(self):
        self.development();self.automation()
        for category in ('unit','build'):self.eng('run','check',{'check_id':category})
        doc=self.base();doc.update(source_revision=qa_track.app_source(self.epic(),self.project),plan=engineering.latest(self.epic(),'plan')[0]['baseline_id'],completed_tasks=['T-001'])
        self.eng('write','implementation',doc);self.eng('approve','implementation',{'acknowledged':[q['id'] for q in doc['unresolved']]});self.eng('advance','implementation')
    def run_check(self,cid):return self.update('run','check',{'check_id':cid,'source_revision':qa_track.app_source(self.epic(),self.project)})

    def test_qa_design_does_not_require_technical_design(self):
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')
        self.design_qa()
        self.assertEqual(self.view()['stage'],'test_design')
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')
        self.assertFalse(engineering.events(self.epic(),'write','design'))
        self.assertEqual(self.view()['analysis_baseline'],work_tracks.current(self.epic().metadata)['analysis_baseline'])

    def test_scenario_approval_is_separate_and_requires_exact_acknowledgement(self):
        self.design_qa()
        self.reject('E_ACKNOWLEDGEMENT',lambda:self.update('approve','scenarios',{'acknowledged':[]}))
        self.approve_scenarios()
        self.assertTrue(self.view()['approvals']['scenarios']['valid'])
        self.assertEqual(self.view()['stage'],'test_design')
        self.update('advance','scenarios')
        self.assertEqual(self.view()['stage'],'test_automation')
        self.assertEqual(self.epic().metadata['status'],'ready_for_technical_design')

    def test_engineering_artifacts_do_not_invalidate_qa_revision_or_scenarios(self):
        self.design_qa();self.approve_scenarios();before=self.view()
        self.eng('write','design',self.base())
        self.assertEqual(self.view()['revision'],before['revision'])
        self.assertTrue(self.view()['approvals']['scenarios']['valid'])
        (self.project/'app.py').write_text('value = 9\n')
        self.assertEqual(self.view()['revision'],before['revision'])
        self.assertTrue(self.view()['approvals']['scenarios']['valid'])

    def test_qa_changes_do_not_modify_engineering_history_or_owner(self):
        before=deepcopy(self.epic().metadata)
        self.design_qa();self.approve_scenarios();self.update('advance','scenarios')
        after=self.epic().metadata
        self.assertEqual(after['lifecycle'],before['lifecycle'])
        self.assertEqual(after.get('engineering_history'),before.get('engineering_history'))
        self.assertEqual(work_tracks.current(after)['engineering'],work_tracks.current(before)['engineering'])

    def test_incomplete_qa_track_is_never_integration_ready(self):
        result=qa_track.integration_readiness(self.epic(),self.project)
        self.assertFalse(result['ready']);self.assertTrue(result['reasons'])
        self.design_qa();self.approve_scenarios()
        self.assertFalse(qa_track.integration_readiness(self.epic(),self.project)['ready'])

    def test_cases_and_automation_cannot_claim_blocked_behavior(self):
        self.update('write','strategy',self.base())
        doc=self.scenarios();doc['cases'][0]['requirements'].append('FR-002')
        self.reject('E_QA_TRACE',lambda:self.update('write','scenarios',doc))
        doc=self.scenarios();doc['cases'][0]['requirements']=['FR-001']
        self.reject('E_QA_TRACE',lambda:self.update('write','scenarios',doc))

    def test_every_specified_case_needs_automation_even_with_same_ac(self):
        self.design_engineering()
        self.update('write','strategy',self.base())
        cases=self.scenarios();cases['cases'].append({**cases['cases'][0],'id':'TC-002','action':'Exercise a second boundary.'})
        self.update('write','scenarios',cases);self.approve_scenarios();self.update('advance','scenarios')
        self.reject('E_QA_TRACE',lambda:self.update('write','automation',self.automation_doc()))

    def test_scenario_revisions_preserve_history_and_invalidate_approval(self):
        self.design_qa();self.approve_scenarios()
        before=deepcopy(work_tracks.current(self.epic().metadata)['qa']['history'])
        self.update('write','scenarios',self.scenarios())
        self.assertFalse(self.view()['approvals']['scenarios']['valid'])
        self.assertEqual(work_tracks.current(self.epic().metadata)['qa']['history'][:len(before)],before)

    def test_idempotency_and_stale_revision_rejection(self):
        request=self.request('write','strategy',self.base());first=qa_track.update(**request)
        self.assertTrue(qa_track.update(**request)['replayed'])
        self.assertEqual(len(work_tracks.current(self.epic().metadata)['qa']['history']),1)
        self.reject('E_IDEMPOTENCY',lambda:qa_track.update(**{**request,'decision':'Different fixture words'}))
        self.reject('E_REVISION_CONFLICT',lambda:qa_track.update(**{**request,'operation_id':self.unique()}))

    def test_malformed_cases_and_nested_paths_are_diagnostics(self):
        self.update('write','strategy',self.base())
        for cases in ({},[{}],[{'id':[]}],None):
            doc=self.scenarios();doc['cases']=cases
            self.reject('E_QA_TRACE',lambda:self.update('write','scenarios',doc))

    def test_concurrent_qa_updates_cannot_both_commit(self):
        first=self.request('write','strategy',self.base());second={**first,'operation_id':self.unique()}
        def run(r):
            try:return qa_track.update(**r)
            except business.BusinessError as exc:return {'ok':False,'code':exc.code}
            except sdlc.Rejected as exc:return {'ok':False,'code':exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,(first,second)))
        self.assertEqual(sum(v['ok'] for v in results),1)
        self.assertIn(next(v['code'] for v in results if not v['ok']),('E_PROJECT_BUSY','E_REVISION_CONFLICT'))

    def test_interrupted_publication_has_no_partial_decision_and_retries(self):
        request=self.request('write','strategy',self.base());before=(self.directory/'metadata.yaml').read_bytes()
        with patch.object(sdlc,'atomic_history_write',side_effect=OSError('Fixture precommit failure')):
            with self.assertRaises(OSError):qa_track.update(**request)
        self.assertEqual((self.directory/'metadata.yaml').read_bytes(),before)
        result=qa_track.update(**request)
        self.assertTrue(result['ok']);self.assertTrue(qa_track.update(**request)['replayed'])

    def test_lost_success_response_replays_without_duplicate_audit(self):
        request=self.request('write','strategy',self.base());real=sdlc.atomic_history_write
        def lost(*args):
            real(*args)
            raise sdlc.Rejected([sdlc.error('E_WRITE_UNCERTAIN',self.directory/'metadata.yaml','Fixture lost response')])
        with patch.object(sdlc,'atomic_history_write',side_effect=lost):
            self.reject('E_WRITE_UNCERTAIN',lambda:qa_track.update(**request))
        self.assertTrue(qa_track.update(**request)['replayed'])
        self.assertEqual(len(work_tracks.current(self.epic().metadata)['qa']['history']),1)

    def test_corrupted_qa_baseline_blocks_mutation(self):
        saved=self.update('write','strategy',self.base())
        Path(self.view()['drafts']['strategy']['document']['path']).write_text('corruption')
        self.reject('E_BASELINE_INTEGRITY',self.epic)

    def test_automation_preparation_needs_interfaces_but_not_implementation(self):
        self.design_engineering();self.automation()
        self.assertTrue(self.view()['approvals']['automation']['valid'])
        self.assertEqual(self.view()['stage'],'ready_for_verification')
        self.reject('E_INTEGRATION_NOT_READY',lambda:self.run_check('QA-ui'))

    def test_automation_files_are_separate_and_changed_files_need_fresh_review(self):
        self.development();before=engineering.review(self.epic(),self.project)['revision'];self.automation()
        # Metadata records only the other track; separate QA files do not alter engineering token.
        self.assertEqual(engineering.review(self.epic(),self.project)['revision'],before)
        scenarios=self.view()['approvals']['scenarios']
        (self.project/'qa/check.py').write_text('print("changed fixture")\n')
        self.assertFalse(self.view()['approvals']['automation']['valid'])
        self.assertEqual(self.view()['approvals']['scenarios'],scenarios)

    def test_real_qa_execution_and_explicit_completion_gate(self):
        self.reviewed_implementation()
        before=self.epic().metadata['status']
        self.run_check('QA-integration');self.run_check('QA-ui')
        self.assertFalse(qa_track.integration_readiness(self.epic(),self.project)['ready'])
        self.update('advance','verification')
        joined=qa_track.integration_readiness(self.epic(),self.project)
        self.assertTrue(joined['ready'],joined)
        self.assertEqual(set(joined['checks']),{'QA-integration','QA-ui'})
        self.assertEqual(self.epic().metadata['status'],before)
        self.assertIn('Executed QA fixture',joined['checks']['QA-ui']['output'])
        (self.project/'app.py').write_text('value = 2\n')
        self.assertFalse(qa_track.integration_readiness(self.epic(),self.project)['ready'])
        self.assertTrue(self.view()['approvals']['scenarios']['valid'])

    def test_new_scenario_revision_invalidates_only_its_dependent_automation(self):
        self.design_engineering();self.automation()
        engineering_before=engineering.review(self.epic(),self.project)['revision']
        self.update('write','scenarios',self.scenarios())
        self.assertFalse(self.view()['approvals']['scenarios']['valid'])
        self.assertFalse(self.view()['approvals']['automation']['valid'])
        self.assertEqual(engineering.review(self.epic(),self.project)['revision'],engineering_before)

    def test_upstream_reopening_preserves_both_track_history_and_invalidates_qa(self):
        self.design_qa();self.approve_scenarios();before=deepcopy(self.epic().metadata['work_tracks'])
        self.fixture.business_fixture.reopen()
        self.assertEqual(self.epic().metadata['work_tracks'],before)
        self.assertFalse(self.view()['active'])
