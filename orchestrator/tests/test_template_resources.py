"""Resource failures are structural diagnostics, never partially usable catalogs."""
from pathlib import Path
import shutil,sys,tempfile,unittest
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
