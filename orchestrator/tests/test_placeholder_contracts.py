"""Named-slot rendering and legacy preservation; no model-output simulation."""
from copy import deepcopy
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import artifact_templates as templates
import business_refinement as business
import sdlc
import test_business_approval as fixtures


class PlaceholderTests(unittest.TestCase):
    def reject(self,code,action):
        with self.assertRaises(business.BusinessError) as error:action()
        self.assertEqual(error.exception.code,code)

    def test_every_registered_layout_matches_explicit_slot_contract_and_render_context(self):
        for name,item in templates.catalog().items():
            keys=templates.lint(name,item['pin']['version'],item['content'])
            context={key:'Fixture '+key for key in keys}
            rendered=templates.render(item,context)
            self.assertNotIn('{{',rendered)
            self.assertEqual(templates.validate_document(item,rendered),item['pin'])
            self.assertEqual(item['pin']['validation_contract'],templates.CONTRACTS[name])

    def test_unknown_missing_duplicate_and_malformed_scaffold_slots_are_rejected(self):
        item=templates.resolve('idea');text=item['content']
        for invalid in (text.replace('{{users}}','{{typo}}'),text.replace('{{users}}',''),text+'\n{{users}}',text.replace('{{users}}','{{ users }}'),text+'\n{{unfinished',text+'\n}}'):
            self.reject('E_TEMPLATE_CONTRACT',lambda:templates.lint('idea','1.1.0',invalid))
        context={key:'Fixture' for key in templates.PLACEHOLDERS['idea']}
        for invalid in ({**context,'extra':'unused'},{key:value for key,value in context.items() if key!='users'},{**context,'users':None}):
            self.reject('E_TEMPLATE_CONTEXT',lambda:templates.render(item,invalid))

    def test_new_idea_all_sections_and_unknowns_preserve_declarations_without_invention(self):
        item=templates.resolve('idea');self.assertEqual(item['pin']['version'],'1.1.0')
        details={'users':'People recording expenses.','expected_value':'Understand spending.','initial_scope':'Record expenses.','success_criteria':'Usability feedback.',
                 'assumptions':'Confirmed: none.','open_questions':'Deferred: discuss reporting with users.'}
        rendered=templates.render_idea(item,'Track personal spending.',details)
        for key,value in details.items():self.assertIn(value,rendered)
        self.assertNotIn('{{',rendered);self.assertNotIn(templates.UNKNOWN,rendered)
        unknown=templates.render_idea(item,'An original idea.')
        self.assertEqual(unknown.count(templates.UNKNOWN),6)
        self.assertNotIn('None recorded.',unknown)
        self.assertEqual(templates.render_idea(item,'An original idea.',{'users':None}),unknown)
        self.reject('E_TEMPLATE_CONTEXT',lambda:templates.render_idea(item,'Idea',{'invented':'Rule'}))

    def test_literal_business_text_is_not_interpreted_as_a_nested_template(self):
        literal='The user typed {{users}} and {{not_a_variable}}.\n\n## Users\nOriginal Markdown context.'
        rendered=templates.render_idea(templates.resolve('idea'),literal)
        self.assertIn(literal,rendered)
        self.assertIn('## Users\n\nNot provided.',rendered)
        self.reject('E_TEMPLATE_DOCUMENT',lambda:templates.assert_resolved('Still {{unknown}}'))
        templates.assert_resolved(r'Literal example: \{{unknown}}')

    def test_real_new_cli_details_unknown_warnings_and_original_history_unchanged(self):
        with tempfile.TemporaryDirectory() as area:
            root=Path(area);details=root/'details.json'
            details.write_text(json.dumps({'users':'Students.','assumptions':'Unconfirmed proposal: shared access.'}))
            cli=[sys.executable,'-B',sdlc.__file__,'--project',str(root)]
            result=subprocess.run(cli+['new','--title','Study tracker','--requester','Fixture Requester','--idea','Track studying.','--idea-details-file',str(details)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            payload=json.loads(result.stdout);directory=Path(payload['epic']['directory']);idea=(directory/'idea.md').read_bytes()
            self.assertIn(b'Students.',idea);self.assertNotIn(b'{{',idea)
            warnings=[d for d in payload['diagnostics'] if d['code']=='W_DISCOVERY_INCOMPLETE'];self.assertEqual(len(warnings),4)
            self.assertEqual(payload['epic']['metadata']['template_provenance']['idea'],templates.resolve('idea')['pin'])
            sdlc.discovery_update(root,'REQ-0001',payload['epic']['revision'],'unchanged-idea',[])
            self.assertEqual((directory/'idea.md').read_bytes(),idea)
            self.assertEqual(sdlc.inspect_epics(root,'validate','REQ-0001')['ok'],True)

    def test_invalid_creation_context_is_structured_and_leaves_no_request(self):
        with tempfile.TemporaryDirectory() as area:
            root=Path(area);path=root/'details.yaml'
            for content in ('users: one\nusers: two\n','[]','users: [one]','unknown: value','!!map hello'):
                path.write_text(content)
                run=subprocess.run([sys.executable,'-B',sdlc.__file__,'--project',str(root),'new','--title','Fixture','--requester','Fixture Requester','--idea-details-file',str(path)],capture_output=True,text=True)
                self.assertEqual(run.returncode,1,run.stdout+run.stderr)
                diagnostic=json.loads(run.stdout)['diagnostics'][0]
                self.assertEqual(diagnostic['code'],'E_TEMPLATE_CONTEXT')
                self.assertEqual(diagnostic['file'],str(path))
                self.assertFalse((root/'requirements').exists())

    def test_legacy_idea_and_other_template_packages_are_still_resolvable(self):
        old=templates.package('idea','1.0.0');self.assertEqual(templates.variables('idea','1.0.0'),('problem',))
        self.assertEqual(templates.render_idea(old,'Original.'),old['content'].replace('{{problem}}','Original.'))
        self.reject('E_TEMPLATE_CONTEXT',lambda:templates.render_idea(old,'Original.',{'users':'Unavailable slot'}))
        for name,item in templates.catalog().items():
            if name!='idea':self.assertEqual(item['pin']['version'],'1.0.0')

    def test_new_business_writes_and_approvals_reject_unresolved_slots(self):
        fixture=fixtures.BusinessApprovalTests('test_approval_freezes_exact_context_and_advancement_is_separate');fixture.setUp();self.addCleanup(fixture.doCleanups)
        original=(fixture.directory/'business.md').read_bytes();text=original.decode().replace('Record deadlines against tasks.','{{unfilled_statement}}')
        # Existing stage validator accepts the prose syntactically; template boundary rejects it.
        with self.assertRaises(sdlc.Rejected) as caught:fixture.revise(text)
        self.assertIn('E_TEMPLATE_DOCUMENT',{d.code for d in caught.exception.diagnostics})
        self.assertEqual(original,(fixture.directory/'business.md').read_bytes())
        with patch.object(templates,'validate_document',return_value=None):fixture.revise(text)
        with self.assertRaises(sdlc.Rejected) as caught:fixture.approve()
        self.assertIn('E_TEMPLATE_DOCUMENT',{d.code for d in caught.exception.diagnostics})
        self.assertFalse((fixture.directory/'business-baselines').exists())
