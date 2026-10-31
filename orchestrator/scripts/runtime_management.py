"""Explicit external runtime preparation, activation and rollback. No application writes."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse
import base64
import json
import os
import re
import sys
import tempfile

import install

HISTORY_FIELDS={'id','action','previous','selected','actor','decision','timestamp','expected_default'}


def fail(condition, message, path, code='E_INSTALL_REGISTRATION'):
    install.require(condition, code, message, path)


def read_json(path):
    def mapping(pairs):
        value={}
        for key,item in pairs:
            if key in value: raise ValueError('Duplicate JSON key: '+key)
            value[key]=item
        return value
    fail(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'Expected a regular nonsymlink JSON file.',path)
    try:return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=mapping)
    except (ValueError,UnicodeError,OSError,RecursionError) as exc:raise install.InstallError('E_INSTALL_INTEGRITY',str(exc),path) from exc


def atomic(path, raw):
    """One durable file replacement; callers own the relevant lock/journal."""
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.runtime-',delete=False) as stream:
            temporary=Path(stream.name);os.chmod(temporary,0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path);sync(path.parent)
    finally:
        if temporary and temporary.exists():temporary.unlink()


def sync(path):
    descriptor=os.open(path,os.O_RDONLY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def pointer(runtime, digest=None):
    path=Path(runtime).expanduser().absolute()
    fail(path.resolve()==path and not any(p.is_symlink() for p in (path,*path.parents)), 'Unsafe runtime path.',path,'E_INSTALL_PATH')
    checked=install.verify(path,digest)
    return {'runtime':str(path),'snapshot_digest':checked['snapshot_digest']}


def loader(runtime, manifest, manager=None):
    manager=manager or {'runtime':str(runtime),'snapshot_digest':manifest['snapshot_digest']}
    return f'''---
name: sdlc
description: Resolve a pinned SDLC runtime before guiding requirements, human approvals and governed Engineering and QA.
---

# Installed runtime resolver

Always invoke installed Python tools with -B to prevent bytecode writes inside the
immutable snapshot. Use the retained interpreter, never a guessed system Python.

Read the adjacent installation.json and find this registration's skill-root. Before any
SDLC work verify the administrative registration and selected runtime using the pinned
manager at {manager['runtime']}/orchestrator/scripts/install.py (its retained interpreter
is in that runtime's installation.json). Invoke show --skill-root SKILL_ROOT, then verify
the returned runtime/digest and registration. A pending switch or verification failure
blocks work; never repair or change the default silently.

Default workflow resource: {runtime}/orchestrator/skill/SKILL.md
Default runtime digest: {manifest['snapshot_digest']}
Manager digest: {manager['snapshot_digest']}

Do NOT load the default workflow as the effective request workflow automatically. Resolve
the explicit application and request/track with runtime-status using the manager's CLI.
For a missing legacy binding ask for an explicit initial future-work binding; never infer
historical runtime versions. Use runtime-check before proposing promotion. An unsupported
old runtime can be inspected but cannot perform managed writes.

Before governed writes use a fresh conversation/context for the resolved runtime. Read
its complete shared SKILL.md, commands.md and conversation.md; resolve and read that
runtime's selected domain packages and templates. Open a runtime-session only after
reading them, declaring the fresh context ID and exact instructions digest returned by
runtime-status. Pass --runtime-session TOKEN to deterministic calls from that exact
runtime. Never reuse a context ID across runtime switches. If the current host context
already contains another runtime's workflow, stop and require a fresh conversation or
host reload, rather than mixing instructions. These declarations are procedural, not
proof of the model's context or authenticated authorization.

Keep application --project explicit. First adoption is read-only preflight; new creates
Discovery only. Approval, promotion, advancement, assignment and start are separate human
decisions. No automatic Git operations, upgrades, project restructuring or notifications.
Codex invocation is $sdlc COMMAND; domain packages are file guidance, not native registrations
or automatic agents. This installer does not register Claude Code.
'''


def pending(skill_root):return Path(skill_root)/'.sdlc-runtime-switch.json'


def valid_pointer(value):
    return isinstance(value,dict) and set(value)=={'runtime','snapshot_digest'} and isinstance(value['runtime'],str) and Path(value['runtime']).is_absolute() and isinstance(value['snapshot_digest'],str) and bool(re.fullmatch('[0-9a-f]{64}',value['snapshot_digest']))


def registration(skill_root, allow_pending=False):
    root=Path(skill_root).expanduser().absolute();folder=root/'sdlc';path=folder/'installation.json'
    fail(allow_pending or not pending(root).exists(),'An interrupted switch requires explicit recover.',pending(root),'E_INSTALL_RECOVERY')
    fail(folder.is_dir() and not folder.is_symlink() and folder.stat().st_uid==os.getuid()
         and {p.name for p in folder.iterdir()}=={'SKILL.md','installation.json'}
         and all((folder/n).is_file() and not (folder/n).is_symlink() for n in ('SKILL.md','installation.json')),
         'Unsafe or unexpected registration resources.',folder)
    data=read_json(path)
    fail(isinstance(data,dict),'Registration metadata must be an object.',path)
    if set(data)=={'runtime','snapshot_digest'}:
        selected=pointer(data['runtime'],data['snapshot_digest'])
        install.verify(selected['runtime'],selected['snapshot_digest'],root)
        return {**data,'schema_version':'0.1','manager':selected,'history':[]}
    fail(set(data)=={'schema_version','runtime','snapshot_digest','manager','history'} and data['schema_version']=='0.2'
         and isinstance(data['history'],list),'Invalid managed registration.',path)
    fail(valid_pointer({'runtime':data['runtime'],'snapshot_digest':data['snapshot_digest']}) and valid_pointer(data['manager']),'Invalid active/manager pin.',path)
    selected=pointer(data['runtime'],data['snapshot_digest']);manager=pointer(data['manager']['runtime'],data['manager']['snapshot_digest'])
    previous=None;seen=set()
    for event in data['history']:
        fail(isinstance(event,dict) and set(event)==HISTORY_FIELDS and all(isinstance(event[k],str) and event[k].strip() for k in ('id','actor','decision','timestamp','expected_default'))
             and event['id'] not in seen and event['action'] in ('update','rollback') and valid_pointer(event['previous']) and valid_pointer(event['selected']),'Invalid administrative history.',path)
        fail(previous is None or event['previous']==previous,'Administrative history was disconnected.',path)
        fail(event['expected_default']==event['previous']['snapshot_digest'],'Decision differs from expected default.',path)
        for value in (event['previous'],event['selected']):
            fail(isinstance(value,dict) and set(value)=={'runtime','snapshot_digest'},'Invalid historical runtime reference.',path)
        seen.add(event['id']);previous=event['selected']
    fail(bool(seen) and previous==selected,'Default differs from recorded history.',path)
    manifest=install.read_manifest(selected['runtime'],selected['snapshot_digest'])
    fail((folder/'SKILL.md').read_text()==loader(Path(selected['runtime']),manifest,manager),'Managed loader differs.',folder/'SKILL.md')
    return data


def validate_registration(folder, runtime, manifest):
    data=registration(folder.parent)
    fail(data['runtime']==str(runtime) and data['snapshot_digest']==manifest['snapshot_digest'],
         'Registration selects another runtime.',folder)


@contextmanager
def lock(root):
    root=Path(root);fail(root.is_dir() and root.stat().st_uid==os.getuid() and not any(p.is_symlink() for p in (root,*root.parents)),'Unsafe registration root.',root,'E_INSTALL_PATH')
    path=root/'.sdlc-install.lock'
    try:path.mkdir()
    except FileExistsError as exc:raise install.InstallError('E_INSTALL_BUSY','Installer is busy; inspect before retrying.',path) from exc
    try:yield
    finally:path.rmdir()


def switch(root, candidate, expected, operation, actor, decision, action):
    root=Path(root).expanduser().absolute()
    fail(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',operation)) and bool(actor.strip()) and bool(decision.strip()),'Supply an operation ID and actual declared decision.',root,'E_INSTALL_INPUT')
    with lock(root):
        old=registration(root)
        for event in old['history']:
            if event['id']==operation:
                fail(event['action']==action and (candidate is None or event['selected']==candidate) and event['actor']==actor and event['decision']==decision and event['expected_default']==expected,'Operation ID reused with changed intent.',root,'E_IDEMPOTENCY')
                return {**old,'replayed':True}
        fail(old['snapshot_digest']==expected,'Default changed; review again.',root,'E_INSTALL_STALE')
        if candidate is None:
            fail(not old['history'] or old['history'][-1]['action']!='rollback','The previous default is already restored; select an explicit recorded target. ',root,'E_INSTALL_ALREADY_ACTIVE')
            fail(bool(old['history']),'No previous selection is recorded.',root,'E_INSTALL_NO_PREVIOUS')
            candidate=old['history'][-1]['previous']
        candidate=pointer(candidate['runtime'],candidate['snapshot_digest'])
        before={'runtime':old['runtime'],'snapshot_digest':old['snapshot_digest']}
        fail(candidate!=before,'Selected runtime is already the default; use show.',root,'E_INSTALL_ALREADY_ACTIVE')
        manager=old['manager']
        # Updating adopts the candidate resolver. Default rollback retains the verified
        # manager: older protocol-capable readers may lack newer artifact envelopes.
        if action=='update' and (Path(candidate['runtime'])/'orchestrator/scripts/runtime_selection.py').is_file():manager=candidate
        fail((Path(manager['runtime'])/'orchestrator/scripts/runtime_selection.py').is_file()
             and (Path(manager['runtime'])/'orchestrator/scripts/runtime_management.py').is_file(),
             'A capable resolver must remain installed; select a managed runtime before rolling back to a legacy default.',
             root,'E_INSTALL_CONTRACT')
        new={'schema_version':'0.2',**candidate,'manager':manager,'history':old['history']+[{'id':operation,'action':action,'previous':before,'selected':candidate,'actor':actor,'decision':decision,'timestamp':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'expected_default':expected}]}
        folder=root/'sdlc';manifest=install.read_manifest(candidate['runtime'],candidate['snapshot_digest'])
        after={'SKILL.md':loader(Path(candidate['runtime']),manifest,manager).encode(),'installation.json':install.canonical(new)}
        prior={n:(folder/n).read_bytes() for n in after}
        journal={'schema_version':'0.1','before':{n:base64.b64encode(v).decode() for n,v in prior.items()},'after':{n:base64.b64encode(v).decode() for n,v in after.items()}}
        atomic(pending(root),install.canonical(journal))
        try:
            for name,raw in after.items():atomic(folder/name,raw)
            # Verify runtime/loader while the journal still blocks external readers.
            fail((folder/'SKILL.md').read_bytes()==after['SKILL.md'],'Loader switch failed.',folder)
            pointer(candidate['runtime'],candidate['snapshot_digest'])
            registration(root,allow_pending=True)
            pending(root).unlink();sync(root)
        except Exception:
            try:
                if not pending(root).exists():atomic(pending(root),install.canonical(journal))
                for name,raw in prior.items():atomic(folder/name,raw)
                if pending(root).exists():pending(root).unlink()
                sync(root)
            except Exception as exc:raise install.InstallError('E_INSTALL_RECOVERY','Switch outcome uncertain; inspect and recover.',pending(root)) from exc
            raise
        return {**registration(root),'replayed':False}


def recover(root):
    root=Path(root).absolute()
    with lock(root):
        path=pending(root);data=read_json(path)
        fail(set(data)=={'schema_version','before','after'} and data['schema_version']=='0.1','Invalid switch journal.',path,'E_INSTALL_RECOVERY')
        folder=root/'sdlc'
        for side in ('before','after'):fail(set(data[side])=={'SKILL.md','installation.json'},'Unsafe recovery targets.',path,'E_INSTALL_RECOVERY')
        original={n:base64.b64decode(v,validate=True) for n,v in data['before'].items()}
        for name,raw in original.items():
            current=(folder/name).read_bytes()
            fail(current in (raw,base64.b64decode(data['after'][name],validate=True)),'Unrelated edit blocks recovery.',folder/name,'E_INSTALL_RECOVERY')
        # Recovery explicitly restores the last valid registration, never invents activation.
        for name,raw in original.items():atomic(folder/name,raw)
        pending(root).unlink();sync(root)
        return registration(root)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='operation',required=True)
    for name in ('prepare','update','rollback','list','show','recover'):
        p=commands.add_parser(name);p.add_argument('--skill-root',type=Path,default=Path.home()/'.agents/skills')
        if name in ('prepare','update'):
            p.add_argument('--source',type=Path,required=True);p.add_argument('--revision',required=True);p.add_argument('--project',type=Path,required=True)
            p.add_argument('--runtime-root',type=Path);p.add_argument('--python');p.add_argument('--preview-working-tree',action='store_true')
        if name in ('update','rollback'):
            p.add_argument('--expected-default',required=True);p.add_argument('--operation-id',required=True);p.add_argument('--actor',required=True);p.add_argument('--decision',required=True)
        if name=='rollback':p.add_argument('--runtime',type=Path)
        if name=='list':p.add_argument('--runtime-root',type=Path,default=Path.home()/'.local/share/ai-sdlc/runtimes')
    args=parser.parse_args(argv)
    try:
        if args.operation in ('prepare','update'):
            fail(bool(re.fullmatch('[0-9a-f]{40,64}',args.revision)) or args.preview_working_tree,'Use an exact committed revision, or explicitly labelled HEAD preview.',args.source,'E_INSTALL_REVISION')
            old=registration(args.skill_root) if args.operation=='update' else None
            root=args.runtime_root or (Path(old['runtime']).parent if old else Path.home()/'.local/share/ai-sdlc/runtimes')
            replay=next((event for event in old['history'] if event['id']==args.operation_id),None) if old else None
            if replay:
                recorded=install.read_manifest(replay['selected']['runtime'],replay['selected']['snapshot_digest'])
                fail(recorded['source_revision']==args.revision and recorded['preview']==args.preview_working_tree
                     and (args.python is None or str(Path(args.python).absolute())==recorded['python'])
                     and (args.runtime_root is None or Path(replay['selected']['runtime']).parent==args.runtime_root.absolute()),
                     'Retry changed its installation intent.',args.skill_root,'E_IDEMPOTENCY')
                value=switch(args.skill_root,replay['selected'],args.expected_default,args.operation_id,args.actor,args.decision,'update')
                print(json.dumps({'ok':True,'operation':'update','diagnostics':[],**value}));return 0
            python=args.python or (install.read_manifest(old['runtime'])['python'] if old else sys.executable)
            value=install.prepare(args.source,args.revision,args.project,root,python,args.preview_working_tree)
            if old:value=switch(args.skill_root,{'runtime':value['runtime'],'snapshot_digest':value['snapshot_digest']},args.expected_default,args.operation_id,args.actor,args.decision,'update')
        elif args.operation=='rollback':
            candidate=pointer(args.runtime) if args.runtime else None
            if candidate is not None:
                old=registration(args.skill_root)
                fail(candidate in [e['previous'] for e in old['history']]+[e['selected'] for e in old['history']],'Rollback target has no recorded activation history.',args.runtime,'E_INSTALL_NO_PREVIOUS')
            value=switch(args.skill_root,candidate,args.expected_default,args.operation_id,args.actor,args.decision,'rollback')
        elif args.operation=='recover':value=recover(args.skill_root)
        elif args.operation=='show':value=registration(args.skill_root)
        else:
            value={'runtimes':[]}
            if args.runtime_root.is_dir():
                for path in sorted(args.runtime_root.iterdir()):
                    if path.is_dir() and not path.name.startswith('.'):
                        try:value['runtimes'].append({'ok':True,**install.verify(path)})
                        except install.InstallError as exc:value['runtimes'].append({'ok':False,'runtime':str(path),'code':exc.code,'message':str(exc)})
        output={'ok':True,'operation':args.operation,'diagnostics':[],**value}
    except (install.InstallError,OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
        output={'ok':False,'operation':args.operation,'diagnostics':[{'severity':'error','code':getattr(exc,'code','E_INSTALL_IO'),'file':getattr(exc,'path',str(args.skill_root)),'message':str(exc)}]}
    print(json.dumps(output,ensure_ascii=False));return 0 if output['ok'] else 1
