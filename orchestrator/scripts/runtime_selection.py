"""Request-scoped future runtime authority and source-bound execution provenance.

Local cooperating writers only. A context declaration cannot authenticate model context.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import install
import runtime_management as management

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL='sdlc-execution/1'
FILE='runtime-history.json'
CALL=ContextVar('runtime_call',default=None)
OWNED=ContextVar('runtime_owned',default=False)
ADMIN=ContextVar('runtime_admin',default=False)
READS={'open','validate','command-context','inbox','pending-assignments','identity-show','skills','templates','adoption-preflight','business-review','analysis-review','engineering-review','track-review','qa-review'}
SAFE={'discovery','ready_for_refinement','ready_for_analysis','ready_for_technical_design','ready_for_implementation_planning','ready_for_development'}


def require(condition,message,code='E_RUNTIME',file=FILE):
    if not condition:
        import business_refinement
        raise business_refinement.BusinessError(code,message,str(file))


def sha(value):return hashlib.sha256(value).hexdigest()
def canonical(value):return install.canonical(value)
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def pin(runtime):
    selected=management.pointer(runtime)
    return {**selected,'source_revision':install.read_manifest(selected['runtime'])['source_revision']}

def current_pin():return pin(ROOT) if (ROOT/'installation.json').is_file() else None

def validate_pin(value):
    require(isinstance(value,dict) and set(value)=={'runtime','snapshot_digest','source_revision'} and
            isinstance(value['runtime'],str) and Path(value['runtime']).is_absolute() and
            isinstance(value['snapshot_digest'],str) and re.fullmatch('[0-9a-f]{64}',value['snapshot_digest']) and
            isinstance(value['source_revision'],str) and re.fullmatch('[0-9a-f]{40,64}',value['source_revision']),
            'Invalid runtime provenance.','E_RUNTIME_HISTORY')


def read(directory):
    path=directory/FILE
    if not path.exists():return None
    try:value=management.read_json(path)
    except install.InstallError as exc:require(False,str(exc),'E_RUNTIME_HISTORY',path)
    require(isinstance(value,dict) and set(value)=={'schema_version','request_id','events'} and value['schema_version']=='0.1'
            and isinstance(value['request_id'],str) and re.fullmatch('REQ-[0-9]{4}',value['request_id']) and isinstance(value['events'],list),
            'Malformed runtime history.','E_RUNTIME_HISTORY',path)
    previous=None;seen=set();selections={}
    for wrapper in value['events']:
        require(isinstance(wrapper,dict) and set(wrapper)=={'previous','event','digest'} and wrapper['previous']==previous
                and wrapper['digest']==sha(canonical({'previous':previous,'event':wrapper['event']})),
                'Disconnected or modified runtime audit.','E_RUNTIME_HISTORY',path)
        event=wrapper['event'];require(isinstance(event,dict) and event.get('kind') in ('bind','promote','execution') and
            isinstance(event.get('operation_id'),str) and event['operation_id'] not in seen and isinstance(event.get('scope'),str)
            and isinstance(event.get('timestamp'),str),'Invalid runtime audit event.','E_RUNTIME_HISTORY',path)
        validate_pin(event.get('runtime'));seen.add(event['operation_id'])
        if event['kind'] in ('bind','promote'):
            require(all(isinstance(event.get(k),str) and event[k].strip() for k in ('actor','decision','reason','stage'))
                    and event.get('previous_runtime')==selections.get(event['scope'],selections.get('shared')) and isinstance(event.get('compatibility'),dict),
                    'Invalid runtime selection decision.','E_RUNTIME_HISTORY',path)
            if event['kind']=='bind':require(not selections and event['scope']=='shared','Initial binding must be explicit and request-wide.','E_RUNTIME_HISTORY',path)
            else:require(bool(selections),'Promotion cannot invent initial history.','E_RUNTIME_HISTORY',path)
            selections[event['scope']]=event['runtime']
        else:
            require(bool(selections) and isinstance(event.get('files'),dict) and isinstance(event.get('operation'),str),
                    'Execution receipt lacks selection or artifact bindings.','E_RUNTIME_HISTORY',path)
            require(event['runtime']==selections.get(event['scope'],selections.get('shared')),
                    'Execution differs from the effective historical selection.','E_RUNTIME_HISTORY',path)
        previous=wrapper['digest']
    require(bool(selections),'Runtime history has no initial binding.','E_RUNTIME_HISTORY',path)
    return value


def append(value,event):
    previous=value['events'][-1]['digest'] if value['events'] else None
    wrapper={'previous':previous,'event':event}
    return {**value,'events':value['events']+[{**wrapper,'digest':sha(canonical(wrapper))}]}


def find(project,epic_id):
    import sdlc
    epic=sdlc.selected_epic(project,epic_id)
    return epic


def scope_for(epic,track=None):
    if track:
        import work_tracks
        require(track in work_tracks.NAMES and epic.metadata.get('work_tracks') and epic.metadata['status'] in __import__('engineering_contract').DOWNSTREAM,
                'Select an active Engineering or QA track.','E_TRACK_REQUIRED')
        return track+':'+work_tracks.active(epic)['id']
    return 'shared'


def selected(value,scope):
    if value is None:return None,None
    records=[v['event'] for v in value['events'] if v['event']['kind'] in ('bind','promote') and v['event']['scope'] in ('shared',scope)]
    # A track-specific selection overrides inherited shared authority for that cycle.
    specific=[v for v in records if v['scope']==scope]
    event=(specific or records)[-1]
    return event['runtime'],event['operation_id']


def snapshots(directory):
    result={}
    if not directory.exists():return result
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(),'Symlink in governed request.','E_RUNTIME_HISTORY',path)
        if path.is_file() and path!=directory/FILE:result[path.relative_to(directory).as_posix()]=sha(path.read_bytes())
    return result


def revision(project,epic,value):
    import engineering
    return sha(canonical({'files':snapshots(epic.directory),'runtime_history':value,'application':engineering.fingerprint(engineering.tree(project))}))


def capabilities(project,epic_id=None):
    import sdlc,domain_skills,artifact_templates,engineering,engineering_contract,qa_track
    skills=domain_skills.catalog(sdlc.StrictLoader);templates=artifact_templates.catalog()
    result={'protocol':PROTOCOL,'metadata':['0.1','0.2','0.3','0.4','0.5','0.6'],
        'storage':['business/0.1','analysis/0.1','engineering/0.1','engineering/0.2','discovery/0.2','business-history/0.3','analysis-history/0.3'],
        'governance':['legacy','governance/0.1'],'work_track_schemas':['0.1','0.2'],
        'approval_contracts':['business/1','analysis/1','engineering/1','qa/1'],
        'evidence_contract':'source-bound-checks/1','recovery_contract':'journal-and-atomic-metadata/1',
        'engineering_transitions':engineering_contract.TRANSITIONS,'qa_states':qa_track.STATUSES,
        'source_fingerprint':engineering.fingerprint(engineering.tree(project)),
        'domain_contracts':{k:v.get('validation_contract','legacy/'+v.get('orchestrator','')) for k,v in skills.items()},
        'template_contracts':{k:v['pin']['validation_contract'] for k,v in templates.items()},
        'domain_pins':{k:{'version':v['version'],'digest':v['digest']} for k,v in skills.items()},
        'template_pins':{k:v['pin'] for k,v in templates.items()},'request_readable':True}
    if epic_id:
        epic=find(project,epic_id)
        # These readers verify retained baselines, audit prefixes and current join inputs.
        if epic.metadata['status'] in engineering_contract.DOWNSTREAM:
            engineering.review(epic,project)
            if epic.metadata.get('work_tracks'):qa_track.review(epic,project)
        result['state']=epic.metadata['status']
    return result


def probe(runtime,project,epic_id=None):
    chosen=pin(runtime)
    require((Path(chosen['runtime'])/'orchestrator/scripts/runtime_selection.py').is_file(),
            'This legacy runtime has no managed execution protocol; read-only historical inspection only.','E_RUNTIME_CONTRACT')
    manifest=install.read_manifest(chosen['runtime'])
    argv=[manifest['python'],'-B',str(Path(chosen['runtime'])/'orchestrator/scripts/sdlc.py'),'--project',str(project),'runtime-probe']
    if epic_id:argv.append(epic_id)
    try:
        run=subprocess.run(argv,capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        data=json.loads(run.stdout)
        require(isinstance(data,dict),'Candidate must return a JSON object.','E_RUNTIME_CONTRACT')
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        require(False,'Candidate inspection failed: '+str(exc),'E_RUNTIME_CONTRACT')
    require(run.returncode==0 and data.get('ok') and isinstance(data.get('capabilities'),dict),
            'Candidate cannot read current inputs: '+str(data.get('diagnostics',run.stderr)),'E_RUNTIME_INCOMPATIBLE')
    return chosen,data['capabilities']


def boundary(epic,track):
    if track=='qa':
        import work_tracks
        qa=work_tracks.active(epic)['qa'];stage=qa['status']
        ready=stage=='ready_for_test_design' or (stage=='test_automation' and not any(e['kind']=='automation' and e['action']=='write' for e in qa['history']))
        return ready,stage
    status=epic.metadata['status']
    if status=='discovery':return epic.discovery is None,'discovery'
    return status in SAFE,status


# Additive reader/package support is compatible; changes to an existing contract are
# not. Actual candidate readers still validate the entire current request and inputs.
CONTRACTS=('protocol','metadata','storage','governance','work_track_schemas','approval_contracts','evidence_contract','recovery_contract','engineering_transitions','qa_states','source_fingerprint','domain_contracts','template_contracts')


def compatible_contracts(previous, candidate):
    for key in CONTRACTS:
        old,new=previous.get(key),candidate.get(key)
        if key in ('metadata','storage','governance','work_track_schemas'):
            if not isinstance(old,list) or not isinstance(new,list) or not set(old)<=set(new):return False
        elif key in ('domain_contracts','template_contracts'):
            if not isinstance(old,dict) or not isinstance(new,dict) or any(new.get(k)!=v for k,v in old.items()):return False
        elif json.loads(json.dumps(old))!=json.loads(json.dumps(new)):return False
    return True


def assessment(project,epic_id,candidate,track=None):
    epic=find(project,epic_id);value=read(epic.directory);scope=scope_for(epic,track);old,_=selected(value,scope)
    token=revision(project,epic,value);safe,stage=boundary(epic,track)
    try:
        new,new_contract=probe(candidate,project,epic_id)
        old_contract=probe(old['runtime'],project,epic_id)[1] if old else capabilities(project,epic_id)
        stable=CONTRACTS
        same=compatible_contracts(old_contract,new_contract)
        classification='compatible' if same else 'incompatible'
        reasons=[] if same else ['Validation, transitions, storage or actual source interpretation differs.']
        pins_changed=any(old_contract[k]!=new_contract[k] for k in ('domain_pins','template_pins'))
        if same and (not safe or pins_changed):
            classification='requires_reconciliation';reasons=['Defer until a safe work boundary.' if not safe else 'Changed instruction/template content needs explicit future-scope impact assessment.']
        return {'classification':classification,'reasons':reasons,'safe_boundary':safe,'stage':stage,'scope':scope,
            'previous_runtime':old,'runtime':new,'revision':token,'contracts':{k:new_contract[k] for k in stable if k!='source_fingerprint'},
            'requires_reconciliation':classification=='requires_reconciliation'}
    except (install.InstallError,__import__('business_refinement').BusinessError) as exc:
        return {'classification':'incompatible','reasons':[str(exc)],'safe_boundary':safe,'stage':stage,'scope':scope,
                'previous_runtime':old,'runtime':None,'revision':token,'contracts':{},'requires_reconciliation':False}


def select_runtime(project,epic_id,candidate,track,expected,operation,actor,decision,reason,reconciliation=None,initial=False):
    import sdlc
    require(all(isinstance(v,str) and v.strip() for v in (actor,decision,reason)) and __import__('discovery_history').valid_operation_id(operation),
            'Supply actual human attribution, decision, reason and operation ID.','E_UPDATE_INPUT')
    context=ADMIN.set(True)
    try:
        with sdlc.project_lock(project):
            require(not transaction(project).exists(),'Finish interrupted provenance before selecting another runtime.','E_RUNTIME_RECOVERY')
            epic=find(project,epic_id);value=read(epic.directory);scope=scope_for(epic,track)
            if value:
                for wrapper in value['events']:
                    event=wrapper['event']
                    if event['operation_id']==operation:
                        require(event.get('kind')==('bind' if initial else 'promote') and event.get('requested')==str(Path(candidate).absolute()) and
                                all(event.get(k)==v for k,v in {'actor':actor,'decision':decision,'reason':reason,'expected':expected,'reconciliation':reconciliation,'scope':scope}.items()),
                                'Promotion operation ID reused with different intent.','E_IDEMPOTENCY')
                        return {'replayed':True,'runtime_history':value}
            require(initial or not epic.metadata.get('work_tracks') or epic.metadata['status'] not in __import__('engineering_contract').DOWNSTREAM or track is not None,
                    'Promote Engineering and QA separately.','E_TRACK_AMBIGUOUS')
            require((value is None)==initial and (not initial or track is None),'Legacy requests need initial request-wide binding; existing bindings use promotion.','E_RUNTIME_BIND_REQUIRED')
            report=assessment(project,epic_id,candidate,track)
            require(report['revision']==expected,'Runtime/source context changed; inspect again.','E_REVISION_CONFLICT')
            require(report['classification']!='incompatible','Candidate is incompatible: '+'; '.join(report['reasons']),'E_RUNTIME_INCOMPATIBLE')
            require(report['safe_boundary'] or initial and isinstance(reconciliation,str) and reconciliation.strip(),
                    'Work has begun; defer promotion or explicitly reconcile an initial legacy binding.','E_RUNTIME_BOUNDARY')
            require(not report['requires_reconciliation'] or isinstance(reconciliation,str) and reconciliation.strip(),
                    'Supply explicit future-scope impact reconciliation before promotion.','E_RUNTIME_RECONCILIATION')
            # Recheck after the subprocess probe; hostile edits are not coordinated by the lock.
            require(revision(project,epic,read(epic.directory))==expected,'Inputs changed during compatibility inspection.','E_REVISION_CONFLICT')
            previous,_=selected(value,scope)
            require(initial or report['runtime']!=previous,'This exact runtime is already selected.','E_RUNTIME_ALREADY_SELECTED')
            event={'kind':'bind' if initial else 'promote','operation_id':operation,'scope':scope,'stage':report['stage'],
                'previous_runtime':previous,'runtime':report['runtime'],'compatibility':{k:report[k] for k in ('classification','reasons','contracts','safe_boundary')},
                'actor':actor,'decision':decision,'reason':reason,'timestamp':now(),'future_scope':scope+' from '+report['stage'],
                'requested':str(Path(candidate).absolute()),'expected':expected,'reconciliation':reconciliation}
            value=value or {'schema_version':'0.1','request_id':epic_id,'events':[]}
            candidate_history=append(value,event)
            raw=canonical(candidate_history)
            try:management.atomic(epic.directory/FILE,raw)
            except OSError:
                require(not (epic.directory/FILE).exists() or (epic.directory/FILE).read_bytes()!=raw,
                        'Runtime selection may have committed; retry the exact operation.','E_RUNTIME_WRITE_UNCERTAIN')
                raise
            return {'replayed':False,'runtime_history':read(epic.directory),'assessment':report}
    finally:ADMIN.reset(context)


def instructions(chosen):
    root=Path(chosen['runtime'])/'orchestrator/skill'
    return sha(canonical({'runtime':chosen,'files':{n:sha((root/n).read_bytes()) for n in ('SKILL.md','commands.md','conversation.md')}}))


def status(project,epic_id=None,track=None,skill_root=None,artifact=None):
    default=management.registration(skill_root or Path.home()/'.agents/skills')
    default_pin=pin(default['runtime'])
    value=None;scope='new';effective=default_pin;selection='default:'+default_pin['snapshot_digest'];token=None
    if epic_id:
        epic=find(project,epic_id);value=read(epic.directory);scope=scope_for(epic,track)
        effective,selection=selected(value,scope);token=revision(project,epic,value)
    if effective:
        require(pin(effective['runtime'])==effective,'Selected runtime changed.','E_RUNTIME_INTEGRITY')
        digest=instructions(effective) if (Path(effective['runtime'])/'orchestrator/scripts/runtime_selection.py').is_file() else None
    else:digest=None
    tracks={}
    if epic_id and epic.metadata.get('work_tracks') and epic.metadata['status'] in __import__('engineering_contract').DOWNSTREAM and track is None:
        tracks={name:selected(value,scope_for(epic,name))[0] for name in ('engineering','qa')}
    provenance=[]
    if artifact and value:
        for wrapper in value['events']:
            event=wrapper['event']
            if event['kind']=='execution':
                matches={n:d for n,d in event['files'].items() if artifact==Path(n).name or artifact in Path(n).parts or artifact==n}
                if matches:provenance.append({'operation_id':event['operation_id'],'runtime':event['runtime'],'files':matches})
    return {'effective_tracks':tracks,'artifact_provenance':provenance,'default_runtime':default_pin,'effective_runtime':effective,'scope':scope,'selection':selection,'revision':token,
            'binding_required':effective is None,'instructions_digest':digest,'runtime_history':value,
            'fresh_context_required_for_new_runtime':True}


def sessions_root():
    path=Path(os.environ.get('SDLC_RUNTIME_SESSION_ROOT',str(Path.home()/'.local/share/ai-sdlc/sessions'))).expanduser().absolute()
    require(path.resolve()==path,'Session storage must use a canonical absolute path.','E_RUNTIME_CONTEXT',path)
    require(not any(p.is_symlink() for p in (path,*path.parents)) and not any((p/'.git').exists() for p in (path,*path.parents)),
            'Session receipts must be outside Git repositories and nonsymlink.','E_RUNTIME_CONTEXT',path)
    require(not path.exists() or path.stat().st_uid==os.getuid(),'Session storage must belong to the current operator.','E_RUNTIME_CONTEXT',path)
    return path


def session(project,epic_id,track,context_id,digest,skill_root):
    view=status(project,epic_id,track,skill_root);chosen=view['effective_runtime']
    require(not view['effective_tracks'],'Select Engineering or QA for a fresh execution context.','E_TRACK_AMBIGUOUS')
    require(chosen is not None,'Explicitly bind the legacy request first.','E_RUNTIME_BIND_REQUIRED')
    probe(chosen['runtime'],project,epic_id)
    require(isinstance(context_id,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',context_id) and digest==view['instructions_digest'],
            'Declare a fresh context after reading the resolved runtime instructions.','E_RUNTIME_CONTEXT')
    root=sessions_root();require(not root.is_relative_to(project.resolve()),'Session receipts must be outside the application.','E_RUNTIME_CONTEXT');root.mkdir(parents=True,exist_ok=True)
    data={'schema_version':'0.1','project':str(project.resolve()),'request_id':epic_id,'scope':view['scope'],
          'runtime':chosen,'selection':view['selection'],'instructions_digest':digest,'skill_root':str(Path(skill_root).absolute()),'context_id':context_id}
    # One host context may address multiple scopes under the same exact runtime.
    marker=root/('context-'+sha(context_id.encode())+'.json')
    claim={'context_id':context_id,'runtime':chosen}
    try:
        with marker.open('x',encoding='utf-8') as stream:
            os.chmod(marker,0o600);stream.write(canonical(claim).decode());stream.flush();os.fsync(stream.fileno())
    except FileExistsError:
        require(management.read_json(marker)==claim,'This host context already loaded another runtime; start a fresh conversation.','E_RUNTIME_CONTEXT_RELOAD')
    key=sha(canonical(data));path=root/(key+'.json')
    # Receipts bind scope and selection independently without reassigning host context.
    try:
        with path.open('x',encoding='utf-8') as stream:
            os.chmod(path,0o600);stream.write(canonical(data).decode());stream.flush();os.fsync(stream.fileno())
        management.sync(root)
    except FileExistsError:
        require(management.read_json(path)==data,'This host context already carries another selection; start a fresh conversation.','E_RUNTIME_CONTEXT_RELOAD')
    return {'runtime_session':key,**view,'declaration':'Procedural caller declaration, not authenticated host-context inspection.'}


def transaction(project):return project/'requirements/.sdlc-runtime-transaction.json'


def check_pending(project):
    require(OWNED.get() or ADMIN.get() or not transaction(project).exists(),
            'Interrupted provenance publication; inspect/retry the original operation or runtime-recover.','E_RUNTIME_RECOVERY',transaction(project))


def context_track(call):
    op=call['operation']
    if op.startswith('qa-'):return 'qa'
    if op.startswith('engineering-') or op in ('development-start','check-run','security-remediate','verification-remediate'):return 'engineering'
    return call.get('track')


def validate_session(project,call,chosen,scope,selection):
    key=call.get('runtime_session')
    require(isinstance(key,str) and re.fullmatch('[0-9a-f]{64}',key),'Read selected instructions in a fresh context and open runtime-session.','E_RUNTIME_CONTEXT')
    record=management.read_json(sessions_root()/(key+'.json'))
    require(isinstance(record,dict) and set(record)=={'schema_version','project','request_id','scope','runtime','selection','instructions_digest','skill_root','context_id'}
            and record['schema_version']=='0.1','Malformed execution context receipt.','E_RUNTIME_CONTEXT')
    require(record['runtime']==chosen and record['selection']==selection and record['scope']==scope and record['request_id']==call.get('id')
            and record['project']==str(project.resolve()) and record['instructions_digest']==instructions(chosen),
            'Session differs from effective runtime or scope; start a fresh context.','E_RUNTIME_CONTEXT_RELOAD')
    require(current_pin()==chosen,'Wrong runtime executable; load instructions and CLI from the effective pin.','E_RUNTIME_MISMATCH')
    if call['operation']=='new':
        default=management.registration(record['skill_root'])
        require(default['snapshot_digest']==chosen['snapshot_digest'],'New-work default changed; obtain a fresh context.','E_RUNTIME_DEFAULT_CHANGED')


def validate_intent(project,intent):
    require(isinstance(intent,dict) and set(intent)=={'schema_version','operation_id','operation','scope','runtime','directory','before','after','creation','selection'}
            and intent['schema_version']=='0.1' and all(isinstance(intent[k],str) and intent[k] for k in ('operation_id','operation','scope')),
            'Malformed provenance transaction.','E_RUNTIME_RECOVERY',transaction(project))
    validate_pin(intent['runtime'])
    if intent['directory'] is not None:
        directory=Path(intent['directory'])
        require(directory.parent==project/'requirements' and directory.resolve()==directory and not any(p.is_symlink() for p in (directory,*directory.parents)),
                'Unsafe provenance transaction directory.','E_RUNTIME_RECOVERY',transaction(project))
    for side in ('before','after'):
        values=intent[side]
        require(side=='after' and values is None or isinstance(values,dict) and all(install.safe_name(n) and isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for n,v in values.items()),
                'Invalid transaction file bindings.','E_RUNTIME_RECOVERY',transaction(project))


def verify_join(project,epic,value):
    if not value:return
    scopes={'shared',scope_for(epic,'engineering'),scope_for(epic,'qa')}
    pins={}
    # Historical shared-stage writers need not understand new downstream envelopes.
    # Current readers verify their frozen inputs; current-cycle track evidence keeps
    # its own recorded execution runtime and is still checked at the join.
    for scope in scopes:
        chosen,_=selected(value,scope)
        if chosen:pins[chosen['snapshot_digest']]=chosen
    for wrapper in value['events']:
        event=wrapper['event']
        if event['scope'] in scopes-{'shared'}:pins[event['runtime']['snapshot_digest']]=event['runtime']
    contracts=[]
    for chosen in pins.values():
        _,contract=probe(chosen['runtime'],project,epic.metadata['id']);contracts.append(contract)
    stable=CONTRACTS
    require(all(compatible_contracts(a,b) or compatible_contracts(b,a) for i,a in enumerate(contracts) for b in contracts[i+1:]),
            'Mixed-runtime verification inputs are incompatible.','E_RUNTIME_INCOMPATIBLE')


def note_directory(directory):
    call=CALL.get()
    if call is None or '_intent' not in call:return
    intent=call['_intent'];intent['directory']=str(directory);intent['before']=snapshots(directory)
    management.atomic(transaction(directory.parent.parent),canonical(intent))
    call['created_directory']=str(directory)


def note_creation(metadata,content):
    call=CALL.get()
    if call is None or '_intent' not in call:return
    import yaml
    intent=call['_intent']
    intent['creation']={'metadata.yaml':sha(yaml.safe_dump(metadata,sort_keys=False,allow_unicode=True).encode('utf-8')),'idea.md':sha(content.encode('utf-8'))}
    management.atomic(transaction(Path(intent['directory']).parent.parent),canonical(intent))


def finish(project,intent):
    path=Path(intent['directory']);value=read(path)
    if value is None:
        require(intent['operation']=='new','Missing runtime binding.','E_RUNTIME_BIND_REQUIRED')
        metadata=__import__('yaml').load((path/'metadata.yaml').read_text(),Loader=__import__('sdlc').StrictLoader)
        value={'schema_version':'0.1','request_id':metadata['id'],'events':[]}
        value=append(value,{'kind':'bind','operation_id':intent['operation_id']+':binding','scope':'shared','stage':'discovery',
            'previous_runtime':None,'runtime':intent['runtime'],'compatibility':{'classification':'compatible','new_request':True},
            'actor':metadata['ownership']['owner'],'decision':'Create this request using the selected default runtime.',
            'reason':'Initial future execution selection; no historical runtime inferred.','timestamp':now()})
    if intent['operation']!='new':
        require(selected(value,intent['scope'])==(intent['runtime'],intent['selection']),
                'Runtime authority changed during the operation; inspect original intent.','E_RUNTIME_RECOVERY',transaction(project))
    existing=[w['event'] for w in value['events'] if w['event']['operation_id']==intent['operation_id']]
    if existing:
        require(existing[0]['kind']=='execution' and existing[0]['runtime']==intent['runtime'] and existing[0]['operation']==intent['operation'],
                'Operation provenance conflicts with a previous event.','E_IDEMPOTENCY')
    elif intent['after']==intent['before'] and intent['operation']!='new':
        # A legacy replay performed no new write; never retroactively attribute its artifact.
        transaction(project).unlink();management.sync(transaction(project).parent);return
    else:
        changed={name:d for name,d in intent['after'].items() if intent['before'].get(name)!=d}
        removed=[name for name in intent['before'] if name not in intent['after']]
        event={'kind':'execution','operation_id':intent['operation_id'],'operation':intent['operation'],
            'scope':intent['scope'],'runtime':intent['runtime'],'timestamp':now(),'files':changed,'removed':removed}
        value=append(value,event)
        management.atomic(path/FILE,canonical(value))
    transaction(project).unlink();management.sync(transaction(project).parent)


@contextmanager
def managed_write(project):
    if ADMIN.get():yield;return
    call=CALL.get();current=current_pin()
    if call is None:
        check_pending(project)
        bound=any((p/FILE).exists() for p in (project/'requirements').iterdir() if p.is_dir()) if (project/'requirements').is_dir() else False
        require(current is None and not bound,'Managed writes require the runtime-aware CLI context.','E_RUNTIME_CONTEXT')
        yield;return
    if current is None:
        bound=any((p/FILE).exists() for p in (project/'requirements').iterdir() if p.is_dir()) if (project/'requirements').is_dir() else False
        if not bound:
            # Preserve legacy recovery's own narrow reader: an ordinary full Epic
            # read rejects the partial publication that recovery must finish.
            check_pending(project)
            yield;return
    op=call['operation'];epic=None;value=None;scope='new';selection=None;chosen=current
    if op!='new':
        # Journal inspection must precede normal readers, which reject pending publication.
        admin=ADMIN.set(True)
        try:epic=find(project,call['id'])
        finally:ADMIN.reset(admin)
        value=read(epic.directory);scope=scope_for(epic,context_track(call) if epic.metadata.get('work_tracks') and epic.metadata['status'] in __import__('engineering_contract').DOWNSTREAM else None)
        chosen,selection=selected(value,scope)
        if chosen is None:
            check_pending(project)
            require(current is None,'Legacy request needs explicit future-work binding.','E_RUNTIME_BIND_REQUIRED')
            yield;return
    else:
        if current is None:yield;return
        selection='default:'+current['snapshot_digest']
    validate_session(project,call,chosen,scope,selection)
    joining=op in ('qa-check-run','engineering-finalize') or (op in ('qa-advance','engineering-advance') and call.get('kind') in ('verification','security')) or (op=='engineering-write' and call.get('kind')=='security')
    if joining and epic and epic.metadata.get('work_tracks'):verify_join(project,epic,value)
    opid=call.get('operation_id') or 'local-'+__import__('uuid').uuid4().hex
    path=transaction(project)
    if path.exists():
        intent=management.read_json(path)
        require(intent.get('directory')==(str(epic.directory) if epic else intent.get('directory')),'Recovery targets another request.','E_RUNTIME_RECOVERY',path)
        require(intent['operation_id']==opid and intent['operation']==op and intent['runtime']==chosen,
                'Retry the exact interrupted operation before further writes.','E_RUNTIME_RECOVERY',path)
    else:
        directory=epic.directory if epic else None
        intent={'schema_version':'0.1','operation_id':opid,'operation':op,'scope':scope,'runtime':chosen,
            'directory':str(directory) if directory else None,'before':snapshots(directory) if directory else {},'after':None,'creation':None,'selection':selection}
        path.parent.mkdir(exist_ok=True);management.atomic(path,canonical(intent))
    validate_intent(project,intent)
    call['_intent']=intent
    own=OWNED.set(True)
    try:
        yield
        if intent['directory'] is None:
            require(call.get('created_directory') is not None,'Creation did not identify its request.','E_RUNTIME_RECOVERY')
            intent['directory']=call['created_directory']
        intent['after']=snapshots(Path(intent['directory']))
        management.atomic(path,canonical(intent))
        finish(project,intent)
    except Exception:
        # Before a state mutation there is nothing to recover. After one, fail closed.
        directory=Path(intent['directory']) if intent['directory'] else None
        if directory and snapshots(directory)==intent['before']:
            if path.exists():path.unlink();management.sync(path.parent)
            raise
        require(False,'Governed result may have committed; inspect/retry exact operation and recover provenance.','E_RUNTIME_RECOVERY',path)
    finally:OWNED.reset(own)


def recover(project):
    import sdlc
    token=ADMIN.set(True)
    try:
        with sdlc.project_lock(project):
            path=transaction(project);intent=management.read_json(path)
            validate_intent(project,intent)
            require(isinstance(intent.get('directory'),str),'Creation has not selected a directory; inspect the abandoned intent.','E_RUNTIME_RECOVERY',path)
            directory=Path(intent['directory'])
            if intent['after'] is None:
                call=CALL.get()
                require(call is not None and call.get('runtime_session'),'Recovery of unfinished work requires the original runtime context.','E_RUNTIME_CONTEXT')
                ledger=read(directory)
                _,selection_id=selected(ledger,intent['scope']) if ledger else (intent['runtime'],'default:'+intent['runtime']['snapshot_digest'])
                metadata_path=directory/'metadata.yaml'
                require(not metadata_path.is_symlink(),'Unsafe recovery metadata.','E_RUNTIME_RECOVERY',metadata_path)
                try:metadata=__import__('yaml').load(metadata_path.read_text(),Loader=sdlc.StrictLoader) if metadata_path.exists() else {}
                except (OSError,UnicodeError,__import__('yaml').YAMLError,RecursionError) as exc:require(False,str(exc),'E_RUNTIME_RECOVERY',metadata_path)
                require(isinstance(metadata,dict),'Malformed recovery metadata.','E_RUNTIME_RECOVERY',metadata_path)
                validate_session(project,{'operation':'runtime-recover','id':None if intent['operation']=='new' else metadata.get('id'),
                                         'runtime_session':call['runtime_session']},intent['runtime'],intent['scope'],selection_id)
                if intent['operation']=='new':
                    expected=intent.get('creation');actual=snapshots(directory)
                    require(isinstance(expected,dict) and set(expected)=={'metadata.yaml','idea.md'} and all(actual.get(n)==v for n,v in expected.items()),
                            'Incomplete creation cannot be published as a complete request; inspect original intent without inventing content.','E_RUNTIME_RECOVERY',path)
                else:
                    original=intent['operation']
                    analysis=original.startswith('analysis-')
                    journal=directory/('.analysis-transaction.json' if analysis else '.business-transaction.json')
                    require(original in ('business-generate','business-revise','analysis-generate','analysis-revise') and journal.is_file(),
                            'Retry the original idempotent operation; no known multi-file transaction can be rolled forward.','E_RUNTIME_RECOVERY',path)
                    __import__('business_refinement').recover(directory,analysis=analysis)
                intent['after']=snapshots(directory);management.atomic(path,canonical(intent))
            require(snapshots(directory)==intent['after'],
                    'Unrelated edits block provenance recovery.','E_RUNTIME_RECOVERY',path)
            require(pin(intent['runtime']['runtime'])==intent['runtime'],'Original runtime is unavailable or changed.','E_RUNTIME_INTEGRITY')
            finish(project,intent)
            return {'recovered':True,'runtime_history':read(directory)}
    finally:ADMIN.reset(token)
