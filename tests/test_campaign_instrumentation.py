import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstrumentationTests(unittest.TestCase):
    def test_fresh_campaign_coverage_and_captures(self):
        folder = ROOT/'docs/lanta-runs/2026-09-26-performance'
        rows = json.loads((folder/'workflow-status.json').read_text())
        self.assertEqual(len(rows), 72)
        self.assertTrue(all(r['states']=='COMPLETED' for r in rows))
        self.assertEqual(sum(r['workflow'].startswith('tutorial:') for r in rows), 44)
        captures = json.loads((folder/'capture-manifest.json').read_text())['captures']
        self.assertEqual(len(captures), 41)
        for record in captures:
            self.assertEqual(hashlib.sha256((folder/record['html']).read_bytes()).hexdigest(),record['html_sha256'])
            self.assertEqual(hashlib.sha256((folder/record['screenshot']).read_bytes()).hexdigest(),record['png_sha256'])
        self.assertTrue(json.loads((folder/'seir-correctness.json').read_text())['pass'])

    def test_directives_and_body_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'tutorials').mkdir()
            (root/'tutorials/manifest.json').write_text('[]')
            original = '#!/bin/bash\n#SBATCH --cpus-per-task=2\necho hello\n'
            job = root/'tutorials/test.sbatch'
            job.write_text(original)
            subprocess.run([sys.executable, ROOT/'scripts/instrument_campaign.py', root], check=True, capture_output=True)
            self.assertEqual(job.with_suffix('.sbatch.body').read_text(), original)
            self.assertIn('#SBATCH --cpus-per-task=2', job.read_text())
            subprocess.run(['bash', '-n', job], check=True)
            self.assertEqual(len(json.loads((root/'instrumentation.json').read_text())), 1)

    def test_snapshot_redacts_and_limits_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'results').mkdir()
            (root/'notes').mkdir()
            (root/'results/example.txt').write_text('token=abcdefghijklmnopqrstuv')
            (root/'results/large.txt').write_bytes(b'x'*2_000_001)
            subprocess.run([sys.executable, ROOT/'scripts/snapshot_campaign_result.py', root/'notes', root], check=True)
            self.assertEqual((root/'notes/results/example.txt').read_text(), 'token=REDACTED')
            self.assertFalse((root/'notes/results/large.txt').exists())


if __name__ == '__main__':
    unittest.main()
