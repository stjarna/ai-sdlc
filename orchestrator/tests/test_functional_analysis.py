"""Functional Analysis regression fixtures; fictional decisions are not human approval."""
from concurrent.futures import ThreadPoolExecutor
import base64
import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

import yaml
import test_business_approval as fixtures
import sdlc
import functional_analysis as analysis
import business_refinement as business


def document(source):
    inherited = '\n'.join(v['line'] for k, v in analysis.baseline_items(source).items() if not k.startswith('B-')) or 'None recorded.'
    return f'''# Functional Analysis — REQ-0001

Baseline: {source['baseline_id']}
Approval: {source['approval_id']}
Handoff: {source['handoff_id']}

## Functional requirements
### FR-001 — Optional task due dates
Business sources: B-001, B-003
Discovery evidence: D-0001, D-0005, D-0004
Status: specified
Questions: -
Statement: Users can assign an optional due date to a task.

### FR-002 — Past-date handling
Business sources: B-001
Discovery evidence: D-0001
Status: blocked
Questions: AQ-001
Statement: Past-date behavior is not yet specified.

## Use cases
### UC-001 — Record a due date
Business sources: B-001, B-003
Discovery evidence: D-0001, D-0005
Status: specified
Questions: -
Requirements: FR-001
Actor: Task user
Preconditions: A task is available.
Trigger: The user chooses to assign a due date.
Main flow: 1. The user supplies a due date.
  2. The task has the supplied due date.
Alternative flows: No due date is required. Past-date behavior remains unresolved.
Outcome: The task has an optional due date.

## Business rules
### BR-001 — Due dates are optional
Business sources: B-003
Discovery evidence: D-0005, D-0004
Status: specified
Questions: -
Requirements: FR-001
Statement: A task need not have a due date.

## Acceptance criteria
### AC-001 — Optional due date
Business sources: B-003
Discovery evidence: D-0005
Status: specified
Questions: -
Requirements: FR-001
Given: A task without a due date.
When: Its due-date requirement is evaluated.
Then: A due date is not required.

## Business coverage
- **B-001** [elaborated] FR-001 | Task due dates support commitments.
- **B-002** [excluded] - | Reminders are outside scope.
- **B-003** [elaborated] FR-001, BR-001 | Due dates are optional.

## Inherited unresolved items
{inherited}

## Analysis questions
### AQ-001 — Past due dates
Business sources: B-001
Discovery evidence: D-0006
Status: deferred
Affected items: FR-002
Statement: Whether past dates are allowed remains deferred pending support discussion.

## Analysis proposals
None recorded.
'''


class FunctionalAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BusinessApprovalTests('test_approval_freezes_exact_context_and_advancement_is_separate')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.project, self.directory = self.fixture.project, self.fixture.directory
        self.approved = self.fixture.approve()
        self.fixture.advance()

    def review(self):
        return sdlc.analysis_review(self.project, 'REQ-0001')

    def request(self, content=None, mode='generate', **extra):
        view = self.review()
        path = self.project / (self.fixture.unique('spec-input') + '.md')
        path.write_text(document(view['input']) if content is None else content)
        active = view['input'] or view['epic']['analysis']
        return dict(project=self.project, epic_id='REQ-0001', expected_review=view['analysis_review_revision'], expected_analysis=view['epic']['analysis']['revision'] if view['epic']['analysis'] else None, expected_baseline=active['baseline_id'], expected_handoff=active['handoff_id'], operation_id=self.fixture.unique('analysis'), editor='Fixture analyst', reason='Fictional analysis drafting', document_path=path, mode=mode, **extra)

    def generate(self):
        return sdlc.analysis_write(**self.request())

    def reject(self, code, action):
        self.fixture.rejected(code, action)

    def revise(self, text):
        return sdlc.analysis_write(**self.request(text, 'revise'))

    def test_initial_generation_uses_frozen_input_and_enters_analysis_without_approval(self):
        before = self.review()
        frozen = self.fixture.baseline(self.approved)
        saved = {p.name: p.read_bytes() for p in frozen.iterdir()}
        output = self.generate()
        e = output['epic']
        self.assertEqual(e['metadata']['schema_version'], '0.4')
        self.assertEqual(e['metadata']['status'], 'functional_analysis')
        self.assertTrue(e['approval']['valid'])
        self.assertEqual(e['approval']['analysis_input'], before['epic']['approval']['analysis_input'])
        self.assertEqual(e['metadata']['business_decisions'], before['epic']['metadata']['business_decisions'])
        self.assertEqual(saved, {p.name: p.read_bytes() for p in frozen.iterdir()})
        review = self.review()
        self.assertTrue(review['current'])
        self.assertFalse(review['approval_implemented'])
        self.assertEqual(review['input']['business'], (frozen/'business.md').read_text())
        self.assertIn('D-0005', review['details']['items']['BR-001']['fields']['Discovery evidence'])
        self.assertIn('U-001', review['details']['inherited'][0])
        self.assertEqual(review['details']['items']['FR-002']['fields']['Status'], 'blocked')
        self.assertFalse((self.directory/'stories').exists())

    def test_generation_requires_advancement_not_just_approval(self):
        request = self.request()
        # Remove the test fixture's advancement to test the genuine pre-handoff state.
        path = self.directory/'metadata.yaml'
        metadata = yaml.safe_load(path.read_text())
        metadata['lifecycle'].pop()
        metadata['status'] = 'business_refinement'
        path.write_text(yaml.safe_dump(metadata))
        self.reject('E_ANALYSIS_INPUT', lambda: sdlc.analysis_write(**request))
        self.assertIsNone(self.review()['input'])
        self.assertFalse((self.directory/'specification.md').exists())

    def test_missing_corrupt_and_unsafe_baselines_fail_closed(self):
        request = self.request()
        baseline = self.fixture.baseline(self.approved)
        for name in ('business.md', 'discovery.yaml', 'manifest.json'):
            with self.subTest(name=name):
                path = baseline/name
                saved = path.read_bytes()
                path.write_bytes(saved + b'bad')
                self.assertFalse(self.review()['ok'])
                self.reject('E_BASELINE_INTEGRITY', lambda: sdlc.analysis_write(**request))
                path.write_bytes(saved)
        retained = self.project/'retained'
        baseline.rename(retained)
        self.reject('E_BASELINE_MISSING', lambda: sdlc.analysis_write(**request))
        baseline.symlink_to(retained, target_is_directory=True)
        self.reject('E_BASELINE_INTEGRITY', lambda: sdlc.analysis_write(**request))

    def test_arbitrary_historical_baseline_or_wrong_handoff_is_rejected(self):
        request = self.request()
        for changes in ({'expected_baseline': '0'*64}, {'expected_handoff': 'old-handoff'}):
            self.reject('E_ANALYSIS_INPUT', lambda: sdlc.analysis_write(**{**request, **changes}))

    def test_invalid_traceability_and_cross_baseline_headers_are_rejected(self):
        source = self.review()['input']
        original = document(source)
        cases = [('Business sources: B-003', 'Business sources: B-999', 'E_ANALYSIS_REFERENCE'), ('Discovery evidence: D-0005\n', 'Discovery evidence: D-9999\n', 'E_ANALYSIS_REFERENCE'), ('Discovery evidence: D-0005\n', 'Discovery evidence: D-0006\n', 'E_ANALYSIS_PROVENANCE'), ('Requirements: FR-001', 'Requirements: FR-999', 'E_ANALYSIS_REFERENCE'), (source['baseline_id'], '0'*64, 'E_ANALYSIS_INPUT')]
        for old, new, code in cases:
            with self.subTest(new=new):
                self.reject(code, lambda: sdlc.analysis_write(**self.request(original.replace(old, new))))

    def test_all_business_items_require_coverage_but_context_and_exclusions_need_no_fr(self):
        original = document(self.review()['input'])
        self.reject('E_ANALYSIS_COVERAGE', lambda: sdlc.analysis_write(**self.request(original.replace('- **B-002** [excluded] - | Reminders are outside scope.\n', ''))))
        self.assertTrue(sdlc.analysis_write(**self.request(original.replace('[excluded]', '[contextual]')))['ok'])
        self.assertNotIn('B-002', self.review()['details']['items']['FR-001']['fields']['Business sources'])

    def test_proposed_items_do_not_count_as_confirmed_coverage(self):
        original = document(self.review()['input'])
        proposed = original.replace('Status: specified', 'Status: proposed')
        self.reject('E_ANALYSIS_COVERAGE', lambda: sdlc.analysis_write(**self.request(proposed)))

    def test_deferred_business_items_cannot_be_dropped_or_rewritten(self):
        original = document(self.review()['input'])
        inherited = analysis.baseline_items(self.review()['input'])['U-001']['line']
        for changed in ('None recorded.', inherited.replace('Past-date rule', 'Resolved rule')):
            self.reject('E_ANALYSIS_UNRESOLVED', lambda: sdlc.analysis_write(**self.request(original.replace(inherited, changed))))

    def test_blocked_requirements_cannot_have_specified_dependent_criteria(self):
        original = document(self.review()['input'])
        self.reject('E_ANALYSIS_UNRESOLVED', lambda: sdlc.analysis_write(**self.request(original.replace('Requirements: FR-001', 'Requirements: FR-002'))))
        self.reject('E_ANALYSIS_UNRESOLVED', lambda: sdlc.analysis_write(**self.request(original.replace('Status: blocked', 'Status: specified'))))
        self.reject('E_ANALYSIS_UNRESOLVED', lambda: sdlc.analysis_write(**self.request(original.replace('Questions: AQ-001', 'Questions: -'))))

    def test_required_fields_duplicate_ids_and_given_when_then(self):
        original = document(self.review()['input'])
        cases = [original.replace('Then: A due date is not required.', ''), original.replace('Then: A due date is not required.', 'Then: '), original.replace('### AC-001', '### FR-001'), original.replace('  2. The task', '  3. The task'), original.replace('Actor: Task user', 'Actor: Task user\nActor: Other')]
        for text in cases:
            with self.subTest(text=text[-80:]):
                self.reject('E_ANALYSIS_DOCUMENT', lambda: sdlc.analysis_write(**self.request(text)))
        without_ac = original[0:original.index('### AC-001')] + original[original.index('## Business coverage'):]
        self.reject('E_ANALYSIS_COVERAGE', lambda: sdlc.analysis_write(**self.request(without_ac)))

    def test_revision_history_recoverability_feedback_and_resume(self):
        generated = self.generate()
        previous = generated['epic']['analysis']['content']
        feedback = self.project/'feedback.yaml'
        feedback.write_text(yaml.safe_dump({'actor': 'Fixture PO', 'text': 'Please say “may assign” here.\nKeep the deferred issue.', 'items': ['FR-001']}))
        request = self.request(previous.replace('Users can assign', 'Users may assign'), 'revise', feedback_path=feedback)
        result = sdlc.analysis_write(**request)
        ledger = yaml.safe_load((self.directory/'analysis-history.yaml').read_text())
        self.assertEqual(base64.b64decode(ledger['revisions'][0]['content_base64']).decode(), previous)
        self.assertEqual(ledger['revisions'][1]['previous'], generated['epic']['analysis']['revision'])
        self.assertEqual(ledger['revisions'][1]['feedback']['text'], yaml.safe_load(feedback.read_text())['text'])
        run = subprocess.run([sys.executable, str(fixtures.SCRIPT), '--project', str(self.project), 'analysis-review', 'REQ-0001'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        resumed = json.loads(run.stdout)
        self.assertEqual(resumed['epic']['analysis'], result['epic']['analysis'])
        self.assertTrue(resumed['current'])

    def test_assigned_ids_cannot_disappear(self):
        self.generate()
        original = self.review()['epic']['analysis']['content']
        modified = original.replace('AC-001', 'AC-002')
        self.reject('E_ANALYSIS_HISTORY', lambda: self.revise(modified))

    def test_idempotency_conflicting_retry_and_same_byte_revisions(self):
        request = self.request()
        first = sdlc.analysis_write(**request)
        before = (self.directory/'analysis-history.yaml').read_bytes()
        self.assertTrue(sdlc.analysis_write(**request)['replayed'])
        self.assertEqual(before, (self.directory/'analysis-history.yaml').read_bytes())
        for key, value in (('reason', 'Changed reason'), ('expected_review', '0'*64), ('expected_handoff', 'different')):
            self.reject('E_IDEMPOTENCY', lambda: sdlc.analysis_write(**{**request, key:value}))
        second = self.revise(first['epic']['analysis']['content'])
        self.assertEqual(first['epic']['analysis']['revision'], second['epic']['analysis']['revision'])
        self.assertNotEqual(first['epic']['analysis_review_revision'], second['epic']['analysis_review_revision'])
        self.fixture.reopen()
        replay = sdlc.analysis_write(**request)
        self.assertTrue(replay['replayed'])
        self.assertTrue(replay['epic']['analysis']['needs_reconciliation'])
        self.assertEqual(replay['epic']['metadata']['status'], 'discovery')

    def test_stale_revisions_and_concurrent_writers(self):
        self.generate()
        first = self.request(mode='revise')
        second = self.request(mode='revise')
        def execute(request):
            try:
                return sdlc.analysis_write(**request)
            except sdlc.Rejected as exc:
                return {'ok':False, 'code':exc.diagnostics[0].code}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(execute, (first, second)))
        self.assertEqual(sum(v['ok'] for v in results), 1)
        self.assertIn(next(v['code'] for v in results if not v['ok']), ('E_PROJECT_BUSY', 'E_REVISION_CONFLICT'))
        stale = {**first, 'operation_id':self.fixture.unique('stale')}
        self.reject('E_REVISION_CONFLICT', lambda: sdlc.analysis_write(**stale))

    def test_reopen_cannot_race_generation_or_silently_reconcile(self):
        request = self.request()
        entered, release = threading.Event(), threading.Event()
        real = business.publish
        def pause(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('Test synchronization timeout')
            return real(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as pool, patch.object(business, 'publish', side_effect=pause):
            future = pool.submit(sdlc.analysis_write, **request)
            self.assertTrue(entered.wait(5))
            try:
                self.reject('E_PROJECT_BUSY', self.fixture.reopen)
            finally:
                release.set()
            future.result(timeout=10)
        self.fixture.reopen()
        self.assertFalse(self.review()['current'])
        self.reject('E_ANALYSIS_INPUT', lambda: self.revise('stale'))

    def test_reopening_requires_new_business_cycle_and_explicit_reconciliation(self):
        self.generate()
        original = self.review()['epic']['analysis']['content']
        old = self.request(original, 'revise')
        self.fixture.reopen()
        self.fixture.complete()
        self.fixture.revise(self.fixture.initial_document, mode='generate')
        self.fixture.approve()
        self.fixture.advance()
        review = self.review()
        self.assertFalse(review['current'])
        self.reject('E_ANALYSIS_INPUT', lambda: sdlc.analysis_write(**old))
        changed = original.replace(old['expected_baseline'], review['input']['baseline_id']).replace('Approval: BD-0001', 'Approval: '+review['input']['approval_id']).replace('Handoff: '+old['expected_handoff'], 'Handoff: '+review['input']['handoff_id'])
        revised = self.revise(changed)
        self.assertEqual(revised['epic']['metadata']['status'], 'functional_analysis')
        self.assertTrue(self.review()['current'])
        self.assertEqual(len(revised['epic']['analysis']['history']), 2)

    def test_partial_publication_recovers_and_rejects_intervening_edits(self):
        request = self.request()
        real = business.atomic_bytes
        calls = 0
        def fail_second(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('Injected interruption')
            return real(*args)
        with patch.object(business, 'atomic_bytes', side_effect=fail_second):
            self.reject('E_WRITE_UNCERTAIN', lambda: sdlc.analysis_write(**request))
        self.reject('E_ANALYSIS_RECOVERY', self.review)
        (self.directory/'specification.md').write_text('unrelated edit')
        self.reject('E_ANALYSIS_RECOVERY', lambda: sdlc.business_recover(self.project, 'REQ-0001', recover_analysis=True))
        (self.directory/'specification.md').write_bytes(request['document_path'].read_bytes())
        recovered = sdlc.business_recover(self.project, 'REQ-0001', recover_analysis=True)
        self.assertTrue(recovered['ok'])
        self.assertTrue(self.review()['current'])
        self.assertTrue(sdlc.analysis_write(**request)['replayed'])

    def test_revision_interruption_keeps_previous_contents_recoverable(self):
        self.generate()
        old = self.review()['epic']['analysis']['content']
        request = self.request(old.replace('Users can assign', 'Users may assign'), 'revise')
        with patch.object(business, 'atomic_bytes', side_effect=OSError('Injected failure')):
            self.reject('E_WRITE_UNCERTAIN', lambda: sdlc.analysis_write(**request))
        sdlc.business_recover(self.project, 'REQ-0001', recover_analysis=True)
        ledger = yaml.safe_load((self.directory/'analysis-history.yaml').read_text())
        self.assertEqual(base64.b64decode(ledger['revisions'][0]['content_base64']).decode(), old)
        self.assertEqual(len(ledger['revisions']), 2)

    def test_abrupt_exit_and_inspected_lock_recovery(self):
        request = self.request()
        args = {k:str(v) if isinstance(v, Path) else v for k,v in request.items()}
        program = "import os,sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import sdlc,business_refinement; a=json.loads(sys.argv[2]); a['project']=Path(a['project']); a['document_path']=Path(a['document_path']); business_refinement.atomic_bytes=lambda *args: os._exit(17); sdlc.analysis_write(**a)"
        child = subprocess.run([sys.executable, '-c', program, str(fixtures.SCRIPT.parent), json.dumps(args)], capture_output=True, text=True)
        self.assertEqual(child.returncode,17,child.stderr)
        self.assertTrue((self.project/'.sdlc-discovery.lock').exists())
        self.reject('E_ANALYSIS_RECOVERY', self.review)
        # Child has terminated; explicit test-operator inspection permits lock removal.
        (self.project/'.sdlc-discovery.lock').rmdir()
        self.assertTrue(sdlc.business_recover(self.project, 'REQ-0001', recover_analysis=True)['ok'])

    def test_history_corruption_unsafe_artifacts_and_direct_edits_are_not_repaired(self):
        self.generate()
        spec = self.directory/'specification.md'
        original = spec.read_bytes()
        spec.write_bytes(original+b'changed')
        self.reject('E_ANALYSIS_MISMATCH', self.review)
        spec.unlink()
        external = self.project/'external.md'
        external.write_bytes(original)
        spec.symlink_to(external)
        self.reject('E_ANALYSIS_FILE', self.review)
        spec.unlink()
        spec.write_bytes(original)
        path = self.directory/'analysis-history.yaml'
        ledger = yaml.safe_load(path.read_text())
        ledger['revisions'][0]['content_base64'] = base64.b64encode(b'bad').decode()
        path.write_text(yaml.safe_dump(ledger))
        self.reject('E_ANALYSIS_HISTORY', self.review)

    def test_initial_publication_interruptions_at_each_artifact_and_post_commit_retry(self):
        for stop in (1, 2, 3):
            if stop > 1:
                self.setUp()
            with self.subTest(stop=stop):
                request = self.request()
                real = business.atomic_bytes
                calls = 0
                def fail(*args):
                    nonlocal calls
                    calls += 1
                    if calls == stop:
                        raise OSError('Injected publication interruption')
                    return real(*args)
                with patch.object(business, 'atomic_bytes', side_effect=fail):
                    self.reject('E_WRITE_UNCERTAIN', lambda: sdlc.analysis_write(**request))
                recovered = sdlc.business_recover(self.project, 'REQ-0001', recover_analysis=True)
                self.assertEqual(recovered['epic']['metadata']['status'], 'functional_analysis')
                self.assertTrue(sdlc.analysis_write(**request)['replayed'])
        # Simulate a lost success response after the complete transaction.
        request = self.request(mode='revise')
        real_publish = business.publish
        def lose_response(*args, **kwargs):
            real_publish(*args, **kwargs)
            raise business.BusinessError('E_WRITE_UNCERTAIN', 'Injected lost success response')
        with patch.object(business, 'publish', side_effect=lose_response):
            self.reject('E_WRITE_UNCERTAIN', lambda: sdlc.analysis_write(**request))
        self.assertTrue(sdlc.analysis_write(**request)['replayed'])
        self.assertEqual(len(self.review()['epic']['analysis']['history']), 2)

    def test_feedback_validation_and_retired_ids_remain_retired(self):
        self.generate()
        original = self.review()['epic']['analysis']['content']
        feedback = self.project/'bad-feedback.yaml'
        feedback.write_text('actor: Fixture PO\ntext: Change this.\nitems: [FR-999]\n')
        self.reject('E_ANALYSIS_REFERENCE', lambda: sdlc.analysis_write(**self.request(original,'revise',feedback_path=feedback)))
        changed = original.replace('Status: blocked', 'Status: retired')
        self.revise(changed)
        saved = (self.directory/'analysis-history.yaml').read_bytes()
        self.reject('E_ANALYSIS_HISTORY', lambda: self.revise(original))
        self.assertEqual(saved,(self.directory/'analysis-history.yaml').read_bytes())

    def test_analysis_without_inherited_questions_or_proposals(self):
        # A separate approved baseline can have all Discovery questions answered.
        self.fixture.reopen()
        self.fixture.append([fixtures.record('human_decision', 'Test fixture: only future dates.', action='answer', target='D-0006')])
        self.fixture.complete()
        source = self.fixture.view()['epic']['source_revision']
        business_text = self.fixture.initial_document.replace(self.fixture.view()['epic']['business']['source_revision'],source).replace('D-0005, D-0004', 'D-0005, D-0004, D-0008')
        old_line = next(line for line in business_text.splitlines() if '**U-001**' in line)
        business_text = business_text.replace(old_line, 'None recorded.')
        self.fixture.revise(business_text,mode='generate')
        request = self.fixture.request(acknowledged=[])
        self.fixture.execute(request)
        self.fixture.advance()
        text = document(self.review()['input']).replace('Status: deferred', 'Status: open')
        self.assertTrue(sdlc.analysis_write(**self.request(text))['ok'])
        self.assertEqual(self.review()['details']['inherited'],[])

    def test_inherited_analysis_question_cannot_be_retired_or_undeferred(self):
        text = document(self.review()['input'])
        for state in ('open','retired'):
            self.reject('E_ANALYSIS_UNRESOLVED', lambda: sdlc.analysis_write(**self.request(text.replace('Status: deferred','Status: '+state))))

    def test_inherited_unconfirmed_proposals_are_visible_but_never_confirmed_coverage(self):
        self.fixture.reopen()
        self.fixture.append([fixtures.record('ai_assumption', 'Test fixture: date colours might help.')])
        self.fixture.complete()
        source = self.fixture.view()['epic']['source_revision']
        previous_source = self.fixture.view()['epic']['business']['source_revision']
        business_text = self.fixture.initial_document.replace(previous_source,source).replace('None recorded.', '- **P-001** [D-0008] Unconfirmed date colours.')
        self.fixture.revise(business_text,mode='generate')
        self.fixture.execute(self.fixture.request(acknowledged=['U-001','P-001']))
        self.fixture.advance()
        text = document(self.review()['input']).replace('## Analysis proposals\nNone recorded.', '## Analysis proposals\n### AP-001 — Date colours\nBusiness sources: B-001\nDiscovery evidence: D-0008\nStatus: proposed\nAffected items: FR-001\nStatement: Unconfirmed potential date colours; outside specified behavior.')
        self.assertTrue(sdlc.analysis_write(**self.request(text))['ok'])
        self.assertEqual(len(self.review()['details']['inherited']),2)
        self.assertEqual(self.review()['details']['items']['AP-001']['fields']['Status'],'proposed')
        self.reject('E_ANALYSIS_COVERAGE', lambda: self.revise(text.replace('[elaborated] FR-001 | Task', '[elaborated] AP-001 | Task')))

    def test_recovery_allowlist_rejects_path_traversal_without_writes(self):
        request = self.request()
        with patch.object(business,'atomic_bytes',side_effect=OSError('Injected interruption')):
            self.reject('E_WRITE_UNCERTAIN', lambda: sdlc.analysis_write(**request))
        journal = self.directory/analysis.JOURNAL
        data = json.loads(journal.read_text())
        data['before']['../escape'] = None
        data['after']['../escape'] = base64.b64encode(b'bad').decode()
        journal.write_text(json.dumps(data))
        self.reject('E_ANALYSIS_RECOVERY', lambda: sdlc.business_recover(self.project,'REQ-0001',recover_analysis=True))
        self.assertFalse((self.directory.parent/'escape').exists())

    def test_existing_business_reference_whitespace_remains_compatible(self):
        self.fixture.reopen()
        self.fixture.complete()
        self.fixture.revise(self.fixture.initial_document.replace('D-0005, D-0004','D-0005,D-0004'),mode='generate')
        self.fixture.approve()
        self.fixture.advance()
        self.assertIn('[D-0005,D-0004]',self.review()['input']['business'])
        self.assertTrue(self.generate()['ok'])

    def test_cli_generation_revision_review_and_no_later_operations(self):
        request = self.request()
        args = [sys.executable,str(fixtures.SCRIPT),'--project',str(self.project),'analysis-generate','REQ-0001','--expected-analysis-review-revision',request['expected_review'],'--expected-baseline-id',request['expected_baseline'],'--expected-handoff-id',request['expected_handoff'],'--operation-id',request['operation_id'],'--editor',request['editor'],'--reason',request['reason'],'--document-file',str(request['document_path'])]
        run = subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertTrue(json.loads(run.stdout)['ok'])
        helptext = subprocess.run([sys.executable,str(fixtures.SCRIPT),'--project',str(self.project),'--help'],capture_output=True,text=True).stdout
        for name in ('analysis-review','analysis-generate','analysis-revise','analysis-recover'):
            self.assertIn(name,helptext)
        for name in ('analysis-approve','analysis-advance','technical-design','story-new'):
            self.assertNotIn(name,helptext)
