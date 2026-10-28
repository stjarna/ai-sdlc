"""Canonical document names and backward-compatible exact-file descriptors."""
from pathlib import Path
from urllib.parse import quote


NAMES = {
    ('discovery', 'idea'): ('idea.md', 'Original Business Idea'),
    ('discovery', 'history'): ('discovery.yaml', 'Discovery History'),
    ('business', 'specification'): ('business.md', 'Business Specification'),
    ('analysis', 'specification'): ('specification.md', 'Functional Specification'),
    ('engineering', 'design'): ('technical-design.md', 'Technical Design'),
    ('engineering', 'plan'): ('implementation-plan.md', 'Engineering Implementation Plan'),
    ('engineering', 'implementation'): ('code-review.md', 'Engineering Code Review'),
    ('engineering', 'security'): ('security-review.md', 'Security Review'),
    ('engineering', 'final'): ('verification-report.md', 'Final Verification Report'),
    ('qa', 'strategy'): ('test-strategy.md', 'QA Test Strategy'),
    ('qa', 'scenarios'): ('test-scenarios.md', 'QA Test Scenarios'),
    ('qa', 'automation'): ('test-automation.md', 'QA Test Automation Review'),
}


def filename(stage, kind, action='write'):
    if kind == 'check':
        return 'qa-check-evidence.md' if stage == 'qa' else 'check-evidence.md'
    if stage == 'engineering' and kind == 'development' and action == 'start':
        return 'development-start.md'
    if kind == 'verification':
        return 'qa-verification-completion.md' if stage == 'qa' else 'verification-' + ('remediation' if action == 'remediate' else 'advancement') + '.md'
    name = NAMES[stage, kind][0]
    if action in ('write', 'finalize'):
        return name
    suffix = {'approve': 'approval', 'request_changes': 'change-request',
              'advance': 'advancement', 'remediate': 'remediation'}[action]
    return name.removesuffix('.md') + '-' + suffix + '.md'


def storage_names(stage):
    """Closed filename allowlist; never trust a path supplied by a manifest."""
    kinds = ('design', 'plan', 'implementation', 'security', 'final') if stage == 'engineering' else ('strategy', 'scenarios', 'automation')
    actions = ('write', 'approve', 'request_changes', 'advance', 'remediate', 'finalize')
    names = {filename(stage, kind, action) for kind in kinds for action in actions}
    names.add(filename(stage, 'check', 'run'))
    if stage == 'engineering':
        names.add(filename(stage, 'development', 'start'))
    names.update(filename(stage, 'verification', action) for action in ('advance', 'remediate'))
    return names


def document(stage, kind, path):
    """Physical/display names agree; identify immutable legacy storage explicitly."""
    canonical, title = NAMES[stage, kind]
    path = Path(path).resolve()
    name = path.name
    legacy = name == 'content.md'
    label = f'{title} (legacy content.md)' if legacy else name
    target = quote(str(path), safe='/:-._~')
    return {'name': name, 'canonical_name': canonical, 'title': title, 'legacy': legacy,
            'path': str(path), 'link': f'[{label}](<{target}>)'}


def documents(view):
    """A compact index for status/details, without repeating business content."""
    found = {kind: draft['document'] for kind, draft in view.get('drafts', {}).items()}
    if view.get('final_report'):
        found['final'] = view['final_report']['document']
    return found


def epic_documents(epic):
    found = {}
    for kind, stage, present, filename in (
        ('idea', 'discovery', epic.idea is not None, epic.metadata.get('artifacts', {}).get('idea', 'idea.md')),
        ('history', 'discovery', epic.discovery is not None, 'discovery.yaml'),
        ('business', 'business', epic.business is not None, 'business.md'),
        ('analysis', 'analysis', epic.analysis is not None, 'specification.md'),
    ):
        if present:
            identity = kind if stage == 'discovery' else 'specification'
            found[kind] = document(stage, identity, epic.directory / filename)
    return found
