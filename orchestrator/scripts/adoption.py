"""Read-only adoption preflight; never initializes, rearranges or repairs a project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import install as installation

OUTPUTS = {'dist','build','coverage','.coverage','htmlcov','.next','.nuxt','test-results',
           'playwright-report','.cache','.run','target','venv'}


def preflight(project, runtime=None, skill_root=None):
    project=Path(project).expanduser().resolve()
    runtime=Path(runtime).expanduser().resolve() if runtime else Path(__file__).resolve().parents[2]
    skill_root=Path(skill_root).expanduser().resolve() if skill_root else Path.home()/'.agents/skills'
    nested_skill_roots=[]
    diagnostics=[];info={'project':str(project),'runtime':str(runtime),'instructions':[], 'registrations':[]}
    def add(severity,code,path,message):
        diagnostics.append({'severity':severity,'code':code,'file':str(path),'message':message})
    def git(*args):
        run=subprocess.run(['git','-c','core.fsmonitor=false','-C',str(project),*args],capture_output=True,text=True,
                           env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},timeout=20)
        return run
    if not project.is_dir():
        add('error','E_ADOPTION_PROJECT',project,'Application directory must already exist.')
    else:
        try:
            root=git('rev-parse','--show-toplevel')
            if root.returncode:
                add('error','E_ADOPTION_GIT',project,'Expected an existing Git application repository; no repository was initialized.')
            elif Path(root.stdout.strip()).resolve()!=project:
                add('error','E_ADOPTION_ROOT',project,'Select the existing repository root explicitly.')
            else:
                revision=git('rev-parse','--verify','HEAD')
                if revision.returncode:
                    add('error','E_ADOPTION_BASELINE',project,'No initial application commit exists. Capture its baseline explicitly before adoption.')
                else:info['application_revision']=revision.stdout.strip()
                status=git('status','--porcelain=v1','--untracked-files=all')
                if status.returncode:add('error','E_ADOPTION_GIT',project,status.stderr.strip())
                else:
                    info['working_tree_clean']=not bool(status.stdout)
                    info['working_tree_status']=status.stdout.splitlines()
                    if status.stdout:add('warning','W_ADOPTION_DIRTY',project,'Working tree has existing changes. Preserve and review them; the initial product baseline is not clean.')
            if (project/'.sdlc-discovery.lock').exists():
                add('error','E_ADOPTION_BUSY',project/'.sdlc-discovery.lock','An SDLC writer or abandoned lock may exist; inspect it without deleting it automatically.')
        except (OSError,subprocess.SubprocessError) as exc:
            add('error','E_ADOPTION_GIT',project,str(exc))
    try:
        if (runtime/'installation.json').exists():
            info['installation']=installation.verify(runtime,skill_root=skill_root)
            if info['installation']['preview']:
                add('warning','W_ADOPTION_PREVIEW',runtime,'This is an explicitly content-pinned working-tree preview, not a committed release.')
        else:
            info['environment']=installation.environment(runtime,sys.executable)
            add('warning','W_ADOPTION_UNREGISTERED',runtime,'Checkout mode: no verified external installation manifest. Install/register a pinned runtime before the independent-repository demonstration.')
        import engineering
        import sdlc
        ignored=engineering.IGNORED
        if project.is_dir():
            managed=False
            requirements=project/'requirements'
            if requirements.is_symlink() or (requirements.exists() and not requirements.is_dir()):
                add('error','E_ADOPTION_REQUIREMENTS',requirements,'Reserved requirements/ must be a regular directory, never a symlink or existing file.')
            elif requirements.exists():
                epics,found=sdlc.scan(project)
                for diagnostic in found:
                    if diagnostic.severity=='error':add('error','E_ADOPTION_REQUIREMENTS',diagnostic.file,diagnostic.code+': '+diagnostic.message)
                managed=bool(epics) and not any(d.severity=='error' for d in found)
                info['existing_requests']=[e.metadata.get('id') for e in epics]
                if not epics and any(requirements.iterdir()):
                    add('warning','W_ADOPTION_REQUIREMENTS',requirements,'Directory exists without managed requests. Review its contents before reserving this namespace; nothing was changed.')
            qa=project/'qa'
            if qa.is_symlink() or (qa.exists() and not qa.is_dir()):
                add('error','E_ADOPTION_QA',qa,'Reserved qa/ conflicts with an existing file or symlink.')
            elif qa.exists() and not (managed and any(
                    event.get('action')=='write' and event.get('kind')=='automation'
                    for epic in epics for cycle in epic.metadata.get('work_tracks',{}).get('cycles',[])
                    for event in cycle['qa']['history'])):
                add('error','E_ADOPTION_QA',qa,'Existing qa/ is not established SDLC-managed QA. Do not repartition, move or claim its tests automatically.')
            elif qa.exists():
                add('warning','W_ADOPTION_QA',qa,'Existing QA namespace retained. Review current track history and allowed paths before new automation.')
            def walk(folder):
                for path in sorted(folder.iterdir()):
                    if path.name in ignored or (folder==project and path.name=='requirements'):continue
                    if path.is_symlink():
                        add('error','E_ADOPTION_SYMLINK',path,'Current application fingerprinting rejects source symlinks; no link was followed or changed.')
                    elif path.is_dir():
                        if path.name=='skills' and path.parent.name=='.agents':nested_skill_roots.append(path)
                        if path.name in OUTPUTS:
                            add('warning','W_ADOPTION_OUTPUT',path,'This directory participates in existing source fingerprints. Build/test writes here may stale approvals or violate development boundaries; no exclusion was added.')
                        walk(path)
                    elif path.is_file() and path.name in ('AGENTS.md','CLAUDE.md'):
                        info['instructions'].append(str(path))
                    elif not path.is_file():add('error','E_ADOPTION_FILE',path,'Application inputs must be regular files.')
                    elif path.name in OUTPUTS:
                        add('warning','W_ADOPTION_OUTPUT',path,'This generated-looking file is fingerprinted; review test side effects before adoption.')
            walk(project)
            ignore=project/'.gitignore'
            if ignore.is_file() and not ignore.is_symlink():
                patterns=ignore.read_text(errors='replace').splitlines()
                if any(any(word in line for word in OUTPUTS) for line in patterns if not line.lstrip().startswith('#')):
                    add('warning','W_ADOPTION_OUTPUT_POLICY',ignore,'Git ignore rules are not source exclusions. Review configured output paths even if directories do not yet exist.')
            config=project/'.codex/config.toml'
            if config.is_file():info['instructions'].append(str(config))
            info['instructions']=sorted(set(info['instructions']))
            if info['instructions']:
                add('info','I_ADOPTION_INSTRUCTIONS',project,'Existing project instructions were found and must remain authoritative; no files were edited.')
    except installation.InstallError as exc:
        add('error',exc.code,exc.path,str(exc))
    except (OSError,ValueError,TypeError,RecursionError,ImportError) as exc:
        add('error','E_ADOPTION_READ',project,str(exc))
    roots=[('user',skill_root),('admin',Path('/etc/codex/skills')),('project',project/'.agents/skills')]
    # Codex also discovers nested repo skills when launched in an application subdirectory.
    roots += [('nested-project',p) for p in nested_skill_roots if p!=project/'.agents/skills']
    try:
        seen=set()
        for scope,root in roots:
            if scope in ('project','nested-project') and any(p.is_symlink() for p in (root,root.parent)):
                continue  # The application walk already reports these unsupported links.
            for path in installation.skill_registrations(root):
                key=str(path.absolute())
                if key not in seen:
                    info['registrations'].append({'scope':scope,'path':key});seen.add(key)
        if len(seen)>1:
            add('error','E_ADOPTION_SKILL_CONFLICT',project,'Multiple sdlc skill registrations were found. Select one deliberately; nothing was overwritten.')
        elif not seen:
            add('warning','W_ADOPTION_SKILL_MISSING',skill_root,'No sdlc registration found in the inspected user/admin/project locations.')
    except OSError as exc:
        add('error','E_ADOPTION_READ',skill_root,str(exc))
    errors=any(d['severity']=='error' for d in diagnostics)
    return {'ok':not errors,'operation':'adoption-preflight','diagnostics':diagnostics,
            'ready':not errors,'baseline_ready':not errors and info.get('working_tree_clean',False),
            'assessment':'structural preflight only; not business approval, test execution or lifecycle authorization',**info}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path);parser.add_argument('--runtime',type=Path);parser.add_argument('--skill-root',type=Path)
    args=parser.parse_args(argv);result=preflight(args.project,args.runtime,args.skill_root)
    print(json.dumps(result,ensure_ascii=False));return 0 if result['ok'] else 1


if __name__=='__main__':sys.exit(main())
