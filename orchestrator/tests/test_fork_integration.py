"""Joined-track regression probes; all human decisions are fictional fixtures.

Named tiny commands are executed, but do not claim real browser acceptance or
security certification. The external human acceptance project is never used.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_qa_track as fixtures
import engineering
import qa_track
import sdlc
import work_tracks


class ForkIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.QATrackTests('test_real_qa_execution_and_explicit_completion_gate')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.project,self.directory=self.fixture.project,self.fixture.directory

    def cli(self,*args,ok=True):
        result=subprocess.run([sys.executable,str(Path(sdlc.__file__)),'--project',str(self.project),*args],text=True,capture_output=True)
        self.assertEqual(result.stderr,'',result.stderr)
        value=json.loads(result.stdout)
        self.assertEqual(value['ok'],ok,value)
        self.assertEqual(result.returncode,0 if ok else 1)
        return value

    def test_failed_qa_check_returns_engineering_to_development_without_rewriting_qa(self):
        original=self.fixture.automation_doc
        def failing_doc():
            document=original()
            document['checks'][0]['argv']=[sys.executable,'-c','print("Fixture actual integration failure");raise SystemExit(1)']
            return document
        self.fixture.automation_doc=failing_doc
        self.fixture.reviewed_implementation()
        failure=self.fixture.run_check('QA-integration')
        evidence=failure['qa']['evidence'][-1]
        self.assertEqual(evidence['status'],'failed')
        self.assertEqual(evidence['exit_code'],1)
        qa_before=deepcopy(work_tracks.current(self.fixture.epic().metadata)['qa'])
        scenarios_approved=self.fixture.view()['approvals']['scenarios']
        changed=self.fixture.eng('remediate','verification',{'checks':['QA-integration']})
        self.assertEqual(changed['epic']['metadata']['status'],'development')
        self.assertEqual(work_tracks.current(self.fixture.epic().metadata)['qa'],qa_before)
        self.assertEqual(self.fixture.view()['approvals']['scenarios'],scenarios_approved)
        self.assertFalse(engineering.review(self.fixture.epic(),self.project)['approvals']['implementation']['valid'])
        entry=changed['epic']['metadata']['engineering_history'][-1]
        artifact,_=engineering.load_artifact(self.directory,entry['baseline_id'])
        self.assertEqual(artifact['payload']['failure_evidence']['QA-integration'],failure['baseline_id'])
        document=self.fixture.base()
        document.update(source_revision=qa_track.app_source(self.fixture.epic(),self.project),
                        plan=engineering.latest(self.fixture.epic(),'plan')[0]['baseline_id'],completed_tasks=['T-001'])
        self.fixture.reject('E_VERIFICATION',lambda:self.fixture.eng('write','implementation',document))

    def test_joined_security_and_final_report_require_current_completed_qa(self):
        self.fixture.reviewed_implementation()
        self.fixture.reject('E_INTEGRATION_NOT_READY',lambda:self.fixture.eng('advance','verification'))
        self.fixture.run_check('QA-integration');self.fixture.run_check('QA-ui')
        # Actual passes alone do not complete the QA track.
        self.fixture.reject('E_INTEGRATION_NOT_READY',lambda:self.fixture.eng('advance','verification'))
        self.fixture.update('advance','verification')
        self.fixture.eng('advance','verification')
        security=self.fixture.base()
        security.update(source_revision=qa_track.app_source(self.fixture.epic(),self.project),
                        plan=engineering.latest(self.fixture.epic(),'plan')[0]['baseline_id'],findings=[])
        self.fixture.eng('write','security',security)
        self.fixture.eng('advance','security')
        result=self.fixture.eng('finalize','final')
        self.assertEqual(result['epic']['metadata']['status'],'verified')
        report,_=engineering.load_artifact(self.directory,result['baseline_id'])
        self.assertEqual(set(report['payload']['checks']),{'unit','build','qa:QA-integration','qa:QA-ui'})
        self.assertEqual(report['payload']['qa_context'],qa_track.execution_context(self.fixture.epic(),self.project))
        self.assertTrue(engineering.review(self.fixture.epic(),self.project)['current'])
        (self.project/'qa/check.py').write_text('print("Fixture automation changed after final report")\n')
        self.assertFalse(engineering.review(self.fixture.epic(),self.project)['current'])
        self.assertTrue(self.fixture.view()['approvals']['scenarios']['valid'])
        self.assertFalse(self.fixture.view()['approvals']['automation']['valid'])

    def test_reopened_discovery_retains_scalar_requester_assignment(self):
        old=deepcopy(self.fixture.epic().metadata['work_tracks'])
        self.fixture.fixture.business_fixture.reopen()
        epic=self.fixture.epic()
        context=sdlc.command_context(self.project,'assign','REQ-0001')
        self.assertEqual(context['routing']['stage'],'discovery')
        self.assertEqual(context['routing']['required_role'],'Requester / Business Stakeholder')
        result=sdlc.ownership_change(self.project,'REQ-0001',epic.revision,'fixture-new-requester',
                                     'Fixture Requester','Fixture: assign Discovery to another requester.','Fixture New Requester')
        self.assertEqual(result['epic']['metadata']['ownership']['owner'],'Fixture New Requester')
        self.assertEqual(result['epic']['metadata']['work_tracks'],old)
        self.assertEqual(result['epic']['metadata']['status'],'discovery')

    def test_new_analysis_cycle_preserves_schema_after_engineering_history(self):
        self.fixture.eng('write','design',self.fixture.base())
        before=deepcopy(self.fixture.epic().metadata['engineering_history'])
        self.assertEqual(self.fixture.epic().metadata['schema_version'],'0.6')
        analysis_fixture=self.fixture.fixture
        original=self.fixture.epic().analysis['content']
        upstream=analysis_fixture.business_fixture
        upstream.reopen();upstream.complete()
        upstream.revise(upstream.initial_document,mode='generate')
        upstream.approve();upstream.advance()
        view=analysis_fixture.review()
        for field,prefix in [('baseline_id','Baseline: '),('approval_id','Approval: '),('handoff_id','Handoff: ')]:
            old=next(line[len(prefix):] for line in original.splitlines() if line.startswith(prefix))
            original=original.replace(prefix+old,prefix+view['input'][field])
        analysis_fixture.revise(original)
        approved=analysis_fixture.approve()
        self.assertEqual(approved['epic']['metadata']['schema_version'],'0.6')
        self.assertEqual(approved['epic']['metadata']['engineering_history'],before)
        advanced=analysis_fixture.advance()
        self.assertEqual(advanced['epic']['metadata']['schema_version'],'0.6')
        self.assertEqual(len(advanced['epic']['metadata']['work_tracks']['cycles']),2)
        for track in ('engineering','qa'):
            self.fixture.reject('E_TRACK_RECONCILIATION',lambda track=track:work_tracks.require_reconciled(self.fixture.epic(),track))

    def test_fresh_process_cli_qa_context_approval_and_separate_advancement(self):
        self.fixture.design_qa()
        ambiguous=self.cli('command-context','review','--request','REQ-0001',ok=False)
        self.assertEqual(ambiguous['diagnostics'][0]['code'],'E_TRACK_AMBIGUOUS')
        selected=self.cli('command-context','review','--request','REQ-0001','--track','qa')
        self.assertEqual(selected['routing']['track'],'qa')
        self.assertEqual(selected['review']['stage'],'test_design')
        before=self.cli('qa-review','REQ-0001')
        view=before['review'];words='Fixture: approve the reviewed QA scenarios.\nI acknowledge every listed unresolved item.'
        args=['qa-approve','REQ-0001','--kind','scenarios','--expected-qa-revision',view['revision'],
              '--operation-id','fixture-cli-qa-approve','--actor','Fixture QA Lead','--decision',words]
        for item in qa_track.unresolved(self.fixture.epic()):args+=['--acknowledge-open-item',item['id']]
        approved=self.cli(*args)
        self.assertEqual(approved['qa']['stage'],'test_design')
        self.assertEqual(approved['epic']['metadata']['status'],'ready_for_technical_design')
        self.assertEqual(work_tracks.current(approved['epic']['metadata'])['qa']['history'][-1]['decision'],words)
        fresh=self.cli('qa-review','REQ-0001')['review']
        self.cli('qa-advance','REQ-0001','--kind','scenarios','--expected-qa-revision',fresh['revision'],
                 '--operation-id','fixture-cli-qa-advance','--actor','Fixture QA Lead','--decision','Fixture: separately advance QA scenarios.')
        self.assertEqual(self.cli('qa-review','REQ-0001')['review']['stage'],'test_automation')
        malformed=self.cli('qa-advance','REQ-0001','--kind','automation','--expected-qa-revision',view['revision'],
                           '--operation-id','fixture-cli-qa-stale','--actor','Fixture QA Lead','--decision','Fixture: stale attempt.',ok=False)
        self.assertEqual(malformed['diagnostics'][0]['code'],'E_REVISION_CONFLICT')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.yaml';path.write_text('!!map hello')
            invalid=self.cli('qa-write','REQ-0001','--kind','automation','--input-file',str(path),
                             '--expected-qa-revision',fresh['revision'],'--operation-id','fixture-cli-qa-malformed',
                             '--actor','Fixture QA Lead','--decision','Fixture malformed draft.',ok=False)
            self.assertEqual(invalid['diagnostics'][0]['code'],'E_QA_DOCUMENT')
            self.assertEqual(Path(invalid['diagnostics'][0]['file']),path)
