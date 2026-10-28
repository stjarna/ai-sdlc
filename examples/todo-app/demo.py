#!/usr/bin/env python3
"""Rehearse the preserved demo without editing its approved project or audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
REQUEST = 'REQ-0001'
CHECKS = {
    'unit': ['node', 'scripts/check.mjs', 'unit'],
    'build': ['node', 'scripts/check.mjs', 'build'],
    'integration': ['node', '--test', 'qa/integration.test.mjs'],
    'ui': ['node', 'qa/ui.mjs'],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_archive(base=BASE):
    manifest = json.loads((base/'preservation-manifest.json').read_text())
    expected = manifest['files']
    actual = set()
    for folder in ('project', 'acceptance-evidence', 'acceptance-inputs'):
        for path in (base/folder).rglob('*'):
            if path.is_symlink():
                raise ValueError('Symlink in preserved archive: ' + str(path))
            if path.is_file():
                actual.add(path.relative_to(base).as_posix())
    if actual != set(expected):
        raise ValueError('Preserved archive file set differs from its manifest.')
    for name, value in expected.items():
        path = base/name
        if not path.resolve().is_relative_to(base.resolve()) or digest(path) != value:
            raise ValueError('Preservation hash mismatch: ' + name)
    return manifest


def workspace(base=BASE):
    manifest = check_archive(base)
    parent, target = base/'.run', base/'.run/project'
    if parent.is_symlink() or target.is_symlink():
        raise ValueError('Rehearsal workspace must not be a symlink.')
    if not target.exists():
        parent.mkdir(exist_ok=True)
        shutil.copytree(base/'project', target)
    expected = {name.removeprefix('project/'): value for name, value in manifest['files'].items() if name.startswith('project/')}
    for name, value in expected.items():
        path = target/name
        if path.is_symlink() or not path.is_file() or digest(path) != value:
            raise ValueError('Rehearsal changed a preserved input: ' + name + '. Keep that work and create a fresh workspace manually.')
    for path in target.rglob('*'):
        name = path.relative_to(target).as_posix()
        if name.startswith('qa/node_modules/'):
            continue
        if path.is_symlink():
            raise ValueError('Unexpected rehearsal symlink: ' + name)
        if path.is_file() and name not in expected and not name.startswith('requirements/REQ-0001-task-due-date-management/test-evidence/'):
            raise ValueError('Unexpected rehearsal source file: ' + name)
    return target


def cli(*args):
    python = ROOT/'.venv/bin/python'
    command = [str(python) if python.exists() else sys.executable,
               str(ROOT/'orchestrator/scripts/sdlc.py'), '--project', str(BASE/'project'), *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise ValueError('Read-only CLI check failed: ' + result.stdout + result.stderr)
    return json.loads(result.stdout)


def original_path(path, manifest, base=BASE):
    """Resolve recorded historical paths locally; never read the old temporary tree."""
    for folder, roots in manifest['historical_roots'].items():
        for root in roots:
            prefix = root.rstrip('/') + '/'
            if path.startswith(prefix):
                target = base/folder/path[len(prefix):]
                if target.resolve().is_relative_to((base/folder).resolve()):
                    return target
    raise ValueError('Unmapped historical evidence path: ' + path)


def package_digest(path):
    if not path.is_dir() or path.is_symlink():
        raise ValueError('Missing historical domain package: ' + str(path))
    files = {}
    for file in sorted(path.rglob('*')):
        if file.is_symlink():
            raise ValueError('Symlink in domain package.')
        if file.is_file():
            files[file.relative_to(path).as_posix()] = digest(file)
    return hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def verify():
    manifest = check_archive()
    validated = cli('validate', REQUEST)
    engineering = cli('engineering-review', REQUEST)['engineering']
    qa = cli('qa-review', REQUEST)['review']
    catalog = cli('skills')['skills']
    if not (validated['ok'] and engineering['stage'] == 'verified' and engineering['current']
            and qa['stage'] == 'verified' and qa['integration']['ready']):
        raise ValueError('Preserved acceptance state is not current and Verified.')
    report = engineering['final_report']['document']
    if Path(report['path']).name != 'verification-report.md' or not Path(report['path']).is_file():
        raise ValueError('Final canonical report is missing.')
    pins, evidence = set(), set()
    for path in (BASE/'project/requirements').rglob('artifact.json'):
        obj = json.loads(path.read_text())
        for name, pin in obj.get('skills', {}).items():
            if name not in catalog or not re.fullmatch(r'\d+\.\d+\.\d+', pin['version']):
                raise ValueError('Unknown recorded domain skill/version.')
            package = ROOT/'orchestrator/domain-skills'/name if pin['version'] == catalog[name]['version'] else ROOT/'orchestrator/domain-skills/versions'/name/pin['version']
            if package_digest(package) != pin['digest']:
                raise ValueError('Recorded domain instruction hash mismatch: ' + name)
            pins.add((name, pin['version'], pin['digest']))
        for line in obj.get('payload', {}).get('output', '').splitlines():
            if line.startswith('{"evidence":'):
                item = json.loads(line)
                local = original_path(item['evidence'], manifest)
                if not local.is_file() or digest(local) != item['sha256']:
                    raise ValueError('Historical test evidence differs: ' + str(local))
                evidence.add(str(local))
    summary = {'preserved_files': len(manifest['files']), 'engineering': 'verified', 'qa': 'verified',
               'recorded_skill_pins_verified': len(pins), 'referenced_test_evidence_verified': len(evidence),
               'final_report': report['link'], 'unresolved': engineering['final_report']['payload']['unresolved']}
    print(json.dumps(summary, indent=2))


def execute(command, directory, env=None):
    result = subprocess.run(command, cwd=directory.resolve(), env=env, capture_output=True, text=True)
    logs = BASE/'.run/executions'
    logs.mkdir(parents=True, exist_ok=True)
    record = {'purpose': 'Presentation rehearsal only; not a new SDLC approval or historical acceptance result',
              'argv': command, 'cwd': str(directory.resolve()), 'exit_code': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr}
    path = logs/(str(uuid.uuid4()) + '.json')
    path.write_text(json.dumps(record, indent=2) + '\n')
    print(result.stdout, end='')
    print(result.stderr, end='', file=sys.stderr)
    print('Fresh rehearsal execution record:', path)
    # Existing source, metadata and historical evidence must still match after a run.
    workspace()
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verify', 'setup', 'start', 'unit', 'build', 'integration', 'ui', 'details'])
    args = parser.parse_args()
    if args.command == 'verify':
        verify(); return 0
    if args.command == 'details':
        check_archive(); print(json.dumps(cli('command-context', 'details', '--request', REQUEST), indent=2)); return 0
    target = workspace()
    if args.command == 'setup':
        env = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1')
        return execute(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], target/'qa', env)
    if args.command == 'start':
        os.chdir(target)
        os.execvp('node', ['node', 'src/server.mjs'])
    if args.command == 'ui' and not Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome').is_file():
        raise ValueError('Preserved approved QA runner requires installed macOS Google Chrome; no browser download or source rewrite is automatic.')
    return execute(CHECKS[args.command], target)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print('Demo preparation failed:', error, file=sys.stderr)
        sys.exit(1)
