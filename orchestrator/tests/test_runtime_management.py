"""External admin switching with disposable source/application installations only."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import install
import runtime_management as management
import test_installation as fixture

class RuntimeManagementTests(unittest.TestCase):
    setUpClass=classmethod(fixture.InstallationTests.setUpClass.__func__)
    setUp=fixture.InstallationTests.setUp
    installed=fixture.InstallationTests.installed
    def candidate(self):
        # Exact committed fictional fixture revision B, never an implementation commit.
        (self.source/'README.md').write_bytes((self.source/'README.md').read_bytes()+b'\nFixture B.\n')
        fixture.git(self.source,'add','README.md');fixture.git(self.source,'commit','-qm','Fictional runtime B')
        revision=fixture.git(self.source,'rev-parse','HEAD').strip()
        value=install.prepare(self.source,revision,self.project,self.runtime_root,sys.executable)
        return {'runtime':value['runtime'],'snapshot_digest':value['snapshot_digest']}
    def update(self,a,b,operation='update-b'):
        return management.switch(self.skills,b,a['snapshot_digest'],operation,'Fixture operator','Explicit fixture update','update')
    def test_side_by_side_default_update_rollback_and_exact_retries(self):
        before=fixture.hashes(self.project);a=self.installed();old=fixture.hashes(self.runtime)
        self.assertIn('with -B',(self.skills/'sdlc/SKILL.md').read_text())
        b=self.candidate();self.assertEqual(management.registration(self.skills)['runtime'],a['runtime'])
        with self.assertRaises(install.InstallError):install.install(**{**self.args,'revision':install.read_manifest(b['runtime'])['source_revision']})
        selected=self.update(a,b);self.assertEqual(selected['runtime'],b['runtime'])
        self.assertTrue(self.update(a,b)['replayed'])
        rollback=management.switch(self.skills,None,b['snapshot_digest'],'rollback-a','Fixture operator','Restore prior default','rollback')
        self.assertEqual(rollback['runtime'],a['runtime'])
        self.assertTrue(management.switch(self.skills,None,b['snapshot_digest'],'rollback-a','Fixture operator','Restore prior default','rollback')['replayed'])
        self.assertEqual(old,fixture.hashes(self.runtime));self.assertTrue(Path(b['runtime']).is_dir())
        self.assertEqual(before,fixture.hashes(self.project));install.verify(a['runtime'],a['snapshot_digest'],self.skills)
    def test_failed_switch_restores_exact_registration(self):
        a=self.installed();b=self.candidate();before=fixture.hashes(self.skills/'sdlc');original=management.atomic;failed=False
        def fault(path,raw):
            nonlocal failed
            if path.name=='installation.json' and not failed:failed=True;raise OSError('injected switch failure')
            return original(path,raw)
        with patch.object(management,'atomic',side_effect=fault):
            with self.assertRaises(OSError):self.update(a,b)
        self.assertEqual(before,fixture.hashes(self.skills/'sdlc'));self.assertFalse(management.pending(self.skills).exists())
    def test_hard_interruption_blocks_reads_and_explicit_recovery_restores(self):
        class Crash(BaseException):pass
        a=self.installed();b=self.candidate();before=fixture.hashes(self.skills/'sdlc');original=management.atomic
        def crash(path,raw):
            if path.name=='installation.json':raise Crash()
            return original(path,raw)
        with patch.object(management,'atomic',side_effect=crash):
            with self.assertRaises(Crash):self.update(a,b)
        with self.assertRaises(install.InstallError) as caught:management.registration(self.skills)
        self.assertEqual(caught.exception.code,'E_INSTALL_RECOVERY')
        management.recover(self.skills);self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))
    def test_corruption_stale_context_and_missing_previous_fail_without_switch(self):
        a=self.installed()
        with self.assertRaises(install.InstallError) as caught:management.switch(self.skills,None,a['snapshot_digest'],'r','Fixture','Rollback','rollback')
        self.assertEqual(caught.exception.code,'E_INSTALL_NO_PREVIOUS')
        b=self.candidate();before=fixture.hashes(self.skills/'sdlc')
        with self.assertRaises(install.InstallError):management.switch(self.skills,b,'0'*64,'stale','Fixture','Update','update')
        self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))
        (Path(b['runtime'])/'README.md').write_text('Corrupt')
        with self.assertRaises(install.InstallError):self.update(a,b)
        self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))
    def test_corrupt_previous_runtime_prevents_rollback(self):
        a=self.installed();b=self.candidate();self.update(a,b);before=fixture.hashes(self.skills/'sdlc')
        (Path(a['runtime'])/'README.md').write_text('Corrupt previous')
        with self.assertRaises(install.InstallError):management.switch(self.skills,None,b['snapshot_digest'],'r','Fixture','Rollback','rollback')
        self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))
    def test_lock_and_changed_idempotent_intent_reject(self):
        a=self.installed();b=self.candidate()
        with management.lock(self.skills):
            with self.assertRaises(install.InstallError) as caught:self.update(a,b)
        self.assertEqual(caught.exception.code,'E_INSTALL_BUSY');self.update(a,b)
        with self.assertRaises(install.InstallError):management.switch(self.skills,b,a['snapshot_digest'],'update-b','Other','Different','update')

    def test_second_rollback_does_not_toggle_forward_and_concurrent_switches_are_serialized(self):
        from concurrent.futures import ThreadPoolExecutor
        a=self.installed();b=self.candidate()
        def attempt(number):
            try:return self.update(a,b,'race-'+str(number))['runtime']
            except install.InstallError as exc:return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,(1,2)))
        self.assertEqual(results.count(b['runtime']),1,results)
        self.assertTrue(set(results)-{b['runtime']} <= {'E_INSTALL_BUSY','E_INSTALL_STALE'})
        management.switch(self.skills,None,b['snapshot_digest'],'rollback','Fixture','Explicit rollback','rollback')
        before=fixture.hashes(self.skills/'sdlc')
        with self.assertRaises(install.InstallError) as caught:management.switch(self.skills,None,a['snapshot_digest'],'rollback-again','Fixture','Another rollback','rollback')
        self.assertEqual(caught.exception.code,'E_INSTALL_ALREADY_ACTIVE');self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))

    def test_failure_during_final_switch_durability_restores_previous_default(self):
        a=self.installed();b=self.candidate();before=fixture.hashes(self.skills/'sdlc');original=management.sync;count=0
        def fault(path):
            nonlocal count
            if path==self.skills:
                count+=1
                if count==2:raise OSError('Injected final directory fsync failure')
            return original(path)
        with patch.object(management,'sync',side_effect=fault):
            with self.assertRaises(OSError):self.update(a,b)
        self.assertEqual(before,fixture.hashes(self.skills/'sdlc'))

    def test_malformed_managed_history_and_symlink_destinations_are_structured_failures(self):
        import json
        a=self.installed();b=self.candidate();self.update(a,b)
        path=self.skills/'sdlc/installation.json';value=json.loads(path.read_text());value['history'][0]['previous']=[];path.write_text(json.dumps(value))
        with self.assertRaises(install.InstallError) as caught:install.verify(b['runtime'],b['snapshot_digest'],self.skills)
        self.assertEqual(caught.exception.code,'E_INSTALL_REGISTRATION')
        for malformed in ([],None,'invalid'):
            path.write_text(json.dumps(malformed))
            with self.assertRaises(install.InstallError) as caught:install.verify(b['runtime'],b['snapshot_digest'],self.skills)
            self.assertEqual(caught.exception.code,'E_INSTALL_REGISTRATION')
        alias=self.base/'runtime-alias';alias.symlink_to(self.runtime_root,target_is_directory=True)
        with self.assertRaises(install.InstallError) as caught:install.prepare(self.source,self.revision,self.project,alias,sys.executable)
        self.assertEqual(caught.exception.code,'E_INSTALL_PATH')
