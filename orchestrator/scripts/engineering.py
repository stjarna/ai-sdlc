"""A fixed sequential engineering slice using existing approval/storage primitives.

The agent writes application code; this module records reviewed artifacts, runs named
approved checks and enforces source-bound gates. It is not a shell sandbox or AI runtime.
"""
from __future__ import annotations
import json
import hashlib
from copy import deepcopy
from functools import lru_cache
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile

import yaml
import approval_common as common
import analysis_approval as analysis_gate
import business_refinement as business
import discovery_history as discovery
import domain_skills
import artifact_names
from engineering_contract import STAGES, DOWNSTREAM

FILES = ('metadata.yaml', 'artifact.json', 'content.md')
KINDS = ('design', 'plan', 'implementation', 'security')
WRITE_STAGE = {'design':'technical_design','plan':'implementation_planning','implementation':'development','security':'security_review'}
SKILLS = {'design':['architecture'], 'plan':['development','testing'], 'implementation':['development','testing'], 'security':['security']}
IGNORED = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.DS_Store'}
EVENT_FIELDS = {'operation_id','action','kind','actor','identity_source','decision','expected_revision','timestamp','baseline_id','cycle'}


def require(value, message, code='E_ENGINEERING', file='metadata.yaml'):
    business.require(value, code, message, file)


def canonical(data):
    return common.canonical_manifest(data)


def path_valid(value, directory=False):
    if not isinstance(value,str) or not value or '\\' in value:
        return False
    p=Path(value)
    return not p.is_absolute() and not any(v in ('..','.') for v in value.split('/')) and not any(v in IGNORED or v=='requirements' for v in p.parts) and (directory or not value.endswith('/'))


def tree(project):
    result={}
    def walk(folder):
        for p in sorted(folder.iterdir()):
            if p.name in IGNORED or (folder==project and p.name=='requirements'):
                continue
            require(not p.is_symlink(), 'Application snapshots do not follow symlinks.', 'E_IMPLEMENTATION_BOUNDARY', str(p))
            if p.is_dir(): walk(p)
            else:
                require(p.is_file(), 'Expected regular application files.', 'E_IMPLEMENTATION_BOUNDARY', str(p))
                result[p.relative_to(project).as_posix()]=business.digest(p.read_bytes())
    walk(project)
    return result


def source_tree(epic,project):
    if epic.metadata.get('work_tracks'):
        import work_tracks
        return work_tracks.engineering_tree(epic,project)
    return tree(project)


def fingerprint(files):
    return business.digest(canonical(files))


def cycle(epic):
    event=next((e for e in reversed(epic.metadata.get('lifecycle',[])) if e['action']=='analysis_advance'),None)
    require(event is not None and epic.analysis_approval and epic.analysis_approval['valid'] and epic.metadata['status'] in DOWNSTREAM,
            'An active approved and explicitly advanced Analysis baseline is required.', 'E_ENGINEERING_INPUT')
    # selected_epic/read_epic already verified every retained Analysis baseline.
    return event


def _loader():
    # Imported only at call time; the CLI owns the strict YAML dialect.
    import sdlc
    return sdlc.StrictLoader


@lru_cache(maxsize=128)
def decode_metadata(raw):
    # Exact bytes key, never an mtime or trusted-path cache. Hashes are still checked
    # on every read, including corrupted historical bundles.
    return yaml.load(raw.decode('utf-8'),Loader=_loader())


@lru_cache(maxsize=128)
def decode_artifact(raw):
    return json.loads(raw.decode('utf-8'))


def artifact_files(manifest, root_name):
    require(isinstance(manifest, dict), 'Invalid engineering manifest.', 'E_BASELINE_INTEGRITY')
    version = manifest.get('schema_version')
    if version == '0.1':
        require(set(manifest) == {'schema_version', 'request_id', 'files'}, 'Invalid legacy manifest.', 'E_BASELINE_INTEGRITY')
        return FILES
    require(version == '0.2' and set(manifest) == {'schema_version', 'request_id', 'files', 'document'},
            'Unsupported artifact manifest format.', 'E_BASELINE_INTEGRITY')
    stage = 'qa' if root_name == 'qa-baselines' else 'engineering'
    name = manifest['document']
    require(isinstance(name, str) and name in artifact_names.storage_names(stage),
            'Invalid canonical document filename.', 'E_BASELINE_INTEGRITY')
    return ('metadata.yaml', 'artifact.json', name)


def baseline_snapshot(stage, kind, action, request_id, metadata, stored, content):
    name = artifact_names.filename(stage, kind, action)
    files = {'metadata.yaml': metadata, 'artifact.json': canonical(stored), name: content}
    manifest = {'schema_version': '0.2', 'request_id': request_id, 'document': name,
                'files': {n: business.digest(v) for n, v in files.items()}}
    return manifest, files


def _read_artifact(directory, baseline_id, root_name='engineering-baselines'):
    def validate(manifest, files):
        names = artifact_files(manifest, root_name)
        common.validate_files(manifest, files, names)
        obj = decode_artifact(files['artifact.json'])
        require(isinstance(obj, dict) and set(obj) == {'action','kind','payload','skills','analysis_baseline','analysis_handoff','source_revision'}, 'Malformed engineering artifact.', 'E_BASELINE_CONTEXT')
        require(isinstance(obj['payload'], dict) and isinstance(obj['skills'], dict), 'Invalid engineering payload.', 'E_BASELINE_CONTEXT')
        require('content' not in obj['payload'], 'Prose belongs only in the document file.', 'E_BASELINE_CONTEXT')
        if manifest['schema_version'] == '0.2':
            stage = 'qa' if root_name == 'qa-baselines' else 'engineering'
            try:
                expected = artifact_names.filename(stage, obj['kind'], obj['action'])
            except (KeyError, TypeError):
                require(False, 'Unsupported artifact kind/action.', 'E_BASELINE_CONTEXT')
            require(manifest['document'] == expected, 'Document filename differs from artifact type.', 'E_BASELINE_CONTEXT')
        files[names[-1]].decode('utf-8')
        frozen = decode_metadata(files['metadata.yaml'])
        require(isinstance(frozen, dict) and frozen.get('id') == manifest['request_id'], 'Frozen request mismatch.', 'E_BASELINE_CONTEXT')
    try:
        manifest, files = common.read_baseline(directory, baseline_id, root_name,
            lambda m: artifact_files(m, root_name), validate)
    except (yaml.YAMLError, KeyError, RecursionError) as exc:
        raise business.BusinessError('E_BASELINE_CONTEXT', str(exc), root_name+'/'+str(baseline_id)) from exc
    obj = deepcopy(decode_artifact(files['artifact.json']))
    obj['payload']['content'] = files[artifact_files(manifest, root_name)[-1]].decode('utf-8')
    return obj, deepcopy(decode_metadata(files['metadata.yaml'])), artifact_files(manifest, root_name)[-1]


def load_artifact(directory, baseline_id, root_name='engineering-baselines'):
    obj, metadata, _ = _read_artifact(directory, baseline_id, root_name)
    return obj, metadata


def artifact_document(directory, baseline_id, kind, root_name='engineering-baselines'):
    # Validate before selecting a path, including hashes, exact set and kind/name binding.
    _, _, name = _read_artifact(directory, baseline_id, root_name)
    return artifact_names.document('qa' if root_name == 'qa-baselines' else 'engineering',
                                   kind, directory/root_name/baseline_id/name)


def validate_history(epic):
    entries=epic.metadata.get('engineering_history',[])
    require(isinstance(entries,list),'Engineering history must be a list.')
    operations=set()
    for index,e in enumerate(entries):
        require(isinstance(e,dict) and set(e)==EVENT_FIELDS,'Invalid engineering audit entry.')
        require(discovery.valid_operation_id(e['operation_id']) and e['operation_id'] not in operations and discovery.valid_revision(e['expected_revision']) and discovery.valid_revision(e['baseline_id']), 'Invalid engineering operation/revision.')
        require(business.valid_person(e['actor']) and analysis_gate.valid_decision_text(e['decision']) and analysis_gate.business_gate.valid_timestamp(e['timestamp']) and e['identity_source'] in ('declared','local_profile'), 'Invalid engineering attribution.')
        require(e['kind'] in (*KINDS,'check','development','verification','final') and e['action'] in ('write','approve','request_changes','advance','start','run','remediate','finalize'), 'Invalid engineering action.')
        obj,frozen=load_artifact(epic.directory,e['baseline_id'])
        require(obj['kind']==e['kind'] and obj['action']==e['action'] and obj['analysis_handoff']==e['cycle'],'Engineering audit differs from frozen artifact.','E_BASELINE_CONTEXT')
        require(frozen.get('engineering_history',[])==entries[:index] and frozen['lifecycle']==epic.metadata['lifecycle'][:len(frozen['lifecycle'])], 'Engineering audit/lifecycle prefix was rewritten.','E_APPROVAL_AUDIT')
        from ownership import preserve_prefix
        preserve_prefix(frozen,epic.metadata)
        from work_tracks import preserve_prefix as preserve_tracks
        preserve_tracks(frozen,epic.metadata)
        upstream=next((v for v in epic.metadata['lifecycle'] if v['id']==e['cycle'] and v['action']=='analysis_advance'),None)
        require(upstream is not None and upstream['baseline_id']==obj['analysis_baseline'], 'Engineering artifact references an unknown Analysis handoff.', 'E_ENGINEERING_INPUT')
        linked=next((v for v in epic.metadata['lifecycle'] if v['id']==e['operation_id']),None)
        if linked is not None:
            require(linked['action']=='engineer' and linked['baseline_id']==e['baseline_id'], 'Engineering lifecycle/audit binding mismatch.', 'E_APPROVAL_AUDIT')
        operations.add(e['operation_id'])

    require(all(v['id'] in operations for v in epic.metadata['lifecycle'] if v['action']=='engineer'), 'Engineering transition has no retained audit event.', 'E_APPROVAL_AUDIT')


def events(epic, action=None, kind=None):
    handoff=cycle(epic)
    return [e for e in epic.metadata.get('engineering_history',[]) if e['cycle']==handoff['id'] and (action is None or e['action']==action) and (kind is None or e['kind']==kind)]


def latest(epic,kind):
    found=events(epic,'write',kind)
    require(bool(found),'No current '+kind+' revision exists.','E_ENGINEERING_INPUT')
    entry=found[-1]
    return entry,load_artifact(epic.directory,entry['baseline_id'])[0]['payload']


def approval(epic,kind,source):
    draft,payload=latest(epic,kind)
    decisions=[e for e in events(epic,kind=kind) if e['action'] in ('approve','request_changes')]
    require(bool(decisions) and decisions[-1]['action']=='approve', 'An explicit current '+kind+' approval is required.','E_APPROVAL_REQUIRED')
    selected=load_artifact(epic.directory,decisions[-1]['baseline_id'])[0]['payload']
    require(selected['draft']==draft['baseline_id'], 'The '+kind+' approval is stale.','E_APPROVAL_STALE')
    if kind=='implementation':
        recent=events(epic)
        changes=[i for i,e in enumerate(recent) if e['action']=='remediate']
        require(not changes or recent.index(decisions[-1])>changes[-1], 'Remediation requires fresh human implementation approval.', 'E_APPROVAL_STALE')
        require(payload['source_revision']==source,'Code changed after human implementation review.','E_APPROVAL_STALE')
    return draft,payload


def review(epic, project):
    if epic.metadata['status'] not in DOWNSTREAM:
        return {'active':False,'stage':epic.metadata['status'],'reason':'No active Analysis handoff.'}
    handoff=cycle(epic)
    source=fingerprint(source_tree(epic,project))
    if epic.metadata.get('work_tracks'):
        import work_tracks
        token=work_tracks.revision(epic,'engineering',project)
    else:
        token=fingerprint({'review':epic.analysis_review_revision,'source':source})
    drafts={}
    for kind in KINDS:
        found=events(epic,'write',kind)
        if found:
            e=found[-1]; p=load_artifact(epic.directory,e['baseline_id'])[0]
            drafts[kind]={'baseline_id':e['baseline_id'],'operation_id':e['operation_id'],'payload':p['payload'],'skills':p['skills'],
                          'document':artifact_document(epic.directory,e['baseline_id'],kind)}
    finals=events(epic,'finalize','final')
    report=load_artifact(epic.directory,finals[-1]['baseline_id'])[0] if finals else None
    current=report is None or report['source_revision']==source
    if report is not None and epic.metadata.get('work_tracks'):
        import qa_track
        current=current and qa_track.integration_readiness(epic,project)['ready']
    approvals={}
    for kind in ('design','plan','implementation'):
        try:
            approval(epic,kind,source); approvals[kind]={'valid':True}
        except business.BusinessError as exc:
            approvals[kind]={'valid':False,'reason':str(exc),'code':exc.code}
    return {'active':True,'stage':epic.metadata['status'],'current':current,'final_report':{'baseline_id':finals[-1]['baseline_id'],'payload':report['payload'],'document':artifact_document(epic.directory,finals[-1]['baseline_id'],'final')} if report else None,'approvals':approvals,'revision':token,'source_revision':source,
            'analysis_baseline':handoff['baseline_id'],'analysis_handoff':handoff['id'],'drafts':drafts,
            'decisions':[e for e in events(epic) if e['action'] in ('approve','request_changes')],
            'evidence':[load_artifact(epic.directory,e['baseline_id'])[0]['payload'] for e in events(epic,'run','check')]}


def analysis_items(epic):
    handoff=cycle(epic)
    _, frozen=analysis_gate.read_baseline(epic.directory,handoff['baseline_id'],_loader())
    import functional_analysis as fa
    _, business_files=__import__('business_approval').read_baseline(epic.directory,epic.analysis['baseline_id'],_loader())
    details=fa.validate_document(frozen['specification.md'],epic.metadata['id'],{**epic.analysis,'business':business_files['business.md'].decode(),'discovery':yaml.load(business_files['discovery.yaml'].decode(),Loader=_loader())})
    return {rid:v['fields']['Status'] for rid,v in details['items'].items() if rid.startswith(('FR-','AC-')) and v['fields']['Status']!='retired'}, analysis_gate.open_items(details)


def validate_document(epic,kind,payload):
    require(isinstance(payload,dict),'Expected JSON object.','E_ENGINEERING_DOCUMENT')
    fields={'content','coverage','unresolved'} | ({'tasks','checks'} if kind=='plan' else {'source_revision','plan','completed_tasks'} if kind=='implementation' else {'source_revision','plan','findings'} if kind=='security' else set())
    require(set(payload)==fields and discovery.text(payload['content']), 'Unexpected or missing artifact fields.','E_ENGINEERING_DOCUMENT')
    items, inherited=analysis_items(epic)
    coverage=payload['coverage']
    require(isinstance(coverage,dict) and set(coverage)==set(items),'Cover every active Analysis FR and AC exactly.','E_ENGINEERING_TRACE')
    for rid,value in coverage.items():
        require(isinstance(value,dict) and set(value)=={'disposition','reason'} and value['disposition'] in ('implemented','excluded','blocked') and discovery.text(value['reason']),'Invalid coverage disposition.','E_ENGINEERING_TRACE')
        require(items[rid] not in ('blocked','proposed') or value['disposition']!='implemented','Blocked/proposed Analysis behavior cannot become implementation scope.','E_ENGINEERING_TRACE')
    unresolved=payload['unresolved']
    require(isinstance(unresolved,list) and all(isinstance(v,dict) and set(v)=={'id','text'} and business.valid_person(v['id']) and discovery.text(v['text']) for v in unresolved),'Invalid unresolved items.','E_ENGINEERING_DOCUMENT')
    ids=[v['id'] for v in unresolved]
    require(len(ids)==len(set(ids)) and {v['id'] for v in inherited}<=set(ids), 'Preserve inherited uncertainties explicitly.','E_ENGINEERING_TRACE')
    if kind!='design':
        _,upstream=latest(epic,'design' if kind=='plan' else 'plan')
        require({v['id'] for v in upstream['unresolved']}<=set(ids),'Upstream uncertainty cannot disappear.','E_ENGINEERING_TRACE')
        require(all(coverage[rid]['disposition']!='implemented' or upstream['coverage'][rid]['disposition']=='implemented' for rid in items),'Downstream artifacts cannot expand approved scope.','E_ENGINEERING_TRACE')
    if kind in ('implementation','security'):
        require(all(coverage[rid]['disposition']==upstream['coverage'][rid]['disposition'] for rid in items), 'Implementation and Security must retain approved plan dispositions; replan explicitly for scope changes.', 'E_ENGINEERING_TRACE')
    if kind=='plan':
        tasks=payload['tasks']; checks=payload['checks']; seen=set()
        require(isinstance(tasks,list) and bool(tasks) and isinstance(checks,list) and bool(checks),'Plan needs tasks and checks.','E_ENGINEERING_PLAN')
        for t in tasks:
            require(isinstance(t,dict) and set(t)=={'id','description','requirements','depends_on','paths'} and isinstance(t['id'],str) and re.fullmatch(r'T-[0-9]{3,}',t['id']) and t['id'] not in seen and discovery.text(t['description']),'Invalid plan task.','E_ENGINEERING_PLAN')
            require(isinstance(t['depends_on'],list) and all(isinstance(v,str) and v in seen for v in t['depends_on']),'Tasks must be in dependency order.','E_ENGINEERING_PLAN')
            require(isinstance(t['requirements'],list) and bool(t['requirements']) and all(isinstance(v,str) and v in items and coverage[v]['disposition']=='implemented' for v in t['requirements']),'Task references unavailable behavior.','E_ENGINEERING_TRACE')
            require(isinstance(t['paths'],list) and bool(t['paths']) and all(path_valid(p,True) for p in t['paths']),'Declare safe application paths for every task.','E_IMPLEMENTATION_BOUNDARY')
            if epic.metadata.get('work_tracks'):
                require(all(p.rstrip('/')!='qa' and not p.startswith('qa/') for p in t['paths']),'QA owns the reserved qa/ source namespace.','E_IMPLEMENTATION_BOUNDARY')
            seen.add(t['id'])
        require({rid for rid in items if coverage[rid]['disposition']=='implemented'} <= {rid for t in tasks for rid in t['requirements']}, 'Every implemented requirement/criterion needs a plan task.', 'E_ENGINEERING_TRACE')
        seen_checks=set()
        for c in checks:
            require(isinstance(c,dict) and set(c)=={'id','category','argv','cwd','timeout','requirements','scenario'} and business.valid_person(c['id']) and c['id'] not in seen_checks and c['category'] in ('unit','build','integration','ui'),'Invalid named check.','E_ENGINEERING_PLAN')
            require(isinstance(c['argv'],list) and bool(c['argv']) and all(isinstance(v,str) and '\x00' not in v for v in c['argv']) and c['argv'][0].strip() and (c['cwd']=='.' or path_valid(c['cwd'],True)) and type(c['timeout']) is int and 1<=c['timeout']<=120 and discovery.text(c['scenario']),'Invalid argv, directory, scenario or timeout.','E_ENGINEERING_PLAN')
            require(Path(c['argv'][0]).name not in ('git','gh','sh','bash','zsh','fish','cmd','powershell','pwsh'), 'Checks must not invoke Git mutations or shell interpreters; use a reviewed project runner.', 'E_ENGINEERING_PLAN')
            require(isinstance(c['requirements'],list) and bool(c['requirements']) and all(isinstance(r,str) and r in items and coverage[r]['disposition']=='implemented' for r in c['requirements']),'Invalid check requirement coverage.','E_ENGINEERING_TRACE')
            seen_checks.add(c['id'])
        categories={'unit','build'} if epic.metadata.get('work_tracks') else {'unit','build','integration','ui'}
        require({c['category'] for c in checks}==categories,'Engineering track owns unit/build; integration/UI belong to QA (legacy plans retain all four categories).','E_ENGINEERING_PLAN')
        target={rid for rid in items if rid.startswith('AC-') and coverage[rid]['disposition']=='implemented'}
        require(bool(epic.metadata.get('work_tracks')) or target<={r for c in checks if c['category'] in ('integration','ui') for r in c['requirements']},'Implemented acceptance criteria need verification checks.','E_ENGINEERING_TRACE')
    if kind in ('implementation','security'):
        plan,_=latest(epic,'plan')
        require(payload['plan']==plan['baseline_id'] and discovery.valid_revision(payload['source_revision']),'Review must bind exact plan and source.','E_ENGINEERING_TRACE')
    if kind=='implementation':
        _,plan=latest(epic,'plan')
        require(isinstance(payload['completed_tasks'],list) and all(isinstance(v,str) for v in payload['completed_tasks']) and len(payload['completed_tasks'])==len(set(payload['completed_tasks'])) and set(payload['completed_tasks'])=={t['id'] for t in plan['tasks']},'Implementation review must cover every task.','E_ENGINEERING_TRACE')
    if kind=='security':
        findings=payload['findings']; ids=set()
        require(isinstance(findings,list),'Findings must be a list.','E_SECURITY_FINDINGS')
        for f in findings:
            require(isinstance(f,dict) and set(f)=={'id','severity','status','requirements','evidence','remediation'} and isinstance(f['id'],str) and re.fullmatch(r'SF-[0-9]{3,}',f['id']) and f['id'] not in ids and f['severity'] in ('critical','high','medium','low') and f['status'] in ('open','resolved') and discovery.text(f['evidence']) and isinstance(f['remediation'],str),'Invalid security finding.','E_SECURITY_FINDINGS')
            require(isinstance(f['requirements'],list) and bool(f['requirements']) and all(isinstance(r,str) and r in items for r in f['requirements']),'Finding needs valid Analysis references.','E_ENGINEERING_TRACE')
            require(f['status']!='resolved' or discovery.text(f['remediation']), 'Resolved findings need remediation/retest evidence.','E_SECURITY_FINDINGS')
            ids.add(f['id'])
        past=events(epic,'write','security')
        if past:
            old=load_artifact(epic.directory,past[-1]['baseline_id'])[0]['payload']['findings']
            require({f['id'] for f in old}<=ids,'Do not erase previous security findings.','E_SECURITY_FINDINGS')
            for f in findings:
                earlier=next((v for v in old if v['id']==f['id']),None)
                if f['status']=='resolved' and (earlier is None or earlier['status']!='resolved'):
                    ordered=events(epic)
                    remediations=[e for e in events(epic,'remediate','security') if ordered.index(e)>ordered.index(past[-1])]
                    require(earlier is not None and any(f['id'] in load_artifact(epic.directory,e['baseline_id'])[0]['payload']['findings'] for e in remediations), 'Resolution needs an authorized remediation linked to the finding.','E_SECURITY_FINDINGS')


def boundary(epic,files):
    starts=events(epic,'start','development')
    require(bool(starts),'Explicit development start is required.','E_IMPLEMENTATION_BOUNDARY')
    start=load_artifact(epic.directory,starts[-1]['baseline_id'])[0]['payload']
    _,plan=latest(epic,'plan')
    require(start['plan']==latest(epic,'plan')[0]['baseline_id'],'Development start refers to another plan.','E_APPROVAL_STALE')
    allowed=[p.rstrip('/') for t in plan['tasks'] for p in t['paths']]
    changed=[p for p in set(start['tree'])|set(files) if start['tree'].get(p)!=files.get(p)]
    require(all(any(p==a or p.startswith(a+'/') for a in allowed) for p in changed),'Changes exceed approved paths: '+', '.join(p for p in changed if not any(p==a or p.startswith(a+'/') for a in allowed)), 'E_IMPLEMENTATION_BOUNDARY')
    return changed


def check_results(epic,source,categories):
    _,plan=latest(epic,'plan'); latest_results={}
    all_events=events(epic)
    floor=max((i for i,e in enumerate(all_events) if e['action'] in ('start','remediate')), default=-1)
    for e in events(epic,'run','check'):
        if all_events.index(e)<=floor: continue
        obj=load_artifact(epic.directory,e['baseline_id'])[0]['payload']
        if obj['source_revision']==source and obj['plan']==latest(epic,'plan')[0]['baseline_id']:
            latest_results[obj['check_id']]=obj
    for check in plan['checks']:
        if check['category'] in categories:
            evidence=latest_results.get(check['id'])
            require(evidence is not None and evidence['status']=='passed','Missing, failed or stale check: '+check['id'],'E_VERIFICATION')
    return latest_results


def verified_checks(epic,source,project):
    if not epic.metadata.get('work_tracks'):
        return check_results(epic,source,('unit','build','integration','ui'))
    import qa_track
    own=check_results(epic,source,('unit','build'))
    joined=qa_track.integration_readiness(epic,project)
    require(joined['ready'],'Integrated verification is incomplete: '+', '.join(v['message'] if isinstance(v,dict) else str(v) for v in joined['reasons']),'E_INTEGRATION_NOT_READY')
    return {**own,**{'qa:'+k:v for k,v in joined['checks'].items()}}


def execute_check(project,check):
    cwd=project/ check['cwd']
    require(cwd.is_dir() and cwd.resolve().is_relative_to(project.resolve()) and not cwd.is_symlink(),'Unsafe check working directory.','E_IMPLEMENTATION_BOUNDARY')
    # Commands are explicitly plan-approved. This is execution evidence, not sandboxing.
    with tempfile.TemporaryFile() as output:
        child=None
        try:
            child=subprocess.Popen(check['argv'],cwd=cwd,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                exit_code=child.wait(timeout=check['timeout'])
                status='passed' if exit_code==0 else 'failed'
            except subprocess.TimeoutExpired:
                exit_code=None; status='timeout'
        except OSError as exc:
            output.write(str(exc).encode()); exit_code=None; status='not_run'
        finally:
            if child is not None:
                # Bound helper servers/browser children to this named local check.
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                child.wait()
        output.seek(0); digest=hashlib.sha256(); prefix=bytearray(); size=0
        while True:
            chunk=output.read(65536)
            if not chunk: break
            digest.update(chunk); size+=len(chunk)
            prefix.extend(chunk[:max(0,1000000-len(prefix))])
    return {'status':status,'exit_code':exit_code,'output':prefix.decode('utf-8',errors='replace'),'output_sha256':digest.hexdigest(),'output_truncated':size>1000000}


def update(project,epic_id,expected_revision,operation_id,action,kind,payload,actor,decision,identity_source=None):
    import sdlc
    require(discovery.valid_revision(expected_revision) and discovery.valid_operation_id(operation_id) and business.valid_person(actor) and analysis_gate.valid_decision_text(decision),'Expected revision, operation ID, actor and explicit wording.','E_UPDATE_INPUT')
    require(action in ('write','approve','request_changes','advance','start','run','remediate','finalize') and kind in (*KINDS,'development','check','verification','final') and isinstance(payload,dict),'Unsupported engineering operation.','E_UPDATE_INPUT')
    require(identity_source in (None,'local_profile'),'Invalid identity source.','E_UPDATE_INPUT')
    with sdlc.project_lock(project):
        epic=sdlc.selected_epic(project,epic_id)
        # Exact replay is checked before lifecycle and currency checks.
        for e in epic.metadata.get('engineering_history',[]):
            if e['operation_id']==operation_id:
                obj=load_artifact(epic.directory,e['baseline_id'])[0]
                request=dict(obj['payload'].get('_request',{}))
                if action=='write': request['content']=obj['payload']['content']
                require(all(e[k]==v for k,v in {'action':action,'kind':kind,'actor':actor,'decision':decision,'expected_revision':expected_revision,'identity_source':identity_source or 'declared'}.items()) and request==payload,'Operation ID reused with different intent.','E_IDEMPOTENCY')
                return sdlc.result('engineering-'+action,epic.diagnostics,epic=epic.payload(),engineering=review(epic,project),replayed=True)
        sdlc.reject_gate_operation_reuse(epic,operation_id)
        handoff=cycle(epic)
        if epic.metadata.get('work_tracks'):
            import work_tracks
            work_tracks.require_reconciled(epic,'engineering')
        current=review(epic,project)
        require(current['revision']==expected_revision,'Engineering inputs or source changed; review again.','E_REVISION_CONFLICT')
        source=current['source_revision']; status=epic.metadata['status']; target=status
        content=dict(payload); skills={}
        if action=='write':
            require(kind in KINDS,'Unsupported document kind.','E_UPDATE_INPUT')
            allowed=(WRITE_STAGE[kind], 'ready_for_technical_design' if kind=='design' else 'ready_for_implementation_planning' if kind=='plan' else WRITE_STAGE[kind])
            require(status in allowed,'Cannot write '+kind+' at this stage.','E_STATUS')
            if kind=='plan': approval(epic,'design',source)
            if kind in ('implementation','security'):
                approval(epic,'plan',source); boundary(epic,source_tree(epic,project))
                require(payload.get('source_revision')==source,'Review is for another source revision.','E_REVISION_CONFLICT')
            validate_document(epic,kind,payload)
            if kind=='implementation': check_results(epic,source,('unit','build'))
            if kind=='security': verified_checks(epic,source,project)
            target=WRITE_STAGE[kind]
            skills=domain_skills.pins(['development'] if epic.metadata.get('work_tracks') and kind in ('plan','implementation') else SKILLS[kind],target,_loader())
        elif action in ('approve','request_changes'):
            require(kind in ('design','plan','implementation') and status==WRITE_STAGE[kind], 'No active approvable artifact in this stage.','E_STATUS')
            draft,doc=latest(epic,kind)
            if action=='approve' and kind=='plan' and epic.metadata.get('work_tracks'):
                import work_tracks
                require(draft['operation_id']!=work_tracks.active(epic)['engineering']['legacy_plan'],'The adopted combined plan is historical and unapproved; prepare an Engineering-only replacement.','E_TRACK_RECONCILIATION')
            if kind=='implementation':
                boundary(epic,source_tree(epic,project)); check_results(epic,source,('unit','build'))
                require(doc['source_revision']==source,'Code changed after review.','E_APPROVAL_STALE')
            require(set(payload)=={'acknowledged'} and isinstance(payload['acknowledged'],list) and all(isinstance(v,str) for v in payload['acknowledged']) and len(set(payload['acknowledged']))==len(payload['acknowledged']),'Invalid acknowledgement list.','E_UPDATE_INPUT')
            if action=='approve': common.exact_acknowledgements(payload['acknowledged'],doc['unresolved'],'Acknowledge exactly the unresolved items without resolving them.')
            else: require(not payload['acknowledged'],'Feedback does not acknowledge uncertainty.','E_UPDATE_INPUT')
            content={'draft':draft['baseline_id'],'acknowledged':payload['acknowledged'],'content':decision}
            skills=domain_skills.pins(['development'] if epic.metadata.get('work_tracks') and kind in ('plan','implementation') else SKILLS[kind],status,_loader())
        elif action=='start':
            require(kind=='development' and status=='ready_for_development' and not payload,'Development start requires separately advanced approved plan.','E_STATUS')
            draft,plan=approval(epic,'plan',source)
            planned_source=load_artifact(epic.directory,draft['baseline_id'])[0]['source_revision']
            require(planned_source==source,'Application changed since the approved plan; replan before development.', 'E_APPROVAL_STALE')
            content={'plan':draft['baseline_id'],'tree':source_tree(epic,project),'content':decision}
            target='development'; skills=domain_skills.pins(['development'],target,_loader())
        elif action=='run':
            require(not epic.metadata.get('work_tracks') or status=='development','Forked integration/UI execution belongs to the QA track.','E_TRACK_ROUTE')
            require(kind=='check' and set(payload)=={'check_id'} and isinstance(payload['check_id'],str),'Choose one named approved check.','E_UPDATE_INPUT')
            require(status in ('development','verification','security_review','final_verification'),'Checks are unavailable at this stage.','E_STATUS')
            plan_entry,plan=approval(epic,'plan',source)
            checks=[c for c in plan['checks'] if c['id']==payload['check_id']]
            require(len(checks)==1,'Unknown named check.','E_VERIFICATION')
            check=checks[0]
            require(status!='development' or check['category'] in ('unit','build'),'Integration/UI verification follows human code review.','E_STATUS')
            boundary(epic,source_tree(epic,project))
            if check['category'] in ('integration','ui'): approval(epic,'implementation',source)
            executed=execute_check(project,check)
            require(fingerprint(source_tree(epic,project))==source,'Check changed application inputs; inspect effects and rerun.','E_REVISION_CONFLICT')
            content={**executed,'check_id':check['id'],'check':check,'plan':plan_entry['baseline_id'],'source_revision':source,'content':executed['output']}
            skill='development' if status=='development' else 'testing'
            skills=domain_skills.pins([skill],status,_loader())
        elif action=='advance':
            require(not payload,'Advancement takes no document payload.','E_UPDATE_INPUT')
            if kind in ('design','plan','implementation'):
                require(status==WRITE_STAGE[kind],'No available advancement.','E_STATUS')
                approval(epic,kind,source)
                if kind=='implementation': boundary(epic,source_tree(epic,project)); check_results(epic,source,('unit','build'))
                target={'design':'ready_for_implementation_planning','plan':'ready_for_development','implementation':'verification'}[kind]
            elif kind=='verification':
                require(status=='verification','Verification is not active.','E_STATUS')
                boundary(epic,source_tree(epic,project)); approval(epic,'implementation',source); verified_checks(epic,source,project)
                target='security_review'
            elif kind=='security':
                require(status=='security_review','Security review is not active.','E_STATUS')
                _,sec=latest(epic,'security')
                require(sec['source_revision']==source and not any(f['status']=='open' for f in sec['findings']),'Current security findings require remediation.','E_SECURITY_FINDINGS')
                approval(epic,'implementation',source); verified_checks(epic,source,project)
                target='final_verification'
            else: require(False,'No available advancement.','E_STATUS')
            content={'content':decision,'source_revision':source}
        elif action=='remediate':
            if kind=='verification':
                require(status=='verification' and set(payload)=={'checks'} and isinstance(payload['checks'],list) and bool(payload['checks']) and all(isinstance(v,str) for v in payload['checks']), 'Name failed verification checks for explicit remediation.', 'E_VERIFICATION')
                failures={}
                if epic.metadata.get('work_tracks'):
                    import qa_track
                    context=qa_track.execution_context(epic,project)
                    for e in qa_track.history(epic,'run','check'):
                        evidence=qa_track.artifact(epic,e['baseline_id'])[0]['payload']
                        if evidence['context']==context: failures[evidence['check_id']]=(e,evidence)
                else:
                    for e in events(epic,'run','check'):
                        evidence=load_artifact(epic.directory,e['baseline_id'])[0]['payload']
                        if evidence['source_revision']==source: failures[evidence['check_id']]=(e,evidence)
                require(all(cid in failures and failures[cid][1]['status']!='passed' for cid in payload['checks']), 'Remediation must link current failed verification evidence.', 'E_VERIFICATION')
                content={**payload,'failure_evidence':{cid:failures[cid][0]['baseline_id'] for cid in payload['checks']},'content':decision}
            else:
                require(kind=='security' and status in ('security_review','final_verification') and set(payload)=={'findings'} and isinstance(payload['findings'],list) and bool(payload['findings']) and all(isinstance(v,str) for v in payload['findings']),'Explicit named findings are required for remediation.','E_STATUS')
                _,sec=latest(epic,'security')
                require(set(payload['findings'])<={f['id'] for f in sec['findings'] if f['status']=='open'},'Only existing open findings may be remediated.','E_SECURITY_FINDINGS')
                content={**payload,'content':decision}
            target='development'
            # A new start snapshot retains the ORIGINAL allowed boundary; do not bless out-of-plan changes.
            boundary(epic,source_tree(epic,project))
        else:
            require(action=='finalize' and kind=='final' and status=='final_verification' and not payload,'Final verification must be explicitly authorized.','E_STATUS')
            boundary(epic,source_tree(epic,project)); approval(epic,'implementation',source)
            checks=verified_checks(epic,source,project)
            _,sec=latest(epic,'security')
            require(sec['source_revision']==source and not any(f['status']=='open' for f in sec['findings']),'Security review is stale or unresolved.','E_SECURITY_FINDINGS')
            _,plan=latest(epic,'plan')
            content={'content':'# Final Verification Report\n\nAll approved named checks passed for this exact source revision.\nSecurity review has no open findings. This is not a security certification or release approval.\n', 'source_revision':source,'checks':checks,'coverage':plan['coverage'],'unresolved':plan['unresolved'],'security':latest(epic,'security')[0]['baseline_id']}
            if epic.metadata.get('work_tracks'):
                import qa_track
                content['qa_context']=qa_track.integration_readiness(epic,project)['context']
            skills=domain_skills.pins(['testing'],status,_loader()); target='verified'
        # Keep original intent for exact retries without reconstructing generated execution output.
        content['_request']=payload
        obj={'action':action,'kind':kind,'payload':content,'skills':skills,'analysis_baseline':handoff['baseline_id'],'analysis_handoff':handoff['id'],'source_revision':source}
        stored={**obj,'payload':{k:v for k,v in content.items() if k!='content'}}
        stored['payload']['_request']={k:v for k,v in payload.items() if k!='content'}
        manifest,snapshot=baseline_snapshot('engineering',kind,action,epic_id,
            (epic.directory/'metadata.yaml').read_bytes(),stored,content.get('content','').encode())
        baseline=common.publish_baseline(epic.directory,'engineering-baselines',manifest,snapshot,
            lambda m,f:common.validate_files(m,f,artifact_files(m,'engineering-baselines')),lambda bid:load_artifact(epic.directory,bid))
        candidate={**epic.metadata,'schema_version':'0.6','engineering_history':list(epic.metadata.get('engineering_history',[]))}
        entry={'operation_id':operation_id,'action':action,'kind':kind,'actor':actor,'identity_source':identity_source or 'declared','decision':decision,'expected_revision':expected_revision,'timestamp':business.timestamp(),'baseline_id':baseline,'cycle':handoff['id']}
        candidate['engineering_history'].append(entry)
        if target!=status:
            candidate['status']=target
            candidate['lifecycle']=[*candidate['lifecycle'],{'id':operation_id,'action':'engineer','from':status,'to':target,'base_revision':epic.revision,'actor':actor,'decision':decision,'timestamp':entry['timestamp'],'baseline_id':baseline,**({'identity_source':identity_source} if identity_source else {})}]
            import ownership
            if ownership.needs_handoff(candidate['lifecycle'][-1]):
                ownership.handoff(epic.metadata,candidate,actor,identity_source)
        def validate(value):
            sdlc.validate_gate_metadata(value)
        def read(directory):
            checked=sdlc.read_epic(directory); sdlc.require_valid(checked.diagnostics); return checked
        common.persist_decision(epic,candidate,expected_revision,read,lambda e:review(e,project)['revision'],validate,
            lambda path,value:sdlc.atomic_history_write(path,yaml.safe_dump(value,sort_keys=False,allow_unicode=True)))
        updated=sdlc.selected_epic(project,epic_id)
        return sdlc.result('engineering-'+action,updated.diagnostics,epic=updated.payload(),engineering=review(updated,project),replayed=False,baseline_id=baseline)
