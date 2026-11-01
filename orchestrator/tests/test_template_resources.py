"""Resource failures are structural diagnostics, never partially usable catalogs."""
from pathlib import Path
import json,shutil,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import artifact_templates as templates
import business_refinement as business


class TemplateResourceTests(unittest.TestCase):
    def test_missing_registered_document_manifest_or_package_fails_closed(self):
        with tempfile.TemporaryDirectory() as area:
            root=Path(area)/'templates';shutil.copytree(templates.ROOT,root)
            selected=templates.catalog(root)['idea'];package=Path(selected['path'])
            for name in ('document.md','manifest.yaml'):
                path=package/name;raw=path.read_bytes();path.unlink()
                with self.assertRaises(business.BusinessError) as caught:templates.catalog(root)
                self.assertIn(caught.exception.code,('E_TEMPLATE','E_TEMPLATE_INTEGRITY'))
                path.write_bytes(raw)
                self.assertEqual(templates.catalog(root)['idea']['pin'],selected['pin'])
            moved=package.with_name('unregistered');package.rename(moved)
            with self.assertRaises(business.BusinessError):templates.catalog(root)

    def test_fresh_cli_and_packaged_resources_need_no_root_idea_template(self):
        # Fresh interpreter import is essential: an already imported module could
        # conceal the old import-time filesystem dependency.
        with tempfile.TemporaryDirectory() as area:
            runtime=Path(area).resolve()/'runtime';project=Path(area).resolve()/'application';project.mkdir()
            shutil.copytree(templates.ROOT.parent,runtime/'orchestrator',
                            ignore=shutil.ignore_patterns('tests','__pycache__','*.pyc'))
            root=runtime/'orchestrator/templates'
            self.assertFalse((root/'idea.md').exists())
            script=runtime/'orchestrator/scripts/sdlc.py'
            def cli(*args,ok=True):
                run=subprocess.run([sys.executable,'-B',str(script),'--project',str(project),*args],
                                   capture_output=True,text=True)
                self.assertEqual(run.stderr,'')
                value=json.loads(run.stdout)
                self.assertEqual(value['ok'],ok,value)
                self.assertEqual(run.returncode,0 if ok else 1)
                return value
            resolved=cli('templates')['templates'];self.assertEqual(len(resolved),11)
            created=cli('new','--title','Catalog fixture','--idea','Original business idea.',
                        '--requester','Fixture Requester')
            pin=created['epic']['metadata']['template_provenance']['idea']
            self.assertEqual(pin,resolved['idea']['pin'])
            directory=Path(created['epic']['directory'])
            self.assertEqual(directory/'idea.md',project/'requirements/REQ-0001-catalog-fixture/idea.md')
            original=(directory/'idea.md').read_bytes()
            # An unusable root-level path cannot become a fallback.
            (root/'idea.md').mkdir()
            cli('open','REQ-0001');cli('validate','REQ-0001')
            self.assertEqual((directory/'idea.md').read_bytes(),original)
            selected=Path(resolved['idea']['path'])/'document.md';selected.unlink()
            failure=cli('new','--title','Must fail','--requester','Fixture Requester',ok=False)
            self.assertTrue({d['code'] for d in failure['diagnostics']} & {'E_TEMPLATE','E_TEMPLATE_INTEGRITY'})
            self.assertEqual(len(list((project/'requirements').iterdir())),1)
