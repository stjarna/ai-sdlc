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


# Named data slots, independent of prose/layout and validated for every package.
PLACEHOLDERS = {'business': ('epic_id',
              'source_revision',
              'confirmed_information',
              'unresolved_issues_or_none_recorded',
              'unconfirmed_proposals_or_none_recorded'),
 'code-review': ('request_id',
                 'scope_and_source',
                 'verification_evidence',
                 'semantic_conformance',
                 'findings_and_limitations',
                 'change_summary'),
 'idea': ('problem',
          'users',
          'expected_value',
          'initial_scope',
          'success_criteria',
          'assumptions',
          'open_questions'),
 'implementation-plan': ('request_id',
                         'authority_and_scope',
                         'tasks',
                         'checks',
                         'unresolved_items_and_limitations',
                         'execution_environment'),
 'security-review': ('request_id',
                     'scope_and_method',
                     'findings',
                     'evidence',
                     'limitations_and_unresolved_items',
                     'remediation'),
 'specification': ('epic_id',
                   'baseline_id',
                   'approval_id',
                   'handoff_id',
                   'fr_id',
                   'fr_title',
                   'fr_business_sources',
                   'fr_discovery_evidence',
                   'fr_status',
                   'fr_questions',
                   'fr_statement',
                   'uc_id',
                   'uc_title',
                   'uc_business_sources',
                   'uc_discovery_evidence',
                   'uc_status',
                   'uc_requirements',
                   'uc_questions',
                   'uc_actor',
                   'uc_preconditions',
                   'uc_trigger',
                   'uc_main_flow_first_step',
                   'uc_alternative_flows',
                   'uc_outcome',
                   'br_id',
                   'br_title',
                   'br_business_sources',
                   'br_discovery_evidence',
                   'br_status',
                   'br_requirements',
                   'br_questions',
                   'br_statement',
                   'ac_id',
                   'ac_title',
                   'ac_business_sources',
                   'ac_discovery_evidence',
                   'ac_status',
                   'ac_requirements',
                   'ac_questions',
                   'ac_given',
                   'ac_when',
                   'ac_then',
                   'business_id',
                   'coverage_disposition',
                   'covered_items_or_dash',
                   'coverage_reason',
                   'unchanged_inherited_items_or_none_recorded',
                   'aq_id',
                   'aq_title',
                   'aq_business_sources',
                   'aq_discovery_evidence',
                   'aq_status',
                   'aq_affected_items',
                   'aq_statement',
                   'ap_id',
                   'ap_title',
                   'ap_business_sources',
                   'ap_discovery_evidence',
                   'ap_status',
                   'ap_affected_items',
                   'ap_statement'),
 'technical-design': ('request_id',
                      'context_and_authority',
                      'proposed_solution',
                      'security_considerations',
                      'coverage_and_uncertainty',
                      'prototype_limitations',
                      'alternatives',
                      'interfaces_and_data'),
 'test-automation': ('request_id',
                     'authority_and_source',
                     'product_checks',
                     'prototype_limitation_checks',
                     'execution_and_evidence',
                     'unresolved_items',
                     'dependency_setup'),
 'test-scenarios': ('request_id',
                    'authority',
                    'scenarios',
                    'coverage_and_unresolved_items',
                    'test_data'),
 'test-strategy': ('request_id',
                   'authority_and_scope',
                   'test_approach',
                   'coverage_and_unresolved_items',
                   'risks'),
 'verification-report': ('result',
                         'governance',
                         'scenarios',
                         'checks',
                         'coverage',
                         'blocked',
                         'unresolved',
                         'excluded',
                         'exclusion_authority',
                         'limitations',
                         'residual_risks',
                         'references')}
UNKNOWN = "Not provided."
TOKEN = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")


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
        lint(template_id,version,text)
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


def validate_document(item, content, *, literal_values=False):
    try:
        text=content.decode('utf-8') if isinstance(content,bytes) else content
    except UnicodeError:
        require(False, 'Expected UTF-8 Markdown text.', 'E_TEMPLATE_DOCUMENT')
    require(isinstance(text,str), 'Expected Markdown text.', 'E_TEMPLATE_DOCUMENT')
    if not literal_values:assert_resolved(text)
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



def variables(template_id, version):
    # Published Idea 1.0.0 deliberately rendered just the original description.
    return ('problem',) if template_id=='idea' and version=='1.0.0' else PLACEHOLDERS[template_id]


def lint(template_id, version, text):
    slots=TOKEN.findall(text)
    remainder=TOKEN.sub('',text)
    require('{{' not in remainder and '}}' not in remainder,'Invalid placeholder syntax.','E_TEMPLATE_CONTRACT')
    expected=variables(template_id,version)
    require(set(slots)==set(expected) and len(slots)==len(expected),
            'Template slots must match the named generation contract exactly once: '+', '.join(expected),'E_TEMPLATE_CONTRACT')
    return tuple(slots)


def assert_resolved(text):
    require(not re.search(r'(?<!\\)\{\{',text),
            'Unresolved template syntax in draft; fill slots or escape literal examples.','E_TEMPLATE_DOCUMENT')


def render(item, values, *, check_layout=True):
    """Exact single-pass substitution. Inserted user/evidence text is never evaluated."""
    expected=lint(item['pin']['id'],item['pin']['version'],item['content'])
    require(isinstance(values,dict) and set(values)==set(expected) and all(isinstance(v,str) for v in values.values()),
            'Rendering context must supply exactly the named string slots; no unknown or unused values.','E_TEMPLATE_CONTEXT')
    validate_document(item,item['content'],literal_values=True)
    rendered=TOKEN.sub(lambda match:values[match[1]],item['content'])
    if check_layout:validate_document(item,rendered,literal_values=True)
    return rendered


def render_idea(item, problem, details=None):
    require(details is None or isinstance(details,dict),'Idea details must be a mapping.','E_TEMPLATE_CONTEXT')
    details={} if details is None else details
    allowed=set(PLACEHOLDERS['idea'])-{'problem'}
    require(set(details)<=allowed and all(v is None or isinstance(v,str) for v in details.values()),
            'Idea details accept only named section strings or null; problem comes from the original idea.','E_TEMPLATE_CONTEXT')
    require(isinstance(problem,str),'Original idea must be text.','E_TEMPLATE_CONTEXT')
    expected=variables('idea',item['pin']['version'])
    require(len(expected)>1 or not details,'This legacy template cannot represent extra Idea sections.','E_TEMPLATE_CONTEXT')
    context={key:(problem.strip() if key=='problem' else (details.get(key) or '').strip()) for key in expected}
    if item['pin']['version']!='1.0.0':context={k:v or UNKNOWN for k,v in context.items()}
    # Original user Markdown is literal data, including headings; preserve the
    # pre-existing creation contract rather than interpreting it as scaffold layout.
    return render(item,context,check_layout=False)
