"""Opt-in native Git publication. Existing SDLC operations own human decisions/state.

Remote fast-forward checks serialize authority; local journals never claim push success.
No stash/reset/force push, automatic PR/merge, identity service or artifact migration.
"""
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,re,subprocess,sys,tempfile,uuid
import business_refinement as business
import runtime_management as persistence

CONFIG='.sdlc-git.yaml'
ROOT=Path(__file__).resolve().parents[2]
OID=re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
EVENTS={
 'new':'request-created','discovery-update':'discovery-evidence','discovery-complete':'discovery-completed',
 'discovery-reopen':'upstream-reopened','business-generate':'business-draft','business-revise':'business-refinement',
 'business-approve':'business-approved','business-request-changes':'business-feedback','business-advance':'business-advanced',
 'analysis-generate':'analysis-draft','analysis-revise':'analysis-refinement','analysis-approve':'analysis-approved',
 'analysis-request-changes':'analysis-feedback','analysis-advance':'analysis-advanced',
 'engineering-write':'engineering-artifact','engineering-approve':'engineering-approved',
 'engineering-request-changes':'engineering-feedback','engineering-advance':'engineering-advanced',
 'development-start':'development-started','check-run':'engineering-evidence','engineering-finalize':'engineering-verified',
 'qa-write':'qa-artifact','qa-approve':'qa-approved','qa-request-changes':'qa-feedback',
 'qa-advance':'qa-advanced','qa-check-run':'qa-evidence','assign':'assignment','ownership-initialize':'ownership',
 'tracks-adopt':'tracks-adopted','track-reconcile':'track-reconciled','runtime-bind':'runtime-bound','runtime-promote':'runtime-promoted',
 'security-remediate':'security-remediation','verification-remediate':'verification-remediation'}
CLOSED={'published','working_published','abandoned','rejected'}


def require(value,message,code='E_GIT',file=CONFIG):
    business.require(value,code,message,str(file))


def now():return datetime.now(timezone.utc).isoformat()


def git(project,*args,allowed=(0,)):
    env={k:v for k,v in os.environ.items() if k not in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE')}
    env.update(GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
    try:run=subprocess.run(['git','--literal-pathspecs','-C',str(project),*map(str,args)],capture_output=True,env=env,timeout=45)
    except (OSError,subprocess.TimeoutExpired) as exc:require(False,'Git is unavailable or timed out; files were not reset/stashed.','E_GIT_TRANSPORT')
    require(run.returncode in allowed,'Git '+str(args[0])+' failed. Inspect connectivity, authentication, policy/hooks or conflicts; no automatic resolution.','E_GIT_COMMAND')
    return run.stdout.decode('utf-8')


def config(project):
    path=Path(project)/CONFIG
    if not path.exists() and not path.is_symlink():return None
    require(path.is_file() and not path.is_symlink(),'Expected a regular Git workflow configuration.')
    import yaml
    from sdlc import StrictLoader
    try:data=yaml.load(path.read_text(),Loader=StrictLoader)
    except (OSError,UnicodeError,yaml.YAMLError,RecursionError) as exc:require(False,str(exc),'E_GIT_CONFIG')
    require(isinstance(data,dict) and set(data)=={'schema_version','remote','integration_branch','policy'} and data['schema_version']=='0.1'
            and data['policy'] in ('direct','pull_request'),'Invalid Git workflow configuration.','E_GIT_CONFIG')
    for key in ('remote','integration_branch'):
        require(isinstance(data[key],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*',data[key]),'Unsafe remote/branch.','E_GIT_CONFIG')
    require(Path(git(project,'rev-parse','--show-toplevel').strip()).resolve()==Path(project).resolve(),'Use the application repository root.','E_GIT_REPOSITORY')
    git(project,'check-ref-format','--branch',data['integration_branch'])
    url=git(project,'remote','get-url',data['remote']).strip()
    from urllib.parse import urlsplit
    if url.startswith(('http:','https:')):require(urlsplit(url).username is None,'Do not put credentials in remote URLs.','E_GIT_CONFIG')
    return data


def branch(project):return git(project,'symbolic-ref','--short','HEAD').strip()
def head(project):return git(project,'rev-parse','--verify','HEAD^{commit}').strip()
def ref(c):return 'refs/remotes/'+c['remote']+'/'+c['integration_branch']


def fetch(project,c,selected=None):
    target=selected or c['integration_branch'];require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*',target),'Unsafe branch.')
    git(project,'fetch','--no-tags',c['remote'],'refs/heads/'+target+':refs/remotes/'+c['remote']+'/'+target)
    return git(project,'rev-parse','refs/remotes/'+c['remote']+'/'+target).strip()


def oid(value):require(isinstance(value,str) and OID.fullmatch(value),'Use an immutable full commit OID, never HEAD or a branch.','E_GIT_BASELINE');return value


def safe(path):
    require(isinstance(path,str) and path and not path.startswith(('/','-')) and '\\' not in path and all(p not in ('','.','..','.git') for p in path.split('/')),'Unsafe authorized path.','E_GIT_SCOPE')
    return path


def within(path,scopes):return any(path==s or path.startswith(s+'/') for s in scopes)


def index_clean(project):require(not git(project,'diff','--cached','--name-only').strip(),'Pre-existing staged files must remain untouched.','E_GIT_INDEX')
def clean(project):index_clean(project);require(not git(project,'status','--porcelain=v1','--untracked-files=all').strip(),'Dirty workspace: preserve work and inspect; no automatic stash/cleanup.','E_GIT_DIRTY')


def tree(project,commit,scopes=()):
    oid(commit);require(git(project,'cat-file','-t',commit).strip()=='commit','Baseline must identify a commit object, not a tree, tag or blob.','E_GIT_BASELINE');result={}
    for line in git(project,'ls-tree','-r','-z',commit,*(['--',*scopes] if scopes else [])).split('\0'):
        if line:
            prefix,name=line.split('\t',1);mode,kind,value=prefix.split()
            require(mode in ('100644','100755') and kind=='blob','Unsupported Git symlink/submodule in bound scope.','E_GIT_PATH',name)
            result[name]={'oid':value,'mode':mode}
    return result


def working(project,scopes):
    result={}
    for name in scopes:
        p=project/safe(name)
        candidates=list(p.rglob('*')) if p.is_dir() else [p]
        for candidate in candidates:
            require(not any(v.is_symlink() for v in (candidate,*candidate.parents)),'Source symlinks are unsupported.','E_GIT_PATH',candidate)
            if candidate.is_file():
                key=candidate.relative_to(project).as_posix()
                result[key]={'oid':git(project,'hash-object','--no-filters','--',key).strip(),'mode':'100755' if candidate.stat().st_mode&0o111 else '100644'}
    return result


def source(project,commit=None):
    if commit:values=tree(project,commit)
    else:
        import engineering
        values=working(project,[n for n in engineering.tree(project) if not n.startswith('qa/')])
    return {n:v for n,v in values.items() if not n.startswith(('requirements/','qa/'))}


def state_root(project):
    root=Path(os.environ.get('SDLC_GIT_STATE_ROOT',str(Path.home()/'.local/share/ai-sdlc/git-operations'))).expanduser().absolute()
    require(root.resolve()==root and not any(p.is_symlink() or (p/'.git').exists() for p in (root,*root.parents)),'Git operation journals must be outside repositories, nonsymlink and owned.','E_GIT_PATH',root)
    require(not root.exists() or root.stat().st_uid==os.getuid(),'Journal root belongs to another user.','E_GIT_PATH',root)
    return root/persistence.install.digest(str(project.resolve()).encode())


def records(project):
    root=state_root(project)
    return [persistence.read_json(p) for p in sorted(root.glob('*.json'))] if root.exists() else []


def save(project,record,state=None):
    if state:
        record['state']=state;record['history'].append({'state':state,'time':now()})
    persistence.atomic(state_root(project)/(record['id']+'.json'),persistence.install.canonical(record))


@contextmanager
def lock(project):
    root=state_root(project);root.mkdir(parents=True,exist_ok=True);os.chmod(root,0o700);p=root/'.busy'
    try:p.mkdir()
    except FileExistsError:require(False,'Another Git operation may be active; inspect an abandoned lock before retrying.','E_GIT_BUSY',p)
    try:yield
    finally:p.rmdir()


def read_record(project,operation):
    require(isinstance(operation,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',operation),'Invalid operation ID.','E_GIT_INPUT')
    return persistence.read_json(state_root(project)/(operation+'.json'))


def authority_view(project):
    c=config(project)
    if c is None:return None
    pending=[{'id':r['id'],'state':r['state'],'commit':r.get('commit')} for r in records(project) if r['state'] not in CLOSED]
    return {'integration_branch':c['integration_branch'],'local_branch':branch(project),'pending':pending,
            'authoritative':False,'fresh_fetch_required':True,'message':'Local view; fetch/CAS and publication verification are required before consequential actions.'}


@contextmanager
def guard(project):
    c=config(project)
    if c is None:yield;return
    operation=os.environ.get('SDLC_GIT_OPERATION');require(operation,'Configured Git workflow requires git_collaboration.py run; a local decision is not remote authority.','E_GIT_REQUIRED')
    record=read_record(project,operation)
    require(record['project']==str(project.resolve()) and record['nonce']==os.environ.get('SDLC_GIT_NONCE') and record['state']=='prepared','Wrong or inactive Git operation context.','E_GIT_CONTEXT')
    require(c==record['config'] and git(project,'remote','get-url',c['remote']).strip()==record['repository'],'Publication repository/configuration changed.','E_GIT_CONFIG')
    require(branch(project)==record['branch'] and fetch(project,c)==record['authority'],'Authoritative state changed; re-review before writing.','E_GIT_STALE')
    import runtime_selection
    call=runtime_selection.CALL.get()
    require(call is not None and call['operation']==record['spec']['cli'][0],'Git context cannot authorize a different operation.','E_GIT_CONTEXT')
    yield


def status(project):
    c=config(project);require(c is not None,'Explicitly configure Git collaboration first.','E_GIT_CONFIG')
    return {'configuration':c,'head':head(project),'branch':branch(project),'operations':records(project),'authority':authority_view(project)}


def sync(project):
    c=config(project);require(c is not None,'Missing Git configuration.');clean(project)
    require(not any(r['state'] not in CLOSED for r in records(project)),'Finish pending publication before phase-start synchronization.','E_GIT_PENDING')
    target=fetch(project,c)
    require(branch(project)==c['integration_branch'],'Feature work needs explicit impact review; no automatic rebase or merge.','E_GIT_BRANCH')
    git(project,'merge','--ff-only',target)
    return {'head':head(project),'fetched_authority':target,'message':'Synchronized only; no SDLC approval, advancement or start.'}


def metadata_equal(project,request,authority):
    if request is None:return
    import sdlc
    epic=sdlc.selected_epic(project,request);path=(epic.directory/'metadata.yaml').relative_to(project).as_posix()
    require(working(project,[path])==tree(project,authority,[path]),'Local lifecycle/approval metadata differs from authoritative remote; impact review and reconciliation required.','E_GIT_STALE',path)


def changes(project):
    return set(filter(None,(git(project,'diff','--name-only','--no-renames','-z')+git(project,'ls-files','--others','--exclude-standard','-z')).split('\0')))


def input_pins(project,cli):
    result={}
    for i,arg in enumerate(cli[:-1]):
        if arg in ('--input-file','--document-file','--changes-file','--feedback-file','--idea-details-file'):
            path=Path(cli[i+1]).absolute();result[str(path)]=git(project,'hash-object','--no-filters','--',str(path)).strip()
    return result


def apply(project,record):
    spec=record['spec'];cli=spec['cli']
    for path,value in record['inputs'].items():require(git(project,'hash-object','--no-filters','--',path).strip()==value,'Original input changed; do not retry a changed human decision.','E_GIT_INPUT')
    env={**os.environ,'SDLC_GIT_OPERATION':record['id'],'SDLC_GIT_NONCE':record['nonce'],'PYTHONDONTWRITEBYTECODE':'1'}
    command=[sys.executable,'-B',str(ROOT/'orchestrator/scripts/sdlc.py'),'--project',str(project)]
    if spec.get('runtime_session'):command+=['--runtime-session',spec['runtime_session']]
    try:
        run=subprocess.run(command+cli,capture_output=True,text=True,env=env,timeout=180)
        result=json.loads(run.stdout)
    except (OSError,ValueError,subprocess.TimeoutExpired):save(project,record,'operation_uncertain');require(False,'CLI outcome is uncertain; inspect original operation/core recovery before retrying.','E_GIT_OPERATION')
    require(isinstance(result,dict),'CLI returned an unexpected JSON shape.','E_GIT_OPERATION')
    if not result.get('ok') or run.returncode:
        record['diagnostics']=result.get('diagnostics',[])
        save(project,record,'operation_uncertain' if changes(project) else 'rejected')
        require(False,'SDLC operation did not complete; inspect diagnostics/core recovery. No Git approval/publication claimed.','E_GIT_OPERATION')
    if spec.get('tested_commit'):
        require(source(project,spec['tested_commit'])==source(project),'Execution changed the pinned implementation; preserve evidence but rerun/revalidate.','E_GIT_TESTED')
    if cli[0]=='new':
        directory=Path(result['epic']['directory']);require(directory.parent==project/'requirements','Invalid new request scope.')
        record['scopes']=[directory.relative_to(project).as_posix()];record['request_id']=result['epic']['metadata']['id']
        record['before']=tree(project,record['head'],record['scopes'])
    record['event_id']=result.get('decision_id') or (cli[cli.index('--operation-id')+1] if '--operation-id' in cli else record['id'])
    record['local_result']={'operation':result['operation'],'ok':True}
    record['after']=working(project,record['scopes'])
    require(changes(project)<=set(record['after'])|set(record['before']),'CLI changed an unauthorized path; preserve and inspect.','E_GIT_SCOPE')
    save(project,record,'local_applied')


def staged_snapshot(project,paths):
    result={}
    for line in git(project,'ls-files','--stage','-z','--',*paths).split('\0'):
        if line:
            prefix,name=line.split('\t',1);mode,value,stage=prefix.split();require(stage=='0','Unmerged index.','E_GIT_CONFLICT');result[name]={'oid':value,'mode':mode}
    return result


def message(record):
    text=f"sdlc({record['request_id'] or 'project'}): {record['event']}\n\nSDLC-Operation: {record['id']}\nSDLC-Event: {record['event_id']}\nSDLC-Authority-Base: {record['authority']}\n"
    if record['spec'].get('tested_commit'):text+='SDLC-Tested-Commit: '+record['spec']['tested_commit']+'\n'
    return text


def commit(project,record):
    require(head(project)==record['head'],'Checkout changed before committing.','E_GIT_COMMIT')
    require(working(project,record['scopes'])==record['after'],'Working artifacts changed after the recorded decision.','E_GIT_BYTES')
    paths=sorted(n for n in record['before'].keys()|record['after'].keys() if record['before'].get(n)!=record['after'].get(n))
    require(bool(paths),'No changes to publish; no empty authority event is invented.','E_GIT_EMPTY')
    index_clean(project)
    # Exact filenames, never add . or a directory. Ignored evidence fails rather than
    # silently disappearing; the operator must explicitly reconcile repository policy.
    git(project,'add','--',*paths)
    staged=set(filter(None,git(project,'diff','--cached','--name-only','-z').split('\0')))
    require(staged==set(paths),'Staged paths differ; preserve the index for inspection.','E_GIT_INDEX')
    require(staged_snapshot(project,paths)=={n:record['after'][n] for n in paths if n in record['after']},'Git filters/line endings changed approved bytes; resolve attributes explicitly.','E_GIT_BYTES')
    git(project,'diff','--cached','--check')
    record['paths']=paths;record['staged_summary']=git(project,'diff','--cached','--stat');save(project,record,'commit_pending')
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=state_root(project),delete=True) as f:
        f.write(message(record));f.flush();git(project,'commit','--cleanup=verbatim','-F',f.name)
    record['commit']=head(project)
    verify_commit(project,record)
    save(project,record,'committed')


def verify_commit(project,record):
    commit=oid(record['commit'])
    require(git(project,'rev-parse',commit+'^').strip()==record['head'],'Commit has an unexpected parent.','E_GIT_COMMIT')
    paths=set(filter(None,git(project,'diff','--name-only','--no-renames','-z',record['head'],commit).split('\0')))
    require(paths==set(record['paths']) and tree(project,commit,record['scopes'])==record['after'],'Commit/hook changed recorded files; do not publish.','E_GIT_COMMIT')
    message=git(project,'show','-s','--format=%B',commit)
    require('\nSDLC-Operation: '+record['id']+'\n' in '\n'+message,'Commit correlation is missing.','E_GIT_COMMIT')


def published(project,record,tip):
    state='working_published' if record['kind']=='working' else 'pr_pending' if record['config']['policy']=='pull_request' else 'published'
    record['reference']={'repository':git(project,'remote','get-url',record['config']['remote']).strip(),'commit':record['commit'],
                         'path':next((n for n in record['paths'] if n.endswith('/metadata.yaml')),record['paths'][0]),'event_id':record['event_id']}
    record['remote_tip']=tip;save(project,record,state)
    return view(record)


def push(project,record):
    c=config(project);require(c==record['config'] and git(project,'remote','get-url',c['remote']).strip()==record['repository'],'Git publication repository/configuration changed.','E_GIT_CONFIG')
    verify_commit(project,record)
    current=fetch(project,c)
    # Recover a successful push even if the process stopped before journaling it.
    if record['state']=='push_pending':
        target=current if record['branch']==c['integration_branch'] else None
        if target is None and git(project,'ls-remote','--heads',c['remote'],'refs/heads/'+record['branch']).strip():
            target=fetch(project,c,record['branch'])
        if target and git_ancestor(project,record['commit'],target):
            return published(project,record,target)
    require(current==record['authority'],'Remote authority changed; keep the local commit and obtain fresh review/reconciliation.','E_GIT_STALE')
    require(head(project)==record['commit'] and branch(project)==record['branch'],'Checkout changed since commit.','E_GIT_COMMIT')
    clean(project)
    if record['spec'].get('tested_commit'):require(source(project,record['spec']['tested_commit'])==source(project),'Implementation changed; evidence must be revalidated.','E_GIT_TESTED')
    save(project,record,'push_pending')
    git(project,'push',c['remote'],record['commit']+':refs/heads/'+record['branch'])
    tip=fetch(project,c,record['branch'])
    require(git_ancestor(project,record['commit'],tip),'Remote does not contain the operation commit.','E_GIT_COMMIT')
    return published(project,record,tip)


def git_ancestor(project,ancestor,descendant):
    # git helper returns stdout; --is-ancestor communicates through exit status.
    return git(project,'merge-base',ancestor,descendant).strip()==ancestor


def view(record):
    return {'operation_id':record['id'],'state':record['state'],'authoritative':record['state']=='published',
            'commit':record.get('commit'),'reference':record.get('reference'),'tested_commit':record['spec'].get('tested_commit'),
            'message':'Published authority verified.' if record['state']=='published' else 'Working/proposed/pending material; not authoritative SDLC approval or advancement.'}


def execute(project,spec,kind='run'):
    c=config(project);require(c is not None,'Configure Git collaboration explicitly.','E_GIT_CONFIG')
    required={'operation_id','expected_authority','allowed_paths','request_id'}|({'cli'} if kind=='run' else set())
    require(isinstance(spec,dict) and required<=set(spec)<=required|{'tested_commit','runtime_session'},'Invalid publication request.','E_GIT_INPUT')
    import discovery_history
    require(discovery_history.valid_operation_id(spec['operation_id']) and isinstance(spec['allowed_paths'],list) and bool(spec['allowed_paths']),'Invalid ID/scopes.','E_GIT_INPUT')
    require(all(isinstance(p,str) for p in spec['allowed_paths']),'Scopes must be strings.','E_GIT_INPUT')
    if kind=='run':require(isinstance(spec['cli'],list) and bool(spec['cli']) and all(isinstance(v,str) for v in spec['cli']) and spec['cli'][0] in EVENTS,'Unsupported SDLC operation.','E_GIT_INPUT')
    import sdlc
    require(spec['request_id'] is None or sdlc.valid_id(spec['request_id']),'Use a valid stable request ID.','E_GIT_INPUT')
    if kind=='run':
        require(spec['request_id'] is None if spec['cli'][0]=='new' else len(spec['cli'])>1 and spec['cli'][1]==spec['request_id'],
                'CLI and publication request must identify the same request.','E_GIT_INPUT')
    scopes=[safe(p.rstrip('/')) for p in spec['allowed_paths']]
    require(not any(p in (CONFIG,'qa','requirements') for p in scopes) or kind=='run' and spec['cli'][0]=='new' and scopes==['requirements'],'Authorize bounded request/files, not project namespaces.','E_GIT_SCOPE')
    with lock(project):
        existing=next((r for r in records(project) if r['id']==spec['operation_id']),None)
        if existing:
            require(existing['spec']==spec and existing['kind']==kind,'Operation ID reused with changed intent.','E_IDEMPOTENCY')
            return resume(project,existing)
        require(not any(r['state'] not in CLOSED for r in records(project)),'Resolve pending publication before another operation.','E_GIT_PENDING')
        index_clean(project)
        if kind=='run':clean(project)
        authority=fetch(project,c);require(authority==oid(spec['expected_authority']),'Authoritative remote changed; re-review.','E_GIT_STALE')
        metadata_equal(project,spec['request_id'],authority)
        require(tree(project,head(project),['requirements'])==tree(project,authority,['requirements']),'Working branches cannot carry independent lifecycle history.','E_GIT_STALE')
        selected=branch(project)
        if kind=='run':
            require((selected==c['integration_branch'])==(c['policy']=='direct'),'Direct authority requires its integration checkout; protected policy requires a proposal branch.','E_GIT_BRANCH')
            if selected==c['integration_branch']:require(head(project)==authority,'Synchronize at a safe phase boundary; do not pull mid-decision.','E_GIT_STALE')
            git(project,'merge-base','--is-ancestor',authority,head(project))
            require(all(s.startswith('requirements/') or s=='requirements' and spec['cli'][0]=='new' or s.startswith('qa/') for s in scopes),'SDLC operations publish request/QA records only.','E_GIT_SCOPE')
        else:
            require(selected!=c['integration_branch'],'Publish work on an explicit workstream branch.','E_GIT_BRANCH')
            require(not any(s.startswith('requirements/') for s in scopes),'Working publication cannot create authoritative lifecycle/approval copies.','E_GIT_AUTHORITY')
            require(git_ancestor(project,authority,head(project)),'Work must consume current authoritative history.','E_GIT_STALE')
            require(changes(project) and all(within(p,scopes) for p in changes(project)),'Unrelated dirty paths are not authorized.','E_GIT_DIRTY')
        tested=spec.get('tested_commit')
        if kind=='run' and spec['cli'][0] in ('qa-check-run','check-run'):require(tested is not None,'Evidence requires an exact tested commit/build reference.','E_GIT_TESTED')
        if tested:require(source(project,oid(tested))==source(project),'Working implementation differs from tested commit; rerun/revalidate.','E_GIT_TESTED')
        record={'schema_version':'0.1','id':spec['operation_id'],'project':str(project.resolve()),'config':c,'kind':kind,'spec':spec,
                'repository':git(project,'remote','get-url',c['remote']).strip(),'authority':authority,'head':head(project),'branch':selected,'scopes':scopes,'request_id':spec['request_id'],
                'event':EVENTS[spec['cli'][0]] if kind=='run' else 'working-material','event_id':spec['operation_id'],
                'nonce':uuid.uuid4().hex,'history':[],'state':'prepared','inputs':input_pins(project,spec['cli']) if kind=='run' else {},
                'before':tree(project,head(project),scopes)}
        save(project,record,'prepared')
        if kind=='run':apply(project,record)
        else:record['after']=working(project,scopes);save(project,record,'local_applied')
        return resume(project,record)


def resume(project,record):
    if record['state'] in CLOSED or record['state']=='pr_pending':return view(record)
    if record['state'] in ('prepared','operation_uncertain'):
        require(record['kind']=='run' and record['spec']['cli'][0]!='new','Uncertain initial creation needs explicit inspection/core recovery; never create a duplicate.','E_GIT_OPERATION')
        save(project,record,'prepared');apply(project,record)
    if record['state']=='local_applied':commit(project,record)
    if record['state']=='commit_pending':
        candidates=[]
        for value in git(project,'rev-list',record['head']+'..HEAD').splitlines():
            if '\nSDLC-Operation: '+record['id']+'\n' in '\n'+git(project,'show','-s','--format=%B',value):candidates.append(value)
        require(len(candidates)<=1,'Ambiguous commit correlation.','E_GIT_COMMIT')
        if candidates:record['commit']=candidates[0];verify_commit(project,record);save(project,record,'committed')
        else:
            # Index may contain only the exact recorded operation's pending files.
            staged=set(filter(None,git(project,'diff','--cached','--name-only','-z').split('\0')))
            require(staged==set(record['paths']),'Unrelated index edits block recovery.','E_GIT_INDEX')
            require(head(project)==record['head'] and working(project,record['scopes'])==record['after'],'Checkout or files changed during interruption.','E_GIT_BYTES')
            require(staged_snapshot(project,record['paths'])=={n:record['after'][n] for n in record['paths'] if n in record['after']},'Staged bytes changed during interruption.','E_GIT_BYTES')
            # Reuse the original intent and native commit; do not unstage or reset.
            git(project,'diff','--cached','--check')
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=state_root(project)) as f:
                f.write(message(record));f.flush();git(project,'commit','--cleanup=verbatim','-F',f.name)
            record['commit']=head(project);verify_commit(project,record);save(project,record,'committed')
    return push(project,record)


def recover(project,operation):
    with lock(project):return resume(project,read_record(project,operation))


def confirm(project,operation):
    with lock(project):
        record=read_record(project,operation);c=config(project)
        require(c==record['config'] and git(project,'remote','get-url',c['remote']).strip()==record['repository'],'Git publication repository/configuration changed.','E_GIT_CONFIG')
        if record['state']=='published':return view(record)
        require(record['state']=='pr_pending','No pending protected-branch proposal.','E_GIT_PENDING')
        tip=fetch(project,c);commit=record['commit'];git(project,'merge-base','--is-ancestor',commit,tip)
        if tip!=commit:
            parents=git(project,'show','-s','--format=%P',tip).split()
            require(len(parents)==2 and parents[0]==record['authority'] and parents[1]==commit,'Integration changed authority since review; re-review/reconciliation required. Squash/rebase is not inferred.','E_GIT_STALE')
        require(tree(project,tip,record['scopes'])==record['after'],'Integrated record differs from the reviewed proposal.','E_GIT_BYTES')
        require(source(project,tip)==source(project,commit),'Integration changed implementation inputs.','E_GIT_TESTED')
        record['integration_commit']=tip;save(project,record,'published');return view(record)


def abandon(project,operation,actor,decision):
    with lock(project):
        record=read_record(project,operation)
        require(record['state'] not in CLOSED,'Completed operations cannot be abandoned.','E_GIT_PENDING')
        require(isinstance(actor,str) and actor.strip() and isinstance(decision,str) and decision.strip(),'Supply the actual declared actor and explicit recovery decision.','E_GIT_INPUT')
        # Preserve every local artifact/commit/index and original journal entry.
        record['abandonment']={'actor':actor,'decision':decision,'time':now(),'identity_source':'explicit_declaration'}
        save(project,record,'abandoned');return view(record)


def integration_check(project,commit,expected):
    """Advisory only; native integration still needs protected expected-base policy."""
    c=config(project);require(c is not None,'Missing Git configuration.','E_GIT_CONFIG')
    authority=fetch(project,c);require(authority==oid(expected),'Authority changed; impact review/reconciliation required.','E_GIT_STALE')
    commit=oid(commit);message=git(project,'show','-s','--format=%B',commit)
    require('\nSDLC-Authority-Base: '+authority+'\n' in '\n'+message,'Working output consumed another lifecycle revision.','E_GIT_STALE')
    require(git_ancestor(project,authority,commit),'Working output does not descend from current authority.','E_GIT_STALE')
    require(tree(project,commit,['requirements'])==tree(project,authority,['requirements']),'Working output changes authoritative approvals/lifecycle.','E_GIT_AUTHORITY')
    return {'commit':commit,'expected_authority':authority,'eligible_at_fetch':True,'integrated':False,
            'message':'Read-only check. Integrate only with an expected-base protected review; recheck before native merge/publication. A clean merge is not semantic approval.'}


def baseline(project,commit,path,event,compare=False):
    oid(commit);safe(path);bound=tree(project,commit,[path]);require(path in bound,'Artifact is absent from the commit.','E_GIT_BASELINE')
    require(path.startswith('requirements/') and len(Path(path).parts)>=3,'Use a request-local artifact path.','E_GIT_BASELINE')
    metadata='/'.join(Path(path).parts[:2])+'/metadata.yaml'
    import yaml
    from sdlc import StrictLoader
    try:data=yaml.load(git(project,'show',commit+':'+metadata),Loader=StrictLoader)
    except (yaml.YAMLError,RecursionError):require(False,'Malformed committed metadata.','E_GIT_BASELINE',metadata)
    def events(value):
        if isinstance(value,dict):
            if any(k in ('id','operation_id') and v==event for k,v in value.items()):yield value
            for child in value.values():yield from events(child)
        elif isinstance(value,list):
            for child in value:yield from events(child)
    matched=list(events(data));message_text=git(project,'show','-s','--format=%B',commit)
    require(isinstance(event,str) and bool(event),'Invalid event ID.','E_GIT_BASELINE')
    require(matched or '\nSDLC-Event: '+event+'\n' in '\n'+message_text,'Approval/event is absent; Git authorship is not approval.','E_GIT_BASELINE')
    approvals=[e for e in matched if e.get('action')=='approve']
    if approvals and path!=metadata:
        prefix='/'.join(Path(metadata).parts[:2])
        candidates=[]
        for entry in approvals:
            for namespace in ('business-baselines','analysis-baselines','engineering-baselines','qa-baselines'):
                bid=entry.get('baseline_id')
                if not isinstance(bid,str):continue
                folder=prefix+'/'+namespace+'/'+bid
                objects=tree(project,commit,[folder]);candidates+=list(objects.values())
                artifact=folder+'/artifact.json'
                if artifact in objects:
                    obj=json.loads(git(project,'show',commit+':'+artifact))
                    require(isinstance(obj,dict) and isinstance(obj.get('payload'),dict),'Invalid committed approval artifact.','E_GIT_BASELINE')
                    draft=obj['payload'].get('draft')
                    if isinstance(draft,str) and re.fullmatch('[0-9a-f]{64}',draft):
                        candidates+=list(tree(project,commit,[prefix+'/'+namespace+'/'+draft]).values())
        require(bound[path] in candidates,'Artifact bytes are not in this approval baseline. Use the immutable approved path.','E_GIT_BASELINE')
    if compare:require(working(project,[path])==bound,'Working artifact differs from approved Git object.','E_GIT_BYTES')
    return {'repository':git(project,'remote','get-url',config(project)['remote']).strip(),'commit':commit,'path':path,'event_id':event,'git_object':bound[path],'binding':'approval' if approvals else 'event','identity':'declared; Git authorship is not authentication'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,required=True);sub=parser.add_subparsers(dest='action',required=True)
    for name in ('status','sync','run','publish','recover','confirm','abandon','integration-check','baseline'):
        p=sub.add_parser(name)
        if name in ('run','publish'):p.add_argument('--request-file',type=Path,required=True)
        if name in ('recover','confirm','abandon'):p.add_argument('--operation-id',required=True)
        if name=='abandon':p.add_argument('--actor',required=True);p.add_argument('--decision',required=True)
        if name=='integration-check':p.add_argument('--commit',required=True);p.add_argument('--expected-authority',required=True)
        if name=='baseline':
            p.add_argument('--commit',required=True);p.add_argument('--path',required=True);p.add_argument('--event-id',required=True);p.add_argument('--compare',action='store_true')
    args=parser.parse_args(argv);project=args.project.resolve()
    import sdlc
    spec={}
    try:
        if args.action in ('run','publish'):
            spec=persistence.read_json(args.request_file);value=execute(project,spec,'run' if args.action=='run' else 'working')
        elif args.action in ('recover','confirm'):value=globals()[args.action](project,args.operation_id)
        elif args.action=='abandon':value=abandon(project,args.operation_id,args.actor,args.decision)
        elif args.action=='integration-check':value=integration_check(project,args.commit,args.expected_authority)
        elif args.action=='baseline':value=baseline(project,args.commit,args.path,args.event_id,args.compare)
        else:value=globals()[args.action](project)
        output={'ok':True,'operation':'git-'+args.action,'diagnostics':[],**value}
    except sdlc.Rejected as exc:
        from dataclasses import asdict
        output={'ok':False,'operation':'git-'+args.action,'diagnostics':[asdict(d) for d in exc.diagnostics]}
    except (business.BusinessError,persistence.install.InstallError,OSError,ValueError,KeyError,TypeError,IndexError,RecursionError) as exc:
        output={'ok':False,'operation':'git-'+args.action,'diagnostics':[{'severity':'error','code':getattr(exc,'code','E_GIT_IO'),'file':getattr(exc,'filename',str(project/CONFIG)),'message':str(exc)}]}
        if args.action in ('run','publish','recover','confirm'):
            try:
                record=read_record(project,spec['operation_id'] if args.action in ('run','publish') else args.operation_id)
                output['publication']=view(record)
            except (business.BusinessError,persistence.install.InstallError,OSError,ValueError,KeyError,TypeError):pass
    print(json.dumps(output,ensure_ascii=False));return 0 if output['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
