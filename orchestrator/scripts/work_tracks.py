"""Two fixed Analysis work tracks; no scheduler, Git branch or workflow engine."""
from copy import deepcopy
import hashlib

import approval_common as common
import business_refinement as business
import discovery_history as discovery
import ownership
from engineering_contract import DOWNSTREAM

NAMES = ('engineering', 'qa')
ROLES = {'engineering':'Engineering Lead', 'qa':'QA Lead / Tester'}
QA_STATES = ('ready_for_test_design','test_design','test_automation','ready_for_verification','verified')
OP_FIELDS = {'operation_id','action','track','cycle','actor','identity_source','decision','expected_revision','assignee','timestamp'}


def require(value,message,code='E_WORK_TRACKS'):
    business.require(value,code,message,'metadata.yaml')


def current(metadata):
    value=metadata.get('work_tracks')
    return value['cycles'][-1] if isinstance(value,dict) and isinstance(value.get('cycles'),list) and value['cycles'] else None


def ownership_for(track, owner, actor, source, operation_id, decision, timestamp):
    # Reuse the existing event/state dialect, with a track responsibility rather
    # than the legacy scalar lifecycle's specialist handoffs.
    value=ownership.initialized('ready_for_implementation_planning',owner,actor,source,operation_id,decision,timestamp)
    event=value['history'][0]
    event.update(target_stage=track,required_role=ROLES[track],assignee=None,assignment_status='awaiting_assignment')
    return {**ownership.state(event),'history':[event]}


def fork(before,candidate,actor,source,origin='advance',operation=None):
    selected=next(e for e in reversed(candidate['lifecycle']) if e['action']=='analysis_advance')
    previous=current(before)
    require(previous is None or previous['id']!=selected['id'],'Two tracks already exist for this Analysis handoff.','E_TRACK_EXISTS')
    owner=ownership.view(candidate)['owner']
    require(business.valid_person(owner),'Declare an unambiguous accountable owner before creating tracks.','E_OWNER_REQUIRED')
    op=operation or {'operation_id':selected['id'],'action':'fork','track':None,'cycle':selected['id'],'actor':actor,'identity_source':source or 'declared','decision':selected['decision'],'expected_revision':selected['review_revision'],'assignee':None,'timestamp':selected['timestamp']}
    value=deepcopy(before.get('work_tracks',{'schema_version':'0.1','cycles':[],'operations':[]}))
    # Old cycles are retained verbatim. Only a newly advanced Analysis cycle
    # activates the strengthened contract; adoption preserves legacy authority.
    if value['schema_version']=='0.1':
        value.update(schema_version='0.2',legacy_cycle_count=len(value['cycles']))
    if origin=='adopt':
        value['legacy_cycle_count']+=1
    cycle={'id':selected['id'],'analysis_baseline':selected['baseline_id'],'origin':origin}
    if origin=='advance':cycle['governance_version']='0.1'
    for track in NAMES:
        initial='track-init-'+hashlib.sha256((op['operation_id']+track).encode()).hexdigest()
        track_owner=previous[track]['ownership']['owner'] if previous else owner
        block={'ownership':ownership_for(track,track_owner,actor,source,initial,op['decision'],op['timestamp']),'reconciliation':[]}
        if track=='engineering':
            plans=[e for e in candidate.get('engineering_history',[]) if e['cycle']==selected['id'] and e['action']=='write' and e['kind']=='plan']
            block['legacy_plan']=plans[-1]['operation_id'] if origin=='adopt' and plans else None
        else:
            block.update(status='ready_for_test_design',history=[])
        cycle[track]=block
    value['cycles'].append(cycle);value['operations'].append(op)
    candidate['work_tracks']=value


def validate(metadata):
    value=metadata.get('work_tracks')
    if value is None:return
    require(isinstance(value,dict) and value.get('schema_version') in ('0.1','0.2'),'Invalid work track version.')
    fields={'schema_version','cycles','operations'}|({'legacy_cycle_count'} if value['schema_version']=='0.2' else set())
    require(set(value)==fields,'Invalid work track fields.')
    require(isinstance(value['cycles'],list) and bool(value['cycles']) and isinstance(value['operations'],list),'Tracks require retained cycles and operation history.')
    legacy=value.get('legacy_cycle_count',len(value['cycles']))
    require(type(legacy) is int and 0<=legacy<=len(value['cycles']),'Invalid legacy cycle boundary.')
    handoffs={e['id']:e for e in metadata.get('lifecycle',[]) if e['action']=='analysis_advance'}
    cycle_ids=set()
    for index,c in enumerate(value['cycles']):
        fields={'id','analysis_baseline','origin','engineering','qa'}|({'governance_version'} if index>=legacy else set())
        require(isinstance(c,dict) and set(c)==fields,'Invalid track cycle or missing governance marker.')
        if index>=legacy:require(c['governance_version']=='0.1' and c['origin']=='advance','Unsupported governance contract.')
        require(isinstance(c['id'],str) and c['id'] in handoffs and c['id'] not in cycle_ids and c['analysis_baseline']==handoffs[c['id']]['baseline_id'] and c['origin'] in ('advance','adopt'),'Invalid Analysis track authority.')
        cycle_ids.add(c['id'])
        for name in NAMES:
            block=c[name];fields={'ownership','reconciliation','legacy_plan'} if name=='engineering' else {'ownership','reconciliation','status','history'}
            require(isinstance(block,dict) and set(block)==fields and isinstance(block['reconciliation'],list),'Invalid track state.')
            if name=='engineering':require(block['legacy_plan'] is None or discovery.valid_operation_id(block['legacy_plan']),'Invalid legacy plan reference.')
            else:require(block['status'] in QA_STATES and isinstance(block['history'],list),'Invalid QA lifecycle/history.')
            own=block['ownership']
            require(isinstance(own,dict) and set(own)==ownership.STATE_FIELDS|{'history'} and isinstance(own['history'],list) and bool(own['history']),'Invalid track ownership.')
            previous=None;ids=set()
            for index,event in enumerate(own['history']):
                require(isinstance(event,dict) and set(event)==ownership.EVENT_FIELDS,'Invalid track assignment event.')
                require(discovery.valid_operation_id(event['operation_id']) and event['operation_id'] not in ids and event['action']==('initialize' if index==0 else 'assign'),'Invalid assignment operation.')
                require(all(business.valid_person(event[k]) for k in ('actor','to_owner')) and ownership.text(event['decision']) and ownership.timestamp_valid(event['timestamp']) and event['identity_source'] in ('declared','local_profile'),'Invalid assignment attribution.')
                require(event['from_owner']==(previous['owner'] if previous else None) and event['required_role']==ROLES[name] and event['target_stage']==name and event['lifecycle_id'] is None,'Broken assignment chain or role.')
                require(event['assignment_status'] in ('assigned','awaiting_assignment') and (event['assignee']==event['to_owner'] if event['assignment_status']=='assigned' else event['assignee'] is None),'Invalid track assignee.')
                require((event['expected_revision'] is None or discovery.valid_revision(event['expected_revision'])) if index==0 else discovery.valid_revision(event['expected_revision']),'Invalid assignment revision.')
                require(index!=0 or event['assignment_status']=='awaiting_assignment','Fork cannot auto-assign a person.')
                ids.add(event['operation_id']);previous=ownership.state(event)
            require({k:own[k] for k in ownership.STATE_FIELDS}==previous,'Current track owner differs from history.')
    ids=set()
    for op in value['operations']:
        require(isinstance(op,dict) and set(op)==OP_FIELDS and discovery.valid_operation_id(op['operation_id']) and op['operation_id'] not in ids,'Invalid track management operation.')
        require(op['action'] in ('fork','adopt','assign','reconcile') and op['track'] in (*NAMES,None) and isinstance(op['cycle'],str) and op['cycle'] in cycle_ids,'Invalid management action/cycle.')
        require(business.valid_person(op['actor']) and ownership.text(op['decision']) and ownership.timestamp_valid(op['timestamp']) and discovery.valid_revision(op['expected_revision']) and op['identity_source'] in ('declared','local_profile'),'Invalid management evidence.')
        require(business.valid_person(op['assignee']) if op['action']=='assign' else op['assignee'] is None,'Invalid assignment recipient.')
        require(op['track'] in NAMES if op['action'] in ('assign','reconcile') else op['track'] is None,'Invalid track selection.')
        ids.add(op['operation_id'])
    for c in value['cycles']:
        require(sum(o['action'] in ('fork','adopt') and o['cycle']==c['id'] for o in value['operations'])==1,'Cycle must have one auditable fork.')
        creation=next(o for o in value['operations'] if o['action'] in ('fork','adopt') and o['cycle']==c['id'])
        if c['origin']=='advance':
            linked=handoffs[c['id']]
            require(creation['action']=='fork' and creation['operation_id']==linked['id'] and creation['actor']==linked['actor'] and creation['decision']==linked['decision'] and creation['timestamp']==linked['timestamp'] and creation['expected_revision']==linked['review_revision'],'Automatic fork differs from explicit Analysis advancement.','E_APPROVAL_AUDIT')
        else:require(creation['action']=='adopt','Adoption needs its own explicit decision.','E_APPROVAL_AUDIT')
        for name in NAMES:
            require(all(op in value['operations'] and op['action']=='reconcile' and op['track']==name and op['cycle']==c['id'] for op in c[name]['reconciliation']),'Invalid reconciliation evidence.')
            for event in c[name]['ownership']['history'][1:]:
                require(any(op['operation_id']==event['operation_id'] and op['action']=='assign' and op['track']==name and op['cycle']==c['id'] and op['assignee']==event['to_owner'] and all(op[k]==event[k] for k in ('actor','identity_source','decision','expected_revision','timestamp')) for op in value['operations']),'Assignment has no retained management decision.')


def preserve_prefix(before,after):
    old=before.get('work_tracks')
    if old is None:return
    new=after.get('work_tracks')
    require(isinstance(new,dict) and new['operations'][:len(old['operations'])]==old['operations'] and len(new['cycles'])>=len(old['cycles']),'Track audit cannot be truncated.','E_APPROVAL_AUDIT')
    if old['schema_version']=='0.2':
        require(new.get('schema_version')=='0.2' and new.get('legacy_cycle_count')==old['legacy_cycle_count'],'Governance cannot be downgraded or bypassed.','E_APPROVAL_AUDIT')
    elif new.get('schema_version')=='0.2':
        require(new.get('legacy_cycle_count')==len(old['cycles']),'Historical cycle boundary cannot be reinterpreted.','E_APPROVAL_AUDIT')
    if len(new['cycles'])>len(old['cycles']):
        require(new['cycles'][:len(old['cycles'])]==old['cycles'],'Historical work cycles must remain unchanged.','E_APPROVAL_AUDIT')
        return
    require(new['cycles'][:-1]==old['cycles'][:-1],'Historical cycles must remain immutable.','E_APPROVAL_AUDIT')
    a,b=old['cycles'][-1],new['cycles'][-1]
    require(all(a.get(k)==b.get(k) for k in ('id','analysis_baseline','origin','governance_version')),'Track authority cannot be rewritten.','E_APPROVAL_AUDIT')
    for name in NAMES:
        ownership.preserve_prefix({'ownership':a[name]['ownership']},{'ownership':b[name]['ownership']})
        require(b[name]['reconciliation'][:len(a[name]['reconciliation'])]==a[name]['reconciliation'],'Reconciliation audit prefix changed.','E_APPROVAL_AUDIT')
    require(b['engineering']['legacy_plan']==a['engineering']['legacy_plan'],'Legacy references cannot be rewritten.','E_APPROVAL_AUDIT')
    require(b['qa']['history'][:len(a['qa']['history'])]==a['qa']['history'],'QA history cannot be rewritten.','E_APPROVAL_AUDIT')


def active(epic):
    c=current(epic.metadata)
    handoff=next((e for e in reversed(epic.metadata.get('lifecycle',[])) if e['action']=='analysis_advance'),None)
    require(c is not None and handoff is not None and c['id']==handoff['id'] and c['analysis_baseline']==handoff['baseline_id'] and epic.analysis_approval and epic.analysis_approval['valid'] and epic.metadata['status'] in DOWNSTREAM,'Tracks require the active approved Analysis handoff.','E_TRACK_RECONCILIATION')
    return c


def require_reconciled(epic,track):
    c=active(epic)
    require(track in NAMES,'Select Engineering or QA.','E_TRACK_AMBIGUOUS')
    require(len(epic.metadata['work_tracks']['cycles'])==1 or bool(c[track]['reconciliation']),'Assess upstream changes and explicitly reconcile this track first.','E_TRACK_RECONCILIATION')


def engineering_tree(epic,project):
    import engineering
    files=engineering.tree(project)
    return {p:v for p,v in files.items() if not p.startswith('qa/') and p!='qa'}


def revision(epic,track,project):
    import engineering
    c=active(epic)
    require(track in NAMES,'Select Engineering or QA.','E_TRACK_AMBIGUOUS')
    obj={'cycle':c['id'],'analysis_baseline':c['analysis_baseline'],'track':c[track]}
    if 'governance_version' in c:obj['governance_version']=c['governance_version']
    if track=='engineering':
        obj.update(status=epic.metadata['status'],history=[e for e in epic.metadata.get('engineering_history',[]) if e['cycle']==c['id']],source=engineering.fingerprint(engineering_tree(epic,project)))
    return engineering.fingerprint(obj)


def operation_ids(metadata):
    value=metadata.get('work_tracks')
    if not value:return set()
    return {op['operation_id'] for op in value['operations']}|{e['operation_id'] for c in value['cycles'] for e in c['qa']['history']}


def review(epic,project):
    c=current(epic.metadata)
    require(c is not None,'This legacy request has no work tracks. Explicitly adopt if appropriate.','E_TRACK_REQUIRED')
    try:active(epic); is_active=True
    except business.BusinessError:is_active=False
    tracks={}
    for name in NAMES:
        block=c[name];own=block['ownership']
        status=epic.metadata['status'] if name=='engineering' else block['status']
        recon=not is_active or (len(epic.metadata['work_tracks']['cycles'])>1 and not block['reconciliation'])
        tracks[name]={'status':status,**own,'needs_reconciliation':recon,'next_action':'Assess upstream impact and reconcile' if recon else 'Assign '+ROLES[name] if own['assignee'] is None else 'Start or review this track only when explicitly requested','revision':revision(epic,name,project) if is_active else None}
    return {'active':is_active,'cycle':c['id'],'analysis_baseline':c['analysis_baseline'],'governance':c.get('governance_version','legacy: not assessed under strengthened controls'),'tracks':tracks}


def update(project,epic_id,expected_revision,operation_id,action,track,actor,decision,assignee=None,identity_source=None):
    import sdlc,engineering
    require(action in ('assign','reconcile','adopt') and (track in NAMES if action!='adopt' else track is None) and discovery.valid_revision(expected_revision) and discovery.valid_operation_id(operation_id) and business.valid_person(actor) and ownership.text(decision) and identity_source in (None,'local_profile'),'Invalid track operation inputs.','E_UPDATE_INPUT')
    require(business.valid_person(assignee) if action=='assign' else assignee is None,'Declare the assignee explicitly.','E_UPDATE_INPUT')
    with sdlc.project_lock(project):
        epic=sdlc.selected_epic(project,epic_id)
        for op in epic.metadata.get('work_tracks',{}).get('operations',[]):
            if op['operation_id']==operation_id:
                require(all(op[k]==v for k,v in {'action':action,'track':track,'actor':actor,'decision':decision,'assignee':assignee,'identity_source':identity_source or 'declared','expected_revision':expected_revision}.items()),'Track operation ID reused with different intent.','E_IDEMPOTENCY')
                return sdlc.result('tracks-'+action,epic.diagnostics,epic=epic.payload(),work_tracks=review(epic,project),replayed=True)
        sdlc.reject_gate_operation_reuse(epic,operation_id)
        if action=='adopt':
            require(current(epic.metadata) is None,'This request already has tracks.','E_TRACK_EXISTS')
            require(epic.metadata['status'] in ('ready_for_technical_design','technical_design','ready_for_implementation_planning','implementation_planning'),'Adoption is supported only before development.','E_TRACK_COMPATIBILITY')
            require(not any(e['action']=='start' for e in engineering.events(epic)),'Do not adopt after development has started.','E_TRACK_COMPATIBILITY')
            if any(e['kind']=='plan' and e['action']=='approve' for e in engineering.events(epic)):
                require(False,'An approved legacy combined plan requires upstream reconciliation, not adoption.','E_TRACK_COMPATIBILITY')
            token=lambda e:engineering.review(e,project)['revision']
            c=engineering.cycle(epic)
        else:
            c=active(epic);token=lambda e:revision(e,track,project)
        require(token(epic)==expected_revision,'Track context changed; reopen before applying this decision.','E_REVISION_CONFLICT')
        op={'operation_id':operation_id,'action':action,'track':track,'cycle':c['id'],'actor':actor,'identity_source':identity_source or 'declared','decision':decision,'expected_revision':expected_revision,'assignee':assignee,'timestamp':business.timestamp()}
        candidate=deepcopy(epic.metadata)
        if action=='adopt':fork(epic.metadata,candidate,actor,identity_source,'adopt',op)
        else:
            selected=current(candidate)[track]
            if action=='assign':
                own=selected['ownership']
                event=ownership.event_for('assign',own,'ready_for_implementation_planning',actor,identity_source,operation_id,expected_revision,decision,owner=assignee)
                event.update(target_stage=track,required_role=ROLES[track])
                selected['ownership']=ownership.append(own,event)
            else:
                require(len(candidate['work_tracks']['cycles'])>1,'Initial tracks need no upstream reconciliation.','E_STATUS')
                selected['reconciliation'].append(deepcopy(op))
            candidate['work_tracks']['operations'].append(op)
        def read(directory):
            checked=sdlc.read_epic(directory);sdlc.require_valid(checked.diagnostics);return checked
        common.persist_decision(epic,candidate,expected_revision,read,token,lambda m:(sdlc.validate_gate_metadata(m),validate(m)),lambda p,m:sdlc.atomic_history_write(p,__import__('yaml').safe_dump(m,sort_keys=False,allow_unicode=True)))
        after=sdlc.selected_epic(project,epic_id)
        return sdlc.result('tracks-'+action,after.diagnostics,epic=after.payload(),work_tracks=review(after,project),replayed=False)
