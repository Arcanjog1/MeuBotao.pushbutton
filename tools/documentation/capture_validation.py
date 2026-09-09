"""Capture a bounded validation command and its Git provenance outside benchmarks."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import signal
import time


def stop_process_tree(process):
    if os.name == 'nt':
        killed = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                capture_output=True, text=True, timeout=20)
        if killed.returncode and process.poll() is None:
            raise RuntimeError('Unable to stop validation process tree: ' + killed.stderr)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=20)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('a command and positive timeout are required')
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.with_suffix('.txt')
    if output.exists() or log.exists():
        parser.error('refusing to overwrite an existing validation result')
    def git(*argv):
        return subprocess.check_output(['git', *argv], cwd=args.cwd,
                                       text=True, encoding='utf-8').strip()
    metadata = {
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cwd': str(args.cwd.resolve()), 'head': git('rev-parse', 'HEAD'),
        'tree': git('rev-parse', 'HEAD^{tree}'),
        'status_before': git('status', '--porcelain'),
        'command': command, 'timeout_seconds': args.timeout,
        'python': os.sys.version, 'state': 'running', 'log': log.name,
    }
    start = time.monotonic()
    with log.open('w', encoding='utf-8') as handle:
        process = subprocess.Popen(command, cwd=args.cwd, stdout=handle,
                                   stderr=subprocess.STDOUT, start_new_session=(os.name != 'nt'))
        metadata['pid'] = process.pid
        output.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(json.dumps(metadata), flush=True)
        try:
            metadata['exit_code'] = process.wait(timeout=args.timeout)
            metadata['state'] = 'completed'
        except subprocess.TimeoutExpired:
            stop_process_tree(process)
            metadata['exit_code'] = 124
            metadata['state'] = 'timeout'
            metadata['process_tree_stopped'] = True
    metadata['elapsed_seconds'] = round(time.monotonic() - start, 3)
    metadata['status_after'] = git('status', '--porcelain')
    metadata['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
    output.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata), flush=True)
    return metadata['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
