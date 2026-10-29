"""Approved local instruction packages with exact content pins; no remote execution."""
from pathlib import Path
import re
import yaml
import approval_common as common
import business_refinement as business

ROOT = Path(__file__).resolve().parents[1] / 'domain-skills'
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')
FIELDS = {'name', 'description', 'version', 'owner', 'stages', 'inputs', 'outputs', 'standards', 'dependencies', 'orchestrator'}


def require(value, message):
    business.require(value, 'E_SKILL', message, 'catalog.yaml')


def package(path):
    require(path.is_dir() and not path.is_symlink(), 'Expected a regular local skill directory.')
    files = {}
    for p in sorted(path.rglob('*')):
        require(not p.is_symlink(), 'Skill packages cannot contain symlinks.')
        if p.is_file():
            files[p.relative_to(path).as_posix()] = business.digest(p.read_bytes())
    require('SKILL.md' in files and 'manifest.yaml' in files, 'Skill requires SKILL.md and manifest.yaml.')
    return business.digest(common.canonical_manifest(files))


def catalog(loader, root=ROOT):
    try:
        require(not root.is_symlink() and not (root/'catalog.yaml').is_symlink(), 'Unsafe catalog.')
        data = yaml.load((root/'catalog.yaml').read_text(encoding='utf-8'), Loader=loader)
        require(isinstance(data, dict) and set(data)=={'schema_version','skills'} and data['schema_version']=='0.1' and isinstance(data['skills'],dict) and bool(data['skills']), 'Invalid catalog.')
        result = {}
        for name, pin in data['skills'].items():
            require(isinstance(name,str) and re.fullmatch(r'[a-z][a-z0-9-]*',name) and isinstance(pin,dict) and set(pin)=={'version','digest'}, 'Invalid skill reference.')
            path = root/name
            require(package(path)==pin['digest'], 'Skill content differs from approved catalog pin: '+name)
            m = yaml.load((path/'manifest.yaml').read_text(encoding='utf-8'),Loader=loader)
            require(isinstance(m,dict) and set(m)==FIELDS and m['name']==name and isinstance(m['version'],str) and VERSION.fullmatch(m['version']) and m['version']==pin['version'], 'Invalid skill metadata/version: '+name)
            require(all(isinstance(m[k],str) and m[k].strip() for k in ('description','owner')), 'Missing description/owner.')
            require(m['orchestrator'] in ('0.9','0.10','0.11'), 'Unsupported orchestrator minor contract.')
            for field in ('stages','inputs','outputs','standards'):
                require(isinstance(m[field],list) and bool(m[field]) and all(isinstance(v,str) and v.strip() for v in m[field]) and len(set(m[field]))==len(m[field]), 'Invalid skill '+field)
            require(isinstance(m['dependencies'],dict), 'Skill dependencies must pin exact versions.')
            result[name]={**m,'digest':pin['digest'],'path':str(path)}
        def visit(name, trail):
            require(name not in trail,'Cyclic skill dependency.')
            for dep, version in result[name]['dependencies'].items():
                require(dep in result and result[dep]['version']==version,'Missing or incompatible skill dependency.')
                visit(dep,trail+[name])
        for name in result: visit(name,[])
        return result
    except (OSError,UnicodeError,yaml.YAMLError,ValueError,TypeError,RecursionError) as exc:
        raise business.BusinessError('E_SKILL',str(exc),'catalog.yaml') from exc


def pins(names, stage, loader):
    available=catalog(loader)
    found={}
    def add(name):
        require(name in available,'Unknown domain skill: '+name)
        m=available[name]
        require(stage in m['stages'], 'Skill is incompatible with stage: '+name)
        found[name]={'version':m['version'],'digest':m['digest']}
        for dep in m['dependencies']: add(dep)
    for name in names: add(name)
    return found
