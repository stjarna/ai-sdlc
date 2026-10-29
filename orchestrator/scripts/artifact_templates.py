"""Pinned local document scaffolds; existing stage validators own data/governance.

No executable templates, registry service, semantic interpretation or lifecycle policy.
"""
from pathlib import Path
import hashlib
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1] / 'templates'
# Reuse the canonical document catalog; machine histories have non-Markdown names.
from artifact_names import NAMES
ARTIFACTS = {filename.removesuffix('.md'): (stage+'.'+kind, filename)
             for (stage,kind),(filename,_) in NAMES.items() if filename.endswith('.md')}
CONTRACTS = {name: artifact + '/1' for name, (artifact, _) in ARTIFACTS.items()}
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')
MANIFEST_FIELDS = {'schema_version','id','version','owner','artifact','validation_contract',
                   'content_digest','required_sections','optional_sections'}
PIN_FIELDS = {'id','version','digest','content_digest','validation_contract'}


def require(condition, message, code='E_TEMPLATE'):
    if not condition:
        from business_refinement import BusinessError
        raise BusinessError(code, message, str(ROOT/'catalog.yaml'))


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def loader():
    from sdlc import StrictLoader
    return StrictLoader


def headings(content):
    return [line[3:].strip() for line in content.splitlines() if line.startswith('## ')]


def validate_pin(pin, template_id=None):
    require(isinstance(pin,dict) and set(pin)==PIN_FIELDS, 'Invalid template provenance.')
    name=pin['id']
    require(isinstance(name,str) and name in ARTIFACTS and (template_id is None or name==template_id), 'Wrong artifact template.')
    require(isinstance(pin['version'],str) and VERSION.fullmatch(pin['version']), 'Invalid template version.')
    require(all(isinstance(pin[k],str) and re.fullmatch(r'[0-9a-f]{64}',pin[k]) for k in ('digest','content_digest')), 'Invalid template digest.')
    require(pin['validation_contract']==CONTRACTS[name], 'Unsupported template validation contract.', 'E_TEMPLATE_CONTRACT')
    return pin


def package(template_id, version, root=None):
    root=ROOT if root is None else Path(root)
    require(isinstance(template_id,str) and template_id in ARTIFACTS and isinstance(version,str) and VERSION.fullmatch(version), 'Invalid template selection.')
    path=root/'versions'/template_id/version
    try:
        require(not any(p.is_symlink() for p in (root,root/'versions',path.parent,path)), 'Template paths cannot be symlinks.')
        require(path.is_dir() and {p.name for p in path.iterdir()}=={'manifest.yaml','document.md'}, 'Template package needs exactly manifest.yaml and document.md.')
        require(all((path/n).is_file() and not (path/n).is_symlink() for n in ('manifest.yaml','document.md')), 'Unsafe template file.')
        raw={n:(path/n).read_bytes() for n in ('manifest.yaml','document.md')}
        m=yaml.load(raw['manifest.yaml'].decode(),Loader=loader())
        require(isinstance(m,dict) and set(m)==MANIFEST_FIELDS and m['schema_version']=='0.1' and m['id']==template_id and m['version']==version, 'Invalid template manifest.')
        require(isinstance(m['owner'],str) and bool(m['owner'].strip()), 'Template domain owner is required.')
        require(m['artifact']==ARTIFACTS[template_id][0] and m['validation_contract']==CONTRACTS[template_id], 'Incompatible template/validator binding.', 'E_TEMPLATE_CONTRACT')
        text=raw['document.md'].decode()
        require(m['content_digest']==digest(raw['document.md']), 'Template content digest differs.', 'E_TEMPLATE_INTEGRITY')
        for key in ('required_sections','optional_sections'):
            require(isinstance(m[key],list) and all(isinstance(v,str) and bool(v.strip()) for v in m[key]) and len(m[key])==len(set(m[key])), 'Invalid template sections.')
        declared=m['required_sections']+m['optional_sections']
        actual=headings(text)
        require(len(declared)==len(set(declared)) and len(actual)==len(set(actual)) and set(actual)==set(declared), 'Scaffold headings differ from declared sections.', 'E_TEMPLATE_CONTRACT')
        pin={'id':template_id,'version':version,'digest':digest(canonical({n:digest(v) for n,v in raw.items()})),
             'content_digest':m['content_digest'],'validation_contract':m['validation_contract']}
        return {'manifest':m,'pin':pin,'content':text,'path':str(path)}
    except (OSError,UnicodeError,yaml.YAMLError,RecursionError,ValueError,TypeError) as exc:
        require(False,'Cannot read template package: '+str(exc),'E_TEMPLATE_INTEGRITY')


def catalog(root=None):
    root=ROOT if root is None else Path(root)
    try:
        require(not root.is_symlink() and not (root/'catalog.yaml').is_symlink(), 'Unsafe template catalog.')
        data=yaml.load((root/'catalog.yaml').read_text(),Loader=loader())
        require(isinstance(data,dict) and set(data)=={'schema_version','templates'} and data['schema_version']=='0.1'
                and isinstance(data['templates'],dict) and set(data['templates'])==set(ARTIFACTS), 'Invalid pinned template catalog.')
        result={}
        for name,pin in data['templates'].items():
            require(isinstance(pin,dict) and set(pin)=={'version','digest'}, 'Invalid catalog template pin.')
            item=package(name,pin['version'],root)
            require(item['pin']['digest']==pin['digest'], 'Template differs from catalog pin: '+name,'E_TEMPLATE_INTEGRITY')
            result[name]=item
        return result
    except (OSError,UnicodeError,yaml.YAMLError,RecursionError,ValueError,TypeError) as exc:
        require(False,'Cannot read template catalog: '+str(exc),'E_TEMPLATE_INTEGRITY')


def resolve(template_id, expected_digest=None):
    require(isinstance(template_id,str) and template_id in ARTIFACTS, 'Unknown template ID.')
    item=catalog()[template_id]
    require(expected_digest is None or expected_digest==item['pin']['digest'], 'Template selection changed; review again.', 'E_TEMPLATE_STALE')
    return item


def assert_current(item):
    require(resolve(item['pin']['id'])['pin']==item['pin'], 'Template changed during publication.', 'E_TEMPLATE_STALE')


def validate_document(item, content):
    try:
        text=content.decode('utf-8') if isinstance(content,bytes) else content
    except UnicodeError:
        require(False, 'Expected UTF-8 Markdown text.', 'E_TEMPLATE_DOCUMENT')
    require(isinstance(text,str), 'Expected Markdown text.', 'E_TEMPLATE_DOCUMENT')
    actual=headings(text)
    required=item['manifest']['required_sections']
    require(all(actual.count(h)==1 for h in required), 'Missing or duplicate required template sections: '+', '.join(required), 'E_TEMPLATE_DOCUMENT')
    positions=[actual.index(h) for h in required]
    require(positions==sorted(positions), 'Required template sections are out of order.', 'E_TEMPLATE_DOCUMENT')
    return item['pin']


def scaffold(template_id):
    """Read-only drafting input; placeholders are never interpreted as requirements."""
    return resolve(template_id)['content']


def template_for(stage,kind):
    artifact=stage+'.'+kind
    return next(name for name,(value,_) in ARTIFACTS.items() if value==artifact)


def check_retry(pin, expected_digest):
    """Retries bind the original selection, independently of the current catalog."""
    require(expected_digest is None or (pin is not None and pin["digest"]==expected_digest),
            "Retry changed its template selection.", "E_IDEMPOTENCY")
