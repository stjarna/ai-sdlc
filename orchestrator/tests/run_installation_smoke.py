"""Standalone disposable installation smoke; no model turns or real application approvals.

Creates fixture-only Git commits in a fresh external directory. Never changes the
implementation repository, real user skill registrations, credentials or identity.
Use --codex-probe for actual local native discovery; its result is not a visual IDE test.
"""
from pathlib import Path
import argparse,hashlib,json,os,queue,shutil,signal,subprocess,sys,tempfile,threading,time
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'orchestrator/scripts'))
import install,adoption

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-working-tree',action='store_true')
    parser.add_argument('--codex-probe',action='store_true',help='Query only the local Codex skills/list endpoint; never start a model turn')
    parser.add_argument('--output',type=Path,help='New external evidence directory; must not exist')
    args=parser.parse_args(argv)
    if args.output:
     area=args.output.expanduser().resolve()
     install.outside_repository(area,repo)
     area.mkdir(parents=True,exist_ok=False)
    else:area=Path(tempfile.mkdtemp(prefix='sdlc-external-install-smoke-')).resolve()
    assert not area.is_relative_to(repo), 'Keep smoke fixtures outside the implementation checkout'
    app=area/'independent-application';app.mkdir();(area/'evidence').mkdir()
    (app/'app.py').write_text('def list_items():\n    return []\n')
    (app/'test_app.py').write_text('from app import list_items\ndef test_empty_items():\n    assert list_items()==[]\n')
    (app/'AGENTS.md').write_text('Existing application instructions: preserve existing tests and source.\n')
    def git(*args):
     result=subprocess.run(['git','-C',str(app),*args],capture_output=True,text=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_NOSYSTEM':'1','GIT_AUTHOR_NAME':'Fictional smoke fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fictional smoke fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'})
     assert result.returncode==0,result.stderr
     return result.stdout
    # This commit constructs an isolated test fixture, never an application/user approval.
    git('init','-q');git('add','.');git('commit','-qm','Fictional pre-adoption application fixture')
    def hashes(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    before=hashes(app);head=git('rev-parse','HEAD').strip()
    home=area/'isolated-home';skills=home/'.agents/skills'
    result=install.install(repo,'HEAD',app,area/'runtimes',skills,sys.executable,args.preview_working_tree)
    runtime=Path(result['runtime'])
    (area/'evidence/install.json').write_text(json.dumps(result,indent=2))
    verified=install.verify(runtime,result['snapshot_digest'],skills)
    (area/'evidence/verify.json').write_text(json.dumps(verified,indent=2))
    preflight=adoption.preflight(app,runtime,skills)
    (area/'evidence/preflight.json').write_text(json.dumps(preflight,indent=2))
    assert preflight['ready'] and preflight['baseline_ready'],preflight
    assert hashes(app)==before
    codex=shutil.which('codex');native={'available':bool(codex),'model_turn_started':False,'external_ai_api_called_by_probe':False}
    if codex and args.codex_probe:
     codehome=home/'.codex';codehome.mkdir(parents=True)
     env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','LC_ALL','TMPDIR')}
     env.update(HOME=str(home),CODEX_HOME=str(codehome))
     stderr=(area/'evidence/codex-stderr.txt').open('w')
     process=subprocess.Popen([codex,'app-server','--listen','stdio://'],cwd=app,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,start_new_session=True)
     messages=queue.Queue();transcript=[]
     def reader():
      for line in process.stdout:
       try:messages.put(json.loads(line))
       except ValueError:messages.put({'unparsed':line})
     threading.Thread(target=reader,daemon=True).start()
     def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
     def response(identifier):
      deadline=time.monotonic()+40
      while time.monotonic()<deadline:
       try:value=messages.get(timeout=.5)
       except queue.Empty:
        if process.poll() is not None:raise RuntimeError('Local app-server exited: '+str(process.returncode))
        continue
       transcript.append(value)
       if value.get('id')==identifier:return value
      raise TimeoutError('Local skill discovery timed out')
     try:
      send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'sdlc_acceptance','version':'0.1.0'},'capabilities':{'experimentalApi':True}}})
      initial=response(1);assert 'error' not in initial,initial
      send({'method':'initialized','params':{}})
      send({'id':2,'method':'skills/list','params':{'cwds':[str(app)],'forceReload':True}})
      listing=response(2);assert 'error' not in listing,listing
      found=[skill for data in listing['result']['data'] for skill in data['skills'] if skill['name']=='sdlc']
      native.update(version=subprocess.check_output([codex,'--version'],text=True).strip(),skills=found)
      native['discovered']=any(Path(s.get('path','')).resolve()==(skills/'sdlc/SKILL.md').resolve() and s.get('enabled',True) for s in found)
      assert native['discovered'],listing
     finally:
      try:os.killpg(process.pid,signal.SIGTERM)
      except ProcessLookupError:pass
      try:process.wait(timeout=5)
      except subprocess.TimeoutExpired:
       os.killpg(process.pid,signal.SIGKILL);process.wait()
      stderr.close();(area/'evidence/codex-protocol.json').write_text(json.dumps(transcript,indent=2))
    assert hashes(app)==before,'Installation/preflight/discovery changed the application or Git metadata'
    (area/'evidence/native-discovery.json').write_text(json.dumps(native,indent=2))
    command=[sys.executable,'-B',str(runtime/'orchestrator/scripts/sdlc.py'),'--project',str(app),'new','--title','Smoke incremental request','--requester','Fictional smoke Requester','--idea','A fictional incremental request used only to verify external request initialization.']
    created=subprocess.run(command,capture_output=True,text=True)
    (area/'evidence/new.json').write_text(created.stdout)
    assert created.returncode==0 and not created.stderr,created.stdout+created.stderr
    assert json.loads(created.stdout)['epic']['metadata']['status']=='discovery'
    assert git('rev-parse','HEAD').strip()==head
    for name,sha in before.items():assert hashlib.sha256((app/name).read_bytes()).hexdigest()==sha,name
    added=set(hashes(app))-set(before);assert all(p.startswith('requirements/') for p in added),added
    summary={'area':str(area),'runtime':str(runtime),'runtime_base_revision':result['source_revision'],'runtime_preview':result['preview'],'snapshot_digest':result['snapshot_digest'],'preflight_ready':preflight['ready'],'baseline_ready':preflight['baseline_ready'],'preflight_warnings':[d['code'] for d in preflight['diagnostics'] if d['severity']=='warning'],'native_codex':native,'application_baseline':head,'application_and_git_unchanged_before_new':True,'new_added_only_requirements_files':sorted(added),'lifecycle':'discovery','human_approvals_created':False,'visual_ide_test_performed':False}
    (area/'evidence/summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
