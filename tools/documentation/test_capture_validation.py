"""A timeout must not leave pytest workers running after the wrapper finishes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class CaptureTests(unittest.TestCase):
    def test_timeout_stops_child_as_well_as_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args):
                subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            git('init')
            git('config', 'user.name', 'Capture Test')
            git('config', 'user.email', 'test@example.invalid')
            git('commit', '--allow-empty', '-m', 'base')
            marker = root / 'orphan-completed.txt'
            child = "import time,pathlib; time.sleep(4); pathlib.Path(%r).write_text('orphan')" % str(marker)
            parent = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',%r]); print(p.pid,flush=True); time.sleep(8)" % child
            output = root / 'run.json'
            run = subprocess.run([sys.executable, str(Path(__file__).with_name('capture_validation.py')),
                                  '--cwd', str(root), '--output', str(output), '--timeout', '1',
                                  '--', sys.executable, '-c', parent], capture_output=True, timeout=15)
            self.assertEqual(124, run.returncode, run.stderr)
            metadata = json.loads(output.read_text())
            self.assertEqual('timeout', metadata['state'])
            self.assertTrue(metadata['process_tree_stopped'])
            self.assertGreater(int(output.with_suffix('.txt').read_text().strip()), 0)
            time.sleep(4)
            self.assertFalse(marker.exists(), 'child survived wrapper timeout')


if __name__ == '__main__':
    unittest.main()
