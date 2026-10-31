"""Early domain provenance/contracts; fixture wording is not model-output proof."""
from copy import deepcopy
from types import SimpleNamespace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import sdlc
import domain_skills as domains
import discovery_history as discovery
import business_refinement as business
import functional_analysis as analysis
import runtime_selection as runtime
import runtime_management as management
import install
import runtime_fixtures
import test_functional_analysis as analysis_fixture
import test_installation as installation_fixture
import test_runtime_selection as runtime_fixture

EARLY={'discovery':'discovery','business-requirements':'business_refinement','functional-analysis':'functional_analysis'}


class EarlyDomainTests(unittest.TestCase):
    def test_seven_catalog_packages_pinned_retained_and_stage_compatible(self):
        catalog=domains.catalog(sdlc.StrictLoader)
        self.assertEqual(set(catalog),set(EARLY)|{'architecture','development','testing','security'})
        for name,stage in EARLY.items():
            info=catalog[name];self.assertEqual(info['version'],'1.0.0')
            retained=domains.ROOT/'versions'/name/'1.0.0'
            self.assertEqual(domains.package(retained),info['digest'])
            pins=domains.for_stage(stage,sdlc.StrictLoader)
            domains.validate_pins(pins,name,stage)
            self.assertEqual(pins,{name:{k:info[k] for k in ('version','digest')}})

    def test_actual_cli_stage_resolution_read_only(self):
        import subprocess
        with tempfile.TemporaryDirectory() as area:
            before=list(Path(area).iterdir())
            for stage,name in [('discovery','discovery'),('ready_for_refinement','business-requirements'),('ready_for_analysis','functional-analysis'),('technical_design','architecture'),('test_design','testing')]:
                run=subprocess.run([sys.executable,'-B',str(Path(sdlc.__file__)),'--project',area,'skills','--stage',stage],capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertIn(name,json.loads(run.stdout)['selection'])
            self.assertEqual(list(Path(area).iterdir()),before)

    def test_representative_discovery_projection_is_unchanged_by_extraction(self):
        records=[{'kind':'question','topic':'scope','text':'Which users?','source':{'actor':'ai'}},
                 {'kind':'user_statement','topic':'scope','text':'Individual users.','answers':'D-0001','source':{'actor':'user','quote':'Individual users.'}},
                 {'kind':'question','topic':'scope','text':'Shared accounts?','source':{'actor':'ai'}},
                 {'kind':'human_decision','topic':'scope','text':'Defer.','action':'defer','target':'D-0003','source':{'actor':'user','quote':'Defer.'}}]
        old,old_op=discovery.append(discovery.empty('REQ-0001'),'REQ-0001','same-input','a'*64,records)
        pins=domains.for_stage('discovery',sdlc.StrictLoader)
        new,new_op=discovery.append(discovery.empty('REQ-0001'),'REQ-0001','same-input','a'*64,records,pins)
        self.assertEqual(discovery.project(old,'REQ-0001'),discovery.project(new,'REQ-0001'))
        self.assertEqual(old_op['records'],new_op['records'])
        self.assertEqual(discovery.requested_records(new_op),records)
        self.assertEqual(business.source_sets(old,discovery.project(old,'REQ-0001')),business.source_sets(new,discovery.project(new,'REQ-0001')))
        mixed,_=discovery.append(old,'REQ-0001','later','b'*64,[],pins)
        self.assertEqual(mixed['operations'][0],old_op)
        self.assertEqual(mixed['operations'][1]['skills'],pins)

    def test_new_and_discovery_update_pin_expertise_without_rewriting_idea(self):
        with tempfile.TemporaryDirectory() as area:
            root=Path(area);epic=sdlc.new_epic(root,'Expenses','Help understand spending.','Fixture Requester')['epic'];directory=Path(epic['directory'])
            self.assertEqual(epic['metadata']['domain_provenance']['idea'],domains.for_stage('discovery',sdlc.StrictLoader))
            original=(directory/'idea.md').read_bytes()
            result=sdlc.discovery_update(root,'REQ-0001',epic['revision'],'record',[])
            ledger=yaml.safe_load((directory/'discovery.yaml').read_text())
            self.assertEqual(ledger['schema_version'],'0.2');self.assertIn('discovery',ledger['operations'][0]['skills'])
            self.assertTrue(sdlc.discovery_update(root,'REQ-0001',epic['revision'],'record',[])['replayed'])
            self.assertEqual((directory/'idea.md').read_bytes(),original)
            self.assertEqual(result['epic']['metadata']['status'],'discovery')
            malformed=deepcopy(ledger);malformed['operations'][0]['skills']['discovery']['digest']='0'*64
            with self.assertRaises(business.BusinessError):discovery.project(malformed,'REQ-0001')

    def test_retained_pin_remains_readable_after_catalog_rollforward(self):
        import shutil
        with tempfile.TemporaryDirectory() as area:
            root=Path(area)/'skills';shutil.copytree(domains.ROOT,root)
            pins=domains.for_stage('discovery',sdlc.StrictLoader)
            (root/'discovery/SKILL.md').write_text('A future current package.\n')
            with patch.object(domains,'ROOT',root):
                domains.validate_pins(pins,'discovery','discovery')
                (root/'versions/discovery/1.0.0/SKILL.md').write_text('Corrupt retained package.\n')
                with self.assertRaises(business.BusinessError):domains.validate_pins(pins,'discovery','discovery')

    def test_business_and_analysis_new_envelopes_and_legacy_equivalence(self):
        fixture=analysis_fixture.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        before=installation_fixture.hashes(fixture.directory/'business-baselines')
        view=fixture.review();content=analysis_fixture.document(view['input'])
        generated=sdlc.analysis_write(**fixture.request(content))
        self.assertTrue(generated['ok'],generated)
        for file,name,stage in [('business-history.yaml','business-requirements','business_refinement'),('analysis-history.yaml','functional-analysis','functional_analysis')]:
            data=yaml.safe_load((fixture.directory/file).read_text());self.assertEqual(data['schema_version'],'0.3')
            self.assertEqual(data['revisions'][-1]['skills'],domains.for_stage(stage,sdlc.StrictLoader))
            old=deepcopy(data);old['schema_version']='0.2'
            for entry in old['revisions']:entry.pop('skills',None);entry['schema_version']='0.2'
            if name=='business-requirements':
                business.validate_history(old,'REQ-0001')
                prior=deepcopy(old['revisions'])
                appended=business.append(old,'REQ-0001',business.decode_revision(prior[-1]),prior[-1]['source_revision'],'Fixture PO','Fixture wording review.','new-sourced-revision','revise',prior[-1]['template'],domains.for_stage(stage,sdlc.StrictLoader))
                self.assertEqual(appended['revisions'][:-1],prior)
                self.assertEqual(appended['revisions'][-1]['schema_version'],'0.3')
            else:analysis.validate_history(old,'REQ-0001',fixture.directory,sdlc.StrictLoader)
            self.assertEqual([business.decode_revision(e) for e in data['revisions']],[business.decode_revision(e) for e in old['revisions']])
        self.assertEqual(before,installation_fixture.hashes(fixture.directory/'business-baselines'))
        self.assertEqual(sdlc.inspect_epics(fixture.project,'open','REQ-0001')['epic']['metadata']['status'],'functional_analysis')
        self.assertFalse(fixture.review()['analysis_approval']['valid'])

    def test_domain_drift_rejects_new_write_without_partial_creation(self):
        with tempfile.TemporaryDirectory() as area:
            root=Path(area)
            with patch.object(domains,'assert_current',side_effect=business.BusinessError('E_SKILL','Changed pin.')):
                with self.assertRaises(business.BusinessError):sdlc.new_epic(root,'Example','An idea.','Fixture Requester')
            self.assertFalse((root/'requirements').exists())

    def test_additive_profiles_allow_forward_readers_not_changed_existing_contracts(self):
        with tempfile.TemporaryDirectory() as area:
            old=runtime.capabilities(Path(area));new=deepcopy(old)
            new['domain_contracts']['future-domain']='sdlc-domain/1';new['storage'].append('future-history/1')
            self.assertTrue(runtime.compatible_contracts(old,new));self.assertFalse(runtime.compatible_contracts(new,old))
            new['domain_contracts']['architecture']='different/99';self.assertFalse(runtime.compatible_contracts(old,new))

    def test_join_checks_current_track_evidence_not_obsolete_shared_writers(self):
        a={'runtime':'/fictional/A','snapshot_digest':'a'*64,'source_revision':'a'*40}
        b={'runtime':'/fictional/B','snapshot_digest':'b'*64,'source_revision':'b'*40}
        value={'events':[{'event':{'kind':'bind','operation_id':'old','scope':'shared','runtime':a}},
                         {'event':{'kind':'promote','operation_id':'new','scope':'shared','runtime':b}}]}
        with tempfile.TemporaryDirectory() as area:
            contract=runtime.capabilities(Path(area))
            with patch.object(runtime,'scope_for',side_effect=lambda epic,track:track+':cycle'),patch.object(runtime,'probe',return_value=(b,contract)) as probe:
                runtime.verify_join(Path(area),SimpleNamespace(metadata={'id':'REQ-0001'}),value)
                self.assertEqual([c.args[0] for c in probe.call_args_list],['/fictional/B'])
            value['events'].append({'event':{'kind':'promote','operation_id':'qa','scope':'qa:cycle','runtime':a}})
            with patch.object(runtime,'scope_for',side_effect=lambda epic,track:track+':cycle'),patch.object(runtime,'probe',return_value=(b,contract)) as probe:
                runtime.verify_join(Path(area),SimpleNamespace(metadata={'id':'REQ-0001'}),value)
                self.assertEqual({c.args[0] for c in probe.call_args_list},{'/fictional/A','/fictional/B'})


class EarlyDomainPromotionTests(unittest.TestCase):
    setUpClass=classmethod(installation_fixture.InstallationTests.setUpClass.__func__)
    setUp=runtime_fixture.RuntimeSelectionTests.setUp
    unique=runtime_fixture.RuntimeSelectionTests.unique
    cli=runtime_fixture.RuntimeSelectionTests.cli
    context=runtime_fixture.RuntimeSelectionTests.context
    new=runtime_fixture.RuntimeSelectionTests.new
    epic=runtime_fixture.RuntimeSelectionTests.epic
    business_under_a=runtime_fixture.RuntimeSelectionTests.business_under_a
    select=runtime_fixture.RuntimeSelectionTests.select

    def test_committed_four_domain_runtime_to_new_analysis_package_without_upstream_reapproval(self):
        newer=self.runtime
        self.skills=self.base/'legacy-registration'
        self.a=install.install(installation_fixture.REPO,'d5009d8aae78be6bfefe5aac466a03f080599fbd',self.project,self.runtime_root,self.skills,sys.executable)
        self.runtime=Path(self.a['runtime']);self.business_under_a()
        baseline=installation_fixture.hashes(self.directory/'business-baselines');decisions=deepcopy(self.epic().metadata['business_decisions'])
        report=runtime.assessment(self.project,'REQ-0001',newer)
        self.assertEqual(report['classification'],'requires_reconciliation',report)
        self.select(newer,reconciliation='Fictional impact review: new Analysis guidance only; approved upstream scope is unchanged.')
        token=self.context(newer);view=self.cli(newer,'analysis-review','REQ-0001')
        source=self.base/'analysis.md';source.write_text(analysis_fixture.document(view['input']))
        self.cli(newer,'analysis-generate','REQ-0001','--expected-analysis-review-revision',view['analysis_review_revision'],
                 '--expected-baseline-id',view['input']['baseline_id'],'--expected-handoff-id',view['input']['handoff_id'],
                 '--operation-id','new-domain-analysis','--editor','Fixture Analyst','--reason','Fictional new domain practice.','--document-file',str(source),token=token)
        entry=yaml.safe_load((self.directory/'analysis-history.yaml').read_text())['revisions'][-1]
        self.assertEqual(entry['skills'],domains.for_stage('functional_analysis',sdlc.StrictLoader))
        self.assertEqual(baseline,installation_fixture.hashes(self.directory/'business-baselines'))
        self.assertEqual(decisions,self.epic().metadata['business_decisions'])
        self.assertEqual(self.epic().metadata['status'],'functional_analysis')
        self.assertFalse(self.epic().analysis_approval['valid'])
        event=[w['event'] for w in runtime.read(self.directory)['events'] if w['event']['operation_id']=='new-domain-analysis'][0]
        self.assertEqual(event['runtime']['runtime'],str(newer))

        # Rolling back the default must not select an older resolver that cannot read
        # the newly persisted Analysis envelope; future request authority remains B.
        bpin=runtime.pin(newer)
        management.switch(self.skills,{k:bpin[k] for k in ('runtime','snapshot_digest')},self.a['snapshot_digest'],
                          'default-newer','Fixture operator','Fictional explicit default update.','update')
        management.switch(self.skills,None,bpin['snapshot_digest'],'default-rollback','Fixture operator','Fictional default rollback only.','rollback')
        registration=management.registration(self.skills)
        self.assertEqual(registration['runtime'],str(self.runtime))
        self.assertEqual(registration['manager']['runtime'],str(newer))
        resumed=self.cli(newer,'runtime-status','REQ-0001','--skill-root',str(self.skills))
        self.assertEqual(resumed['effective_runtime']['runtime'],str(newer))
        self.assertEqual(baseline,installation_fixture.hashes(self.directory/'business-baselines'))
