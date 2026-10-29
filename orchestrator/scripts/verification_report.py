"""Pure projection of structured verification evidence into human-readable Markdown.

This renderer does not approve scope, interpret requirements or infer scenario success
from command exit codes. Callers must collect current, validated evidence first.
"""
from collections.abc import Mapping
from html import escape
import json
import re
from pathlib import PurePath
from urllib.parse import quote


def _text(value):
    """Display untrusted prose without letting it add Markdown/HTML structure."""
    if value is None:
        return 'Not recorded'
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    value = escape(str(value), quote=False)
    for char in ('\\', '`', '*', '_', '[', ']', '#', '|'):
        value = value.replace(char, '\\' + char)
    return value.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')


def _label(key):
    label = str(key).replace('_', ' ')
    return _text(label[:1].upper() + label[1:])


def _fields(value, depth=0):
    """Retain additional disclosure fields instead of silently dropping them."""
    prefix = '  ' * depth
    if isinstance(value, Mapping):
        # Descriptors come from validated artifact discovery. Build links from the
        # actual physical path; never display a logical alias for legacy storage.
        if isinstance(value.get('path'), str) and value['path'].startswith('/'):
            path = value['path']
            label = _text(PurePath(path).name)
            lines = [prefix + '- Document: [' + label + '](<' + quote(path, safe='/') + '>)']
            remainder = {k: v for k, v in value.items() if k not in ('path', 'link', 'name')}
            return lines + _fields(remainder, depth)
        lines = []
        for key, item in value.items():
            if isinstance(item, (Mapping, list, tuple)) and item:
                lines.append(prefix + '- ' + _label(key) + ':')
                lines.extend(_fields(item, depth + 1))
            else:
                lines.append(prefix + '- ' + _label(key) + ': ' + ('None recorded' if item in ([], {}) else _text(item)))
        return lines
    if isinstance(value, (list, tuple)):
        lines = []
        for item in value:
            if isinstance(item, (Mapping, list, tuple)):
                lines.append(prefix + '- Record:')
                lines.extend(_fields(item, depth + 1))
            else:
                lines.append(prefix + '- ' + _text(item))
        return lines
    return [prefix + '- ' + _text(value)]


def _section(title, value, empty='None recorded.'):
    return ['## ' + title, ''] + (_fields(value) if value else [empty]) + ['']


def _legacy_render(report):
    """Render a validated final-report mapping without filesystem access or mutation.

    Required historical fields are coverage, unresolved, checks, source_revision
    and security. New collectors may additionally supply scenarios, exclusions,
    limitations, residual_risks and references. Check maps and check lists are both
    accepted. Omitted scenario results are explicitly reported as unassessed.
    """
    # Baselines serialize JSON with sorted keys. Render identically before and
    # after persistence, independently of caller mapping insertion order.
    report = json.loads(json.dumps(report, sort_keys=True))
    coverage = report.get('coverage', {})
    blocked = {rid: item for rid, item in coverage.items() if item.get('disposition') == 'blocked'}
    excluded = {rid: item for rid, item in coverage.items() if item.get('disposition') == 'excluded'}
    unresolved = report.get('unresolved', [])
    limitations = report.get('limitations', [])
    exclusions = report.get('exclusions', [])
    qualified = bool(blocked or excluded or unresolved or limitations or exclusions)
    result = 'Verified for the stated scope' if qualified else 'Verified'
    lines = ['# Final Verification Report', '', result + '.', '',
             'Named check results are execution evidence. A passing command does not by itself establish that every product scenario passed.', '',
             'This report is not release approval or a security certification.', '']
    governance = report.get('governance_status', 'legacy')
    lines += _section('Governance assessment', {'contract': governance})
    if governance == 'legacy':
        lines += ['Legacy governance: not assessed under the strengthened limitation-authorization and semantic-conformance controls.', '']
    lines += _section('Verified scenarios and recorded scenario outcomes', report.get('scenarios'),
                      'No individual scenario outcomes recorded; scenario-level success is not inferred from passing checks.')
    checks = report.get('checks', {})
    if isinstance(checks, Mapping):
        checks = {cid: {k: v for k, v in item.items() if k not in ('content', 'output', '_request')}
                  for cid, item in checks.items()}
    else:
        checks = [{k: v for k, v in item.items() if k not in ('content', 'output', '_request')} for item in checks]
    lines += _section('Actual named check results', checks)
    lines += ['Captured command output remains in the structured execution evidence; the results above retain its recorded hash and references when available.', '']
    lines += _section('Requirement coverage', coverage)
    lines += _section('Blocked requirements', blocked)
    lines += _section('Unresolved questions and assumptions', unresolved)
    lines += _section('Excluded behavior', excluded)
    lines += _section('Exclusion authority', exclusions,
                      'No separate exclusion authority recorded.' if excluded else 'No exclusions recorded.')
    if excluded and not exclusions:
        lines += ['Authority for the declared exclusions is not established by this report.', '']
    lines += _section('Authorized prototype limitations', limitations)
    lines += _section('Residual risks', report.get('residual_risks'), 'No additional residual risks recorded; unresolved and blocked behavior remains disclosed above.')
    refs = {'source_revision': report.get('source_revision'), 'security': report.get('security')}
    if report.get('qa_context') is not None:
        refs['qa_context'] = report['qa_context']
    refs.update(report.get('references', {}))
    lines += _section('Evidence and baseline references', refs)
    return '\n'.join(lines).rstrip() + '\n'


def render(report, template_item=None):
    """Use the selected immutable layout, retaining the historical default renderer.

    The fixed slots below are a projection contract, not an executable template
    language. Supplied evidence is escaped once and never reinterpreted as slots.
    """
    if template_item is None:
        return _legacy_render(report)
    import artifact_templates
    artifact_templates.validate_pin(template_item['pin'], 'verification-report')
    report = json.loads(json.dumps(report, sort_keys=True))
    coverage = report.get('coverage', {})
    blocked = {rid: item for rid, item in coverage.items() if item.get('disposition') == 'blocked'}
    excluded = {rid: item for rid, item in coverage.items() if item.get('disposition') == 'excluded'}
    unresolved, limitations, exclusions = (report.get(k, []) for k in ('unresolved', 'limitations', 'exclusions'))
    def body(value, empty='None recorded.'):
        return '\n'.join(_fields(value)) if value else empty
    governance = report.get('governance_status', 'legacy')
    governance_body = body({'contract': governance})
    if governance == 'legacy':
        governance_body += '\n\nLegacy governance: not assessed under the strengthened limitation-authorization and semantic-conformance controls.'
    checks = report.get('checks', {})
    if isinstance(checks, Mapping):
        checks = {cid: {k: v for k, v in item.items() if k not in ('content', 'output', '_request')} for cid, item in checks.items()}
    else:
        checks = [{k: v for k, v in item.items() if k not in ('content', 'output', '_request')} for item in checks]
    authority = body(exclusions, 'No separate exclusion authority recorded.' if excluded else 'No exclusions recorded.')
    if excluded and not exclusions:
        authority += '\n\nAuthority for the declared exclusions is not established by this report.'
    refs = {'source_revision': report.get('source_revision'), 'security': report.get('security')}
    if report.get('qa_context') is not None:
        refs['qa_context'] = report['qa_context']
    refs.update(report.get('references', {}))
    values = {
        'result': 'Verified for the stated scope' if any((blocked, excluded, unresolved, limitations, exclusions)) else 'Verified',
        'governance': governance_body,
        'scenarios': body(report.get('scenarios'), 'No individual scenario outcomes recorded; scenario-level success is not inferred from passing checks.'),
        'checks': body(checks), 'coverage': body(coverage), 'blocked': body(blocked),
        'unresolved': body(unresolved), 'excluded': body(excluded), 'exclusion_authority': authority,
        'limitations': body(limitations),
        'residual_risks': body(report.get('residual_risks'), 'No additional residual risks recorded; unresolved and blocked behavior remains disclosed above.'),
        'references': body(refs),
    }
    layout = template_item['content']
    slots = re.findall(r'\{\{([a-z_]+)\}\}', layout)
    artifact_templates.require(set(slots) == set(values) and len(slots) == len(values),
                               'Final report template must contain each fixed projection slot exactly once.', 'E_TEMPLATE_CONTRACT')
    rendered = re.sub(r'\{\{([a-z_]+)\}\}', lambda match: values[match[1]], layout)
    artifact_templates.validate_document(template_item, rendered)
    return rendered.rstrip() + '\n'
