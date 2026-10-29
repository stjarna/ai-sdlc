"""Local pinned-runtime installation; standard library only, no Git mutations."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

SCHEMA = '0.1'
PREFIXES = ('orchestrator/scripts/', 'orchestrator/skill/', 'orchestrator/domain-skills/',
            'orchestrator/templates/', 'docs/')
EXACT = {'orchestrator/requirements.txt', '.agents/skills/sdlc/SKILL.md',
         '.claude/skills/sdlc/SKILL.md', '.gitattributes', 'README.md'}
REQUIRED = {'orchestrator/scripts/sdlc.py', 'orchestrator/scripts/install.py',
            'orchestrator/scripts/adoption.py', 'orchestrator/skill/SKILL.md',
            'orchestrator/skill/conversation.md', 'orchestrator/skill/commands.md',
            'orchestrator/domain-skills/catalog.yaml', 'orchestrator/templates/catalog.yaml',
            'orchestrator/requirements.txt', 'docs/specification.md'}


class InstallError(Exception):
    def __init__(self, code, message, path):
        self.code, self.path = code, str(path)
        super().__init__(message)


def require(value, code, message, path):
    if not value:
        raise InstallError(code, message, path)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def git(source, *args):
    run = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(source), *args], capture_output=True,
                         env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    require(run.returncode == 0, 'E_INSTALL_GIT', run.stderr.decode(errors='replace').strip(), source)
    return run.stdout


def selected(name):
    return (name in EXACT or name.startswith(PREFIXES)) and not any(
        p in ('__pycache__', '.DS_Store') or p.endswith('.pyc') for p in PurePosixPath(name).parts)


def safe_name(name):
    return isinstance(name, str) and name and all(ord(c)>=32 and ord(c)!=127 for c in name) and not name.startswith('/') and '\\' not in name and all(
        p not in ('', '.', '..') for p in name.split('/'))


def source_files(source, revision, preview=False):
    source = Path(source).resolve()
    rev = git(source, 'rev-parse', '--verify', revision+'^{commit}').decode().strip()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(git(source, 'archive', rev)), mode='r:') as archive:
        for member in archive:
            if not selected(member.name) or member.isdir():
                continue
            require(safe_name(member.name) and member.isfile(), 'E_INSTALL_RESOURCE',
                    'Runtime resources must be regular files, not symlinks.', member.name)
            files[member.name] = archive.extractfile(member).read()
    if preview:
        require(rev == git(source, 'rev-parse', 'HEAD').decode().strip(), 'E_INSTALL_REVISION',
                'Preview snapshots must name the current HEAD as their base.', source)
        names = git(source, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
        files = {}
        for name in sorted(set(filter(selected, names))):
            path = source/name
            require(safe_name(name) and not any(p.is_symlink() for p in (path, *path.parents)),
                    'E_INSTALL_RESOURCE', 'Runtime resource paths cannot contain symlinks.', path)
            if not path.exists():  # A preview may deliberately remove a tracked file.
                continue
            require(path.is_file(), 'E_INSTALL_RESOURCE', 'Expected a regular runtime file.', path)
            files[name] = path.read_bytes()
    require(REQUIRED <= set(files), 'E_INSTALL_RESOURCE',
            'Selected revision lacks required installation/runtime resources: '+', '.join(sorted(REQUIRED-set(files))), source)
    hashes = {n: digest(raw) for n, raw in files.items()}
    pin = {'source_revision': rev, 'preview': preview, 'files': hashes}
    return files, {**pin, 'snapshot_digest': digest(canonical(pin))}


def environment(runtime, python):
    """Check the selected interpreter and the runtime's existing authoritative catalogs."""
    code = r'''
import json,sys,os,re
from pathlib import Path
assert sys.version_info >= (3,10), 'Python 3.10+ is required'
assert os.name == 'posix', 'The PoC supports local POSIX environments only'
import yaml
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'orchestrator/scripts'))
requirement=(root/'orchestrator/requirements.txt').read_text().strip()
match=re.fullmatch(r'PyYAML==([0-9]+\.[0-9]+\.[0-9]+)',requirement)
assert match and yaml.__version__ == match[1], 'Install the selected runtime pinned requirement: '+requirement
import sdlc,domain_skills,artifact_templates
skills=domain_skills.catalog(sdlc.StrictLoader);templates=artifact_templates.catalog()
paths=[root/'orchestrator/skill'/name for name in ('SKILL.md','conversation.md','commands.md')]
paths += [Path(item['path'])/'SKILL.md' for item in skills.values()]
paths += [root/'.agents/skills/sdlc/SKILL.md']
for path in paths:
    assert path.is_file(), 'Missing skill resource: '+str(path)
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if '://' in link or link.startswith('#'):continue
        target=(path.parent/link.split('#')[0]).resolve()
        assert target.is_relative_to(root.resolve()) and target.exists(), 'Broken skill resource: '+str(target)
print(json.dumps({'python':sys.version.split()[0], 'pyyaml':yaml.__version__,
 'skills':{n:{'version':v['version'],'digest':v['digest']} for n,v in skills.items()},
 'templates':{n:v['pin'] for n,v in templates.items()}}))
'''
    try:
        run = subprocess.run([str(python), '-B', '-c', code, str(runtime)], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallError('E_INSTALL_ENVIRONMENT', str(exc), python) from exc
    require(run.returncode == 0, 'E_INSTALL_ENVIRONMENT', run.stderr.strip(), python)
    return json.loads(run.stdout)


def read_manifest(runtime, expected_digest=None):
    runtime = Path(runtime)
    path = runtime/'installation.json'
    require(not runtime.is_symlink() and path.is_file() and not path.is_symlink(),
            'E_INSTALL_INTEGRITY', 'Expected a regular pinned installation.', path)
    try:
        manifest = json.loads(path.read_text())
        require(isinstance(manifest, dict) and set(manifest) == {'schema_version','source_revision','preview','files','snapshot_digest','python'}
                and manifest['schema_version'] == SCHEMA and type(manifest['preview']) is bool
                and isinstance(manifest['source_revision'], str) and re.fullmatch('[0-9a-f]{40,64}', manifest['source_revision'])
                and isinstance(manifest['files'], dict) and REQUIRED <= set(manifest['files']),
                'E_INSTALL_INTEGRITY', 'Malformed installation manifest.', path)
        require(all(safe_name(n) and selected(n) and isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h)
                    for n,h in manifest['files'].items()), 'E_INSTALL_INTEGRITY', 'Unsafe runtime manifest file set.', path)
        pin = {k: manifest[k] for k in ('source_revision','preview','files','python')}
        require(manifest['snapshot_digest'] == digest(canonical(pin))
                and (expected_digest is None or manifest['snapshot_digest'] == expected_digest),
                'E_INSTALL_INTEGRITY', 'Runtime differs from the expected installation pin.', path)
        actual = set()
        for p in runtime.rglob('*'):
            require(not p.is_symlink(), 'E_INSTALL_INTEGRITY', 'Installed resources cannot be symlinks.', p)
            if p.is_file() and p != path:
                actual.add(p.relative_to(runtime).as_posix())
        require(actual == set(manifest['files']), 'E_INSTALL_INTEGRITY', 'Installed file set differs.', runtime)
        for name, sha in manifest['files'].items():
            require(digest((runtime/name).read_bytes()) == sha, 'E_INSTALL_INTEGRITY', 'Installed resource changed.', runtime/name)
        require(isinstance(manifest['python'],str) and Path(manifest['python']).is_absolute(),
                'E_INSTALL_INTEGRITY', 'Expected an absolute interpreter path.', path)
        return manifest
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise InstallError('E_INSTALL_INTEGRITY', str(exc), path) from exc


def loader_text(runtime, manifest):
    verify = shlex.join([manifest['python'], '-B', str(runtime/'orchestrator/scripts/install.py'),
                        'verify', '--runtime', str(runtime), '--expected-digest', manifest['snapshot_digest']])
    cli = shlex.join([manifest['python'], '-B', str(runtime/'orchestrator/scripts/sdlc.py')])
    return f'''---
name: sdlc
description: Guide existing applications through Discovery, human approvals, Functional Analysis and governed Engineering and QA using a pinned external SDLC runtime.
---

# Installed AI SDLC Assistant

Before operating, run this read-only integrity and environment check:

```sh
{verify}
```

If verification fails, stop and report the diagnostic. Never install, upgrade or repair silently.
Then read and follow [{runtime.name} shared workflow](<{runtime}/orchestrator/skill/SKILL.md>).
Resolve every further resource from that canonical package location.
Use the current application repository as the explicit target project, never the runtime directory.
For first adoption, run `{cli} --project APPLICATION adoption-preflight`; resolve errors before `new`.
Keep existing project instructions, source, tests and Git history intact. Do not copy package AGENTS.md into the application.
Use `{cli}` for deterministic operations. Technical arguments stay internal to the assistant.
Codex CLI and IDE invocation is `$sdlc <command>` or `/skills`; natural language is also supported.
Approval, advancement, assignment and starting work remain separate human decisions.
Runtime base Git revision: {manifest['source_revision']}; preview: {str(manifest['preview']).lower()}.
Exact runtime snapshot: {manifest['snapshot_digest']}.
This local pin detects changes; it is not a signature or authenticated authorization.
'''


def verify(runtime, expected_digest=None, skill_root=None):
    runtime = Path(runtime).absolute()
    manifest = read_manifest(runtime, expected_digest)
    checked = environment(runtime, manifest['python'])
    if skill_root is not None:
        registration = Path(skill_root)/'sdlc'
        require(not registration.is_symlink() and registration.is_dir(), 'E_INSTALL_REGISTRATION', 'Skill registration is missing or unsafe.', registration)
        require({p.name for p in registration.iterdir()} == {'SKILL.md','installation.json'}, 'E_INSTALL_REGISTRATION', 'Skill registration contains unexpected files.', registration)
        require(not (registration/'SKILL.md').is_symlink() and not (registration/'installation.json').is_symlink(), 'E_INSTALL_REGISTRATION', 'Registration resources must be regular files.', registration)
        require((registration/'SKILL.md').read_text() == loader_text(runtime,manifest)
                and json.loads((registration/'installation.json').read_text()) == {'runtime':str(runtime),'snapshot_digest':manifest['snapshot_digest']},
                'E_INSTALL_REGISTRATION', 'Skill registration differs from the pinned loader.', registration)
    return {'runtime':str(runtime), 'source_revision':manifest['source_revision'], 'preview':manifest['preview'],
            'snapshot_digest':manifest['snapshot_digest'], 'environment':checked}


def outside_repository(path, project):
    require(not any(c in str(path) for c in ('\n','\r','`')) and path.is_absolute() and not path.is_relative_to(project) and not any(p.is_symlink() for p in (path,*path.parents)),
            'E_INSTALL_PATH', 'Installation and registration must be outside the application and contain no symlink paths.', path)
    require(not any((p/'.git').exists() for p in (path,*path.parents)), 'E_INSTALL_PATH', 'Keep runtime and user registration outside Git repositories.', path)


def skill_registrations(root):
    """Inspect actual skill names, including a differently named registration folder."""
    root=Path(root)
    if not root.is_dir():return []
    found=[]
    for entry in sorted(root.iterdir()):
        path=entry/'SKILL.md'
        if not path.is_file():continue
        text=path.read_text(encoding='utf-8')[:65536]
        front=text.split('---',2)
        if len(front)>=3 and not front[0].strip() and re.search(r'^name:\s*[\"\']?sdlc[\"\']?\s*$',front[1],re.MULTILINE):
            found.append(path)
    return found


def install(source, revision, project, runtime_root, skill_root, python, preview=False):
    project = Path(project).resolve(); runtime_root = Path(runtime_root).expanduser().resolve(); skill_root = Path(skill_root).expanduser().resolve()
    require(project.is_dir(), 'E_INSTALL_PROJECT', 'Target application must already exist.', project)
    outside_repository(runtime_root,project);outside_repository(skill_root,project)
    files, pin = source_files(source,revision,preview)
    pin = {k:v for k,v in pin.items() if k!='snapshot_digest'}
    pin['python']=str(Path(python).expanduser().absolute())
    pin['snapshot_digest']=digest(canonical(pin))
    runtime = runtime_root/(pin['source_revision'][:12]+'-'+pin['snapshot_digest'][:16])
    manifest = {'schema_version':SCHEMA, **pin}
    registration = skill_root/'sdlc'
    others=[p for p in skill_registrations(skill_root) if p != registration/'SKILL.md']
    require(not others, 'E_INSTALL_CONFLICT', 'Another skill already declares the sdlc name; no files were overwritten.', skill_root)
    # Never replace another skill, including an empty directory or a symlink.
    if registration.exists() or registration.is_symlink():
        require(registration.is_dir() and not registration.is_symlink()
                and (registration/'SKILL.md').is_file() and not (registration/'SKILL.md').is_symlink()
                and (registration/'SKILL.md').read_text() == loader_text(runtime,manifest),
                'E_INSTALL_CONFLICT', 'An SDLC skill is already registered; no files were overwritten.', registration)
        return {**verify(runtime,pin['snapshot_digest'],skill_root), 'replayed':True}
    skill_root.mkdir(parents=True,exist_ok=True)
    lock = skill_root/'.sdlc-install.lock'
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise InstallError('E_INSTALL_BUSY','Another installer may be running; inspect before retrying.',lock) from exc
    try:
        require(not registration.exists() and not registration.is_symlink(), 'E_INSTALL_CONFLICT', 'Registration appeared concurrently.', registration)
        runtime_root.mkdir(parents=True,exist_ok=True)
        if runtime.exists() or runtime.is_symlink():
            existing=read_manifest(runtime,pin['snapshot_digest'])
            require(existing==manifest,'E_INSTALL_CONFLICT','Existing installation uses different environment metadata.',runtime)
            environment(runtime,manifest['python'])
        else:
            with tempfile.TemporaryDirectory(prefix='.install-',dir=runtime_root) as temporary:
                stage=Path(temporary)/'runtime';stage.mkdir()
                for name,raw in files.items():
                    target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                (stage/'installation.json').write_bytes(canonical(manifest))
                environment(stage,manifest['python'])
                stage.rename(runtime)
        with tempfile.TemporaryDirectory(prefix='.register-',dir=skill_root) as temporary:
            stage=Path(temporary)/'sdlc';stage.mkdir()
            (stage/'SKILL.md').write_text(loader_text(runtime,manifest))
            (stage/'installation.json').write_bytes(canonical({'runtime':str(runtime),'snapshot_digest':pin['snapshot_digest']}))
            stage.rename(registration)
        return {**verify(runtime,pin['snapshot_digest'],skill_root), 'registration':str(registration), 'replayed':False}
    finally:
        lock.rmdir()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='operation',required=True)
    create=commands.add_parser('install');create.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]);create.add_argument('--revision',required=True)
    create.add_argument('--project',required=True,type=Path);create.add_argument('--runtime-root',type=Path,default=Path.home()/'.local/share/ai-sdlc/runtimes')
    create.add_argument('--skill-root',type=Path,default=Path.home()/'.agents/skills');create.add_argument('--python',default=sys.executable)
    create.add_argument('--preview-working-tree',action='store_true',help='Explicit uncommitted preview: bind HEAD plus exact selected working-tree bytes, never claim a clean release.')
    check=commands.add_parser('verify');check.add_argument('--runtime',required=True,type=Path);check.add_argument('--expected-digest');check.add_argument('--skill-root',type=Path)
    args=parser.parse_args(argv)
    try:
        value=install(args.source,args.revision,args.project,args.runtime_root,args.skill_root,args.python,args.preview_working_tree) if args.operation=='install' else verify(args.runtime,args.expected_digest,args.skill_root)
        output={'ok':True,'operation':args.operation,'diagnostics':[],**value}
    except InstallError as exc:
        output={'ok':False,'operation':args.operation,'diagnostics':[{'severity':'error','code':exc.code,'file':exc.path,'message':str(exc)}]}
    except (OSError,ValueError,TypeError,RecursionError,subprocess.SubprocessError) as exc:
        output={'ok':False,'operation':args.operation,'diagnostics':[{'severity':'error','code':'E_INSTALL_IO','file':str(getattr(args,'runtime',getattr(args,'source',''))),'message':str(exc)}]}
    print(json.dumps(output,ensure_ascii=False));return 0 if output['ok'] else 1


if __name__=='__main__':
    sys.exit(main())
