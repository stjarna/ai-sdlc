"""Independent QA design, automation and evidence policy over shared SDLC storage.

Functional expectations come from frozen Analysis. Technical Design is only an
interface dependency of executable automation, never an input prerequisite to QA design.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

import yaml

import analysis_approval
import approval_common as common
import business_refinement as business
import discovery_history as discovery
import domain_skills
import artifact_names
import engineering
import work_tracks

KINDS = ('strategy', 'scenarios', 'automation')
STATUSES = ('ready_for_test_design', 'test_design', 'test_automation', 'ready_for_verification', 'verified')
ROOT = 'qa-baselines'


def require(value, message, code='E_QA', file='metadata.yaml'):
    business.require(value, code, message, file)


def current(epic):
    return work_tracks.active(epic)['qa']


def history(epic, action=None, kind=None):
    entries=current(epic)['history']
    return [e for e in entries if (action is None or e['action']==action) and (kind is None or e['kind']==kind)]


def artifact(epic, baseline):
    return engineering.load_artifact(epic.directory, baseline, root_name=ROOT)


def qa_tree(project):
    return {p:v for p,v in engineering.tree(project).items() if p.startswith('qa/')}


def qa_source(project):
    return engineering.fingerprint(qa_tree(project))


def app_source(epic,project):
    return engineering.fingerprint(engineering.source_tree(epic,project))


def latest(epic,kind):
    entries=history(epic,'write',kind)
    require(bool(entries),'No current QA '+kind+' artifact exists.','E_QA_INPUT')
    entry=entries[-1]
    return entry,artifact(epic,entry['baseline_id'])[0]['payload']


def scenario_context(epic):
    strategy,plan=latest(epic,'strategy');scenarios,cases=latest(epic,'scenarios')
    require(all(plan['coverage'][rid]['disposition']==cases['coverage'][rid]['disposition'] for rid in plan['coverage']),
            'QA strategy and scenario coverage require explicit reconciliation.','E_QA_TRACE')
    return {'strategy':strategy['baseline_id'],'scenarios':scenarios['baseline_id']}


def unresolved(epic):
    values={}
    for kind in ('strategy','scenarios'):
        _,doc=latest(epic,kind)
        for item in doc['unresolved']:
            values[item['id']]=item
    return [values[k] for k in sorted(values)]


def decision(epic,kind):
    entries=[e for e in history(epic,kind=kind) if e['action'] in ('approve','request_changes')]
    require(bool(entries) and entries[-1]['action']=='approve','An explicit current QA '+kind+' approval is required.','E_APPROVAL_REQUIRED')
    return entries[-1],artifact(epic,entries[-1]['baseline_id'])[0]['payload']


def scenario_approval(epic):
    entry,approved=decision(epic,'scenarios')
    require(approved['documents']==scenario_context(epic),'QA strategy or scenarios changed after approval.','E_APPROVAL_STALE')
    return entry


def design_context(epic,project):
    source=app_source(epic,project)
    design,_=engineering.approval(epic,'design',source)
    return design['baseline_id']


def automation_approval(epic,project):
    scenario=scenario_approval(epic)
    draft,doc=latest(epic,'automation')
    entry,approved=decision(epic,'automation')
    require(approved['draft']==draft['baseline_id'] and approved['scenarios_approval']==scenario['baseline_id'] and doc['scenarios_approval']==scenario['baseline_id'],
            'QA automation or its scenarios changed after approval.','E_APPROVAL_STALE')
    require(doc['source_revision']==qa_source(project)==approved['source_revision'],
            'QA automation files changed after review.','E_APPROVAL_STALE')
    require(doc['engineering_design']==design_context(epic,project),
            'QA automation requires adaptation to the changed technical interface.','E_APPROVAL_STALE')
    return entry,doc


def execution_context(epic,project):
    scenario=scenario_approval(epic)
    auto,doc=automation_approval(epic,project)
    source=app_source(epic,project)
    plan,_=engineering.approval(epic,'plan',source)
    implementation,_=engineering.approval(epic,'implementation',source)
    approvals=engineering.events(epic,'approve','implementation')
    require(bool(approvals),'No current implementation approval.','E_APPROVAL_REQUIRED')
    return {
        'analysis_baseline':work_tracks.active(epic)['analysis_baseline'],
        'analysis_handoff':work_tracks.active(epic)['id'],
        'engineering_design':doc['engineering_design'],
        'engineering_plan':plan['baseline_id'],
        'implementation':implementation['baseline_id'],
        'implementation_approval':approvals[-1]['baseline_id'],
        'scenarios_approval':scenario['baseline_id'],
        'automation':latest(epic,'automation')[0]['baseline_id'],
        'automation_approval':auto['baseline_id'],
        'source_revision':source,
        'qa_source_revision':qa_source(project),
    }


def results(epic,project):
    context=execution_context(epic,project)
    _,automation=latest(epic,'automation')
    found={}
    for entry in history(epic,'run','check'):
        payload=artifact(epic,entry['baseline_id'])[0]['payload']
        if payload['context']==context:
            found[payload['check_id']]=payload
    for check in automation['checks']+automation.get('limitation_checks',[]):
        value=found.get(check['id'])
        require(value is not None and value['status']=='passed',
                'QA check is missing, failed or stale: '+check['id'],'E_VERIFICATION')
    return found,context


def integration_readiness(epic,project):
    view={'ready':False,'reasons':[],'checks':{},'context':None,'coverage':{}}
    try:
        work_tracks.require_reconciled(epic,'engineering')
        work_tracks.require_reconciled(epic,'qa')
        require(epic.metadata['status'] in ('verification','security_review','final_verification','verified'),
                'Engineering has not explicitly advanced reviewed implementation to Verification.','E_INTEGRATION_NOT_READY')
        require(current(epic)['status']=='verified','QA verification has not explicitly completed.','E_INTEGRATION_NOT_READY')
        checks,context=results(epic,project)
        completions=history(epic,'advance','verification')
        require(bool(completions) and artifact(epic,completions[-1]['baseline_id'])[0]['payload']['context']==context,
                'QA completion is stale for the current implementation or automation.','E_INTEGRATION_NOT_READY')
        _,plan=engineering.latest(epic,'plan')
        _,scenarios=latest(epic,'scenarios')
        implemented={rid for rid,v in plan['coverage'].items() if rid.startswith('AC-') and v['disposition']=='implemented'}
        covered={rid for rid,v in scenarios['coverage'].items() if v['disposition']=='implemented'}
        require(implemented<=covered,'QA does not cover all implemented acceptance criteria.','E_INTEGRATION_NOT_READY')
        view.update(ready=True,checks=checks,context=context,coverage={
            'engineering':plan['coverage'],'qa':scenarios['coverage'],
            'unresolved':unresolved(epic),
        })
    except business.BusinessError as exc:
        view['reasons'].append({'code':exc.code,'message':str(exc)})
    return view


def validate_document(epic,project,kind,payload):
    require(isinstance(payload,dict),'Expected a QA artifact object.','E_QA_DOCUMENT')
    fields={'content','coverage','unresolved'}
    fields |= {'cases'} if kind=='scenarios' else {'paths','checks','source_revision'} if kind=='automation' else set()
    if kind=='automation' and engineering.governed(epic):fields.add('limitation_checks')
    require(set(payload)==fields and discovery.text(payload['content']),'Invalid QA artifact fields.','E_QA_DOCUMENT')
    items,inherited=engineering.analysis_items(epic)
    coverage=payload['coverage']
    require(isinstance(coverage,dict) and set(coverage)==set(items),
            'QA must report every active Analysis FR/AC disposition.','E_QA_TRACE')
    for rid,value in coverage.items():
        require(isinstance(value,dict) and set(value)=={'disposition','reason'} and value['disposition'] in ('implemented','blocked','excluded') and discovery.text(value['reason']),
                'Invalid QA coverage disposition.','E_QA_TRACE')
        require(items[rid] not in ('blocked','proposed') or value['disposition']!='implemented',
                'Unresolved Analysis behavior cannot become a QA expected outcome.','E_QA_TRACE')
    questions=payload['unresolved']
    require(isinstance(questions,list) and all(isinstance(v,dict) and set(v)=={'id','text'} and business.valid_person(v['id']) and discovery.text(v['text']) for v in questions),
            'Invalid QA uncertainty records.','E_QA_DOCUMENT')
    ids=[v['id'] for v in questions]
    require(len(ids)==len(set(ids)) and {v['id'] for v in inherited}<=set(ids),
            'QA must preserve inherited unresolved Analysis items.','E_QA_TRACE')
    if kind=='scenarios':
        cases=payload['cases'];seen=set();covered=set()
        require(isinstance(cases,list) and bool(cases),'QA scenarios need test cases.','E_QA_TRACE')
        for case in cases:
            require(isinstance(case,dict) and set(case)=={'id','requirements','preconditions','action','expected','status'} and isinstance(case['id'],str) and re.fullmatch(r'TC-[0-9]{3,}',case['id']) and case['id'] not in seen,
                    'Invalid or duplicate test case.','E_QA_TRACE')
            require(all(discovery.text(case[k]) for k in ('preconditions','action','expected')) and case['status'] in ('specified','blocked'),
                    'Test cases require preconditions, action, observable expected outcome and status.','E_QA_TRACE')
            require(isinstance(case['requirements'],list) and bool(case['requirements']) and all(isinstance(r,str) and r in items for r in case['requirements']),
                    'Test case has invalid Analysis references.','E_QA_TRACE')
            if case['status']=='specified':
                require(all(coverage[r]['disposition']=='implemented' and items[r] not in ('blocked','proposed') for r in case['requirements']),
                        'A specified case cannot resolve blocked or excluded behavior.','E_QA_TRACE')
                covered.update(case['requirements'])
            seen.add(case['id'])
        require({r for r,v in coverage.items() if v['disposition']=='implemented'}<=covered,
                'Every claimed QA-covered FR/AC needs a specified scenario.','E_QA_TRACE')
    if kind=='automation':
        scenario_approval(epic)
        _,scenarios=latest(epic,'scenarios')
        require({v['id'] for v in unresolved(epic)}<=set(ids),'Automation cannot drop reviewed uncertainty.','E_QA_TRACE')
        require(all(coverage[r]['disposition']==scenarios['coverage'][r]['disposition'] for r in items),
                'Automation cannot silently change functional scenario dispositions.','E_QA_TRACE')
        paths=payload['paths']
        require(isinstance(paths,list) and bool(paths) and all(isinstance(p,str) for p in paths) and len(paths)==len(set(paths)) and all(engineering.path_valid(p,True) and p.startswith('qa/') for p in paths),
                'QA automation source paths must stay under reserved qa/.','E_IMPLEMENTATION_BOUNDARY')
        files=qa_tree(project)
        require(all(any(p==a.rstrip('/') or p.startswith(a.rstrip('/')+'/') for a in paths) for p in files),
                'QA source files exceed the reviewed automation paths.','E_IMPLEMENTATION_BOUNDARY')
        require(discovery.valid_revision(payload['source_revision']) and payload['source_revision']==engineering.fingerprint(files),
                'QA automation source changed before recording its review.','E_REVISION_CONFLICT')
        cases={c['id']:c for c in scenarios['cases']}
        checks=payload['checks'];seen=set();covered=set();covered_cases=set()
        extra=payload.get('limitation_checks',[])
        require(isinstance(extra,list),'Limitation checks must be a list.','E_QA_DOCUMENT')
        limits=engineering.authorized_limitations(epic,app_source(epic,project)) if engineering.governed(epic) else {}
        require(isinstance(checks,list) and bool(checks),'Automation needs named checks.','E_QA_DOCUMENT')
        tested_limits=set()
        for index,check in enumerate(checks+extra):
            supplemental=index>=len(checks)
            fields={'id','category','argv','cwd','timeout','requirements','scenario'}|({'limitations'} if supplemental else {'cases'})
            require(isinstance(check,dict) and set(check)==fields and business.valid_person(check['id']) and check['id'] not in seen and check['category'] in ('integration','ui'),
                    'Invalid QA named check.','E_QA_DOCUMENT')
            require(isinstance(check['argv'],list) and bool(check['argv']) and all(isinstance(v,str) and '\x00' not in v for v in check['argv']) and bool(check['argv'][0].strip()) and Path(check['argv'][0]).name not in ('git','gh','sh','bash','zsh','fish','cmd','powershell','pwsh') and (check['cwd']=='.' or engineering.path_valid(check['cwd'],True)) and type(check['timeout']) is int and 1<=check['timeout']<=120 and discovery.text(check['scenario']),
                    'Invalid QA check argv, directory, timeout or scenario.','E_QA_DOCUMENT')
            if supplemental:
                engineering.references(check['limitations'],limits,'QA check references an unauthorized limitation.')
                require(bool(check['limitations']),'Supplemental check must identify its authorized limitation.','E_QA_TRACE')
                allowed={r for lid in check['limitations'] for r in limits[lid]['requirements']}
                require(isinstance(check['requirements'],list) and bool(check['requirements']) and all(isinstance(r,str) and r in allowed for r in check['requirements']),
                        'Limitation check must reference affected requirements without claiming product coverage.','E_QA_TRACE')
                tested_limits.update(check['limitations']);seen.add(check['id'])
                continue
            require(isinstance(check['cases'],list) and bool(check['cases']) and all(isinstance(c,str) and c in cases and cases[c]['status']=='specified' for c in check['cases']),
                    'Automation must link specified approved cases.','E_QA_TRACE')
            case_requirements={r for cid in check['cases'] for r in cases[cid]['requirements']}
            require(isinstance(check['requirements'],list) and bool(check['requirements']) and all(isinstance(r,str) and r in case_requirements for r in check['requirements']),
                    'Check requirement claims must be supported by linked cases.','E_QA_TRACE')
            covered.update(check['requirements']);covered_cases.update(check['cases']);seen.add(check['id'])
        require({c['id'] for c in scenarios['cases'] if c['status']=='specified'}<=covered_cases,
                'Every specified scenario needs an executable named check.','E_QA_TRACE')
        require({c['category'] for c in checks}=={'integration','ui'},'QA needs integration and UI checks.','E_QA_TRACE')
        require(tested_limits==set(limits),'QA must test each authorized limitation separately from product scenarios.','E_QA_TRACE')
        require({r for r,v in coverage.items() if r.startswith('AC-') and v['disposition']=='implemented'}<=covered,
                'Every claimed acceptance criterion needs named automation.','E_QA_TRACE')


def validate_history(epic):
    tracks=epic.metadata.get('work_tracks')
    if tracks is None:return
    seen=set()
    for cycle in tracks['cycles']:
        entries=cycle['qa']['history']
        for index,entry in enumerate(entries):
            require(isinstance(entry,dict) and set(entry)==engineering.EVENT_FIELDS,'Invalid QA audit fields.','E_QA_AUDIT')
            require(discovery.valid_operation_id(entry['operation_id']) and entry['operation_id'] not in seen and discovery.valid_revision(entry['expected_revision']) and discovery.valid_revision(entry['baseline_id']),
                    'Invalid QA operation or revision binding.','E_QA_AUDIT')
            require(entry['action'] in ('write','approve','request_changes','advance','run') and entry['kind'] in (*KINDS,'verification','check') and business.valid_person(entry['actor']) and analysis_approval.valid_decision_text(entry['decision']) and entry['identity_source'] in ('declared','local_profile') and analysis_approval.business_gate.valid_timestamp(entry['timestamp']) and entry['cycle']==cycle['id'],
                    'Invalid QA audit attribution/context.','E_QA_AUDIT')
            obj,frozen=artifact(epic,entry['baseline_id'])
            require(obj['action']==entry['action'] and obj['kind']==entry['kind'] and obj['analysis_baseline']==cycle['analysis_baseline'] and obj['analysis_handoff']==cycle['id'],
                    'QA audit differs from immutable artifact.','E_QA_AUDIT')
            prior=next((c for c in frozen.get('work_tracks',{}).get('cycles',[]) if c['id']==cycle['id']),None)
            require(prior is not None and prior['qa']['history']==entries[:index],
                    'QA historical decisions were rewritten.','E_QA_AUDIT')
            work_tracks.preserve_prefix(frozen,epic.metadata)
            for field in ('lifecycle','business_decisions','analysis_decisions','engineering_history'):
                prefix=frozen.get(field,[])
                require(epic.metadata.get(field,[])[:len(prefix)]==prefix,'Retained audit prefix differs from the QA snapshot.','E_QA_AUDIT')
            seen.add(entry['operation_id'])
        if entries:
            final=artifact(epic,entries[-1]['baseline_id'])[0]['payload']
            require(final['status_after']==cycle['qa']['status'],'QA status differs from retained history.','E_QA_AUDIT')


def review(epic,project):
    try:
        track=current(epic)
    except business.BusinessError as exc:
        return {'active':False,'reason':str(exc),'code':exc.code}
    drafts={}
    for kind in KINDS:
        entries=history(epic,'write',kind)
        if entries:
            entry=entries[-1];obj,_=artifact(epic,entry['baseline_id'])
            drafts[kind]={'baseline_id':entry['baseline_id'],'operation_id':entry['operation_id'],'payload':obj['payload'],'skills':obj['skills'],
                          'document':engineering.artifact_document(epic.directory,entry['baseline_id'],kind,ROOT)}
    approvals={}
    for kind,check in (('scenarios',lambda:scenario_approval(epic)),('automation',lambda:automation_approval(epic,project))):
        try:check();approvals[kind]={'valid':True}
        except business.BusinessError as exc:approvals[kind]={'valid':False,'code':exc.code,'reason':str(exc)}
    return {'active':True,'stage':track['status'],'revision':work_tracks.revision(epic,'qa',project),
            'analysis_baseline':work_tracks.active(epic)['analysis_baseline'],'analysis_handoff':work_tracks.active(epic)['id'],
            'qa_source_revision':qa_source(project),'source_revision':app_source(epic,project),
            'drafts':drafts,'approvals':approvals,'evidence':[artifact(epic,e['baseline_id'])[0]['payload'] for e in history(epic,'run','check')],
            'integration':integration_readiness(epic,project)}


def update(project,epic_id,expected_revision,operation_id,action,kind,payload,actor,decision,identity_source=None):
    import sdlc
    require(discovery.valid_revision(expected_revision) and discovery.valid_operation_id(operation_id) and business.valid_person(actor) and analysis_approval.valid_decision_text(decision),
            'Expected QA revision, operation ID, declared actor and actual decision wording.','E_UPDATE_INPUT')
    require(action in ('write','approve','request_changes','advance','run') and kind in (*KINDS,'verification','check') and isinstance(payload,dict) and identity_source in (None,'local_profile'),
            'Invalid QA operation.','E_UPDATE_INPUT')
    with sdlc.project_lock(project):
        epic=sdlc.selected_epic(project,epic_id)
        # Replay works after reopening without reactivating an old cycle.
        for cycle in epic.metadata.get('work_tracks',{}).get('cycles',[]):
            for entry in cycle['qa']['history']:
                if entry['operation_id']==operation_id:
                    obj,_=artifact(epic,entry['baseline_id']);request=deepcopy(obj['payload']['_request'])
                    if action=='write':request['content']=obj['payload']['content']
                    require(all(entry[k]==v for k,v in {'expected_revision':expected_revision,'action':action,'kind':kind,'actor':actor,'decision':decision,'identity_source':identity_source or 'declared'}.items()) and request==payload,
                            'QA operation ID was reused with changed intent.','E_IDEMPOTENCY')
                    return sdlc.result('qa-'+action,epic.diagnostics,epic=epic.payload(),qa=review(epic,project),replayed=True)
        sdlc.reject_gate_operation_reuse(epic,operation_id)
        active=work_tracks.active(epic);track=current(epic)
        work_tracks.require_reconciled(epic,'qa')
        require(epic.metadata['status']!='verified','Finalized verification is frozen; reopen upstream for a new cycle.','E_STATUS')
        require(work_tracks.revision(epic,'qa',project)==expected_revision,'QA inputs changed; review again.','E_REVISION_CONFLICT')
        stage=track['status'];target=stage;content=deepcopy(payload);source=app_source(epic,project);own_source=qa_source(project)
        if action=='write':
            require(kind in KINDS,'Unsupported QA document kind.','E_UPDATE_INPUT')
            if kind=='automation':
                require(stage in ('test_automation','ready_for_verification','verified'),'Review and advance QA scenarios before automation.','E_STATUS')
                scenario_approval(epic)
            validate_document(epic,project,kind,payload)
            if kind=='automation':
                content['engineering_design']=design_context(epic,project)
                content['scenarios_approval']=scenario_approval(epic)['baseline_id']
                target='test_automation'
            else:target='test_design'
        elif action in ('approve','request_changes'):
            require(kind in ('scenarios','automation'),'Review strategy with the scenario gate; no separate strategy approval.','E_UPDATE_INPUT')
            fields={'acknowledged','source_revision'} if action=='approve' and kind=='automation' else {'acknowledged'}
            require(set(payload)==fields and isinstance(payload['acknowledged'],list) and all(isinstance(v,str) for v in payload['acknowledged']) and len(set(payload['acknowledged']))==len(payload['acknowledged']),
                    'Invalid QA acknowledgement/source fields.','E_UPDATE_INPUT')
            if action=='request_changes':
                require(kind!='automation' or stage in ('test_automation','ready_for_verification','verified'),
                        'Automation feedback cannot advance an unapproved scenario stage.','E_STATUS')
                require(not payload['acknowledged'],'Feedback is not uncertainty acknowledgement.','E_UPDATE_INPUT')
                latest(epic,kind)
                content={'content':decision};target='test_design' if kind=='scenarios' else 'test_automation'
            elif kind=='scenarios':
                require(stage=='test_design','Scenarios are not awaiting approval.','E_STATUS')
                common.exact_acknowledgements(payload['acknowledged'],unresolved(epic),'Acknowledge all QA design uncertainty without resolving it.')
                content={'documents':scenario_context(epic),'acknowledged':payload['acknowledged'],'content':decision}
            else:
                require(stage=='test_automation','Automation is not awaiting approval.','E_STATUS')
                scenario=scenario_approval(epic);draft,doc=latest(epic,'automation')
                require(doc['scenarios_approval']==scenario['baseline_id'],'Scenarios changed; regenerate or reconcile the automation artifact.','E_APPROVAL_STALE')
                require(payload['source_revision']==own_source==doc['source_revision'],'QA code changed since the automation review.','E_REVISION_CONFLICT')
                require(doc['engineering_design']==design_context(epic,project),'Technical interfaces changed; adapt automation.','E_APPROVAL_STALE')
                common.exact_acknowledgements(payload['acknowledged'],doc['unresolved'],'Acknowledge all QA automation uncertainty without resolving it.')
                content={'draft':draft['baseline_id'],'scenarios_approval':scenario['baseline_id'],'source_revision':own_source,'acknowledged':payload['acknowledged'],'content':decision}
        elif action=='advance':
            require(not payload,'QA advancement takes no document payload.','E_UPDATE_INPUT')
            if kind=='scenarios':
                require(stage=='test_design','QA scenarios cannot advance from this stage.','E_STATUS')
                approved=scenario_approval(epic);target='test_automation'
                content={'content':decision,'approval':approved['baseline_id']}
            elif kind=='automation':
                require(stage=='test_automation','QA automation cannot advance from this stage.','E_STATUS')
                approved,_=automation_approval(epic,project);target='ready_for_verification'
                content={'content':decision,'approval':approved['baseline_id']}
            else:
                require(kind=='verification' and stage in ('ready_for_verification','verified'),'QA verification is not ready.','E_STATUS')
                require(epic.metadata['status'] in ('verification','security_review','final_verification'),'Engineering must explicitly make reviewed code available for verification.','E_INTEGRATION_NOT_READY')
                checks,context=results(epic,project);target='verified'
                content={'content':decision,'context':context,'checks':{k:v['status'] for k,v in checks.items()}}
        else:
            require(kind=='check' and set(payload)=={'check_id','source_revision'} and isinstance(payload['check_id'],str),'Choose a named QA check and the reviewed application source.','E_UPDATE_INPUT')
            require(stage in ('ready_for_verification','verified') and epic.metadata['status'] in ('verification','security_review','final_verification'),
                    'Integration/UI execution waits for both authorized tracks.','E_INTEGRATION_NOT_READY')
            require(payload['source_revision']==source,'Application source changed since execution was requested.','E_REVISION_CONFLICT')
            context=execution_context(epic,project);_,automation=latest(epic,'automation')
            checks=[c for c in automation['checks']+automation.get('limitation_checks',[]) if c['id']==payload['check_id']]
            require(len(checks)==1,'Unknown named QA check.','E_VERIFICATION')
            executed=engineering.execute_check(project,checks[0])
            require(app_source(epic,project)==source and qa_source(project)==own_source,'Check changed fingerprinted source; inspect and rerun.','E_REVISION_CONFLICT')
            content={**executed,'context':context,'check_id':checks[0]['id'],'check':checks[0],'content':executed['output']}
        content['status_after']=target
        stage_for_skill='test_design' if kind in ('strategy','scenarios') else 'test_automation' if kind=='automation' else 'verification'
        pins=domain_skills.pins(['testing'],stage_for_skill,sdlc.StrictLoader)
        stored_payload={k:v for k,v in content.items() if k!='content'}
        stored_payload['_request']={k:v for k,v in payload.items() if k!='content'}
        obj={'action':action,'kind':kind,'payload':stored_payload,'skills':pins,'analysis_baseline':active['analysis_baseline'],'analysis_handoff':active['id'],'source_revision':source}
        manifest,files=engineering.baseline_snapshot('qa',kind,action,epic_id,
            (epic.directory/'metadata.yaml').read_bytes(),obj,content.get('content','').encode('utf-8'))
        baseline=common.publish_baseline(epic.directory,ROOT,manifest,files,
            lambda m,f:common.validate_files(m,f,engineering.artifact_files(m,ROOT)),lambda bid:artifact(epic,bid))
        candidate=deepcopy(epic.metadata);destination=work_tracks.current(candidate)['qa'];destination['status']=target
        destination['history'].append({'operation_id':operation_id,'action':action,'kind':kind,'actor':actor,'identity_source':identity_source or 'declared','decision':decision,'expected_revision':expected_revision,'timestamp':business.timestamp(),'baseline_id':baseline,'cycle':active['id']})
        def read(directory):
            checked=sdlc.read_epic(directory);sdlc.require_valid(checked.diagnostics)
            if action=='run' or kind=='automation':
                require(qa_source(project)==own_source,'QA files changed while preparing the operation.','E_REVISION_CONFLICT')
            if action=='run':require(app_source(checked,project)==source,'Application changed during execution.','E_REVISION_CONFLICT')
            return checked
        common.persist_decision(epic,candidate,expected_revision,read,lambda value:work_tracks.revision(value,'qa',project),
            lambda value:(sdlc.validate_gate_metadata(value),work_tracks.validate(value)),
            lambda path,value:sdlc.atomic_history_write(path,yaml.safe_dump(value,sort_keys=False,allow_unicode=True)))
        updated=sdlc.selected_epic(project,epic_id)
        return sdlc.result('qa-'+action,updated.diagnostics,epic=updated.payload(),qa=review(updated,project),replayed=False,baseline_id=baseline)
