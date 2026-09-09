"""Exercise the validator against real temporary Git repositories."""

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('validator', Path(__file__).with_name('validate.py'))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init')
        self.git('config', 'user.name', 'Documentation Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('engine.py', 'original\n')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.base = self.git('rev-parse', 'HEAD')
        self.state = {'observed_utc': '2026-09-09T00:00:00+00:00', 'main': self.base,
                      'official': [{'head': self.base}], 'candidates': []}
        self.checkpoint = {key: 'not applicable: documentation test' for key in validator.REQUIRED}
        self.checkpoint.update(date='2026-09-09', branch='test', head=self.base,
                               base=self.base, pr='not-created', references=[{'path': 'engine.py'}])
        self.sync()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root,
                                       text=True, encoding='utf-8', stderr=subprocess.DEVNULL).strip()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def sync(self):
        self.write(validator.STATUS, '# Status\n\n```json\n' + json.dumps(self.state) + '\n```\n')
        self.write('docs/checkpoints/test.md', '# Checkpoint\n\n```json\n' + json.dumps(self.checkpoint) + '\n```\n')
        self.git('add', '.')

    def errors(self):
        return validator.validate(self.root, self.base, self.base, True)

    def test_valid_delivery(self):
        self.assertEqual([], self.errors())

    def test_missing_required_field(self):
        del self.checkpoint['tests']
        self.sync()
        self.assertTrue(any('missing field tests' in e for e in self.errors()))

    def test_unavailable_commit(self):
        self.checkpoint['head'] = 'f' * 40
        self.sync()
        self.assertTrue(any('commit unavailable' in e for e in self.errors()))

    def test_ignored_checkpoint_does_not_satisfy_delivery(self):
        self.git('rm', '--cached', 'docs/checkpoints/test.md')
        self.write('.gitignore', '.claude/\n')
        self.write('.claude/checkpoints/only-local.md', 'private working note')
        self.git('add', '.gitignore')
        self.assertTrue(any('requires a versioned' in e for e in self.errors()))

    def test_missing_reference(self):
        self.checkpoint['references'] = [{'path': 'absent.md', 'commit': self.base}]
        self.sync()
        self.assertTrue(any('missing path at commit' in e for e in self.errors()))

    def test_broken_local_link(self):
        self.sync()
        with (self.root / validator.STATUS).open('a', encoding='utf-8') as handle:
            handle.write('\n[Missing](missing.md)\n')
        self.assertTrue(any('broken/untracked link' in e for e in self.errors()))

    def test_untracked_existing_link(self):
        self.write('docs/local.md', 'not staged')
        with (self.root / validator.STATUS).open('a', encoding='utf-8') as handle:
            handle.write('\n[Local](local.md)\n')
        self.assertTrue(any('broken/untracked link' in e for e in self.errors()))

    def test_production_after_reviewed_head(self):
        self.write('engine.py', 'changed\n')
        self.assertTrue(any('after reviewed HEAD' in e for e in self.errors()))

    def test_historical_checkpoint_alone_cannot_approve_delivery(self):
        self.checkpoint['scope'] = 'historical'
        self.sync()
        self.assertTrue(any('requires a current checkpoint' in e for e in self.errors()))

    def test_historical_stage_preserves_its_original_head_with_current_review(self):
        self.checkpoint['scope'] = 'historical'
        self.sync()
        self.write('engine.py', 'changed\n')
        self.git('add', '.')
        self.git('commit', '-m', 'new stage')
        current = dict(self.checkpoint, scope='current', head=self.git('rev-parse', 'HEAD'))
        self.write('docs/checkpoints/current.md', '```json\n' + json.dumps(current) + '\n```\n')
        self.git('add', '.')
        self.assertEqual([], self.errors())
        self.write('engine.py', 'unreviewed\n')
        self.assertTrue(any('after reviewed HEAD' in e for e in self.errors()))

    def test_historical_references_are_still_validated(self):
        self.checkpoint.update(scope='historical', references=[{'path': 'missing.py'}])
        self.sync()
        self.assertTrue(any('missing tracked reference' in e for e in self.errors()))

    def test_old_status_rejected_after_main_moves(self):
        self.git('commit', '-m', 'main advances')
        errors = validator.validate(self.root, self.base, 'HEAD', True)
        self.assertTrue(any('main changed' in e for e in errors))

    def test_candidate_cannot_be_official(self):
        self.git('checkout', '-b', 'candidate')
        self.write('docs/new.md', 'candidate')
        self.git('add', '.')
        self.git('commit', '-m', 'candidate only')
        candidate = self.git('rev-parse', 'HEAD')
        self.state['official'] = [{'head': candidate}]
        self.sync()
        self.assertTrue(any('not integrated' in e for e in self.errors()))

    def test_integrated_candidate_is_stale(self):
        self.state['candidates'] = [{'head': self.base}]
        self.sync()
        self.assertTrue(any('candidate already integrated' in e for e in self.errors()))

    def test_captured_log_hash(self):
        log = 'docs/checkpoints/evidence/run.txt'
        self.write(log, 'passed\n')
        digest = hashlib.sha256((self.root / log).read_bytes()).hexdigest()
        self.write('docs/checkpoints/evidence/run.json', json.dumps({
            'head': self.base, 'state': 'completed', 'log': 'run.txt', 'log_sha256': digest}))
        self.git('add', '.')
        self.assertEqual([], self.errors())
        self.write(log, 'modified\n')
        self.assertTrue(any('log hash mismatch' in e for e in self.errors()))


if __name__ == '__main__':
    unittest.main()
