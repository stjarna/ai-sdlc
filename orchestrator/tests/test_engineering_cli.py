"""Fresh-process CLI acceptance. Every approval/name is fictional fixture data."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import test_engineering as fixtures
import business_refinement as business
import command_ux
import engineering
import local_identity
import sdlc


class EngineeringCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.EngineeringTests('test_design_binds_exact_analysis_and_pinned_skills')
        self.addCleanup(self.fixture.doCleanups); self.fixture.setUp()
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.outside=Path(temp.name)
        self.profile=self.outside/'identity.json'
        self.env=dict(os.environ,SDLC_IDENTITY_FILE=str(self.profile))
        with unittest.mock.patch.dict(os.environ,self.env):
            local_identity.save(self.fixture.project,'Fixture architect',['Informational only'])

    def cli(self,*args,ok=True):
        r=subprocess.run([sys.executable,str(Path(sdlc.__file__)),'--project',str(self.fixture.project),*args],capture_output=True,text=True,env=self.env)
        self.assertEqual(r.stderr,'',r.stderr)
        obj=json.loads(r.stdout)
        self.assertEqual(obj['ok'],ok,obj)
        self.assertEqual(r.returncode,0 if ok else 1)
        return obj

    def test_fresh_process_drafting_approval_replay_and_stale_json_diagnostics(self):
        self.assertEqual(len(self.cli('skills')['skills']),4)
        review=self.cli('engineering-review','REQ-0001')['engineering']
        path=self.outside/'design.json';path.write_text(json.dumps(self.fixture.document('design')))
        common=['REQ-0001','--expected-engineering-revision',review['revision'],'--operation-id','cli-design-fixture','--decision','Fixture: draft this design.']
        self.cli('engineering-write',*common,'--kind','design','--input-file',str(path))
        self.assertTrue(self.cli('engineering-write',*common,'--kind','design','--input-file',str(path))['replayed'])
        stale=self.cli('engineering-advance',*common,'--kind','design',ok=False)
        self.assertEqual(stale['diagnostics'][0]['code'],'E_IDEMPOTENCY')
        current=self.cli('engineering-review','REQ-0001')['engineering']
        args=['REQ-0001','--kind','design','--expected-engineering-revision',current['revision'],'--operation-id','cli-approve-fixture','--decision','Fixture: approve these uncertainties.']
        for i in current['drafts']['design']['payload']['unresolved']: args+=['--acknowledge-open-item',i['id']]
        approved=self.cli('engineering-approve',*args)
        self.assertEqual(approved['epic']['metadata']['status'],'technical_design')
        self.assertIsNone(self.cli('command-context','approve','--request','REQ-0001')['routing']['write_operation'])
        self.assertEqual(approved['epic']['metadata']['engineering_history'][-1]['identity_source'],'local_profile')
        conflict=self.cli('engineering-advance','REQ-0001','--kind','design','--expected-engineering-revision',current['revision'],'--operation-id','cli-stale-fixture','--decision','Fixture advancement.',ok=False)
        self.assertEqual(conflict['diagnostics'][0]['code'],'E_REVISION_CONFLICT')
        self.assertEqual(Path(conflict['diagnostics'][0]['file']),self.fixture.directory/'metadata.yaml')

    def test_malformed_and_unexpected_input_nodes_are_structured(self):
        for index,value in enumerate(('!!map [hello]','!!map hello','[]','content: x\ncontent: y\n')):
            path=self.outside/'invalid.yaml';path.write_text(value)
            r=self.cli('engineering-write','REQ-0001','--kind','design','--expected-engineering-revision',self.fixture.review()['revision'],'--operation-id',f'bad-input-{index}','--decision','Fixture draft.','--input-file',str(path),ok=False)
            self.assertEqual(r['diagnostics'][0]['code'],'E_ENGINEERING_DOCUMENT')
            self.assertEqual(Path(r['diagnostics'][0]['file']),path)

    def test_same_role_drafting_preserves_explicit_assignment(self):
        epic=self.fixture.epic()
        sdlc.ownership_change(self.fixture.project,'REQ-0001',epic.revision,'fixture-assign-architect','Fixture owner','Fixture: assign Architect.','Fixture architect')
        before=self.fixture.epic().metadata['ownership']
        after=self.fixture.design()['epic']['metadata']['ownership']
        self.assertEqual(after,before)
        context=self.cli('command-context','assign','--request','REQ-0001')
        self.assertEqual(context['routing']['required_role'],'Engineering Lead / Architect')
        self.assertFalse(context['routing']['initialization_required'])

    def test_tasks_must_cover_scope_and_later_reviews_cannot_narrow_it(self):
        self.fixture.design()
        plan=self.fixture.document('plan')
        missing=deepcopy(plan);missing['tasks'][0]['requirements']=['AC-001']
        self.fixture.reject('E_ENGINEERING_TRACE',lambda:engineering.validate_document(self.fixture.epic(),'plan',missing))
        shell=deepcopy(plan);shell['checks'][0]['argv']=['bash','-c','true']
        self.fixture.reject('E_ENGINEERING_PLAN',lambda:engineering.validate_document(self.fixture.epic(),'plan',shell))
        self.fixture.approve('design');self.fixture.run_update('advance','design');self.fixture.run_update('write','plan',plan)
        impl=self.fixture.document('implementation');impl['coverage']['AC-001']['disposition']='excluded'
        self.fixture.reject('E_ENGINEERING_TRACE',lambda:engineering.validate_document(self.fixture.epic(),'implementation',impl))

    def test_failed_verification_can_return_to_development_with_linked_evidence(self):
        (self.fixture.project/'check.py').write_text('import app,sys\nassert app.value==1\nsys.exit(1 if sys.argv[1]=="integration" else 0)\n')
        self.fixture.implementation();self.fixture.approve('implementation');self.fixture.run_update('advance','implementation')
        failure=self.fixture.check('integration')
        obj,_=engineering.load_artifact(self.fixture.directory,failure['baseline_id'])
        self.assertEqual(obj['payload']['status'],'failed')
        back=self.fixture.run_update('remediate','verification',{'checks':['integration']})
        self.assertEqual(back['epic']['metadata']['status'],'development')
        linked,_=engineering.load_artifact(self.fixture.directory,back['baseline_id'])
        self.assertEqual(linked['payload']['failure_evidence']['integration'],failure['baseline_id'])
        self.fixture.reject('E_APPROVAL_STALE',lambda:engineering.approval(self.fixture.epic(),'implementation',self.fixture.review()['source_revision']))


class EngineeringRoutingTests(unittest.TestCase):
    def test_engineering_commands_are_stage_aware_and_never_execute(self):
        for stage,kind in [('technical_design','design'),('implementation_planning','plan'),('development','implementation')]:
            for command,operation in [('review',None),('approve','engineering-approve'),('changes','engineering-request-changes'),('advance','engineering-advance')]:
                route=command_ux.route(command,stage)
                self.assertEqual(route['write_operation'],operation)
                self.assertEqual(route['kind'],kind)
                self.assertTrue(route['read_only'])
        self.assertEqual(command_ux.route('advance','ready_for_development')['write_operation'],'development-start')
        self.assertIsNone(command_ux.route('advance','ready_for_implementation_planning')['write_operation'])
        self.assertIsNone(command_ux.route('approve','security_review')['write_operation'])

    def test_timeout_stops_spawned_children(self):
        with tempfile.TemporaryDirectory() as area:
            project=Path(area); marker=project/'leaked-child.txt'
            child='import time,pathlib;time.sleep(1.2);pathlib.Path('+repr(str(marker))+').write_text("leaked")'
            runner='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child)+']);time.sleep(10)'
            result=engineering.execute_check(project,{'argv':[sys.executable,'-c',runner],'cwd':'.','timeout':0.2})
            self.assertEqual(result['status'],'timeout')
            time.sleep(1.3)
            self.assertFalse(marker.exists())
