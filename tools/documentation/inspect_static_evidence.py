"""Inspect frozen benchmark identities and one room calculation, without a sweep."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('evidence exists; use a new filename')
    sys.path.insert(0, str(args.repo / 'nuvem'))
    sys.path.insert(0, str(args.repo / 'tests'))
    from benchmark import model
    import load_script
    from test_block_bonding import ft, seg

    def git(*argv):
        return subprocess.check_output(['git', *argv], cwd=args.repo,
                                       text=True, encoding='utf-8').strip()
    evidence = {'head': git('rev-parse', 'HEAD'), 'files': [], 'room_probe': {}}
    for directory in sorted((args.repo / 'nuvem/benchmark/projects').iterdir()):
        if not directory.is_dir():
            continue
        for name in ('input.json', 'reference.json', 'baseline.json', 'score.json'):
            path = directory / name
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            relative = path.relative_to(args.repo).as_posix()
            entry = {'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'last_commit': git('log', '-1', '--format=%H', 'HEAD', '--', relative)}
            if isinstance(data.get('walls'), list):
                keys = [model.wall_stable_key(w['start_cm'], w['end_cm'], w['thickness_cm']) for w in data['walls']]
                counts = Counter(keys)
                entry.update(walls=len(keys), unique_keys=len(counts),
                             collisions={k: v for k, v in counts.items() if v > 1},
                             stored_key_mismatches=sum(w.get('key') != key for w, key in zip(data['walls'], keys)))
            evidence['files'].append(entry)
    m = load_script.load()
    walls = [(seg(0, 0, 800, 0), ft(14), (False, False))]
    openings = [[(ft(564), ft(750), 0.0, ft(210))]]
    probe = {'wall_length_cm': 800, 'opening_t_cm': [564, 750], 'node_t_cm': 742}
    for sign in (-1, 1):
        probe[str(sign)] = m._room_at_t_on_wall(walls, openings, 0, ft(742), sign) / ft(1)
    # This characterizes the known defect, not an acceptance test for safe geometry.
    assert probe['1'] > 0 and probe['-1'] > 0
    evidence['room_probe'] = probe
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
