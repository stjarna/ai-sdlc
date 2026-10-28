"""Approval fixtures are fictional test decisions, never real Product Owner consent."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

import yaml

import test_functional_analysis as fixtures
import sdlc
import business_approval as business_gate
import business_refinement as business
import analysis_approval as approval
import approval_common as common


class AnalysisApprovalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.FunctionalAnalysisTests('test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.generate()
        self.project, self.directory = self.fixture.project, self.fixture.directory
        self.business_fixture = self.fixture.fixture

    def review(self):
        return self.fixture.review()

    def request(self, action='approve', view=None, **extra):
        v = self.review() if view is None else view
        source = v['input'] or v['epic']['analysis']
        return dict(project=self.project, epic_id='REQ-0001', expected_review=v['analysis_review_revision'],
            expected_analysis=v['epic']['analysis']['revision'], expected_baseline=source['baseline_id'],
            expected_handoff=source['handoff_id'], operation_id=self.business_fixture.unique('analysis-gate'),
            actor='Fixture PO', reason='Test fixture: '+action,
            decision='Test fixture: approve with all listed uncertainties acknowledged.' if action=='approve' else 'Test fixture: '+action,
            action=action, acknowledged=[i['id'] for i in v['analysis_open_items']] if action=='approve' else [], **extra)

    def execute(self, request):
        return sdlc.analysis_gate(**request)

    def approve(self):
        return self.execute(self.request())

    def advance(self, selected=None):
        selected = selected or self.review()['analysis_approval']['latest_decision']['id']
        return self.execute(self.request('advance', approval_id=selected))

    def reject(self, code, operation):
        self.business_fixture.rejected(code, operation)

    def revise(self, content=None):
        return self.fixture.revise(content or self.review()['epic']['analysis']['content'])

    def baseline(self, approved):
        return self.directory/'analysis-baselines'/approved['baseline_id']

    def test_exact_baseline_binding_and_separate_advancement(self):
        before = self.review()
        snapshots = approval.read_snapshot(self.directory)
        approved = self.approve()
        epic = approved['epic']
        self.assertEqual(epic['metadata']['schema_version'], '0.5')
        self.assertEqual(epic['metadata']['status'], 'functional_analysis')
        self.assertTrue(epic['analysis_approval']['can_advance'])
        manifest, frozen = approval.read_baseline(self.directory, approved['baseline_id'], sdlc.StrictLoader)
        self.assertEqual(frozen, snapshots)
        self.assertEqual(manifest['business_baseline_id'], before['input']['baseline_id'])
        self.assertEqual(manifest['business_approval_id'], before['input']['approval_id'])
        self.assertEqual(manifest['business_handoff_id'], before['input']['handoff_id'])
        self.assertEqual(manifest['analysis_operation_id'], before['epic']['analysis']['history'][-1]['operation_id'])
        self.assertEqual(manifest['analysis_revision'], before['epic']['analysis']['revision'])
        _, bf = business_gate.read_baseline(self.directory, manifest['business_baseline_id'], sdlc.StrictLoader)
        self.assertEqual(approval.frozen_review(frozen, bf), before['analysis_review_revision'])
        self.assertEqual(set(frozen), set(approval.BASELINE_FILES))
        advanced = self.advance()
        self.assertEqual(advanced['epic']['metadata']['status'], 'ready_for_technical_design')
        self.assertTrue(advanced['epic']['approval']['valid'])
        self.assertTrue(advanced['epic']['analysis_approval']['valid'])
        self.assertFalse(advanced['epic']['analysis_approval']['can_advance'])
        self.assertEqual(advanced['epic']['analysis_approval']['technical_design_input'], {'approval_id':approved['decision_id'],'baseline_id':approved['baseline_id']})
        self.assertTrue(self.review()['current'])
        self.assertFalse(self.review()['can_approve'])
        self.assertFalse((self.directory/'design.md').exists())

    def test_uncertainty_requires_exact_acknowledgements_without_resolution(self):
        before = self.review()
        self.assertEqual({i['id'] for i in before['analysis_open_items']}, {'U-001','AQ-001','FR-002'})
        for items, code in (([], 'E_ACKNOWLEDGEMENT'), (['U-001'],'E_ACKNOWLEDGEMENT'), (['U-999'],'E_ACKNOWLEDGEMENT'), (['U-001','U-001'],'E_UPDATE_INPUT')):
            self.reject(code, lambda: self.execute({**self.request(), 'acknowledged':items}))
        approved = self.approve()
        self.assertEqual(approved['epic']['analysis']['content'], before['epic']['analysis']['content'])
        self.assertEqual(self.review()['details'], before['details'])

    def test_proposed_items_are_acknowledged_and_not_promoted(self):
        v=self.review()
        text=v['epic']['analysis']['content'].replace('## Analysis proposals\nNone recorded.', '## Analysis proposals\n### AP-001 — Date colours\nBusiness sources: B-001\nDiscovery evidence: D-0001\nStatus: proposed\nAffected items: FR-001\nStatement: Unconfirmed date colours.')
        self.revise(text)
        self.assertIn('AP-001',{i['id'] for i in self.review()['analysis_open_items']})
        self.approve()
        self.assertEqual(self.review()['details']['items']['AP-001']['fields']['Status'],'proposed')

    def test_explicit_actor_and_decision_are_required_actual_words_preserved(self):
        request=self.request()
        for key in ('actor','reason','decision'):
            self.reject('E_UPDATE_INPUT',lambda:self.execute({**request,key:''}))
        words='Approve with past dates deferred and the related behavior blocked.\nI acknowledge the listed uncertainties.'
        approved=self.execute({**request,'decision':words})
        entry=approved['epic']['metadata']['analysis_decisions'][-1]
        self.assertEqual(entry['actor'],request['actor'])
        self.assertEqual(entry['decision'],words)

    def test_request_changes_supersedes_approval_preserves_content_and_history(self):
        approved=self.approve()
        content=(self.directory/'specification.md').read_bytes()
        feedback=self.execute(self.request('request_changes'))
        self.assertEqual(feedback['epic']['metadata']['status'],'functional_analysis')
        self.assertEqual((self.directory/'specification.md').read_bytes(),content)
        self.assertEqual(self.review()['analysis_approval']['status'],'changes_requested')
        self.assertTrue(self.baseline(approved).exists())
        self.reject('E_APPROVAL_SUPERSEDED',lambda:self.advance(approved['decision_id']))
        self.revise()
        again=self.approve()
        self.reject('E_APPROVAL_SUPERSEDED',lambda:self.advance(approved['decision_id']))
        self.assertTrue(self.advance(again['decision_id'])['ok'])

    def test_request_changes_can_be_first_decision_without_baseline(self):
        r=self.execute(self.request('request_changes'))
        self.assertEqual(r['decision_id'],'AD-0001')
        self.assertIsNone(r['baseline_id'])
        self.assertFalse((self.directory/'analysis-baselines').exists())

    def test_no_advance_without_approval(self):
        self.reject('E_APPROVAL_REQUIRED',lambda:self.advance('AD-0001'))

    def test_same_content_revision_invalidates_approval(self):
        approved=self.approve()
        digest=self.review()['epic']['analysis']['revision']
        self.revise()
        self.assertEqual(self.review()['epic']['analysis']['revision'],digest)
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.reject('E_APPROVAL_STALE',lambda:self.advance(approved['decision_id']))

    def test_changed_content_and_return_to_original_never_restore_authority(self):
        approved=self.approve()
        original=self.review()['epic']['analysis']['content']
        self.revise(original.replace('Users can assign','Users may assign'))
        self.revise(original)
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.reject('E_APPROVAL_STALE',lambda:self.advance(approved['decision_id']))

    def test_stale_review_and_wrong_input_are_rejected(self):
        request=self.request()
        self.revise()
        self.reject('E_REVISION_CONFLICT',lambda:self.execute(request))
        for key,value,code in (('expected_analysis','0'*64,'E_REVISION_CONFLICT'),('expected_review','0'*64,'E_REVISION_CONFLICT'),('expected_baseline','0'*64,'E_ANALYSIS_INPUT'),('expected_handoff','other-handoff','E_ANALYSIS_INPUT')):
            self.reject(code,lambda:self.execute({**self.request(),key:value}))

    def test_repeated_approval_supersedes_and_requires_fresh_review(self):
        first=self.request()
        approved=self.execute(first)
        self.reject('E_REVISION_CONFLICT',lambda:self.execute({**first,'operation_id':'new-stale-approval'}))
        second=self.approve()
        self.assertNotEqual(approved['baseline_id'],second['baseline_id'])
        self.reject('E_APPROVAL_SUPERSEDED',lambda:self.advance(approved['decision_id']))
        self.assertTrue(self.execute(first)['replayed'])
        self.assertEqual(self.review()['analysis_approval']['latest_decision']['id'],second['decision_id'])

    def test_idempotency_and_conflicting_approval_retry(self):
        request=self.request()
        approved=self.execute(request)
        saved=(self.directory/'metadata.yaml').read_bytes()
        self.assertTrue(self.execute(request)['replayed'])
        self.assertEqual((self.directory/'metadata.yaml').read_bytes(),saved)
        for key,value in (('actor','Other'),('reason','Other'),('decision','Different'),('expected_review','0'*64),('expected_handoff','different'),('acknowledged',[])):
            self.reject('E_IDEMPOTENCY',lambda:self.execute({**request,key:value}))
        self.execute(self.request('request_changes'))
        replay=self.execute(request)
        self.assertEqual(replay['decision_id'],approved['decision_id'])
        self.assertFalse(replay['epic']['analysis_approval']['valid'])
        self.assertEqual(len(replay['epic']['metadata']['analysis_decisions']),2)

    def test_feedback_and_advance_retries_after_reopen_do_not_restore_authority(self):
        feedback=self.request('request_changes')
        self.execute(feedback)
        self.assertTrue(self.execute(feedback)['replayed'])
        self.reject('E_IDEMPOTENCY',lambda:self.execute({**feedback,'decision':'Changed'}))
        approved=self.approve()
        request=self.request('advance',approval_id=approved['decision_id'])
        self.execute(request)
        self.assertTrue(self.execute(request)['replayed'])
        self.reject('E_IDEMPOTENCY',lambda:self.execute({**request,'approval_id':'AD-9999'}))
        self.business_fixture.reopen()
        replay=self.execute(request)
        self.assertEqual(replay['epic']['metadata']['status'],'discovery')
        self.assertFalse(replay['epic']['analysis_approval']['valid'])

    def test_advancement_freezes_analysis_and_preserves_business_validity(self):
        approved=self.approve()
        write=self.fixture.request(mode='revise')
        self.advance()
        self.reject('E_STATUS',lambda:sdlc.analysis_write(**write))
        self.reject('E_STATUS',self.approve)
        self.reject('E_STATUS',lambda:self.execute(self.request('request_changes')))
        self.reject('E_STATUS',lambda:self.advance(approved['decision_id']))
        self.assertTrue(self.business_fixture.view()['approval']['valid'])

    def test_new_cycle_requires_reconciliation_and_fresh_approval_preserves_schema(self):
        approved=self.approve()
        self.advance()
        old_decisions=deepcopy(self.review()['epic']['metadata']['analysis_decisions'])
        saved={p.name:p.read_bytes() for p in self.baseline(approved).iterdir()}
        original=self.review()['epic']['analysis']['content']
        self.business_fixture.reopen()
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.assertIsNone(self.review()['analysis_approval']['technical_design_input'])
        self.business_fixture.complete()
        self.business_fixture.revise(self.business_fixture.initial_document,mode='generate')
        renewed=self.business_fixture.approve()
        self.business_fixture.advance()
        view=self.review()
        self.assertFalse(view['current'])
        self.reject('E_STATUS',lambda:self.advance(approved['decision_id']))
        old=self.fixture.approved['baseline_id']
        changed=original.replace(old,view['input']['baseline_id']).replace('Approval: BD-0001','Approval: '+view['input']['approval_id'])
        # Use the persisted old handoff rather than depending on fixture counters.
        old_handoff=next(line[9:] for line in original.splitlines() if line.startswith('Handoff: '))
        changed=changed.replace('Handoff: '+old_handoff,'Handoff: '+view['input']['handoff_id'])
        self.revise(changed)
        self.assertEqual(self.review()['epic']['metadata']['schema_version'],'0.5')
        self.assertEqual(self.review()['epic']['metadata']['analysis_decisions'],old_decisions)
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.reject('E_APPROVAL_STALE',lambda:self.advance(approved['decision_id']))
        self.approve()
        self.advance()
        self.assertEqual(saved,{p.name:p.read_bytes() for p in self.baseline(approved).iterdir()})
        self.assertEqual(renewed['epic']['metadata']['schema_version'],'0.5')

    def test_upstream_source_edit_invalidates_approval(self):
        approved=self.approve()
        path=self.directory/'idea.md'
        path.write_bytes(path.read_bytes()+b'\n')
        self.assertFalse(self.review()['current'])
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.reject('E_APPROVAL_STALE',lambda:self.advance(approved['decision_id']))

    def test_corrupt_baseline_missing_files_and_unsafe_paths_fail_closed(self):
        approved=self.approve()
        root=self.baseline(approved)
        original={p.name:p.read_bytes() for p in root.iterdir()}
        for name in ('specification.md','analysis-history.yaml','metadata.yaml','manifest.json'):
            (root/name).write_bytes(b'broken')
            self.assertFalse(self.review()['ok'])
            self.reject('E_BASELINE_INTEGRITY',lambda:self.advance(approved['decision_id']))
            (root/name).write_bytes(original[name])
        (root/'specification.md').unlink()
        self.reject('E_BASELINE_INTEGRITY',self.approve)
        (root/'specification.md').symlink_to(self.directory/'specification.md')
        self.reject('E_BASELINE_INTEGRITY',self.approve)
        (root/'specification.md').unlink()
        (root/'specification.md').write_bytes(original['specification.md'])
        (root/'unexpected').write_text('unexpected')
        self.reject('E_BASELINE_INTEGRITY',self.approve)
        (root/'unexpected').unlink()
        shutil.rmtree(root)
        self.reject('E_BASELINE_MISSING',self.approve)

    def test_historical_baseline_corruption_blocks_even_after_reapproval(self):
        old=self.approve()
        self.revise()
        self.approve()
        (self.baseline(old)/'specification.md').write_text('corrupt historical approval')
        self.reject('E_BASELINE_INTEGRITY',self.advance)

    def test_business_dependency_corruption_blocks_analysis_gate(self):
        approved=self.approve()
        request=self.request('advance',approval_id=approved['decision_id'])
        baseline=self.review()['input']['baseline_id']
        (self.directory/'business-baselines'/baseline/'business.md').write_text('corrupt dependency')
        self.reject('E_BASELINE_INTEGRITY',lambda:self.execute(request))

    def test_audit_tampering_is_detected_against_frozen_prefix(self):
        self.approve()
        self.approve()
        path=self.directory/'metadata.yaml'
        data=yaml.safe_load(path.read_text())
        data['analysis_decisions'][0]['decision']='Tampered historical wording'
        path.write_text(yaml.safe_dump(data,sort_keys=False))
        self.reject('E_BASELINE_CONTEXT',self.approve)

    def test_decision_malformed_or_dangling_references_rejected(self):
        self.approve()
        path=self.directory/'metadata.yaml'
        original=path.read_bytes()
        for key,value in (('id','AD-9999'),('business_handoff_id','missing'),('analysis_operation_id','missing'),('acknowledged_open_items',['AQ-001','AQ-001']),('analysis_revision','0'*64)):
            data=yaml.safe_load(original)
            data['analysis_decisions'][0][key]=value
            path.write_text(yaml.safe_dump(data,sort_keys=False))
            self.reject('E_ANALYSIS_DECISIONS',lambda:sdlc.inspect_epics(self.project,'open','REQ-0001'))
        path.write_bytes(original)

    def test_missing_malformed_and_untracked_analysis_artifacts_block_gate(self):
        request=self.request()
        for name in ('specification.md','analysis-history.yaml'):
            path=self.directory/name
            original=path.read_bytes()
            path.unlink()
            self.reject('E_ANALYSIS_HISTORY',lambda:self.execute(request))
            path.write_bytes(b'!!map [hello]' if name.endswith('yaml') else b'changed')
            self.reject('E_ANALYSIS_HISTORY' if name.endswith('yaml') else 'E_ANALYSIS_MISMATCH',lambda:self.execute(request))
            path.write_bytes(original)

    def test_concurrent_approvals_and_feedback_only_one_commits(self):
        for actions in (('approve','approve'),('approve','request_changes')):
            view=self.review()
            requests=[self.request(a,view=view) for a in actions]
            def run(r):
                try:return self.execute(r)
                except sdlc.Rejected as e:return {'ok':False,'code':e.diagnostics[0].code}
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(run,requests))
            self.assertEqual(sum(r['ok'] for r in results),1)
            self.assertIn(next(r['code'] for r in results if not r['ok']),('E_PROJECT_BUSY','E_REVISION_CONFLICT'))

    def test_approval_lock_blocks_revision_reopening_and_other_gate(self):
        entered,release=threading.Event(),threading.Event()
        real=approval.publish_baseline
        def pause(*args):
            entered.set()
            if not release.wait(5):raise RuntimeError('Test synchronization timeout')
            return real(*args)
        request=self.request()
        with ThreadPoolExecutor(max_workers=1) as pool, patch.object(approval,'publish_baseline',side_effect=pause):
            future=pool.submit(self.execute,request)
            self.assertTrue(entered.wait(5))
            try:
                self.reject('E_PROJECT_BUSY',self.revise)
                self.reject('E_PROJECT_BUSY',self.business_fixture.reopen)
                self.reject('E_PROJECT_BUSY',lambda:self.execute(self.request('request_changes')))
            finally:release.set()
            future.result(timeout=10)
        self.revise()
        self.assertFalse(self.review()['analysis_approval']['valid'])

    def test_advancement_lock_blocks_revision_and_reopening_then_revision_rejected(self):
        self.approve()
        request=self.request('advance',approval_id='AD-0001')
        write=self.fixture.request(mode='revise')
        entered,release=threading.Event(),threading.Event()
        real=sdlc.atomic_history_write
        def pause(*args):
            entered.set()
            if not release.wait(5):raise RuntimeError('Test synchronization timeout')
            return real(*args)
        with ThreadPoolExecutor(max_workers=1) as pool,patch.object(sdlc,'atomic_history_write',side_effect=pause):
            future=pool.submit(self.execute,request)
            self.assertTrue(entered.wait(5))
            try:
                self.reject('E_PROJECT_BUSY',lambda:sdlc.analysis_write(**write))
                self.reject('E_PROJECT_BUSY',self.business_fixture.reopen)
            finally:release.set()
            future.result(timeout=10)
        self.reject('E_STATUS',lambda:sdlc.analysis_write(**write))

    def test_interrupted_publication_and_orphan_reuse(self):
        request=self.request()
        before=(self.directory/'metadata.yaml').read_bytes()
        with patch.object(common.os,'rename',side_effect=OSError('Injected rename failure')):
            self.reject('E_BASELINE_WRITE',lambda:self.execute(request))
        self.assertEqual((self.directory/'metadata.yaml').read_bytes(),before)
        self.assertEqual(list((self.directory/'analysis-baselines').iterdir()),[])
        with patch.object(sdlc,'atomic_history_write',side_effect=OSError('Injected precommit failure')):
            with self.assertRaises(OSError):self.execute(request)
        self.assertFalse(self.review()['analysis_approval']['valid'])
        orphans=list((self.directory/'analysis-baselines').iterdir())
        self.assertEqual(len(orphans),1)
        result=self.execute(request)
        self.assertEqual(result['baseline_id'],orphans[0].name)
        self.assertEqual(len(self.review()['epic']['metadata']['analysis_decisions']),1)

    def test_file_and_directory_fsync_failure_and_exact_retry(self):
        request=self.request()
        real=common.os.fsync
        def fail_file(fd):
            if stat.S_ISREG(os.fstat(fd).st_mode):raise OSError('Injected fsync')
            return real(fd)
        with patch.object(common.os,'fsync',side_effect=fail_file):
            self.reject('E_BASELINE_WRITE',lambda:self.execute(request))
        self.assertFalse(self.review()['analysis_approval']['valid'])
        real_sync=common.fsync_directory
        root=self.directory/'analysis-baselines'
        for stage in ('new_root','staging','published_root'):
            if root.exists():shutil.rmtree(root)
            def fail_directory(path):
                if (stage=='new_root' and path==self.directory) or (stage=='staging' and path.name.startswith('.pending-')) or (stage=='published_root' and path==root):
                    raise OSError('Injected directory durability failure')
                return real_sync(path)
            with patch.object(common,'fsync_directory',side_effect=fail_directory):
                self.reject('E_BASELINE_WRITE',lambda:self.execute(request))
            self.assertFalse(self.review()['analysis_approval']['valid'])
        with patch.object(common,'fsync_directory',side_effect=OSError('Orphan not durable')):
            self.reject('E_BASELINE_WRITE',lambda:self.execute(request))
        self.assertTrue(self.execute(request)['ok'])

    def test_post_commit_uncertainty_replays_decision_and_advancement(self):
        for action in ('approve','advance'):
            request=self.request(action,**({'approval_id':'AD-0001'} if action=='advance' else {}))
            real=sdlc.atomic_history_write
            def lose_response(*args):
                real(*args)
                raise sdlc.Rejected([sdlc.error('E_WRITE_UNCERTAIN',self.directory/'metadata.yaml','Injected lost success response')])
            with patch.object(sdlc,'atomic_history_write',side_effect=lose_response):
                self.reject('E_WRITE_UNCERTAIN',lambda:self.execute(request))
            self.assertTrue(self.execute(request)['replayed'])
        self.assertEqual(len(self.review()['epic']['metadata']['analysis_decisions']),1)
        self.assertEqual(sum(e['action']=='analysis_advance' for e in self.review()['epic']['metadata']['lifecycle']),1)

    def test_manual_source_change_during_publication_prevents_commit(self):
        request=self.request()
        real=approval.publish_baseline
        def change(*args):
            baseline=real(*args)
            path=self.directory/'idea.md'
            path.write_bytes(path.read_bytes()+b'\n')
            return baseline
        with patch.object(approval,'publish_baseline',side_effect=change):
            self.reject('E_REVISION_CONFLICT',lambda:self.execute(request))
        self.assertNotIn('analysis_decisions',yaml.safe_load((self.directory/'metadata.yaml').read_text()))

    def test_cross_stage_operation_id_reuse_rejected(self):
        approved=self.approve()
        op=approved['epic']['metadata']['analysis_decisions'][0]['operation_id']
        self.reject('E_IDEMPOTENCY',lambda:sdlc.analysis_write(**{**self.fixture.request(mode='revise'),'operation_id':op}))
        self.reject('E_IDEMPOTENCY',lambda:sdlc.lifecycle_change(self.project,'REQ-0001',self.review()['epic']['revision'],op,'Fixture','Reopen','reopen'))
        old=approved['epic']['analysis']['history'][-1]['operation_id']
        self.reject('E_IDEMPOTENCY',lambda:self.execute({**self.request(),'operation_id':old}))

    def test_shared_persistence_refuses_audit_truncation(self):
        self.approve()
        epic=sdlc.selected_epic(self.project,'REQ-0001')
        candidate={**epic.metadata,'analysis_decisions':[]}
        self.reject('E_APPROVAL_AUDIT',lambda:sdlc.commit_gate(epic,candidate,epic.analysis_review_revision,lambda e:e.analysis_review_revision))

    def test_fresh_cli_resume_and_gate_contracts_no_git_operations(self):
        script=Path(sdlc.__file__)
        def cli(*args):
            p=subprocess.run([sys.executable,str(script),'--project',str(self.project),*args],text=True,capture_output=True)
            result=json.loads(p.stdout)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            return result
        subprocess.run(['git','init','-q',str(self.project)],check=True)
        original_inputs=set(self.project.glob('spec-input-*.md'))
        before=subprocess.run(['git','-C',str(self.project),'status','--porcelain'],text=True,capture_output=True,check=True).stdout
        def gate(action,view,**extra):
            args=['analysis-'+action,'REQ-0001','--expected-analysis-review-revision',view['analysis_review_revision'],'--expected-analysis-revision',view['epic']['analysis']['revision'],'--expected-baseline-id',view['input']['baseline_id'],'--expected-handoff-id',view['input']['handoff_id'],'--operation-id',self.business_fixture.unique('cli-gate'),'--reason','Test fixture '+action]
            if action=='approve':
                args+=['--approver','Fixture PO','--decision','Approve with all listed uncertainties acknowledged.']
                for item in view['analysis_open_items']:args+=['--acknowledge-open-item',item['id']]
            elif action=='request-changes':args+=['--reviewer','Fixture PO','--feedback','Please refine the wording.']
            else:args+=['--actor','Fixture PO','--approval-id',extra['approval_id']]
            return cli(*args)
        gate('request-changes',cli('analysis-review','REQ-0001'))
        self.revise()
        # Fixture document inputs are test-owned, not created by the CLI gate.
        for path in self.project.glob('spec-input-*.md'):
            if path not in original_inputs:path.unlink()
        approved=gate('approve',cli('analysis-review','REQ-0001'))
        self.assertEqual(approved['epic']['metadata']['status'],'functional_analysis')
        resumed=cli('analysis-review','REQ-0001')
        self.assertTrue(resumed['analysis_approval']['valid'])
        advanced=gate('advance',resumed,approval_id=approved['decision_id'])
        self.assertEqual(advanced['epic']['metadata']['status'],'ready_for_technical_design')
        self.assertTrue(cli('validate','REQ-0001')['ok'])
        after=subprocess.run(['git','-C',str(self.project),'status','--porcelain'],text=True,capture_output=True,check=True).stdout
        self.assertEqual(before,after)
        self.assertEqual(subprocess.run(['git','-C',str(self.project),'diff','--cached','--name-only'],text=True,capture_output=True,check=True).stdout,'')
        self.assertNotEqual(subprocess.run(['git','-C',str(self.project),'rev-parse','HEAD'],capture_output=True).returncode,0)

    def test_supporting_byte_changes_cannot_publish_unreproducible_approval(self):
        path=self.directory/'business-history.yaml'
        path.write_bytes(path.read_bytes()+b'\n')
        self.assertTrue(self.business_fixture.view()['approval']['valid'])
        self.assertFalse(self.review()['can_approve'])
        self.reject('E_APPROVAL_STALE',self.approve)
        self.assertNotIn('analysis_decisions',yaml.safe_load((self.directory/'metadata.yaml').read_text()))
        self.assertFalse((self.directory/'analysis-baselines').exists())

    def test_supporting_bytes_changed_after_approval_invalidate_authority(self):
        approved=self.approve()
        for name in ('business-history.yaml','analysis-history.yaml'):
            path=self.directory/name
            original=path.read_bytes()
            path.write_bytes(original+b'\n')
            view=self.review()
            self.assertFalse(view['analysis_approval']['valid'])
            self.assertIn('supporting_artifacts_changed',view['analysis_approval']['reasons'])
            self.reject('E_APPROVAL_STALE',lambda:self.advance(approved['decision_id']))
            path.write_bytes(original)

    def test_live_revision_history_tampering_is_detected_by_frozen_history_prefix(self):
        self.approve()
        path=self.directory/'analysis-history.yaml'
        data=yaml.safe_load(path.read_text())
        data['revisions'][0]['reason']='Tampered attribution'
        path.write_text(yaml.safe_dump(data,sort_keys=False))
        self.reject('E_BASELINE_CONTEXT',self.advance)

    def test_abrupt_exit_after_baseline_before_commit_leaves_no_authority(self):
        request=self.request()
        args={k:str(v) if isinstance(v,Path) else v for k,v in request.items()}
        program="import os,sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import sdlc; a=json.loads(sys.argv[2]); a['project']=Path(a['project']); sdlc.atomic_history_write=lambda *args:os._exit(17); sdlc.analysis_gate(**a)"
        child=subprocess.run([sys.executable,'-c',program,str(Path(sdlc.__file__).parent),json.dumps(args)],capture_output=True,text=True)
        self.assertEqual(child.returncode,17,child.stderr)
        self.assertTrue((self.project/'.sdlc-discovery.lock').is_dir())
        self.assertFalse(self.review()['analysis_approval']['valid'])
        self.assertNotIn('analysis_decisions',yaml.safe_load((self.directory/'metadata.yaml').read_text()))
        self.assertEqual(len(list((self.directory/'analysis-baselines').iterdir())),1)
        # The test operator has observed child termination; remove only this test lock.
        (self.project/'.sdlc-discovery.lock').rmdir()
        self.assertTrue(self.execute(request)['ok'])
        self.assertTrue(self.execute(request)['replayed'])

    def test_real_metadata_durability_failure_replays_without_duplicate_audit(self):
        request=self.request()
        real_replace=sdlc.os.replace
        real_fsync=sdlc.os.fsync
        published=False
        def replace(source,destination):
            nonlocal published
            result=real_replace(source,destination)
            if Path(destination)==self.directory/'metadata.yaml':published=True
            return result
        def fsync(fd):
            if published and stat.S_ISDIR(os.fstat(fd).st_mode):raise OSError('Injected post-replace fsync failure')
            return real_fsync(fd)
        with patch.object(sdlc.os,'replace',side_effect=replace),patch.object(sdlc.os,'fsync',side_effect=fsync):
            self.reject('E_WRITE_UNCERTAIN',lambda:self.execute(request))
        result=self.execute(request)
        self.assertTrue(result['replayed'])
        self.assertEqual(len(result['epic']['metadata']['analysis_decisions']),1)

    def test_revision_and_reopen_first_reject_pending_gate_without_committing(self):
        request=self.request()
        write=self.fixture.request(mode='revise')
        entered,release=threading.Event(),threading.Event()
        real=business.publish
        def pause(*args,**kwargs):
            entered.set()
            if not release.wait(5):raise RuntimeError('Test synchronization timeout')
            return real(*args,**kwargs)
        with ThreadPoolExecutor(max_workers=1) as pool,patch.object(business,'publish',side_effect=pause):
            future=pool.submit(sdlc.analysis_write,**write)
            self.assertTrue(entered.wait(5))
            try:self.reject('E_PROJECT_BUSY',lambda:self.execute(request))
            finally:release.set()
            future.result(timeout=10)
        self.reject('E_REVISION_CONFLICT',lambda:self.execute(request))
        pending=self.request()
        self.business_fixture.reopen()
        self.reject('E_STATUS',lambda:self.execute(pending))
        self.assertFalse((self.directory/'analysis-baselines').exists())
