"""Installation/adoption fixtures use isolated Git repositories and fictional authors.

Fixture commits create test baselines only; installation and preflight never commit.
No application approvals or AI/model calls are simulated by these tests.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import install
import adoption
import sdlc

REPO=Path(__file__).resolve().parents[2]


def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def git(root,*args):
    result=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,
        env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_AUTHOR_NAME':'Fictional fixture author',
             'GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fictional fixture author',
             'GIT_COMMITTER_EMAIL':'fixture@example.invalid'})
    assert result.returncode==0,(args,result.stderr)
    return result.stdout


class InstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=tempfile.TemporaryDirectory(prefix='sdlc-install-fixture-')
        cls.addClassCleanup(cls.fixture.cleanup)
        cls.source=Path(cls.fixture.name)/'runtime-source';cls.source.mkdir()
        files,_=install.source_files(REPO,'HEAD',True)
        for name,raw in files.items():
            p=cls.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        git(cls.source,'init','-q');git(cls.source,'add','.')
        git(cls.source,'commit','-qm','Fictional installation source fixture')
        cls.revision=git(cls.source,'rev-parse','HEAD').strip()

    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='sdlc-adoption-test-');self.addCleanup(temp.cleanup)
        self.base=Path(temp.name).resolve();self.project=self.base/'application';self.project.mkdir()
        (self.project/'app.py').write_text('def tasks():\n    return []\n')
        (self.project/'AGENTS.md').write_text('Preserve existing application instructions.\n')
        git(self.project,'init','-q');git(self.project,'add','.')
        git(self.project,'commit','-qm','Fictional pre-SDLC application baseline')
        self.runtime_root=self.base/'runtimes';self.skills=self.base/'home/.agents/skills'
        self.args=dict(source=self.source,revision=self.revision,project=self.project,
                       runtime_root=self.runtime_root,skill_root=self.skills,python=sys.executable)

    def reject(self,code,operation):
        with self.assertRaises(install.InstallError) as caught:operation()
        self.assertEqual(caught.exception.code,code,str(caught.exception))

    def installed(self):
        value=install.install(**self.args);self.runtime=Path(value['runtime']);return value

    def check(self):
        return adoption.preflight(self.project,self.runtime,self.skills)

    def codes(self,result):return {d['code'] for d in result['diagnostics']}

    def test_committed_installation_pins_resources_and_leaves_application_and_history_unchanged(self):
        before=hashes(self.project);value=self.installed()
        self.assertEqual(value['source_revision'],self.revision);self.assertFalse(value['preview'])
        self.assertEqual(before,hashes(self.project))
        self.assertEqual(len(value['environment']['templates']),11)
        self.assertEqual(len(value['environment']['skills']),4)
        text=(self.skills/'sdlc/SKILL.md').read_text()
        self.assertIn(str(self.runtime/'orchestrator/skill/SKILL.md'),text)
        self.assertIn(value['snapshot_digest'],text)
        self.assertNotIn('orchestrator', {p.name for p in self.project.iterdir()})
        self.assertTrue(install.verify(self.runtime,value['snapshot_digest'],self.skills))

    def test_installation_is_exactly_idempotent(self):
        self.installed();before=hashes(self.base)
        self.assertTrue(install.install(**self.args)['replayed'])
        self.assertEqual(before,hashes(self.base))

    def test_existing_unrelated_registration_is_never_overwritten(self):
        root=self.skills/'sdlc';root.mkdir(parents=True)
        (root/'SKILL.md').write_text('An existing unrelated registration.')
        before=hashes(self.base)
        self.reject('E_INSTALL_CONFLICT',lambda:install.install(**self.args))
        self.assertEqual(before,hashes(self.base))
        self.assertFalse(self.runtime_root.exists())

    def test_same_skill_name_in_different_folder_is_rejected(self):
        root=self.skills/'another-name';root.mkdir(parents=True)
        (root/'SKILL.md').write_text('---\nname: sdlc\ndescription: Existing\n---\n')
        self.reject('E_INSTALL_CONFLICT',lambda:install.install(**self.args))
        self.assertFalse(self.runtime_root.exists())

    def test_installation_inside_application_is_rejected(self):
        self.reject('E_INSTALL_PATH',lambda:install.install(**{**self.args,'runtime_root':self.project/'runtime'}))
        self.assertFalse((self.project/'runtime').exists())

    def test_working_tree_preview_is_explicit_and_content_pinned(self):
        file=self.source/'README.md';old=file.read_bytes()
        self.addCleanup(file.write_bytes,old)
        file.write_bytes(old+b'\nExplicit preview fixture change.\n')
        normal=install.source_files(self.source,self.revision)[1]
        files,preview=install.source_files(self.source,self.revision,True)
        self.assertTrue(preview['preview']);self.assertEqual(preview['source_revision'],self.revision)
        self.assertNotEqual(normal['snapshot_digest'],preview['snapshot_digest'])
        self.assertTrue(files['README.md'].endswith(b'Explicit preview fixture change.\n'))

    def test_missing_revision_resources_fail_before_installation(self):
        with patch.object(install,'REQUIRED',install.REQUIRED|{'orchestrator/scripts/missing.py'}):
            self.reject('E_INSTALL_RESOURCE',lambda:install.install(**self.args))
        self.assertFalse(self.runtime_root.exists())

    def test_tampered_runtime_and_expected_pin_are_rejected(self):
        value=self.installed()
        self.reject('E_INSTALL_INTEGRITY',lambda:install.verify(self.runtime,'0'*64))
        p=self.runtime/'orchestrator/templates/versions/idea/1.0.0/document.md'
        p.write_bytes(p.read_bytes()+b'\nChanged.\n')
        self.reject('E_INSTALL_INTEGRITY',lambda:install.verify(self.runtime,value['snapshot_digest']))
        self.assertIn('E_INSTALL_INTEGRITY',self.codes(self.check()))

    def test_interpreter_metadata_is_bound_to_the_installation_pin(self):
        value=self.installed();path=self.runtime/'installation.json'
        manifest=json.loads(path.read_text());manifest['python']=str(self.base/'different-python')
        path.write_text(json.dumps(manifest))
        self.reject('E_INSTALL_INTEGRITY',lambda:install.verify(self.runtime,value['snapshot_digest']))

    def test_tampered_catalog_fails_selected_environment_validation(self):
        self.installed();p=self.runtime/'orchestrator/templates/catalog.yaml'
        p.write_text('schema_version: bad\n')
        self.reject('E_INSTALL_ENVIRONMENT',lambda:install.environment(self.runtime,sys.executable))

    def test_changed_loader_is_not_accepted_as_owned_registration(self):
        self.installed();p=self.skills/'sdlc/SKILL.md';p.write_text(p.read_text()+'\nChanged loader.\n')
        self.reject('E_INSTALL_REGISTRATION',lambda:install.verify(self.runtime,skill_root=self.skills))
        self.reject('E_INSTALL_CONFLICT',lambda:install.install(**self.args))

    def test_missing_interpreter_has_structured_error(self):
        self.reject('E_INSTALL_ENVIRONMENT',lambda:install.install(**{**self.args,'python':self.base/'missing-python'}))
        self.assertFalse((self.skills/'sdlc').exists())
        self.assertFalse(list(self.runtime_root.glob('.install-*')))

    def test_failed_registration_can_reuse_complete_unregistered_runtime(self):
        original=Path.rename
        def fail_registration(path,target):
            if '.register-' in str(path):raise OSError('Injected registration failure')
            return original(path,target)
        with patch.object(Path,'rename',fail_registration):
            with self.assertRaises(OSError):install.install(**self.args)
        self.assertFalse((self.skills/'sdlc').exists())
        self.assertEqual(len(list(self.runtime_root.iterdir())),1)
        self.assertTrue(self.installed()['runtime'])
        self.assertFalse(list(self.skills.glob('.register-*')))

    def test_concurrent_installers_preserve_one_registration(self):
        def attempt(_):
            try:return install.install(**self.args)
            except install.InstallError as exc:return exc.code
        with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(attempt,range(2)))
        self.assertTrue(any(isinstance(r,dict) for r in results),results)
        self.assertTrue(all(isinstance(r,dict) or r in ('E_INSTALL_BUSY','E_INSTALL_CONFLICT') for r in results),results)
        value=next(r for r in results if isinstance(r,dict))
        self.assertTrue(install.verify(Path(value['runtime']),skill_root=self.skills))

    def test_clean_preflight_is_read_only_and_finds_instructions(self):
        self.installed();before=hashes(self.project)
        result=self.check()
        self.assertTrue(result['ready'],result);self.assertTrue(result['baseline_ready'])
        self.assertIn(str(self.project/'AGENTS.md'),result['instructions'])
        self.assertEqual(result['registrations'][0]['scope'],'user')
        self.assertEqual(before,hashes(self.project))
        self.assertFalse((self.project/'requirements').exists())

    def test_read_only_preflight_does_not_execute_git_fsmonitor_hooks(self):
        self.installed();marker=self.project/'unexpected-hook-side-effect'
        hook=self.base/'fsmonitor.py'
        hook.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("executed")\n')
        git(self.project,'config','core.fsmonitor',shlex.join([sys.executable,str(hook)]))
        before=hashes(self.project);result=self.check()
        self.assertTrue(result['ready'],result)
        self.assertFalse(marker.exists());self.assertEqual(before,hashes(self.project))

    def test_dirty_tree_warns_without_cleaning_or_staging(self):
        self.installed();(self.project/'app.py').write_text('Existing uncommitted work.\n')
        before=hashes(self.project);result=self.check()
        self.assertIn('W_ADOPTION_DIRTY',self.codes(result));self.assertFalse(result['baseline_ready'])
        self.assertTrue(result['ready']);self.assertEqual(before,hashes(self.project))

    def test_no_git_or_initial_baseline_is_reported_without_initializing(self):
        self.installed();shutil.rmtree(self.project/'.git')
        self.assertIn('E_ADOPTION_GIT',self.codes(self.check()))
        self.assertFalse((self.project/'.git').exists())
        git(self.project,'init','-q')
        self.assertIn('E_ADOPTION_BASELINE',self.codes(self.check()))

    def test_namespace_conflicts_do_not_restructure_application(self):
        self.installed()
        for name,code in [('requirements','E_ADOPTION_REQUIREMENTS'),('qa','E_ADOPTION_QA')]:
            p=self.project/name;p.write_text('Existing application file.')
            before=hashes(self.project)
            self.assertIn(code,self.codes(self.check()));self.assertEqual(before,hashes(self.project));p.unlink()
        root=self.project/'requirements/docs';root.mkdir(parents=True)
        self.assertIn('E_ADOPTION_REQUIREMENTS',self.codes(self.check()))

    def test_existing_unmanaged_qa_directory_is_a_conflict(self):
        self.installed();(self.project/'qa').mkdir();(self.project/'qa/existing.test').write_text('Existing suite')
        self.assertIn('E_ADOPTION_QA',self.codes(self.check()))

    def test_output_hazards_are_reported_without_adding_exclusions(self):
        self.installed();(self.project/'dist').mkdir();(self.project/'dist/app.js').write_text('output')
        (self.project/'.gitignore').write_text('coverage/\n')
        before=hashes(self.project);result=self.check()
        self.assertIn('W_ADOPTION_OUTPUT',self.codes(result));self.assertIn('W_ADOPTION_OUTPUT_POLICY',self.codes(result))
        self.assertEqual(before,hashes(self.project))
        import engineering
        self.assertIn('dist/app.js',engineering.tree(self.project))

    def test_source_symlinks_are_reported_without_following_them(self):
        self.installed();(self.project/'linked.py').symlink_to(self.project/'app.py')
        self.assertIn('E_ADOPTION_SYMLINK',self.codes(self.check()))
        self.assertTrue((self.project/'linked.py').is_symlink())

    def test_project_skill_symlink_is_reported_without_discovering_outside_resources(self):
        self.installed();outside=self.base/'foreign-agents/skills/foreign';outside.mkdir(parents=True)
        (outside/'SKILL.md').write_text('---\nname: sdlc\ndescription: Outside project\n---\n')
        (self.project/'.agents').symlink_to(self.base/'foreign-agents',target_is_directory=True)
        result=self.check()
        self.assertIn('E_ADOPTION_SYMLINK',self.codes(result))
        self.assertEqual(len(result['registrations']),1)

    def test_project_registration_conflict_is_reported_without_editing_instructions(self):
        self.installed();p=self.project/'.agents/skills/other/SKILL.md';p.parent.mkdir(parents=True)
        p.write_text('---\nname: sdlc\ndescription: Existing project skill\n---\n')
        before=hashes(self.project)
        self.assertIn('E_ADOPTION_SKILL_CONFLICT',self.codes(self.check()))
        self.assertEqual(before,hashes(self.project))

    def test_new_remains_the_existing_request_initialization_operation(self):
        self.installed();before=(self.project/'app.py').read_bytes();head=git(self.project,'rev-parse','HEAD')
        run=subprocess.run([sys.executable,'-B',str(self.runtime/'orchestrator/scripts/sdlc.py'),'--project',str(self.project),'new','--requester','Fictional Requester','--title','Fixture incremental change','--idea','A fictional request used only to verify adoption.'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        value=json.loads(run.stdout);self.assertEqual(value['epic']['metadata']['status'],'discovery')
        self.assertEqual((self.project/'app.py').read_bytes(),before);self.assertEqual(git(self.project,'rev-parse','HEAD'),head)
        self.assertIn('template_provenance',value['epic']['metadata'])
        result=self.check();self.assertTrue(result['ready'],result);self.assertEqual(result['existing_requests'],['REQ-0001'])

    def test_legacy_archive_remains_readable_from_installed_runtime(self):
        self.installed();project=REPO/'examples/todo-app/project'
        run=subprocess.run([sys.executable,'-B',str(self.runtime/'orchestrator/scripts/sdlc.py'),'--project',str(project),'validate','REQ-0001'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertTrue(json.loads(run.stdout)['ok'])

    def test_cli_preflight_is_json_and_never_creates_requests(self):
        self.installed();before=hashes(self.project)
        run=subprocess.run([sys.executable,'-B',str(REPO/'orchestrator/scripts/adoption.py'),'--project',str(self.project),'--runtime',str(self.runtime),'--skill-root',str(self.skills)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertTrue(json.loads(run.stdout)['ready']);self.assertEqual(before,hashes(self.project))
