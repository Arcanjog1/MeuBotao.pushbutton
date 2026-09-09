"""Read Git/GitHub metadata into an auditable snapshot; never fetch or publish."""

import argparse
import datetime
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('snapshot already exists; use a new dated filename')

    def run(*command):
        return subprocess.check_output(command, text=True, encoding='utf-8').strip()

    repo = 'Arcanjog1/MeuBotao.pushbutton'
    prs = json.loads(run('gh', 'pr', 'list', '--repo', repo, '--state', 'all',
                         '--limit', '100', '--json',
                         'number,title,state,isDraft,headRefName,headRefOid,baseRefName,mergedAt,closedAt,url,updatedAt'))
    snapshot = {
        'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'repository': repo,
        'main': run('git', 'rev-parse', 'origin/main'),
        'github_main': json.loads(run('gh', 'api', 'repos/' + repo + '/branches/main')),
        'prs': prs,
        'remote_refs': run('git', 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/remotes/origin').splitlines(),
        'main_history': run('git', 'log', '-35', '--format=%H %aI %s', 'origin/main').splitlines(),
        'pr_details': {}, 'documents': {},
    }
    refs = {'main': snapshot['main']}
    for pr in prs:
        if pr['state'] == 'OPEN':
            sha = pr['headRefOid']
            snapshot['pr_details'][str(pr['number'])] = {
                'head': sha,
                'merge_base': run('git', 'merge-base', 'origin/main', sha),
                'diff_from_merge_base': run('git', 'diff', '--name-status', 'origin/main...' + sha).splitlines(),
            }
        if pr['number'] in (28, 30, 31):
            detail = json.loads(run('gh', 'pr', 'view', str(pr['number']), '--repo', repo,
                                    '--json', 'baseRefOid,headRefOid,body,statusCheckRollup'))
            snapshot['pr_details'][str(pr['number'])].update(detail)
            refs['pr' + str(pr['number'])] = pr['headRefOid']
    for label, sha in refs.items():
        files = run('git', 'ls-tree', '-r', '--name-only', sha).splitlines()
        docs = []
        for path in files:
            if path.endswith('.md') or path.startswith('.github/workflows/'):
                history = run('git', 'log', '-1', '--format=%H %aI', sha, '--', path)
                docs.append({'path': path, 'last_commit': history.split()[0],
                             'last_commit_date': history.split()[1]})
        snapshot['documents'][label] = {'head': sha, 'files': docs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Captured', len(prs), 'PRs and', sum(len(d['files']) for d in snapshot['documents'].values()),
          'document revisions:', args.output)


if __name__ == '__main__':
    main()
