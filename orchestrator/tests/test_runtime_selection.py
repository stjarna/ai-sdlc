"""Actual installed A/B processes; fictional decisions, no historical-demo mutation."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

import test_installation as install_fixture
import test_business_approval as business_fixture
import test_functional_analysis as analysis_fixture
import test_qa_track as qa_fixture
import runtime_fixtures
import install
import runtime_management as management
import runtime_selection as selection
import sdlc
import engineering
import qa_track
import work_tracks
from template_fixtures import document_payload

class RuntimeSelectionTests(unittest.TestCase):
    setUpClass=classmethod(install_fixture.InstallationTests.setUpClass.__func__)
    def setUp(self):
        install_fixture.InstallationTests.setUp(self)
        self.a=install.install(**self.args);self.runtime=Path(self.a['runtime'])
        self.sessions=self.base/'sessions';self.environment={**os.environ,'SDLC_RUNTIME_SESSION_ROOT':str(self.sessions)}
        patcher=patch.dict(os.environ,{'SDLC_RUNTIME_SESSION_ROOT':str(self.sessions)})
        patcher.start();self.addCleanup(patcher.stop);self.counter=0
    def unique(self):self.counter+=1;return 'runtime-fixture-'+str(self.counter)
    def candidate(self,change=None):
        self.assertNotEqual(self.source.resolve(),Path(sdlc.__file__).resolve().parents[2])
        self.assertTrue(self.source.is_relative_to(Path(type(self).fixture.name)))
        install_fixture.git(self.source,'reset','--hard',self.revision) # disposable fixture only
        (self.source/'README.md').write_bytes((self.source/'README.md').read_bytes()+b'\nFictional B fixture.\n')
        code=self.source/'orchestrator/scripts/sdlc.py';code.write_text(code.read_text().replace('ORCHESTRATOR_VERSION = "0.16.0"','ORCHESTRATOR_VERSION = "0.16.1"'))
        if change:change(self.source)
        install_fixture.git(self.source,'add','.');install_fixture.git(self.source,'commit','-qm','Fictional runtime B fixture')
        value=install.prepare(self.source,install_fixture.git(self.source,'rev-parse','HEAD').strip(),self.project,self.runtime_root,sys.executable)
        return value
    def cli(self,runtime,*args,token=None,ok=True):
        run,data=runtime_fixtures.cli(runtime,self.project,*args,session=token,env=self.environment)
        self.assertEqual(run.returncode,0 if ok else 1,data);self.assertEqual(data['ok'],ok,data)
        return data
    def context(self,runtime=None,epic='REQ-0001',track=None,context_id=None):
        token,_=runtime_fixtures.session(runtime or self.runtime,self.project,self.skills,self.sessions,epic,track,context_id)
        return token
    def new(self):
        token=self.context(epic=None)
        result=self.cli(self.runtime,'new','--title','Task due dates','--requester','Fixture Requester','--idea','People forget commitments.',token=token)
        self.directory=Path(result['epic']['directory']);return result
    def select(self,runtime,track=None,initial=False,reconciliation=None,expected=None,operation=None):
        report=selection.assessment(self.project,'REQ-0001',runtime,track)
        return selection.select_runtime(self.project,'REQ-0001',runtime,track,expected or report['revision'],operation or self.unique(),
                                        'Fixture operator','Explicit fictional future-runtime decision.','Exercise version governance.',reconciliation,initial)
    def epic(self):return sdlc.selected_epic(self.project,'REQ-0001')
    def test_new_default_persistence_context_mismatch_and_missing_runtime(self):
        self.new();self.assertEqual(selection.read(self.directory)['events'][0]['event']['runtime']['snapshot_digest'],self.a['snapshot_digest'])
        a_token=self.context(context_id='fixture-host-A');b=self.candidate()
        management.switch(self.skills,{'runtime':b['runtime'],'snapshot_digest':b['snapshot_digest']},self.a['snapshot_digest'],'update','Fixture','Explicit update','update')
        view=self.cli(b['runtime'],'runtime-status','REQ-0001','--skill-root',str(self.skills))
        self.assertEqual(view['effective_runtime']['snapshot_digest'],self.a['snapshot_digest'])
        self.select(b['runtime']);self.assertEqual(self.epic().metadata['status'],'discovery')
        stale=self.cli(b['runtime'],'discovery-update','REQ-0001','--expected-revision',self.epic().revision,'--operation-id','stale','--changes-file',str(self.base/'missing.json'),token=a_token,ok=False)
        # Caller input reading can reject first, so directly exercise the guard as well.
        with patch.object(selection,'current_pin',return_value=selection.pin(b['runtime'])):
            call={'operation':'discovery-update','id':'REQ-0001','runtime_session':a_token}
            with self.assertRaises(Exception):selection.validate_session(self.project,call,selection.pin(b['runtime']),'shared',selection.selected(selection.read(self.directory),'shared')[1])
        run,data=runtime_fixtures.cli(b['runtime'],self.project,'runtime-session','REQ-0001','--skill-root',str(self.skills),
            '--fresh-context-id','fixture-host-A','--instructions-digest',selection.instructions(selection.pin(b['runtime'])),env=self.environment)
        self.assertEqual(run.returncode,1,data);self.assertEqual(data['diagnostics'][0]['code'],'E_RUNTIME_CONTEXT_RELOAD')
        shutil.rmtree(b['runtime'])
        self.cli(self.runtime,'runtime-status','REQ-0001','--skill-root',str(self.skills),ok=False)
    def business_under_a(self,advance=True):
        self.new();token=self.context();r=business_fixture.record
        records=[r('user_statement','Record deadlines against tasks.'),r('question','Dates or reminders?'),
            r('user_statement','Dates only; reminders are excluded.',answers='D-0002'),r('ai_assumption','Dates are optional.'),
            r('human_decision','Yes, optional.',action='confirm',target='D-0004'),r('question','Allow past dates?'),
            r('human_decision','Defer until support discussion.',action='defer',target='D-0006',revisit='After support discussion')]
        changes=self.base/'discovery.json';changes.write_text(json.dumps({'records':records}))
        self.cli(self.runtime,'discovery-update','REQ-0001','--expected-revision',self.epic().revision,'--operation-id','discovery-A','--changes-file',str(changes),token=token)
        self.cli(self.runtime,'discovery-complete','REQ-0001','--expected-revision',self.epic().revision,'--operation-id','complete-A','--requester','Fixture Requester','--decision','Fixture explicitly completes Discovery.',token=token)
        source=self.epic().source_revision
        document=f'# Business Refinement — REQ-0001\n\nSource revision: {source}\n\n## Confirmed information\n### Business value\n- **B-001** [D-0001] Record deadlines against tasks.\n### Scope and exclusions\n- **B-002** [D-0003] Dates only; reminders are excluded.\n- **B-003** [D-0005, D-0004] Dates are optional.\n\n## Unresolved issues\n- **U-001** [D-0006] Past-date rule remains deferred until support discussion (D-0007).\n\n## Unconfirmed proposals\nNone recorded.\n'
        proposal=self.base/'business.md';proposal.write_text(document)
        self.cli(self.runtime,'business-generate','REQ-0001','--expected-source-revision',source,'--operation-id','business-A','--editor','Fixture PO','--reason','Fixture business draft','--document-file',str(proposal),token=token)
        if not advance:return token
        view=self.cli(self.runtime,'business-review','REQ-0001')
        self.cli(self.runtime,'business-approve','REQ-0001','--expected-review-revision',view['review_revision'],'--expected-business-revision',self.epic().business['revision'],
                 '--operation-id','business-approval-A','--approver','Fixture PO','--reason','Fixture approval','--decision','Fixture explicitly approves and acknowledges U-001.','--acknowledge-open-item','U-001',token=token)
        view=self.cli(self.runtime,'business-review','REQ-0001')
        self.cli(self.runtime,'business-advance','REQ-0001','--expected-review-revision',view['review_revision'],'--expected-business-revision',self.epic().business['revision'],
                 '--operation-id','business-advance-A','--actor','Fixture PO','--reason','Fixture separately advances.','--approval-id',view['approval']['latest_decision']['id'],token=token)
    def test_discovery_business_a_analysis_b_preserves_approved_history_and_provenance(self):
        self.business_under_a();before=install_fixture.hashes(self.directory/'business-baselines');metadata=deepcopy(self.epic().metadata)
        b=self.candidate();self.select(b['runtime']);token=self.context(b['runtime']);view=self.cli(b['runtime'],'analysis-review','REQ-0001')
        path=self.base/'analysis.md';path.write_text(analysis_fixture.document(view['input']))
        result=self.cli(b['runtime'],'analysis-generate','REQ-0001','--expected-analysis-review-revision',view['analysis_review_revision'],
                        '--expected-baseline-id',view['input']['baseline_id'],'--expected-handoff-id',view['input']['handoff_id'],
                        '--operation-id','analysis-B','--editor','Fixture Analyst','--reason','Fixture analysis under B','--document-file',str(path),token=token)
        self.assertEqual(result['epic']['metadata']['status'],'functional_analysis')
        self.assertEqual(before,install_fixture.hashes(self.directory/'business-baselines'))
        self.assertEqual(metadata['business_decisions'],self.epic().metadata['business_decisions'])
        events=[w['event'] for w in selection.read(self.directory)['events']]
        for event in events:
            if event.get('operation_id')=='analysis-B':self.assertEqual(event['runtime']['snapshot_digest'],b['snapshot_digest'])
            if event.get('operation_id')=='business-approval-A':self.assertEqual(event['runtime']['snapshot_digest'],self.a['snapshot_digest'])
        # Active Analysis is not a promotion boundary, and acknowledgement is not promotion.
        report=selection.assessment(self.project,'REQ-0001',self.runtime)
        self.assertFalse(report['safe_boundary'])
        with self.assertRaises(Exception):self.select(self.runtime)
        self.assertNotIn('analysis_decisions',self.epic().metadata)
    def test_stale_concurrent_and_idempotent_promotions(self):
        self.new();b=self.candidate();report=selection.assessment(self.project,'REQ-0001',b['runtime']);old=selection.read(self.directory)
        self.select(b['runtime'],expected=report['revision'],operation='promote-once')
        replay=self.select(b['runtime'],expected=report['revision'],operation='promote-once');self.assertTrue(replay['replayed'])
        with self.assertRaises(Exception):self.select(self.runtime,expected=report['revision'])
        self.assertEqual(old['events'],selection.read(self.directory)['events'][:len(old['events'])])
        before=(self.directory/selection.FILE).read_bytes()
        admin=selection.ADMIN.set(True)
        try:
            with sdlc.project_lock(self.project):
                with self.assertRaises(Exception):self.select(self.runtime)
        finally:selection.ADMIN.reset(admin)
        self.assertEqual(before,(self.directory/selection.FILE).read_bytes())
    def test_instruction_changes_require_explicit_reconciliation_and_incompatible_contract_blocks(self):
        self.new()
        def changed(source):
            path=source/'orchestrator/domain-skills/development/references/planning.md';path.write_bytes(path.read_bytes()+b'\nReviewed fictional practice change.\n')
            import yaml
            catalog=source/'orchestrator/domain-skills/catalog.yaml';data=yaml.safe_load(catalog.read_text());data['skills']['development']['digest']=__import__('domain_skills').package(path.parent.parent);catalog.write_text(yaml.safe_dump(data,sort_keys=False))
        b=self.candidate(changed);report=selection.assessment(self.project,'REQ-0001',b['runtime'])
        self.assertEqual(report['classification'],'requires_reconciliation')
        before=(self.directory/selection.FILE).read_bytes()
        with self.assertRaises(Exception):self.select(b['runtime'])
        self.assertEqual(before,(self.directory/selection.FILE).read_bytes())
        self.select(b['runtime'],reconciliation='Fixture operator assessed future development guidance; approved inputs unchanged.')
        # Corrupt/unsupported metadata is rejected by the actual candidate process, not version ordering.
        metadata=self.directory/'metadata.yaml';raw=metadata.read_bytes();metadata.write_text('schema_version: unsupported\nid: REQ-0001\n')
        with self.assertRaises(Exception):selection.assessment(self.project,'REQ-0001',self.runtime)
        metadata.write_bytes(raw)
    def test_provenance_failure_blocks_reads_and_recovers_without_reexecuting_business_work(self):
        self.new();token=self.context();changes=self.base/'records.json';changes.write_text('{"records":[]}')
        # Exercise the same installed guard in-process to inject a single receipt-write failure.
        call={'operation':'discovery-update','id':'REQ-0001','operation_id':'interrupted','runtime_session':token}
        ctx=selection.CALL.set(call);original=management.atomic;failed=False
        def fail(path,raw):
            nonlocal failed
            if path.name==selection.FILE and not failed:failed=True;raise OSError('Injected receipt failure')
            return original(path,raw)
        try:
            with patch.object(selection,'current_pin',return_value=selection.pin(self.runtime)),patch.object(management,'atomic',side_effect=fail):
                with self.assertRaises(Exception):sdlc.discovery_update(self.project,'REQ-0001',self.epic().revision,'interrupted',[])
        finally:selection.CALL.reset(ctx)
        self.assertTrue(selection.transaction(self.project).exists())
        self.cli(self.runtime,'open','REQ-0001',ok=False)
        selection.recover(self.project);self.assertFalse(selection.transaction(self.project).exists())
        self.assertEqual(len(selection.read(self.directory)['events']),3)
    def test_legacy_requires_explicit_binding_without_inventing_history(self):
        fixture=analysis_fixture.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        shutil.copytree(fixture.project/'requirements',self.project/'requirements');self.directory=next((self.project/'requirements').iterdir())
        before=install_fixture.hashes(self.directory/'business-baselines')
        self.assertIsNone(selection.read(self.directory));self.select(self.runtime,initial=True)
        self.assertEqual(selection.read(self.directory)['events'][0]['event']['previous_runtime'],None)
        self.assertEqual(before,install_fixture.hashes(self.directory/'business-baselines'))
    def test_audit_corruption_and_unsafe_sessions_fail_closed(self):
        self.new();path=self.directory/selection.FILE;raw=path.read_bytes();value=json.loads(raw);value['events'][0]['event']['runtime']['source_revision']='f'*40;path.write_text(json.dumps(value))
        self.cli(self.runtime,'validate','REQ-0001',ok=False);path.write_bytes(raw)
        with patch.dict(os.environ,{'SDLC_RUNTIME_SESSION_ROOT':str(self.project/'sessions')}):
            with self.assertRaises(Exception):selection.session(self.project,'REQ-0001',None,'ctx',selection.instructions(selection.pin(self.runtime)),self.skills)

    def test_mixed_engineering_b_qa_a_execute_join_and_finalization_with_real_processes(self):
        fixture=qa_fixture.QATrackTests('test_real_qa_execution_and_explicit_completion_gate')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        shutil.copytree(fixture.project/'requirements',self.project/'requirements')
        for name in ('app.py','check.py'):shutil.copyfile(fixture.project/name,self.project/name)
        self.directory=next((self.project/'requirements').iterdir());fixture.project=self.project;fixture.directory=self.directory
        immutable={name:install_fixture.hashes(self.directory/name) for name in ('business-baselines','analysis-baselines')}
        git_before=install_fixture.hashes(self.project/'.git')
        self.select(self.runtime,initial=True)
        qa_token=self.context(track='qa');b=self.candidate()
        def qa_operation(action,kind,payload=None):
            payload=payload or {};view=self.cli(self.runtime,'qa-review','REQ-0001')['review']
            op={'write':'qa-write','approve':'qa-approve','advance':'qa-advance','request_changes':'qa-request-changes','run':'qa-check-run'}[action]
            args=[op,'REQ-0001','--expected-qa-revision',view['revision'],'--operation-id',self.unique(),'--actor','Fixture QA Lead','--decision','Explicit fictional QA '+action]
            if action=='run':args+=['--check-id',payload['check_id'],'--expected-source-revision',payload['source_revision']]
            else:args+=['--kind',kind]
            if action=='write':
                path=self.base/(self.unique()+'.json');path.write_text(json.dumps(document_payload('qa',kind,payload)));args+=['--input-file',str(path)]
            if action=='approve':
                for item in payload['acknowledged']:args+=['--acknowledge-open-item',item]
                if kind=='automation':args+=['--expected-source-revision',payload['source_revision']]
            return self.cli(self.runtime,*args,token=qa_token)
        fixture.update=qa_operation
        fixture.prepare_qa()
        scenario_before=deepcopy(fixture.view()['approvals']['scenarios'])
        self.select(b['runtime'],track='engineering');eng_token=self.context(b['runtime'],track='engineering')
        def eng_operation(action,kind,payload=None):
            payload=deepcopy(payload or {});view=self.cli(b['runtime'],'engineering-review','REQ-0001')['engineering']
            if action=='write':
                if kind=='design':payload.setdefault('governance',{'schema_version':'0.1','prototype_limitations':[]})
                else:payload.setdefault('limitation_refs',[])
                if kind=='implementation':payload.setdefault('conformance',fixture.conformance())
            op={'write':'engineering-write','approve':'engineering-approve','advance':'engineering-advance','start':'development-start','run':'check-run','finalize':'engineering-finalize'}[action]
            args=[op,'REQ-0001','--expected-engineering-revision',view['revision'],'--operation-id',self.unique(),'--actor','Fixture Engineering Lead','--decision','Explicit fictional Engineering '+action]
            if action in ('write','approve','advance'):args+=['--kind',kind]
            if action=='run':args+=['--check-id',payload['check_id']]
            if action=='write':
                path=self.base/(self.unique()+'.json');path.write_text(json.dumps(document_payload('engineering',kind,payload)));args+=['--input-file',str(path)]
            if action=='approve':
                for item in payload['acknowledged']:args+=['--acknowledge-open-item',item]
            return self.cli(b['runtime'],*args,token=eng_token)
        fixture.eng=eng_operation
        fixture.development()
        self.assertEqual(scenario_before,fixture.view()['approvals']['scenarios'])
        folder=self.project/'qa';folder.mkdir();(folder/'check.py').write_text('import sys\nprint("Executed fictional QA check",sys.argv[1])\n')
        fixture.update('write','automation',fixture.automation_doc())
        fixture.update('approve','automation',{'acknowledged':[q['id'] for q in fixture.base()['unresolved']],'source_revision':qa_track.qa_source(self.project)})
        fixture.update('advance','automation')
        for category in ('unit','build'):fixture.eng('run','check',{'check_id':category})
        code=fixture.base();code.update(source_revision=qa_track.app_source(self.epic(),self.project),plan=engineering.latest(self.epic(),'plan')[0]['baseline_id'],completed_tasks=['T-001'])
        fixture.eng('write','implementation',code);fixture.eng('approve','implementation',{'acknowledged':[q['id'] for q in code['unresolved']]});fixture.eng('advance','implementation')
        for cid in ('QA-integration','QA-ui'):
            result=fixture.run_check(cid);self.assertEqual(result['qa']['evidence'][-1]['status'],'passed')
        fixture.update('advance','verification');fixture.eng('advance','verification')
        security=fixture.base();security.update(source_revision=qa_track.app_source(self.epic(),self.project),plan=engineering.latest(self.epic(),'plan')[0]['baseline_id'],findings=[])
        fixture.eng('write','security',security);fixture.eng('advance','security');final=fixture.eng('finalize','final')
        self.assertEqual(final['epic']['metadata']['status'],'verified')
        for name,files in immutable.items():self.assertEqual(files,install_fixture.hashes(self.directory/name))
        self.assertEqual(git_before,install_fixture.hashes(self.project/'.git'))
        view=self.cli(b['runtime'],'runtime-status','REQ-0001','--skill-root',str(self.skills),'--artifact','technical-design.md')
        self.assertTrue(view['artifact_provenance']);self.assertTrue(all(v['runtime']['snapshot_digest']==b['snapshot_digest'] for v in view['artifact_provenance']))
        qa_view=self.cli(self.runtime,'runtime-status','REQ-0001','--track','qa','--skill-root',str(self.skills),'--artifact','test-scenarios.md')
        self.assertTrue(all(v['runtime']['snapshot_digest']==self.a['snapshot_digest'] for v in qa_view['artifact_provenance']))
        # Rollback changes only the default, never this B Engineering selection or Verified history.
        management.switch(self.skills,{'runtime':b['runtime'],'snapshot_digest':b['snapshot_digest']},self.a['snapshot_digest'],'default-b','Fixture','Update default','update')
        management.switch(self.skills,None,b['snapshot_digest'],'default-a','Fixture','Rollback default','rollback')
        self.assertEqual(selection.selected(selection.read(self.directory),selection.scope_for(self.epic(),'engineering'))[0]['snapshot_digest'],b['snapshot_digest'])

    def test_failed_promotion_and_actual_context_mismatch_leave_state_unchanged(self):
        self.new();b=self.candidate();report=selection.assessment(self.project,'REQ-0001',b['runtime']);before=(self.directory/selection.FILE).read_bytes()
        with patch.object(management,'atomic',side_effect=OSError('Injected publication failure')):
            with self.assertRaises(OSError):self.select(b['runtime'])
        self.assertEqual(before,(self.directory/selection.FILE).read_bytes())
        self.select(b['runtime']);context=self.context(b['runtime']);path=self.base/'empty.json';path.write_text('{"records":[]}')
        before=install_fixture.hashes(self.directory)
        wrong=self.cli(self.runtime,'discovery-update','REQ-0001','--expected-revision',self.epic().revision,'--operation-id','wrong-runtime','--changes-file',str(path),token=context,ok=False)
        self.assertEqual(wrong['diagnostics'][0]['code'],'E_RUNTIME_MISMATCH')
        self.assertEqual(before,install_fixture.hashes(self.directory))

    def test_concurrent_promotions_cannot_both_commit(self):
        from concurrent.futures import ThreadPoolExecutor
        self.new();b=self.candidate();token=selection.assessment(self.project,'REQ-0001',b['runtime'])['revision']
        def attempt(number):
            try:self.select(b['runtime'],expected=token,operation='concurrent-'+str(number));return 'committed'
            except Exception as exc:return getattr(exc,'code',getattr(exc,'diagnostics',[None])[0].code if getattr(exc,'diagnostics',None) else type(exc).__name__)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,(1,2)))
        self.assertEqual(results.count('committed'),1,results)
        self.assertTrue(set(results)-{'committed'} <= {'E_PROJECT_BUSY','E_REVISION_CONFLICT'},results)

    def test_original_multi_file_transaction_recovers_under_its_runtime_and_receipt(self):
        import business_refinement as business
        token=self.business_under_a(advance=False);epic=self.epic()
        proposal=self.base/'refinement.md';proposal.write_text(epic.business['content'].replace('Record deadlines against tasks.','Record optional deadlines against tasks.'))
        ctx=selection.CALL.set({'operation':'business-revise','id':'REQ-0001','operation_id':'partial-business','runtime_session':token})
        original=business.atomic_bytes
        def fault(path,raw):
            if path.name=='business-history.yaml':raise OSError('Injected second-file failure')
            return original(path,raw)
        try:
            with patch.object(selection,'current_pin',return_value=selection.pin(self.runtime)),patch.object(business,'atomic_bytes',side_effect=fault):
                with self.assertRaises(Exception):sdlc.business_write(self.project,'REQ-0001',epic.source_revision,epic.business['revision'],'partial-business','Fixture PO','Explicit fictional wording refinement.',proposal,'revise')
        finally:selection.CALL.reset(ctx)
        self.assertTrue((self.directory/'.business-transaction.json').exists())
        self.cli(self.runtime,'runtime-recover',token=token)
        view=self.cli(self.runtime,'business-review','REQ-0001')
        self.assertIn('Record optional deadlines',view['epic']['business']['content'])
        receipt=[w['event'] for w in selection.read(self.directory)['events'] if w['event']['operation_id']=='partial-business']
        self.assertEqual(len(receipt),1);self.assertEqual(receipt[0]['runtime']['snapshot_digest'],self.a['snapshot_digest'])
        self.assertEqual(view['epic']['metadata']['status'],'business_refinement');self.assertFalse(view['approval']['valid'])

    def test_interrupted_new_has_exact_creation_intent_and_no_duplicate_request(self):
        class Crash(BaseException):pass
        token=self.context(epic=None);original=management.atomic
        def fault(path,raw):
            if path==selection.transaction(self.project) and json.loads(raw).get('after') is not None:raise Crash()
            return original(path,raw)
        ctx=selection.CALL.set({'operation':'new','runtime_session':token})
        try:
            with patch.object(selection,'current_pin',return_value=selection.pin(self.runtime)),patch.object(management,'atomic',side_effect=fault):
                with self.assertRaises(Crash):sdlc.new_epic(self.project,'Interrupted fixture','Preserve original fixture idea.','Fixture Requester')
        finally:selection.CALL.reset(ctx)
        self.cli(self.runtime,'runtime-recover',token=token)
        result=self.cli(self.runtime,'open','REQ-0001');self.directory=Path(result['epic']['directory'])
        self.assertIn('Preserve original fixture idea.',result['epic']['idea'])
        self.assertEqual(len([p for p in (self.project/'requirements').iterdir() if p.is_dir()]),1)
        self.assertEqual(len(selection.read(self.directory)['events']),2)

    def test_explicit_contract_incompatibility_is_not_a_version_number_comparison(self):
        self.new()
        def incompatible(source):
            path=source/'orchestrator/scripts/runtime_selection.py'
            path.write_text(path.read_text().replace("'evidence_contract':'source-bound-checks/1'","'evidence_contract':'incompatible-fixture/9'"))
        b=self.candidate(incompatible);report=selection.assessment(self.project,'REQ-0001',b['runtime'])
        self.assertEqual(report['classification'],'incompatible')
        before=(self.directory/selection.FILE).read_bytes()
        with self.assertRaises(Exception):self.select(b['runtime'])
        self.assertEqual(before,(self.directory/selection.FILE).read_bytes())

    def test_rollback_to_legacy_default_retains_managed_request_and_blocks_unprotected_new_work(self):
        self.new();b=self.candidate();self.select(b['runtime'])
        # Read exact existing committed legacy bytes; never modify the real checkout.
        legacy_root=self.base/'legacy-skills'
        legacy=install.install(install_fixture.REPO,'80b6c2e7098210f1cb920c69b8a914e63fd27451',
                               self.project,self.runtime_root,legacy_root,sys.executable)
        another_legacy=install.prepare(install_fixture.REPO,'80b6c2e7098210f1cb920c69b8a914e63fd27451',
                                      self.project,self.base/'other-legacy-runtimes',sys.executable)
        original_registration=install_fixture.hashes(legacy_root/'sdlc')
        with self.assertRaises(install.InstallError) as caught:
            management.switch(legacy_root,{'runtime':another_legacy['runtime'],'snapshot_digest':another_legacy['snapshot_digest']},
                              legacy['snapshot_digest'],'unsupported-legacy-switch','Fixture','Do not publish a broken resolver.','update')
        self.assertEqual(caught.exception.code,'E_INSTALL_CONTRACT')
        self.assertEqual(original_registration,install_fixture.hashes(legacy_root/'sdlc'))
        management.switch(legacy_root,{'runtime':b['runtime'],'snapshot_digest':b['snapshot_digest']},legacy['snapshot_digest'],
                          'legacy-update','Fixture operator','Update a legacy registration explicitly.','update')
        management.switch(legacy_root,None,b['snapshot_digest'],'legacy-rollback','Fixture operator','Restore legacy default only.','rollback')
        before=install_fixture.hashes(self.project)
        view=self.cli(b['runtime'],'runtime-status','REQ-0001','--skill-root',str(legacy_root))
        self.assertEqual(view['effective_runtime']['snapshot_digest'],b['snapshot_digest'])
        self.assertEqual(view['default_runtime']['snapshot_digest'],legacy['snapshot_digest'])
        view=self.cli(b['runtime'],'runtime-status','--skill-root',str(legacy_root))
        rejected=self.cli(b['runtime'],'runtime-session','--skill-root',str(legacy_root),'--fresh-context-id','legacy-new',
                          '--instructions-digest',view['instructions_digest'] or 'no-managed-contract',ok=False)
        self.assertEqual(rejected['diagnostics'][0]['code'],'E_RUNTIME_CONTRACT')
        self.assertEqual(before,install_fixture.hashes(self.project))

    def test_replaying_legacy_approval_does_not_invent_runtime_provenance(self):
        fixture=analysis_fixture.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        shutil.copytree(fixture.project/'requirements',self.project/'requirements');self.directory=next((self.project/'requirements').iterdir())
        self.select(self.runtime,initial=True);token=self.context();entry=self.epic().metadata['business_decisions'][-1]
        before=(self.directory/selection.FILE).read_bytes();baselines=install_fixture.hashes(self.directory/'business-baselines')
        result=self.cli(self.runtime,'business-approve','REQ-0001','--expected-review-revision',entry['review_revision'],
            '--expected-business-revision',entry['business_revision'],'--operation-id',entry['operation_id'],'--approver',entry['actor'],
            '--reason',entry['reason'],'--decision',entry['decision'],'--acknowledge-open-item','U-001',token=token)
        self.assertTrue(result['replayed']);self.assertEqual(before,(self.directory/selection.FILE).read_bytes())
        self.assertEqual(baselines,install_fixture.hashes(self.directory/'business-baselines'))
