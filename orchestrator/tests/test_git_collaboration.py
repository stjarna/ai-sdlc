"""Native Git acceptance fixtures; actors/decisions are fictional, remotes local only."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import git_collaboration as bridge
import sdlc
import runtime_selection
import business_refinement as business
import test_business_approval as business_fixtures
import test_qa_track as qa_fixtures


class Interrupted(BaseException):pass


class GitCollaborationTests(unittest.TestCase):
    def setUp(self):
        area=tempfile.TemporaryDirectory();self.addCleanup(area.cleanup);self.area=Path(area.name).resolve()
        self.project=self.area/'application';self.project.mkdir();self.remote=self.area/'remote.git'
        self.environment=patch.dict(os.environ,{'SDLC_GIT_STATE_ROOT':str(self.area/'journals'),
            'GIT_AUTHOR_NAME':'Fixture Git Writer','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
            'GIT_COMMITTER_NAME':'Fixture Git Writer','GIT_COMMITTER_EMAIL':'fixture@example.invalid'})
        self.environment.start();self.addCleanup(self.environment.stop)
        self.git(self.area,'init','--bare',str(self.remote))
        self.number=0

    def git(self,project,*args):
        result=subprocess.run(['git','-C',str(project),*map(str,args)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);return result.stdout.strip()

    def initialize(self,project=None,policy='direct',branch='develop'):
        project=project or self.project
        self.git(project,'init','-b',branch)
        (project/bridge.CONFIG).write_text(yaml.safe_dump({'schema_version':'0.1','remote':'shared','integration_branch':branch,'policy':policy}))
        if not (project/'app.py').exists():(project/'app.py').write_text('value = 1\n')
        self.git(project,'add','--all');self.git(project,'commit','-m','Fictional application and imported legacy fixture')
        self.git(project,'remote','add','shared',str(self.remote));self.git(project,'push','-u','shared',branch)
        return bridge.head(project)

    def clone(self,name='other',branch='develop'):
        target=self.area/name;self.git(self.area,'clone','-b',branch,'-o','shared',str(self.remote),str(target));return target

    def authority(self,project=None):return bridge.fetch(project or self.project,bridge.config(project or self.project))
    def spec(self,cli,project=None,paths=None,request='REQ-0001',operation=None):
        self.number+=1
        return {'operation_id':operation or 'git-fixture-'+str(self.number),'expected_authority':self.authority(project),
                'allowed_paths':paths or ['requirements/REQ-0001-expenses'],'request_id':request,'cli':cli}
    def create(self,project=None,operation=None):
        return bridge.execute(project or self.project,self.spec(['new','--title','Expenses','--idea','Record everyday expenses.','--requester','Fixture Requester'],project,['requirements'],None,operation))
    def rejected(self,code,callback):
        with self.assertRaises(business.BusinessError) as caught:callback()
        self.assertEqual(caught.exception.code,code,str(caught.exception))

    def approve_cli(self,fixture,op='core-approval'):
        v=fixture.view()
        return ['business-approve','REQ-0001','--expected-review-revision',v['review_revision'],
            '--expected-business-revision',v['epic']['business']['revision'],'--operation-id',op,
            '--approver','Fixture Product Owner','--reason','Explicit fictional decision',
            '--decision','I explicitly approve this exact fixture revision; U-001 remains open.',
            '--acknowledge-open-item','U-001']

    def business_fixture(self):
        fixture=business_fixtures.BusinessApprovalTests('test_legacy_baseline_and_review_hash_golden')
        fixture.setUp(legacy_templates=True);self.addCleanup(fixture.doCleanups)
        self.project=fixture.project.resolve();self.initialize();return fixture

    def test_creation_revision_bound_lookup_retry_and_legacy_hashes(self):
        self.initialize();result=self.create();self.assertEqual(result['state'],'published')
        c=result['commit'];self.assertEqual(self.authority(),c)
        self.assertEqual(self.git(self.project,'show',c+':requirements/REQ-0001-expenses/idea.md'),
                         (self.project/'requirements/REQ-0001-expenses/idea.md').read_text().strip())
        reference=bridge.baseline(self.project,c,'requirements/REQ-0001-expenses/idea.md',result['reference']['event_id'],True)
        self.assertEqual(reference['commit'],c)
        self.assertFalse('sha256' in reference)
        self.assertEqual(bridge.recover(self.project,result['operation_id']),result)
        (self.project/'requirements/REQ-0001-expenses/idea.md').write_text('changed')
        self.rejected('E_GIT_BYTES',lambda:bridge.baseline(self.project,c,reference['path'],reference['event_id'],True))
        self.assertEqual(len(list((self.project/'requirements').glob('REQ-*'))),1)
        self.rejected('E_GIT_BASELINE',lambda:bridge.baseline(self.project,'HEAD',reference['path'],reference['event_id']))
        tree_oid=self.git(self.project,'rev-parse',c+'^{tree}')
        self.rejected('E_GIT_BASELINE',lambda:bridge.baseline(self.project,tree_oid,reference['path'],reference['event_id']))

    def test_actual_business_approval_and_separate_advancement_preserve_baselines(self):
        f=self.business_fixture();old={p.relative_to(f.directory):p.read_bytes() for p in f.directory.rglob('*') if p.is_file()}
        path=f.directory.relative_to(self.project).as_posix()
        result=bridge.execute(self.project,self.spec(self.approve_cli(f),paths=[path]))
        self.assertEqual(f.view()['epic']['metadata']['status'],'business_refinement')
        decision=f.view()['approval']['latest_decision']['id']
        reference=bridge.baseline(self.project,result['commit'],path+'/metadata.yaml',decision,True)
        self.assertEqual(reference['event_id'],decision)
        v=f.view();cli=['business-advance','REQ-0001','--expected-review-revision',v['review_revision'],'--expected-business-revision',v['epic']['business']['revision'],
            '--operation-id','core-advance','--actor','Fixture Product Owner','--reason','Explicit fixture advancement','--approval-id',decision]
        advanced=bridge.execute(self.project,self.spec(cli,paths=[path]));self.assertEqual(advanced['state'],'published')
        self.assertEqual(f.view()['epic']['metadata']['status'],'ready_for_analysis')
        for name,raw in old.items():
            if name.as_posix() not in ('metadata.yaml',):self.assertEqual((f.directory/name).read_bytes(),raw)

    def test_unwrapped_write_is_rejected_and_read_only_view_is_local(self):
        self.initialize()
        self.rejected('E_GIT_REQUIRED',lambda:sdlc.new_epic(self.project,'Forbidden',requester='Fixture'))
        self.assertFalse((self.project/'requirements').exists())
        self.create();epic=sdlc.inspect_epics(self.project,'open','REQ-0001')['epic']
        self.assertFalse(epic['git_publication']['authoritative']);self.assertTrue(epic['git_publication']['fresh_fetch_required'])

    def test_two_clones_racing_shared_lifecycle_only_one_publishes(self):
        self.initialize();other=self.clone();spec=self.spec(['new','--title','Expenses','--requester','Fixture'],paths=['requirements'],request=None)
        def run(p):
            try:return bridge.execute(p,deepcopy(spec))
            except business.BusinessError as exc:return {'error':exc.code}
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,[self.project,other]))
        self.assertEqual(sum(v.get('state')=='published' for v in results),1,results)
        self.assertEqual(sum('error' in v for v in results),1)
        winner=next(v for v in results if v.get('state')=='published')
        self.assertEqual(self.authority(),winner['commit'])
        self.assertEqual(len(self.git(self.project,'ls-tree','--name-only',self.authority()+':requirements').splitlines()),1)

    def test_dirty_workspace_and_index_preserved(self):
        self.initialize();p=self.project/'notes.txt';p.write_text('do not stage')
        before=p.read_bytes();self.rejected('E_GIT_DIRTY',lambda:self.create());self.assertEqual(p.read_bytes(),before)
        self.git(self.project,'add','--','notes.txt')
        self.rejected('E_GIT_INDEX',lambda:self.create());self.assertEqual(self.git(self.project,'diff','--cached','--name-only'),'notes.txt')

    def test_config_invalid_and_unknown_operations_are_structured(self):
        self.initialize();spec=self.spec([],request=None,paths=['requirements'])
        self.rejected('E_GIT_INPUT',lambda:bridge.execute(self.project,spec))
        spec['cli']=['identity-setup'];self.rejected('E_GIT_INPUT',lambda:bridge.execute(self.project,spec))
        (self.project/bridge.CONFIG).write_text('!!map [broken]')
        self.rejected('E_GIT_CONFIG',lambda:bridge.config(self.project))

    def test_offline_fetch_does_not_apply_or_change_files(self):
        self.initialize();spec=self.spec(['new','--title','Expenses','--requester','Fixture'],paths=['requirements'],request=None)
        self.remote.rename(self.area/'unavailable.git')
        self.rejected('E_GIT_COMMAND',lambda:bridge.execute(self.project,spec))
        self.assertFalse((self.project/'requirements').exists());self.assertEqual(self.git(self.project,'status','--porcelain'),'')

    def test_push_rejection_recovery_does_not_duplicate_human_approval(self):
        f=self.business_fixture();path=f.directory.relative_to(self.project).as_posix();before=self.authority()
        hook=self.remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
        spec=self.spec(self.approve_cli(f),paths=[path])
        self.rejected('E_GIT_COMMAND',lambda:bridge.execute(self.project,spec))
        record=bridge.read_record(self.project,spec['operation_id']);self.assertEqual(record['state'],'push_pending')
        self.assertEqual(self.authority(),before);self.assertFalse(bridge.view(record)['authoritative'])
        history=deepcopy(f.view()['epic']['metadata']['business_decisions'])
        hook.unlink();result=bridge.recover(self.project,spec['operation_id']);self.assertEqual(result['state'],'published')
        self.assertEqual(f.view()['epic']['metadata']['business_decisions'],history)
        self.assertEqual(bridge.execute(self.project,spec),result)

    def test_failed_authentication_is_injected_without_a_false_publication(self):
        self.initialize();native=bridge.git
        def denied(project,*args,**kw):
            if args[0]=='push':bridge.require(False,'Fictional authentication failure.','E_GIT_COMMAND')
            return native(project,*args,**kw)
        with patch.object(bridge,'git',side_effect=denied):self.rejected('E_GIT_COMMAND',lambda:self.create())
        record=bridge.records(self.project)[0];self.assertEqual(record['state'],'push_pending')
        self.assertFalse(bridge.view(record)['authoritative'])
        self.assertEqual(bridge.recover(self.project,record['id'])['state'],'published')

    def test_interrupted_commit_recovers_by_correlation_without_reapplying(self):
        self.initialize();native=bridge.save
        def interrupted(project,record,state=None):
            if state=='committed':raise Interrupted()
            return native(project,record,state)
        with patch.object(bridge,'save',side_effect=interrupted):
            with self.assertRaises(Interrupted):self.create()
        record=bridge.records(self.project)[0];self.assertEqual(record['state'],'commit_pending')
        c=bridge.head(self.project);result=bridge.recover(self.project,record['id'])
        self.assertEqual(result['commit'],c);self.assertEqual(result['state'],'published')
        self.assertEqual(len(list((self.project/'requirements').glob('REQ-*'))),1)

    def test_interrupted_successful_push_recovers_remote_receipt(self):
        self.initialize();native=bridge.save
        def interrupted(project,record,state=None):
            if state=='published':raise Interrupted()
            return native(project,record,state)
        with patch.object(bridge,'save',side_effect=interrupted):
            with self.assertRaises(Interrupted):self.create()
        record=bridge.records(self.project)[0];self.assertEqual(record['state'],'push_pending')
        result=bridge.recover(self.project,record['id']);self.assertEqual(result['state'],'published')
        self.assertEqual(result['commit'],self.authority())

    def test_protected_proposal_pending_until_explicit_external_merge(self):
        initial=self.initialize(policy='pull_request');integrator=self.clone();self.git(self.project,'switch','-c','feature/request')
        # Policy forbids direct publication by the bridge; only the explicit
        # external integrator is permitted by the fixture server hook below.
        permit=self.area/'permit-integration';hook=self.remote/'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nwhile read old new ref; do\nif [ "$ref" = refs/heads/develop ] && [ ! -e "'+str(permit)+'" ]; then exit 1; fi\ndone\n');hook.chmod(0o755)
        result=self.create();self.assertEqual(result['state'],'pr_pending');self.assertFalse(result['authoritative']);self.assertEqual(self.authority(),initial)
        self.rejected('E_GIT_COMMAND',lambda:bridge.confirm(self.project,result['operation_id']))
        self.git(integrator,'fetch','shared','feature/request');self.git(integrator,'merge','--no-ff','--no-edit',result['commit'])
        permit.write_text('Explicit fictional integration authorization');self.git(integrator,'push','shared','develop')
        confirmed=bridge.confirm(self.project,result['operation_id']);self.assertTrue(confirmed['authoritative'])
        self.assertEqual(sdlc.selected_epic(self.project,'REQ-0001').metadata['status'],'discovery')

    def test_protected_merge_with_intervening_authority_remains_pending(self):
        self.initialize(policy='pull_request');other=self.clone();self.git(self.project,'switch','-c','feature/request');result=self.create()
        (other/'app.py').write_text('value = 2\n');self.git(other,'add','--','app.py');self.git(other,'commit','-m','Unrelated source evolution')
        self.git(other,'fetch','shared','feature/request');self.git(other,'merge','--no-ff','--no-edit',result['commit']);self.git(other,'push','shared','develop')
        self.rejected('E_GIT_STALE',lambda:bridge.confirm(self.project,result['operation_id']))
        self.assertEqual(bridge.read_record(self.project,result['operation_id'])['state'],'pr_pending')

    def test_two_working_branches_are_not_authority_and_stale_integration_blocked(self):
        self.initialize();other=self.clone()
        results=[]
        for p,name,file in ((self.project,'engineering','app.py'),(other,'qa','qa/check.py')):
            self.git(p,'switch','-c','feature/'+name);target=p/file;target.parent.mkdir(exist_ok=True);target.write_text('print("Fictional working output")\n')
            spec=self.spec([],p,[file],None);spec.pop('cli');results.append(bridge.execute(p,spec,'working'))
        self.assertTrue(all(r['state']=='working_published' and not r['authoritative'] for r in results))
        self.assertTrue(bridge.integration_check(self.project,results[0]['commit'],self.authority())['eligible_at_fetch'])
        integration=self.clone('integration');(integration/'new.txt').write_text('authority evolved')
        self.git(integration,'add','--','new.txt');self.git(integration,'commit','-m','Evolved authority');self.git(integration,'push','shared','develop')
        self.rejected('E_GIT_STALE',lambda:bridge.integration_check(self.project,results[0]['commit'],results[0]['reference']['commit']))

    def test_evidence_requires_exact_tested_commit_and_detects_changed_source(self):
        self.initialize();self.create();tip=self.authority()
        spec=self.spec(['qa-check-run','REQ-0001'],paths=['requirements/REQ-0001-expenses','qa/REQ-0001'])
        self.rejected('E_GIT_TESTED',lambda:bridge.execute(self.project,spec))
        self.assertEqual(bridge.source(self.project,tip),bridge.source(self.project))
        self.git(self.project,'switch','-c','feature/changed');(self.project/'app.py').write_text('value = 2\n')
        w=self.spec([],paths=['app.py'],request=None);w.pop('cli');w['tested_commit']=tip
        self.rejected('E_GIT_TESTED',lambda:bridge.execute(self.project,w,'working'))
        self.assertEqual((self.project/'app.py').read_text(),'value = 2\n')

    def test_phase_sync_only_clean_fast_forward_never_feature_rebase(self):
        self.initialize();other=self.clone();(other/'notes.md').write_text('new upstream')
        self.git(other,'add','--','notes.md');self.git(other,'commit','-m','Upstream');self.git(other,'push','shared','develop')
        self.assertEqual(bridge.sync(self.project)['head'],bridge.head(other))
        self.git(self.project,'switch','-c','feature/work');self.rejected('E_GIT_BRANCH',lambda:bridge.sync(self.project))

    def test_runtime_contract_missing_marker_does_not_enable_managed_bypass(self):
        self.initialize();current=runtime_selection.capabilities(self.project)
        self.assertEqual(current['collaboration_contract'],'git-native/1')
        old=deepcopy(current);old.pop('collaboration_contract')
        self.assertFalse(runtime_selection.compatible_contracts(old,current))
        legacy=deepcopy(current);legacy['collaboration_contract']='legacy-local/1'
        self.assertTrue(runtime_selection.compatible_contracts(old,legacy))

    def test_stale_qa_after_real_upstream_reopen_with_no_text_conflict(self):
        # unittest method name must exist; setup establishes an approved Analysis
        # with independent work tracks, without inventing a real user's decision.
        f=qa_fixtures.QATrackTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        self.project=f.project.resolve();f.development();f.prepare_qa()
        self.assertEqual(f.epic().metadata['status'],'development')
        self.initialize();qa=self.clone('qa-clone')
        self.git(qa,'switch','-c','feature/qa');(qa/'qa').mkdir();(qa/'qa/check.py').write_text('print("QA work consuming baseline A")\n')
        w=self.spec([],qa,['qa/check.py'],'REQ-0001');w.pop('cli');work=bridge.execute(qa,w,'working')
        before=sdlc.selected_epic(self.project,'REQ-0001');old_history=deepcopy(before.metadata['analysis_decisions'])
        path=before.directory.relative_to(self.project).as_posix()
        cli=['discovery-reopen','REQ-0001','--expected-revision',before.revision,'--operation-id','core-upstream-reopen','--requester','Fixture Requester','--decision','Explicit fictional reopen to clarify a missing requirement.']
        reopened=bridge.execute(self.project,self.spec(cli,paths=[path]));self.assertEqual(reopened['state'],'published')
        self.assertEqual(sdlc.selected_epic(self.project,'REQ-0001').metadata['status'],'discovery')
        # Disjoint metadata vs qa/check.py changes merge textually, but source
        # consumption remains A and cannot approve/integrate under new authority.
        self.assertEqual(self.git(qa,'diff','--name-only',work['commit']+'^',work['commit']),'qa/check.py')
        self.assertNotIn('qa/check.py',self.git(self.project,'diff','--name-only',reopened['commit']+'^',reopened['commit']).splitlines())
        stale=self.spec(['qa-approve','REQ-0001'],qa,[path]);stale['expected_authority']=w['expected_authority']
        self.rejected('E_GIT_STALE',lambda:bridge.execute(qa,stale))
        self.rejected('E_GIT_STALE',lambda:bridge.integration_check(qa,work['commit'],reopened['commit']))
        self.assertEqual(sdlc.selected_epic(self.project,'REQ-0001').metadata['analysis_decisions'][:len(old_history)],old_history)
        self.assertEqual((qa/'qa/check.py').read_text(),'print("QA work consuming baseline A")\n')

    def test_actual_approval_race_preserves_one_shared_decision(self):
        f=self.business_fixture();other=self.clone();path=f.directory.relative_to(self.project).as_posix()
        cli=self.approve_cli(f);first=self.spec(cli,paths=[path]);second=deepcopy(first)
        second['operation_id']='second-publication';second['cli']=list(cli);second['cli'][second['cli'].index('--operation-id')+1]='second-human-decision'
        def run(pair):
            try:return bridge.execute(*pair)
            except business.BusinessError as exc:return {'error':exc.code}
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,[(self.project,first),(other,second)]))
        self.assertEqual(sum(r.get('state')=='published' for r in results),1)
        data=yaml.safe_load(self.git(self.project,'show',self.authority()+':'+path+'/metadata.yaml'))
        self.assertEqual(len(data['business_decisions']),1)
        self.assertEqual(data['status'],'business_refinement')

    def test_conflicting_work_is_preserved_and_needs_new_integration_review(self):
        original=self.initialize();other=self.clone();receipts=[]
        for i,p in enumerate((self.project,other)):
            self.git(p,'switch','-c','feature/work-'+str(i));(p/'app.py').write_text('value = '+str(i+2)+'\n')
            spec=self.spec([],p,['app.py'],None);spec.pop('cli');receipts.append(bridge.execute(p,spec,'working'))
        integrator=self.clone('integrator');self.git(integrator,'fetch','shared','feature/work-0')
        self.git(integrator,'merge','--ff-only',receipts[0]['commit']);self.git(integrator,'push','shared','develop')
        self.rejected('E_GIT_STALE',lambda:bridge.integration_check(other,receipts[1]['commit'],original))
        self.assertEqual((other/'app.py').read_text(),'value = 3\n');self.assertEqual(bridge.head(other),receipts[1]['commit'])

    def test_tested_commit_is_persisted_in_git_not_only_external_receipt(self):
        initial=self.initialize();self.git(self.project,'switch','-c','feature/qa')
        (self.project/'qa').mkdir();(self.project/'qa/check.py').write_text('print("QA fixture")\n')
        spec=self.spec([],paths=['qa/check.py'],request=None);spec.pop('cli');spec['tested_commit']=initial
        result=bridge.execute(self.project,spec,'working')
        self.assertIn('SDLC-Tested-Commit: '+initial,self.git(self.project,'show','-s','--format=%B',result['commit']))
        self.assertEqual(bridge.source(self.project,initial),bridge.source(self.project))

    def test_unauthorized_hook_staging_is_not_published(self):
        initial=self.initialize();hook=self.project/'.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nprintf "unexpected" > injected.txt\ngit add -- injected.txt\n');hook.chmod(0o755)
        self.rejected('E_GIT_COMMIT',lambda:self.create())
        self.assertEqual(self.authority(),initial);self.assertTrue((self.project/'injected.txt').exists())
        self.assertEqual(bridge.records(self.project)[0]['state'],'commit_pending')

    def test_commit_failure_retry_checks_index_bytes(self):
        self.initialize();hook=self.project/'.git/hooks/pre-commit';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
        self.rejected('E_GIT_COMMAND',lambda:self.create());record=bridge.records(self.project)[0]
        self.assertEqual(record['state'],'commit_pending');hook.unlink()
        result=bridge.recover(self.project,record['id']);self.assertEqual(result['state'],'published')
        self.assertEqual(len(list((self.project/'requirements').glob('REQ-*'))),1)

    def test_explicit_abandon_preserves_all_local_work_and_decision(self):
        initial=self.initialize();hook=self.remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
        self.rejected('E_GIT_COMMAND',lambda:self.create());record=bridge.records(self.project)[0];local=bridge.head(self.project)
        result=bridge.abandon(self.project,record['id'],'Fixture Operator','Preserve this local proposal; reconcile in another clone.')
        self.assertEqual(result['state'],'abandoned');self.assertEqual(bridge.head(self.project),local);self.assertEqual(self.authority(),initial)
        self.assertTrue((self.project/'requirements/REQ-0001-expenses/metadata.yaml').exists())
        self.assertEqual(bridge.read_record(self.project,record['id'])['abandonment']['actor'],'Fixture Operator')

    def test_approval_cannot_reference_unapproved_working_document(self):
        f=self.business_fixture();path=f.directory.relative_to(self.project).as_posix()
        result=bridge.execute(self.project,self.spec(self.approve_cli(f),paths=[path]));decision=f.view()['approval']['latest_decision']['id']
        reference=bridge.baseline(self.project,result['commit'],path+'/business.md',decision)
        self.assertEqual(reference['binding'],'approval')
        # Corrupt a new, unapproved working revision only in this disposable Git
        # fixture; an old approval must not be asserted for its different blob.
        (f.directory/'business.md').write_text('A different unapproved document.\n')
        self.git(self.project,'add','--',path+'/business.md');self.git(self.project,'commit','-m','Unapproved working document fixture')
        self.rejected('E_GIT_BASELINE',lambda:bridge.baseline(self.project,bridge.head(self.project),path+'/business.md',decision))
        self.assertEqual(bridge.baseline(self.project,result['commit'],path+'/business.md',decision)['commit'],result['commit'])


    def test_cli_missing_or_malformed_request_keeps_json_diagnostics(self):
        self.initialize();missing=self.area/'missing.json'
        for text in (None,'[]','{"operation_id":'):
            if text is not None:missing.write_text(text)
            run=subprocess.run([sys.executable,'-B',str(Path(bridge.__file__)),
                '--project',str(self.project),'run','--request-file',str(missing)],capture_output=True,text=True)
            result=json.loads(run.stdout);self.assertEqual(run.returncode,1);self.assertFalse(result['ok'])
            self.assertTrue(result['diagnostics']);self.assertEqual(run.stderr,'')
        self.assertEqual(self.git(self.project,'status','--porcelain'),'')

    def test_recovery_rejects_retargeted_remote_without_publication(self):
        initial=self.initialize();hook=self.remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
        self.rejected('E_GIT_COMMAND',lambda:self.create());record=bridge.records(self.project)[0]
        other=self.area/'unrelated.git';self.git(self.area,'clone','--bare',str(self.remote),str(other))
        self.git(self.project,'remote','set-url','shared',str(other))
        self.rejected('E_GIT_CONFIG',lambda:bridge.recover(self.project,record['id']))
        self.assertEqual(self.git(other,'rev-parse','refs/heads/develop'),initial)
        self.assertEqual(bridge.read_record(self.project,record['id'])['state'],'push_pending')


    def test_interrupted_proposal_receipt_recovers_after_external_integration(self):
        self.initialize(policy='pull_request');integrator=self.clone();self.git(self.project,'switch','-c','feature/request')
        native=bridge.save
        def interrupted(project,record,state=None):
            if state=='pr_pending':raise Interrupted()
            return native(project,record,state)
        with patch.object(bridge,'save',side_effect=interrupted):
            with self.assertRaises(Interrupted):self.create()
        record=bridge.records(self.project)[0];self.assertEqual(record['state'],'push_pending')
        self.git(integrator,'fetch','shared','feature/request');self.git(integrator,'merge','--no-ff','--no-edit',record['commit'])
        self.git(integrator,'push','shared','develop')
        pending=bridge.recover(self.project,record['id']);self.assertEqual(pending['state'],'pr_pending');self.assertFalse(pending['authoritative'])
        self.assertEqual(bridge.confirm(self.project,record['id'])['state'],'published')


    def test_second_creation_stages_only_new_request_and_preserves_first(self):
        self.initialize();first=self.create();before={p.relative_to(self.project).as_posix():p.read_bytes()
            for p in (self.project/'requirements/REQ-0001-expenses').rglob('*') if p.is_file()}
        second=self.create();self.assertEqual(second['state'],'published')
        names=self.git(self.project,'diff','--name-only',first['commit'],second['commit']).splitlines()
        self.assertTrue(names);self.assertTrue(all(n.startswith('requirements/REQ-0002-expenses/') for n in names))
        for name,raw in before.items():self.assertEqual((self.project/name).read_bytes(),raw)
        self.assertEqual(sdlc.selected_epic(self.project,'REQ-0002').metadata['id'],'REQ-0002')
        self.assertEqual(self.authority(),second['commit'])


    def test_authorized_filenames_are_literal_not_git_pathspec_patterns(self):
        self.initialize();self.git(self.project,'switch','-c','feature/literal')
        name=':(glob)notes.txt';(self.project/name).write_text('Literal filename only.\n')
        spec=self.spec([],paths=[name],request=None);spec.pop('cli')
        result=bridge.execute(self.project,spec,'working');self.assertEqual(result['state'],'working_published')
        self.assertEqual(self.git(self.project,'show',result['commit']+':'+name),'Literal filename only.')
        self.assertEqual(self.git(self.project,'status','--porcelain'),'')



if __name__=='__main__':unittest.main()
