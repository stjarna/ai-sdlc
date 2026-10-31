"""Procedural context declarations for isolated tests; never actual human approvals."""
import json
from pathlib import Path
import subprocess
import sys
import os
import uuid


def cli(runtime,project,*args,session=None,env=None):
    command=[sys.executable,'-B',str(Path(runtime)/'orchestrator/scripts/sdlc.py'),'--project',str(project)]
    if session:command+=['--runtime-session',session]
    run=subprocess.run(command+list(args),capture_output=True,text=True,env=env)
    if run.stderr:raise AssertionError(run.stderr)
    try:return run,json.loads(run.stdout)
    except ValueError:raise AssertionError(run.stdout)


def session(runtime,project,skills,storage,epic_id=None,track=None,context_id=None):
    env={**os.environ,'SDLC_RUNTIME_SESSION_ROOT':str(storage)}
    tail=([epic_id] if epic_id else [])+(['--track',track] if track else [])+['--skill-root',str(skills)]
    run,view=cli(runtime,project,'runtime-status',*tail,env=env)
    assert run.returncode==0,view
    run,result=cli(runtime,project,'runtime-session',*tail,'--fresh-context-id',context_id or 'fictional-context-'+uuid.uuid4().hex,
                   '--instructions-digest',view['instructions_digest'],env=env)
    assert run.returncode==0,result
    return result['runtime_session'],env
