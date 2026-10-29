"""Pure report-projection tests; fixture approvals are not human decisions."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verification_report


class VerificationReportTests(unittest.TestCase):
    def report(self):
        return {
            'source_revision': 'source-123', 'security': 'security-456',
            'checks': {'unit': {'status': 'passed', 'exit_code': 0, 'output_sha256': 'output-hash',
                                'output': 'large captured output', 'check': {'scenario': 'Fixture unit command'},
                                'source_revision': 'source-123'}},
            'coverage': {'FR-001': {'disposition': 'implemented', 'reason': 'Approved scenario'},
                         'FR-002': {'disposition': 'blocked', 'reason': 'Needs human clarification'},
                         'FR-003': {'disposition': 'excluded', 'reason': 'Outside accepted scope'}},
            'unresolved': [{'id': 'AQ-001', 'text': 'Open question remains unanswered'}],
            'scenarios': [{'id': 'TC-001', 'status': 'passed', 'requirements': ['FR-001'], 'evidence': 'actual-result-789'},
                          {'id': 'TC-002', 'status': 'blocked', 'requirements': ['FR-002'], 'reason': 'No product outcome defined'}],
            'limitations': [{'id': 'LIM-001', 'runtime_behavior': 'Return unsupported response without changing state',
                             'requirements': ['FR-002'], 'scope': 'Local prototype', 'validity': 'Current Analysis cycle',
                             'approval': 'design-approval-123', 'actor': 'Fixture human', 'decision': 'I authorize this exact prototype limitation.'}],
            'exclusions': [{'id': 'FR-003', 'authority': 'business-baseline-123'}],
            'residual_risks': ['Local persistence has not been assessed'],
            'references': {'design': {'name': 'technical-design.md', 'path': '/tmp/project [demo]/technical-design.md'},
                           'analysis': 'analysis-baseline-123'},
            'qa_context': {'implementation_approval': 'code-approval-123'},
        }

    def test_complete_disclosure_of_scope_evidence_authority_and_risks(self):
        rendered = verification_report.render(self.report())
        for expected in ('Verified for the stated scope', 'TC-001', 'TC-002', 'actual-result-789',
                         'Needs human clarification', 'Open question remains unanswered', 'Outside accepted scope',
                         'business-baseline-123', 'LIM-001', 'Return unsupported response without changing state',
                         'Local prototype', 'Current Analysis cycle', 'design-approval-123', 'Fixture human',
                         'I authorize this exact prototype limitation.', 'output-hash', 'source-123', 'security-456',
                         'analysis-baseline-123', 'code-approval-123', 'Local persistence has not been assessed'):
            self.assertIn(expected, rendered)
        self.assertIn('[technical-design.md](</tmp/project%20%5Bdemo%5D/technical-design.md>)', rendered)
        self.assertNotIn('large captured output', rendered)

    def test_legacy_fields_render_without_inventing_scenario_results_or_exclusion_authority(self):
        report = self.report()
        for key in ('scenarios', 'limitations', 'exclusions', 'residual_risks', 'references', 'qa_context'):
            report.pop(key)
        rendered = verification_report.render(report)
        self.assertIn('No individual scenario outcomes recorded', rendered)
        self.assertIn('Authority for the declared exclusions is not established', rendered)
        self.assertIn('passing command does not by itself', rendered)
        self.assertIn('No additional residual risks recorded', rendered)
        self.assertIn('FR-002', rendered)
        self.assertIn('AQ-001', rendered)

    def test_governance_version_and_legacy_status_are_explicit(self):
        report = self.report()
        self.assertIn('Legacy governance: not assessed', verification_report.render(report))
        report['governance_status'] = '0.1'
        rendered = verification_report.render(report)
        self.assertIn('Contract: 0.1', rendered)
        self.assertNotIn('Legacy governance: not assessed', rendered)

    def test_full_scope_report_has_unqualified_result_and_explicit_empty_sections(self):
        report = self.report()
        report.update(coverage={'FR-001': report['coverage']['FR-001']}, unresolved=[], limitations=[], exclusions=[])
        rendered = verification_report.render(report)
        self.assertIn('\nVerified.\n', rendered)
        self.assertNotIn('Verified for the stated scope', rendered)
        self.assertIn('## Blocked requirements\n\nNone recorded.', rendered)
        self.assertIn('## Authorized prototype limitations\n\nNone recorded.', rendered)

    def test_unresolved_or_excluded_or_blocked_or_limited_scope_each_qualifies_result(self):
        base = self.report()
        base.update(coverage={}, unresolved=[], limitations=[], exclusions=[])
        for field, value in (('unresolved', [{'id': 'Q-1', 'text': 'unknown'}]),
                             ('coverage', {'FR-1': {'disposition': 'blocked', 'reason': 'pending'}}),
                             ('coverage', {'FR-1': {'disposition': 'excluded', 'reason': 'excluded'}}),
                             ('limitations', [{'id': 'LIM-1', 'runtime_behavior': 'scoped'}]),
                             ('exclusions', [{'id': 'B-1', 'authority': 'approved-business'}])):
            with self.subTest(field=field, value=value):
                report = deepcopy(base)
                report[field] = value
                self.assertIn('Verified for the stated scope', verification_report.render(report))

    def test_renderer_is_deterministic_and_does_not_mutate_input(self):
        report = self.report()
        before = deepcopy(report)
        first = verification_report.render(report)
        self.assertEqual(first, verification_report.render(report))
        self.assertEqual(first, verification_report.render(json.loads(json.dumps(report,sort_keys=True))))
        self.assertEqual(before, report)
        self.assertTrue(first.endswith('\n'))

    def test_check_lists_and_additional_disclosure_fields_are_retained(self):
        report = self.report()
        report['checks'] = [{'check_id': 'UI-001', 'status': 'passed', 'exit_code': 0, 'output_sha256': 'browser-hash'}]
        report['limitations'][0]['supporting_evidence'] = ['source quote', 'approval-reference']
        rendered = verification_report.render(report)
        for expected in ('UI-001', 'browser-hash', 'Supporting evidence', 'source quote', 'approval-reference'):
            self.assertIn(expected, rendered)

    def test_untrusted_prose_cannot_inject_headings_or_html_or_links(self):
        report = self.report()
        report['unresolved'][0]['text'] = '# Fake approval\n<script>bad()</script> [click](https://example.com)'
        rendered = verification_report.render(report)
        self.assertNotIn('\n# Fake approval', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('[click](', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertIn('\\# Fake approval<br>', rendered)

    def test_legacy_document_link_uses_actual_content_filename(self):
        report = self.report()
        report['references']['design'] = {'name': 'technical-design.md', 'path': '/tmp/legacy/content.md',
                                          'title': 'Technical Design (legacy content.md)', 'link': 'untrusted alias'}
        rendered = verification_report.render(report)
        self.assertIn('[content.md](</tmp/legacy/content.md>)', rendered)
        self.assertNotIn('untrusted alias', rendered)
        self.assertNotIn('[technical-design.md](</tmp/legacy/content.md>)', rendered)


if __name__ == '__main__':
    unittest.main()
