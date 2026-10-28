"""Command and declared-identity fixtures; no real human approvals are simulated."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_business_approval as business_fixtures
import test_functional_analysis as analysis_fixtures
import sdlc
import command_ux
import local_identity as identity

SCRIPT = Path(sdlc.__file__)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.project=self.root/'project';self.project.mkdir()
        self.profile=self.root/'preferences'/'identity.json'
        env=patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(self.profile)})
        env.start();self.addCleanup(env.stop)

    def cli(self,*args,ok=True):
        p=subprocess.run([sys.executable,str(SCRIPT),'--project',str(self.project),*args],capture_output=True,text=True)
        data=json.loads(p.stdout)
        self.assertEqual(data['ok'],ok,p.stdout+p.stderr)
        self.assertEqual(p.returncode,0 if ok else 1)
        return data

    def reject(self,code,operation):
        with self.assertRaises(identity.IdentityError) as caught:operation()
        self.assertEqual(caught.exception.code,code)

    def create(self):
        return identity.save(self.project,'Fixture Person',['Product Owner','Requester'])

    def test_create_load_and_edit_preserve_declarations_without_authentication(self):
        created=self.create()
        self.assertEqual(identity.load(self.project),created)
        self.assertFalse(created['authenticated'])
        self.assertFalse(created['roles_enforced'])
        self.assertEqual(created['identity_source'],'local_profile')
        self.assertEqual(self.profile.stat().st_mode & 0o777,0o600)
        changed=identity.save(self.project,'Renamed Fixture',None,edit=True,expected_revision=created['profile_revision'])
        self.assertEqual(changed['declared_roles'],created['declared_roles'])
        edited=identity.save(self.project,None,['Analyst'],edit=True,expected_revision=changed['profile_revision'])
        self.assertEqual(edited['display_name'],'Renamed Fixture')
        self.assertEqual(set(json.loads(self.profile.read_text())),identity.FIELDS)
        self.assertEqual(list(self.project.iterdir()),[])

    def test_cli_setup_edit_and_fresh_process_reuse(self):
        setup=self.cli('identity-setup','--display-name','Fixture User','--role','Product Owner')
        fresh=self.cli('identity-show')
        self.assertEqual(setup['identity'],fresh['identity'])
        edited=self.cli('identity-edit','--expected-profile-revision',fresh['identity']['profile_revision'],'--display-name','Updated Fixture')
        self.assertEqual(self.cli('identity-show')['identity'],edited['identity'])

    def test_missing_profile_never_created_implicitly(self):
        result=self.cli('identity-show',ok=False)
        self.assertEqual(result['diagnostics'][0]['code'],'E_IDENTITY_MISSING')
        self.assertFalse(self.profile.exists())

    def test_setup_never_overwrites_existing_and_stale_edit_rejected(self):
        created=self.create()
        self.reject('E_IDENTITY_EXISTS',self.create)
        identity.save(self.project,'New Fixture',None,edit=True,expected_revision=created['profile_revision'])
        self.reject('E_IDENTITY_REVISION',lambda:identity.save(self.project,'Stale Fixture',None,edit=True,expected_revision=created['profile_revision']))

    def test_invalid_profiles_and_credentials_rejected_without_repair(self):
        self.profile.parent.mkdir()
        for text in ('!!map [hello]','{"display_name":"A","display_name":"B"}','[]',json.dumps({'schema_version':'0.1','display_name':'Fixture','declared_roles':['PO'],'token':'secret fixture'}),json.dumps({'schema_version':'0.1','display_name':'Fixture','declared_roles':[{}]}),json.dumps({'schema_version':'99','display_name':'Fixture','declared_roles':['PO']})):
            self.profile.write_text(text)
            self.reject('E_IDENTITY_PROFILE',lambda:identity.load(self.project))
            self.assertEqual(self.profile.read_text(),text)

    def test_invalid_setup_does_not_create_profile(self):
        for name,roles in (('', ['PO']),('Fixture',[]),('Fixture',['PO','PO']),('Fixture',[{}])):
            self.reject('E_IDENTITY_PROFILE',lambda:identity.save(self.project,name,roles))
            self.assertFalse(self.profile.exists())

    def test_project_repository_and_symlink_paths_rejected(self):
        for target in (self.project/'identity.json',identity.PACKAGE_ROOT/'identity.json'):
            with patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(target)}):
                self.reject('E_IDENTITY_PATH',self.create)
        external=self.root/'other-repository';external.mkdir();(external/'.git').mkdir()
        with patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(external/'identity.json')}):
            self.reject('E_IDENTITY_PATH',self.create)
        self.profile.parent.mkdir(exist_ok=True)
        self.profile.symlink_to(self.project/'identity.json')
        self.reject('E_IDENTITY_PATH',lambda:identity.load(self.project))
        self.assertFalse((self.project/'identity.json').exists())

    def test_default_xdg_path_and_relative_override_rejected(self):
        with patch.dict(os.environ,{'SDLC_IDENTITY_FILE':'','XDG_CONFIG_HOME':str(self.root/'config')}):
            self.assertEqual(identity.profile_path(self.project),(self.root/'config'/'ai-sdlc'/'identity.json').resolve())
        with patch.dict(os.environ,{'SDLC_IDENTITY_FILE':'relative.json'}):
            self.reject('E_IDENTITY_PATH',self.create)

    def test_concurrent_setup_and_lock_handling(self):
        def run(_):
            try:return self.create()
            except identity.IdentityError as e:return e.code
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sum(isinstance(r,dict) for r in results),1)
        self.assertIn(next(r for r in results if isinstance(r,str)),('E_IDENTITY_BUSY','E_IDENTITY_EXISTS'))
        self.assertFalse((self.profile.parent/'.identity.lock').exists())

    def test_profile_write_failure_does_not_replace_previous_data(self):
        previous=self.create();raw=self.profile.read_bytes()
        with patch.object(identity.os,'replace',side_effect=OSError('Injected write failure')):
            self.reject('E_IDENTITY_WRITE',lambda:identity.save(self.project,'Other',None,edit=True,expected_revision=previous['profile_revision']))
        self.assertEqual(self.profile.read_bytes(),raw)
        self.assertEqual(list(self.profile.parent.iterdir()),[self.profile])

    def test_explicit_legacy_attribution_does_not_require_profile_or_read_git(self):
        self.assertEqual(identity.attribution(self.project,'Explicit Fixture'),('Explicit Fixture',None))
        self.assertFalse(self.profile.exists())

    def test_profile_revision_binds_attribution_without_enforcing_roles(self):
        first=self.create()
        self.assertEqual(identity.attribution(self.project,None,first['profile_revision']),('Fixture Person','local_profile'))
        identity.save(self.project,'Changed Fixture',None,edit=True,expected_revision=first['profile_revision'])
        self.reject('E_IDENTITY_REVISION',lambda:identity.attribution(self.project,None,first['profile_revision']))

    def test_parent_symlink_into_project_is_rejected(self):
        self.profile.parent.symlink_to(self.project,target_is_directory=True)
        self.reject('E_IDENTITY_PATH',self.create)
        self.assertFalse((self.project/'identity.json').exists())


    def test_directory_is_invalid_profile_rather_than_missing_setup(self):
        self.profile.mkdir(parents=True)
        self.reject('E_IDENTITY_PROFILE',lambda:identity.load(self.project))

    def test_post_commit_profile_durability_failure_can_be_inspected(self):
        created=self.create()
        real=identity.os.fsync
        import stat
        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):raise OSError('Injected directory fsync failure')
            return real(fd)
        with patch.object(identity.os,'fsync',side_effect=fail_directory):
            self.reject('E_IDENTITY_WRITE_UNCERTAIN',lambda:identity.save(self.project,'Updated Fixture',None,edit=True,expected_revision=created['profile_revision']))
        self.assertEqual(identity.load(self.project)['display_name'],'Updated Fixture')
        self.assertFalse((self.profile.parent/'.identity.lock').exists())



class RoutingTests(unittest.TestCase):
    def test_all_six_commands_are_read_only_routes_at_each_lifecycle(self):
        expected={
            'discovery':('open',None,'discovery-update','discovery-complete'),
            'ready_for_refinement':('business-review',None,None,None),
            'business_refinement':('business-review','business-approve','business-request-changes','business-advance'),
            'ready_for_analysis':('analysis-review',None,None,None),
            'functional_analysis':('analysis-review','analysis-approve','analysis-request-changes','analysis-advance'),
            'ready_for_technical_design':('analysis-review',None,None,None),
            'cancelled':('open',None,None,None),
        }
        for status,(review,approve,changes,advance) in expected.items():
            for command in ("status", "review", "approve", "changes", "advance", "details"):
                with self.subTest(status=status,command=command):
                    route=command_ux.route(command,status)
                    self.assertTrue(route['read_only'])
                    self.assertEqual(route['review_operation'],review)
                    self.assertEqual(route['write_operation'],{'approve':approve,'changes':changes,'advance':advance}.get(command))

    def test_unknown_command_and_status_are_rejected(self):
        for command,status in (('implement','discovery'),('approve','technical_design')):
            with self.assertRaises(ValueError):command_ux.route(command,status)

    def test_missing_and_ambiguous_context_never_guess_or_write(self):
        with tempfile.TemporaryDirectory() as temporary,patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(Path(temporary)/'outside.json')}):
            project=Path(temporary)/'project';project.mkdir()
            def reject(code,command,selector=None):
                with self.assertRaises(sdlc.Rejected) as caught:sdlc.command_context(project,command,selector)
                self.assertIn(code,{d.code for d in caught.exception.diagnostics})
            reject('E_CONTEXT_MISSING','review')
            first=sdlc.new_epic(project,'First request','Original business idea.',requester='Fixture Requester')
            before=(Path(first['epic']['directory'])/'metadata.yaml').read_bytes()
            context=sdlc.command_context(project,'approve')
            self.assertIsNone(context['routing']['write_operation'])
            self.assertEqual(context['identity_diagnostic']['code'],'E_IDENTITY_MISSING')
            self.assertEqual((Path(first['epic']['directory'])/'metadata.yaml').read_bytes(),before)
            sdlc.new_epic(project,'Second request','Other idea.',requester='Fixture Requester')
            reject('E_CONTEXT_AMBIGUOUS','approve')
            reject('E_CONTEXT_MISSING','status','Missing title')
            self.assertEqual(sdlc.command_context(project,'details','first request')['review']['epic']['metadata']['id'],'REQ-0001')
            self.assertEqual(sdlc.command_context(project,'status','REQ-0002')['review']['epic']['metadata']['title'],'Second request')
            sdlc.new_epic(project,'REQ-0001','A title that resembles another stable ID.',requester='Fixture Requester')
            self.assertEqual(sdlc.command_context(project,'status','REQ-0001')['review']['epic']['metadata']['title'],'First request')
            reject('E_COMMAND','implement')


class ProfileGateTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.profile=Path(temporary.name)/'identity.json'
        env=patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(self.profile)})
        env.start();self.addCleanup(env.stop)
        self.fixture=business_fixtures.BusinessApprovalTests('test_approval_freezes_exact_context_and_advancement_is_separate')
        self.addCleanup(self.fixture.doCleanups);self.fixture.setUp()
        self.project=self.fixture.project
        identity.save(self.project,'Fixture Local Person',['Informational role only'])

    def cli(self,*args,ok=True):
        p=subprocess.run([sys.executable,str(SCRIPT),'--project',str(self.project),*args],capture_output=True,text=True)
        data=json.loads(p.stdout)
        self.assertEqual(data['ok'],ok,p.stdout+p.stderr)
        return data

    def business_args(self,v,operation_id):
        return ['--expected-review-revision',v['review_revision'],'--expected-business-revision',v['epic']['business']['revision'],'--operation-id',operation_id,'--reason','Fictional gate test']

    def test_profile_business_approval_and_advance_without_name_flags(self):
        v=self.fixture.view();words='Approve this reviewed draft.\nI acknowledge the deferred past-date question.'
        args=self.business_args(v,'profile-business-approve')+['--decision',words,'--acknowledge-open-item','U-001']
        r=self.cli('business-approve','REQ-0001',*args)
        entry=r['epic']['metadata']['business_decisions'][-1]
        self.assertEqual(entry['actor'],'Fixture Local Person')
        self.assertEqual(entry['identity_source'],'local_profile')
        self.assertEqual(entry['decision'],words)
        self.assertEqual(r['epic']['metadata']['status'],'business_refinement')
        self.assertTrue(self.cli('business-approve','REQ-0001',*args)['replayed'])
        self.assertIsNone(self.cli('command-context','approve')['routing']['write_operation'])
        v=self.fixture.view()
        advanced=self.cli('business-advance','REQ-0001',*self.business_args(v,'profile-business-advance'),'--approval-id',r['decision_id'])
        self.assertEqual(advanced['epic']['metadata']['status'],'ready_for_analysis')
        self.assertEqual(advanced['epic']['metadata']['lifecycle'][-1]['identity_source'],'local_profile')

    def test_missing_acknowledgement_and_stale_review_still_rejected(self):
        v=self.fixture.view();args=self.business_args(v,'missing-ack')+['--decision','Fixture approve']
        self.assertEqual(self.cli('business-approve','REQ-0001',*args,ok=False)['diagnostics'][0]['code'],'E_ACKNOWLEDGEMENT')
        self.fixture.revise(self.fixture.initial_document)
        args+=['--acknowledge-open-item','U-001']
        self.assertEqual(self.cli('business-approve','REQ-0001',*args,ok=False)['diagnostics'][0]['code'],'E_REVISION_CONFLICT')

    def test_profile_edit_does_not_rewrite_audit_or_reactivate_decisions(self):
        v=self.fixture.view();args=self.business_args(v,'before-identity-edit')+['--decision','Fixture approve','--acknowledge-open-item','U-001']
        first=self.cli('business-approve','REQ-0001',*args)
        old=identity.load(self.project)
        identity.save(self.project,'Other Fixture',None,edit=True,expected_revision=old['profile_revision'])
        self.assertEqual(self.fixture.view()['epic']['metadata']['business_decisions'],first['epic']['metadata']['business_decisions'])
        self.assertEqual(self.cli('business-approve','REQ-0001',*args,ok=False)['diagnostics'][0]['code'],'E_IDEMPOTENCY')

    def test_profile_missing_is_setup_error_without_gate_mutation(self):
        self.profile.unlink();v=self.fixture.view()
        result=self.cli('business-approve','REQ-0001',*self.business_args(v,'no-profile'),'--decision','Fixture approval',ok=False)
        self.assertEqual(result['diagnostics'][0]['code'],'E_IDENTITY_MISSING')
        self.assertEqual(self.fixture.view()['epic']['metadata'],v['epic']['metadata'])

    def test_read_only_approval_context_reuses_profile_without_decision(self):
        metadata=self.fixture.view()['epic']['metadata']
        for _ in range(2):
            v=self.cli('command-context','approve')
            self.assertEqual(v['identity']['display_name'],'Fixture Local Person')
            self.assertEqual(v['routing']['write_operation'],'business-approve')
            self.assertEqual(v['review']['epic']['metadata'],metadata)
        self.assertFalse((self.fixture.directory/'business-baselines').exists())

    def test_identity_source_cannot_claim_authentication_and_is_audited(self):
        self.fixture.rejected('E_UPDATE_INPUT',lambda:self.fixture.execute({**self.fixture.request(),'identity_source':'verified_enterprise'}))
        result=self.fixture.execute({**self.fixture.request(),'identity_source':'local_profile'})
        path=self.fixture.directory/'metadata.yaml'
        import yaml
        data=yaml.safe_load(path.read_text());data['business_decisions'][-1]['identity_source']='authenticated_host'
        path.write_text(yaml.safe_dump(data,sort_keys=False))
        self.fixture.rejected('E_BUSINESS_DECISIONS',self.fixture.view)

    def test_profile_discovery_completion_and_reopening_preserve_history(self):
        self.fixture.reopen()
        v=self.fixture.view()['epic']
        r=self.cli('discovery-complete','REQ-0001','--expected-revision',v['revision'],
            '--operation-id','profile-complete','--decision','Fixture: Discovery complete.')
        self.assertEqual(r['epic']['metadata']['status'],'ready_for_refinement')
        self.assertEqual(r['epic']['metadata']['lifecycle'][-1]['actor'],'Fixture Local Person')
        self.assertEqual(r['epic']['metadata']['lifecycle'][-1]['identity_source'],'local_profile')
        v=r['epic']
        reopened=self.cli('discovery-reopen','REQ-0001','--expected-revision',v['revision'],
            '--operation-id','profile-reopen','--decision','Fixture: reopen Discovery.')
        self.assertEqual(reopened['epic']['metadata']['status'],'discovery')
        self.assertEqual(reopened['epic']['metadata']['lifecycle'][:-1],v['metadata']['lifecycle'])

    def test_changed_profile_revision_rejects_attribution_before_gate_write(self):
        v=self.fixture.view();profile=identity.load(self.project)
        identity.save(self.project,'Other Fixture',None,edit=True,expected_revision=profile['profile_revision'])
        args=self.business_args(v,'stale-profile')+['--expected-profile-revision',profile['profile_revision'],
            '--decision','Fixture approve','--acknowledge-open-item','U-001']
        self.assertEqual(self.cli('business-approve','REQ-0001',*args,ok=False)['diagnostics'][0]['code'],'E_IDENTITY_REVISION')
        self.assertEqual(self.fixture.view()['epic']['metadata'],v['epic']['metadata'])



class AnalysisProfileTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        env=patch.dict(os.environ,{'SDLC_IDENTITY_FILE':str(Path(temporary.name)/'identity.json')})
        env.start();self.addCleanup(env.stop)
        self.fixture=analysis_fixtures.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        self.addCleanup(self.fixture.doCleanups);self.fixture.setUp();self.fixture.generate()
        self.project=self.fixture.project
        identity.save(self.project,'Fixture Analysis Owner',['Product Owner'])

    def cli(self,*args):
        p=subprocess.run([sys.executable,str(SCRIPT),'--project',str(self.project),*args],capture_output=True,text=True)
        data=json.loads(p.stdout);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        return data

    def args(self,v,op):
        return ['--expected-analysis-review-revision',v['analysis_review_revision'],'--expected-analysis-revision',v['epic']['analysis']['revision'],'--expected-baseline-id',v['input']['baseline_id'],'--expected-handoff-id',v['input']['handoff_id'],'--operation-id',op,'--reason','Fictional Analysis gate test']

    def test_fresh_process_analysis_approval_and_separate_advancement(self):
        context=self.cli('command-context','approve');v=context['review']
        self.assertEqual(context['routing']['write_operation'],'analysis-approve')
        args=self.args(v,'profile-analysis-approve')+['--decision','Approve.\nI acknowledge all listed uncertainties.']
        for item in v['analysis_open_items']:args+=['--acknowledge-open-item',item['id']]
        r=self.cli('analysis-approve','REQ-0001',*args)
        entry=r['epic']['metadata']['analysis_decisions'][-1]
        self.assertEqual(entry['identity_source'],'local_profile')
        self.assertEqual(entry['actor'],'Fixture Analysis Owner')
        self.assertEqual(r['epic']['metadata']['status'],'functional_analysis')
        self.assertTrue(self.cli('analysis-approve','REQ-0001',*args)['replayed'])
        view=self.cli('command-context','advance')['review']
        advanced=self.cli('analysis-advance','REQ-0001',*self.args(view,'profile-analysis-advance'),'--approval-id',r['decision_id'])
        self.assertEqual(advanced['epic']['metadata']['status'],'ready_for_technical_design')
        self.assertEqual(advanced['epic']['metadata']['lifecycle'][-1]['identity_source'],'local_profile')
        self.assertTrue(self.cli('analysis-review','REQ-0001')['analysis_approval']['valid'])

    def test_request_changes_uses_profile_and_preserves_actual_feedback(self):
        v=self.fixture.review();feedback='Please clarify this statement.\nKeep the deferred question unresolved.'
        r=self.cli('analysis-request-changes','REQ-0001',*self.args(v,'profile-analysis-feedback'),'--feedback',feedback)
        entry=r['epic']['metadata']['analysis_decisions'][-1]
        self.assertEqual(entry['actor'],'Fixture Analysis Owner')
        self.assertEqual(entry['decision'],feedback)
        self.assertEqual(entry['identity_source'],'local_profile')
        self.assertEqual(r['epic']['analysis']['content'],v['epic']['analysis']['content'])
