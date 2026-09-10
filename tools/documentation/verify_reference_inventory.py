"""Read-only verification of published reference JSON and protected solver paths.

Hashes use UTF-8 text with LF line endings so Windows checkouts are portable.
This checks preservation, not physical validity or completeness of extraction.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def canonical(data):
    return data.decode('utf-8').replace('\r\n', '\n').encode('utf-8')


def verify(root, protected_base):
    inventory = json.loads((root / 'reference_projects/inventory.json').read_text(encoding='utf-8'))
    if inventory['status'] != 'EVIDENCE_NOT_NORM':
        raise ValueError('inventory must remain evidence, not norm')
    tracked = set(git(root, 'ls-files', '-z').decode('utf-8').split('\0'))
    seen = set()
    counts = {}
    for project in inventory['projects']:
        if project['portal'] not in tracked:
            raise ValueError('untracked project portal: ' + project['portal'])
        primary = project['primary_path'] + '/'
        for entry in project['files']:
            path = entry['path']
            if path in seen or path not in tracked or not path.startswith(primary):
                raise ValueError('duplicate, untracked or misplaced reference: ' + path)
            seen.add(path)
            current = canonical((root / path).read_bytes())
            original = canonical(git(root, 'show', project['source_commit'] + ':' + path))
            json.loads(current)
            if current != original or hashlib.sha256(current).hexdigest() != entry['sha256']:
                raise ValueError('published JSON changed: ' + path)
        counts[project['id']] = len(project['files'])
    expected = {'torre_easy_lo_r00': 9, 'butanta_r08_lt': 14}
    if counts != expected:
        raise ValueError('reference inventory incomplete: ' + repr(counts))
    actual = {p for p in tracked if p.startswith('docs/revit_reference_extraction/') and p.endswith('.json')}
    if actual != seen:
        raise ValueError('JSON files missing from inventory: ' + repr(sorted(actual ^ seen)))
    protected = ['Script.py', 'script.py', 'nuvem/core', 'nuvem/benchmark', 'tests', '.github/workflows']
    changed = git(root, 'diff', '--name-only', protected_base, '--', *protected).decode('utf-8').strip()
    if changed:
        raise ValueError('protected production/benchmark/test/workflow changed:\n' + changed)
    rules_path = 'nuvem/REGRAS_MODULACAO_BLOCOS.md'
    original_rules = canonical(git(root, 'show', protected_base + ':' + rules_path))
    current_rules = canonical((root / rules_path).read_bytes())
    if not current_rules.startswith(original_rules.rstrip(b'\n')):
        raise ValueError('existing rule text was edited instead of preserving historical authority')
    return {'result': 'PASS', 'json_files': len(seen), 'projects': counts,
            'protected_base': protected_base, 'protected_paths': protected,
            'hash_format': 'UTF-8 with LF line endings',
            'limitations': ['No Revit execution or physical certification',
                            'Rule additions require semantic review; prefix check alone is not approval',
                            'Raw/intermediate inputs remain incomplete as documented']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protected-base', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        print(json.dumps(verify(root, args.protected_base), indent=2))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, 'FAIL: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
