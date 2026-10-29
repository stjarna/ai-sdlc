"""Explicit Markdown section fixtures; business and enforcement data stay in callers."""
from copy import deepcopy

SECTIONS = {
    ('engineering', 'design'): ('Context and authority', 'Proposed solution', 'Security considerations', 'Coverage and uncertainty', 'Prototype limitations'),
    ('engineering', 'plan'): ('Authority and scope', 'Tasks', 'Checks', 'Unresolved items and limitations'),
    ('engineering', 'implementation'): ('Scope and source', 'Verification evidence', 'Semantic conformance', 'Findings and limitations'),
    ('engineering', 'security'): ('Scope and method', 'Findings', 'Evidence', 'Limitations and unresolved items'),
    ('qa', 'strategy'): ('Authority and scope', 'Test approach', 'Coverage and unresolved items'),
    ('qa', 'scenarios'): ('Authority', 'Scenarios', 'Coverage and unresolved items'),
    ('qa', 'automation'): ('Authority and source', 'Product checks', 'Prototype limitation checks', 'Execution and evidence', 'Unresolved items'),
}


def document_payload(stage, kind, payload):
    """Give older fixture prose the new contract's headings, retaining its exact text.

    Only used by fixture writers. Tests for missing sections bypass this helper.
    """
    result = deepcopy(payload)
    sections = SECTIONS[(stage, kind)]
    content = result['content']
    if not any(line.startswith('## ') for line in content.splitlines()):
        result['content'] = content + '\n\n' + '\n\n'.join('## ' + heading + '\n\nFictional fixture section; structured evidence accompanies this document.' for heading in sections) + '\n'
    return result
