"""Governance contracts with fictional decisions and disposable fixture programs.

These tests exercise real persistence/commands, not AI semantic judgment or a new
human acceptance scenario. No preserved demonstration artifacts are modified.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import business_refinement as business
import domain_skills
import engineering
from template_fixtures import document_payload
import qa_track
import sdlc
import work_tracks
import test_qa_track as fixtures


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.QATrackTests('test_real_qa_execution_and_explicit_completion_gate')
        self.addCleanup(self.f.doCleanups); self.f.setUp()

    def call(self, action, kind, payload=None, **changes):
        if action=='write':payload=document_payload('engineering',kind,payload)
        request=dict(project=self.f.project,epic_id='REQ-0001',expected_revision=engineering.review(self.f.epic(),self.f.project)['revision'],
                     operation_id=self.f.unique(),action=action,kind=kind,payload=payload or {},actor='Fixture Approver',
                     decision='Fictional explicit human decision: '+action+' '+kind)
        request.update(changes)
        return engineering.update(**request)

    def limit(self):
        return {'id':'LIM-001','requirements':['FR-002'],'questions':[self.f.base()['unresolved'][0]['id']],
                'observable_behavior':'The prototype refuses the unresolved operation and preserves existing data.',
                'business_impact':'The affected operation cannot be used in this prototype.',
                'scope':'Disposable local fixture only; no production use.','validity':'current_analysis_cycle'}

    def design(self,limits=True):
        doc=self.f.base();doc['governance']={'schema_version':'0.1','prototype_limitations':[self.limit()] if limits else []}
        return self.call('write','design',doc)

    def ack(self):return {'acknowledged':[q['id'] for q in engineering.latest(self.f.epic(),'design')[1]['unresolved']]}

    def consent(self):
        return self.call('approve','design',{**self.ack(),'authorized_limitations':['LIM-001']},
                         decision='Fixture: approve this Design and explicitly authorize LIM-001 refusal with no mutation, for this local prototype only.')

    def plan(self):
        self.design();self.consent();self.call('advance','design')
        doc=self.f.base();doc['limitation_refs']=['LIM-001']
        doc['tasks']=[{'id':'T-001','description':'Implement fixture approved assignment and explicit prototype restriction.',
                       'requirements':['FR-001','AC-001','FR-002'],'depends_on':[],'paths':['app.py','check.py'],'limitations':['LIM-001']}]
        doc['checks']=[{'id':kind,'category':kind,'argv':[sys.executable,'-B','check.py'],'cwd':'.','timeout':10,
                        'requirements':['AC-001','FR-002'],'scenario':'Fixture approved behavior and prototype boundary, separately classified.',
                        'limitations':['LIM-001']} for kind in ('unit','build')]
        self.call('write','plan',doc)
        return doc

    def implementation_doc(self):
        doc=self.f.base();doc.update(source_revision=qa_track.app_source(self.f.epic(),self.f.project),
                                   plan=engineering.latest(self.f.epic(),'plan')[0]['baseline_id'],completed_tasks=['T-001'],
                                   limitation_refs=[],conformance=self.f.conformance())
        return doc

    def reviewed_source(self):
        self.f.development()
        for cid in ('unit','build'):self.f.eng('run','check',{'check_id':cid})
        return self.implementation_doc()

    def behavior(self,kind='none',rid=None,assessment='unsupported'):
        return {'category':'validation','path':'app.py','line':1,'observable_behavior':'Refuse an operation with no approved requirement.',
                'authority':{'kind':kind,'id':rid},'assessment':assessment,'reason':'Fixture review found missing business authority.'}

    def test_new_cycle_requires_marker_and_cannot_downgrade(self):
        before=self.f.epic().metadata
        self.assertEqual(before['work_tracks']['schema_version'],'0.2')
        self.assertTrue(engineering.governed(self.f.epic()))
        changed=deepcopy(before);work_tracks.current(changed).pop('governance_version')
        self.f.reject('E_WORK_TRACKS',lambda:work_tracks.validate(changed))
        changed=deepcopy(before);changed['work_tracks']['schema_version']='0.1';changed['work_tracks'].pop('legacy_cycle_count')
        self.f.reject('E_APPROVAL_AUDIT',lambda:work_tracks.preserve_prefix(before,changed))
        changed=deepcopy(before);changed['work_tracks']['legacy_cycle_count']=1
        self.f.reject('E_APPROVAL_AUDIT',lambda:work_tracks.preserve_prefix(before,changed))

    def test_missing_governance_document_cannot_select_legacy_contract(self):
        self.f.reject('E_ENGINEERING_DOCUMENT',lambda:self.call('write','design',self.f.base()))

    def test_acknowledgement_and_generic_approval_do_not_authorize_limitation(self):
        self.design();before=(self.f.directory/'metadata.yaml').read_bytes()
        self.f.reject('E_LIMITATION_CONSENT',lambda:self.call('approve','design',self.ack(),decision='Fixture: approve Design and acknowledge uncertainty.'))
        self.assertEqual((self.f.directory/'metadata.yaml').read_bytes(),before)
        self.f.reject('E_ACKNOWLEDGEMENT',lambda:self.call('approve','design',{'acknowledged':[],'authorized_limitations':['LIM-001']}))

    def test_explicit_consent_preserves_words_and_does_not_advance(self):
        self.design();result=self.consent()
        entry=self.f.epic().metadata['engineering_history'][-1]
        obj,_=engineering.load_artifact(self.f.directory,result['baseline_id'])
        self.assertEqual(obj['payload']['authorized_limitations'],['LIM-001'])
        self.assertEqual(entry['decision'],obj['payload']['content'])
        self.assertEqual(self.f.epic().metadata['status'],'technical_design')
        self.assertEqual(engineering.authorized_limitations(self.f.epic(),None)['LIM-001']['approval_baseline'],result['baseline_id'])
        self.assertEqual(engineering.latest(self.f.epic(),'design')[1]['coverage']['FR-002']['disposition'],'blocked')

    def test_changed_and_same_content_design_require_fresh_consent(self):
        self.design();self.consent();self.design()
        self.f.reject('E_APPROVAL_STALE',lambda:self.call('advance','design'))
        self.f.reject('E_LIMITATION_CONSENT',lambda:self.call('approve','design',self.ack()))
        doc=deepcopy(engineering.latest(self.f.epic(),'design')[1]);doc.pop('_request',None)
        doc['governance']['prototype_limitations'][0]['scope']='Different fixture audience'
        self.call('write','design',doc)
        self.f.reject('E_APPROVAL_STALE',lambda:engineering.authorized_limitations(self.f.epic(),None))

    def test_malformed_limitations_fail_with_structured_diagnostics(self):
        for change in ({'validity':'forever'},{'observable_behavior':''},{'requirements':['FR-999']},{'questions':['AQ-999']},{'id':[]}):
            doc=self.f.base();doc['governance']={'schema_version':'0.1','prototype_limitations':[{**self.limit(),**change}]}
            with self.assertRaises(business.BusinessError):self.call('write','design',doc)

    def test_unauthorized_and_untraced_plan_limitations_are_rejected(self):
        plan=self.plan()
        bad=deepcopy(plan);bad['limitation_refs']=['LIM-999']
        self.f.reject('E_ENGINEERING_TRACE',lambda:self.call('write','plan',bad))
        bad=deepcopy(plan);bad['checks'][0].pop('limitations');bad['checks'][1].pop('limitations')
        self.f.reject('E_ENGINEERING_TRACE',lambda:self.call('write','plan',bad))
        self.assertEqual(engineering.latest(self.f.epic(),'plan')[1]['coverage']['FR-002']['disposition'],'blocked')

    def test_source_bound_review_requires_categories_and_real_source_locations(self):
        doc=self.reviewed_source()
        for modification in ('missing','category','path','line','authority'):
            bad=deepcopy(doc)
            if modification=='missing':bad.pop('conformance')
            elif modification=='category':bad['conformance']['reviewed_categories'].pop()
            else:
                record=self.behavior('requirement','FR-001','conforms')
                if modification=='path':record['path']='absent.py'
                if modification=='line':record['line']=999
                if modification=='authority':record['authority']={'kind':'requirement','id':'FR-002'}
                bad['conformance']['behaviors']=[record]
            self.f.reject('E_ENGINEERING_DOCUMENT' if modification=='missing' else 'E_CONFORMANCE',
                          lambda:self.call('write','implementation',bad))

    def test_unsupported_runtime_restriction_is_recorded_but_blocks_code_approval(self):
        doc=self.reviewed_source();doc['conformance']['behaviors']=[self.behavior()]
        self.call('write','implementation',doc)
        self.f.reject('E_CONFORMANCE',lambda:self.call('approve','implementation',{'acknowledged':[q['id'] for q in doc['unresolved']]}))
        bad=deepcopy(doc);bad['conformance']['behaviors'][0]['assessment']='conforms'
        self.f.reject('E_CONFORMANCE',lambda:self.call('write','implementation',bad))

    def test_source_change_invalidates_conformance_and_approval(self):
        doc=self.reviewed_source();doc['conformance']['behaviors']=[self.behavior('requirement','FR-001','conforms')]
        self.call('write','implementation',doc)
        self.call('approve','implementation',{'acknowledged':[q['id'] for q in doc['unresolved']]})
        (self.f.project/'app.py').write_text('value = 2\n')
        self.f.reject('E_APPROVAL_STALE',lambda:engineering.approval(self.f.epic(),'implementation',qa_track.app_source(self.f.epic(),self.f.project)))

    def test_consent_idempotency_failure_recovery_and_concurrency(self):
        self.design()
        request=dict(project=self.f.project,epic_id='REQ-0001',expected_revision=engineering.review(self.f.epic(),self.f.project)['revision'],
                     operation_id=self.f.unique(),action='approve',kind='design',payload={**self.ack(),'authorized_limitations':['LIM-001']},
                     actor='Fixture PO',decision='Fixture: explicitly authorize LIM-001 prototype effect and approve Design.')
        before=(self.f.directory/'metadata.yaml').read_bytes()
        with patch.object(sdlc,'atomic_history_write',side_effect=OSError('Fixture publication interrupted')):
            with self.assertRaises(OSError):engineering.update(**request)
        self.assertEqual((self.f.directory/'metadata.yaml').read_bytes(),before)
        result=engineering.update(**request)
        self.assertTrue(engineering.update(**request)['replayed'])
        self.f.reject('E_IDEMPOTENCY',lambda:engineering.update(**{**request,'payload':self.ack()}))
        self.assertEqual(engineering.authorized_limitations(self.f.epic(),None)['LIM-001']['approval_baseline'],result['baseline_id'])
        self.design()
        request.update(expected_revision=engineering.review(self.f.epic(),self.f.project)['revision'],operation_id=self.f.unique())
        other={**request,'operation_id':self.f.unique()}
        def run(r):
            try:return engineering.update(**r)['ok']
            except (business.BusinessError,sdlc.Rejected):return False
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sum(pool.map(run,(request,other))),1)

    def test_cli_consent_uses_existing_design_operation(self):
        self.design();view=engineering.review(self.f.epic(),self.f.project)
        words='Fixture: approve Design and explicitly authorize the refusal in LIM-001 for this prototype.'
        args=[sys.executable,str(Path(sdlc.__file__)),'--project',str(self.f.project),'engineering-approve','REQ-0001','--kind','design',
              '--expected-engineering-revision',view['revision'],'--operation-id',self.f.unique(),'--actor','Fixture PO','--decision',words,'--authorize-limitation','LIM-001']
        for q in self.ack()['acknowledged']:args+=['--acknowledge-open-item',q]
        result=subprocess.run(args,text=True,capture_output=True)
        self.assertEqual(result.stderr,'');self.assertEqual(result.returncode,0,result.stdout)
        self.assertEqual(json.loads(result.stdout)['epic']['metadata']['status'],'technical_design')
        self.assertEqual(self.f.epic().metadata['engineering_history'][-1]['decision'],words)

    def test_qa_limitation_checks_are_separate_from_product_scenarios(self):
        self.design();self.consent();self.f.prepare_qa()
        doc=self.f.automation_doc()
        self.f.reject('E_QA_TRACE',lambda:self.f.update('write','automation',doc))
        doc['limitation_checks']=[{'id':'QA-limit','category':'integration','argv':[sys.executable,'-c','print("fixture explicit limit")'],
                                  'cwd':'.','timeout':10,'requirements':['FR-002'],'scenario':'Authorized prototype refusal only.','limitations':['LIM-001']}]
        self.f.update('write','automation',doc)
        self.assertEqual(qa_track.latest(self.f.epic(),'automation')[1]['coverage']['FR-002']['disposition'],'blocked')
        bad=deepcopy(doc);bad['limitation_checks'][0]['limitations']=['LIM-999']
        self.f.reject('E_ENGINEERING_TRACE',lambda:self.f.update('write','automation',bad))
        bad=deepcopy(doc);bad['checks'][0]['requirements'].append('FR-002')
        self.f.reject('E_QA_TRACE',lambda:self.f.update('write','automation',bad))

    def test_complete_final_report_matches_structured_data_and_keeps_physical_name(self):
        self.f.reviewed_implementation()
        # Add a Security-specific uncertainty to ensure the renderer does not
        # merely repeat the Plan's older question set.
        self.f.run_check('QA-integration');self.f.run_check('QA-ui');self.f.update('advance','verification');self.f.eng('advance','verification')
        doc=self.f.base();doc.update(source_revision=qa_track.app_source(self.f.epic(),self.f.project),
                                  plan=engineering.latest(self.f.epic(),'plan')[0]['baseline_id'],findings=[])
        doc['unresolved'].append({'id':'TECH-001','text':'Fixture environment portability remains unassessed.'})
        original_question=doc['unresolved'][0]['text']
        doc['unresolved'][0]['text']='Different downstream wording of the same still-open question.'
        self.f.eng('write','security',doc);self.f.eng('advance','security')
        saved=self.f.eng('finalize','final');report=engineering.load_artifact(self.f.directory,saved['baseline_id'])[0]['payload']
        import verification_report
        self.assertEqual(report['content'],verification_report.render(report))
        self.assertIn('Verified for the stated scope',report['content'])
        self.assertIn('TECH-001',report['content']);self.assertIn('FR-002',report['content']);self.assertIn('TC-001',report['content'])
        self.assertIn(original_question,report['content'])
        self.assertIn('Different downstream wording',report['content'])
        for q in report['unresolved']:self.assertIn(q['text'],report['content'])
        path=engineering.artifact_document(self.f.directory,saved['baseline_id'],'final')['path']
        self.assertEqual(Path(path).name,'verification-report.md')
        self.assertEqual(Path(path).read_text(),report['content'])

    def test_authorized_limitation_reaches_verified_without_resolving_product_question(self):
        self.plan();self.call('approve','plan',{'acknowledged':self.ack()['acknowledged']})
        self.call('advance','plan');self.call('start','development')
        (self.f.project/'app.py').write_text('value = 1\n')
        self.f.prepare_qa()
        folder=self.f.project/'qa';folder.mkdir()
        (folder/'check.py').write_text('print("Actual fictional QA check")\n')
        automation=self.f.automation_doc()
        automation['limitation_checks']=[{'id':'QA-limit','category':'integration','argv':[sys.executable,'-c','print("Fixture limitation check")'],
            'cwd':'.','timeout':10,'requirements':['FR-002'],'scenario':'Fictional authorized boundary; not product acceptance.','limitations':['LIM-001']}]
        self.f.update('write','automation',automation)
        self.f.update('approve','automation',{'acknowledged':self.ack()['acknowledged'],'source_revision':qa_track.qa_source(self.f.project)})
        self.f.update('advance','automation')
        for cid in ('unit','build'):self.call('run','check',{'check_id':cid})
        code=self.implementation_doc();code['limitation_refs']=['LIM-001']
        self.f.reject('E_CONFORMANCE',lambda:self.call('write','implementation',code))
        code['conformance']['behaviors']=[self.behavior('limitation','LIM-001','conforms')]
        self.call('write','implementation',code);self.call('approve','implementation',self.ack());self.call('advance','implementation')
        for cid in ('QA-integration','QA-ui'):self.f.run_check(cid)
        self.f.reject('E_VERIFICATION',lambda:self.f.update('advance','verification'))
        self.f.run_check('QA-limit');self.f.update('advance','verification');self.call('advance','verification')
        security=self.f.base();security.update(source_revision=qa_track.app_source(self.f.epic(),self.f.project),
            plan=engineering.latest(self.f.epic(),'plan')[0]['baseline_id'],findings=[],limitation_refs=['LIM-001'])
        self.call('write','security',security);self.call('advance','security')
        result=self.call('finalize','final');report=engineering.load_artifact(self.f.directory,result['baseline_id'])[0]['payload']
        self.assertEqual(result['epic']['metadata']['status'],'verified')
        self.assertEqual(report['coverage']['FR-002']['disposition'],'blocked')
        self.assertTrue(report['unresolved']);self.assertEqual(report['limitations'][0]['id'],'LIM-001')
        self.assertIn('QA-limit',report['checks']['qa:QA-limit']['check_id'])
        self.assertNotIn('qa:QA-limit',report['scenarios'][0]['checks'])
        self.assertIn('prototype refuses',report['content']);self.assertIn('approval',report['content'].lower())

    def test_upstream_reopening_and_new_cycle_do_not_reuse_limitation_consent(self):
        self.design();consent=self.consent();old=deepcopy(work_tracks.current(self.f.epic().metadata))
        analysis=self.f.fixture;original=self.f.epic().analysis['content'];upstream=analysis.business_fixture
        upstream.reopen()
        self.f.reject('E_ENGINEERING_INPUT',lambda:engineering.authorized_limitations(self.f.epic(),None))
        upstream.complete();upstream.revise(upstream.initial_document,mode='generate');upstream.approve();upstream.advance()
        view=analysis.review()
        for field,prefix in [('baseline_id','Baseline: '),('approval_id','Approval: '),('handoff_id','Handoff: ')]:
            prior=next(line[len(prefix):] for line in original.splitlines() if line.startswith(prefix))
            original=original.replace(prefix+prior,prefix+view['input'][field])
        analysis.revise(original);analysis.approve();analysis.advance()
        self.assertEqual(self.f.epic().metadata['work_tracks']['cycles'][0],old)
        self.assertEqual(work_tracks.current(self.f.epic().metadata)['governance_version'],'0.1')
        self.f.reject('E_ENGINEERING_INPUT',lambda:engineering.authorized_limitations(self.f.epic(),None))
        self.assertTrue((self.f.directory/'engineering-baselines'/consent['baseline_id']).is_dir())

    def test_archive_and_historical_skill_pins_unchanged(self):
        root=Path(__file__).resolve().parents[2];demo=root/'examples/todo-app'
        manifest=json.loads((demo/'preservation-manifest.json').read_text())
        self.assertEqual(len(manifest['files']),448)
        for path,digest in manifest['files'].items():self.assertEqual(hashlib.sha256((demo/path).read_bytes()).hexdigest(),digest,path)
        # Compare retained packages to their tracked historical originals rather
        # than deriving an expected digest from the newly edited package.
        for name in ('architecture','development','testing'):
            historical=domain_skills.ROOT/'versions'/name/'1.1.0'
            pins={'architecture':'9f48fe04ed806a531c5187cb709318c54e64a27241fddec729c6b3bcecb26aae',
                  'development':'1faa7a9542959a3c2766481c63aab762b6b51cd3f6f592a2d9df10f00d3e5894',
                  'testing':'883067299a993048d3a88b5c87049a90728a8900702a7f2560a2d728d3770bc3'}
            self.assertEqual(domain_skills.package(historical),pins[name])
