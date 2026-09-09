"""Validate documentation provenance, tracked checkpoints and local references.

Read-only. Does not approve domain rules or infer truth from prose.
"""

import argparse
import datetime
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit


STATUS = 'docs/PROJECT_STATUS.md'
REQUIRED = ('date', 'branch', 'head', 'base', 'pr', 'objective', 'changes',
            'tests', 'known_failures', 'physical_deltas', 'decisions_taken',
            'decisions_pending', 'next_steps', 'references')
SHA = re.compile(r'^[0-9a-f]{40}$')


def metadata(text):
    match = re.search(r'^```json\s*\n(.*?)\n```', text, re.M | re.S)
    if not match:
        raise ValueError('missing JSON metadata block')
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError('metadata must be an object')
    return value


def git(root, *args):
    result = subprocess.run(['git', *args], cwd=root, capture_output=True,
                            text=True, encoding='utf-8')
    if result.returncode:
        raise ValueError('git ' + ' '.join(args) + ': ' + result.stderr.strip())
    return result.stdout.strip()


def documentation_only(path):
    return (path.endswith('.md') or path.startswith(('docs/', 'tools/documentation/', '.github/')) or
            path in ('AGENTS.md', 'CLAUDE.md') or
            path.startswith('.claude/skills/'))


def validate(root, base, main, require_current_main=False):
    errors = []
    tracked = set(git(root, 'ls-files').splitlines())
    changed = set(git(root, 'diff', '--name-only', base).splitlines())

    def require(condition, message):
        if not condition:
            errors.append(message)

    def commit(value, label):
        if not isinstance(value, str) or not SHA.fullmatch(value):
            errors.append(label + ': expected full 40-character commit SHA')
            return False
        try:
            git(root, 'cat-file', '-e', value + '^{commit}')
        except ValueError:
            errors.append(label + ': commit unavailable: ' + value)
            return False
        return True

    def read(path):
        require(path in tracked, path + ': not versioned (git add required)')
        return (root / path).read_text(encoding='utf-8')

    def reference(ref, label):
        if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
            errors.append(label + ': invalid reference object')
            return
        path = ref['path']
        require(not PurePosixPath(path).is_absolute() and '..' not in PurePosixPath(path).parts,
                label + ': reference must stay inside repository')
        if ref.get('commit'):
            if commit(ref['commit'], label):
                try:
                    git(root, 'cat-file', '-e', ref['commit'] + ':' + path)
                except ValueError:
                    errors.append(label + ': missing path at commit: ' + path)
        else:
            require(path in tracked and (root / path).is_file(), label + ': missing tracked reference: ' + path)

    try:
        state = metadata(read(STATUS))
        observed = state.get('main', '')
        datetime.datetime.fromisoformat(state['observed_utc'])
        if commit(observed, STATUS):
            git(root, 'merge-base', '--is-ancestor', observed, main)
            if require_current_main:
                require(observed == git(root, 'rev-parse', main),
                        STATUS + ': main changed; fetch and reconcile before publishing')
            for item in state.get('official', []):
                if commit(item.get('head'), 'official'):
                    try:
                        git(root, 'merge-base', '--is-ancestor', item['head'], observed)
                    except ValueError:
                        errors.append('official revision is not integrated: ' + item['head'])
            for item in state.get('candidates', []):
                if commit(item.get('head'), 'candidate'):
                    integrated = subprocess.run(['git', 'merge-base', '--is-ancestor', item['head'], observed],
                                                cwd=root, capture_output=True).returncode == 0
                    require(not integrated, 'candidate already integrated; reconcile status: ' + item['head'])
    except (ValueError, KeyError, OSError, TypeError) as exc:
        errors.append(STATUS + ': ' + str(exc))

    checkpoints = sorted(p for p in changed if p.startswith('docs/checkpoints/') and p.endswith('.md'))
    if changed:
        require(STATUS in changed, 'delivery must reconcile ' + STATUS)
        require(bool(checkpoints), 'delivery requires a versioned docs/checkpoints/*.md checkpoint')
    for path in checkpoints:
        try:
            data = metadata(read(path))
            for field in REQUIRED:
                require(field in data and data[field] not in ('', None, []), path + ': missing field ' + field)
            datetime.date.fromisoformat(data['date'])
            require(data.get('pr') == 'not-created' or
                    re.fullmatch(r'https://github\.com/Arcanjog1/MeuBotao\.pushbutton/pull/[1-9][0-9]*', str(data.get('pr'))),
                    path + ': invalid PR URL (not-created allowed before draft creation)')
            head_ok = commit(data.get('head'), path + ': head')
            base_ok = commit(data.get('base'), path + ': base')
            if head_ok and base_ok:
                git(root, 'merge-base', '--is-ancestor', data['base'], data['head'])
                git(root, 'merge-base', '--is-ancestor', data['head'], 'HEAD')
                uncovered = [p for p in git(root, 'diff', '--name-only', data['head']).splitlines()
                             if not documentation_only(p)]
                require(not uncovered, path + ': non-documentation changes after reviewed HEAD: ' + ', '.join(uncovered))
            refs = data.get('references')
            if isinstance(refs, list):
                for ref in refs:
                    reference(ref, path)
            else:
                errors.append(path + ': references must be a list')
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors.append(path + ': ' + str(exc))

    # Only explicit local Markdown links in managed delivery documents are enforced.
    # Historical prose/backticks and external URLs are not presented as checked links.
    for path in sorted(changed | {STATUS}):
        if not path.endswith('.md') or path not in tracked or not (root / path).is_file():
            continue
        text = (root / path).read_text(encoding='utf-8')
        text = re.sub(r'^```.*?^```', '', text, flags=re.M | re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            target = target.strip('<>')
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            resolved = ((root / path).parent / unquote(parts.path)).resolve()
            try:
                relative = resolved.relative_to(root.resolve()).as_posix()
            except ValueError:
                errors.append(path + ': link outside repository: ' + target)
                continue
            require(relative in tracked and resolved.exists(), path + ': broken/untracked link: ' + target)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--main', default='origin/main')
    parser.add_argument('--require-current-main', action='store_true')
    args = parser.parse_args()
    root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel'))
    try:
        errors = validate(root, args.base, args.main, args.require_current_main)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print('ERROR:', error)
    if not errors:
        print('PASS: versioned documentation, commit provenance and explicit local links')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
