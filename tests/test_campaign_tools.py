import ast
import importlib.util
import json
import re
import tarfile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CampaignTests(unittest.TestCase):
    def test_beginner_images_and_links(self):
        guide = ROOT/'docs/BEGINNER_VISUAL_GUIDE_TH.md'
        text = guide.read_text()
        images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
        self.assertEqual(len(images), 4)
        for image in images:
            path = guide.parent/image
            self.assertTrue(path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        for path in (guide, ROOT/'docs/lanta-runs/2026-09-26-pv915002/README.md'):
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not link.startswith(('http:', 'https:', '#')):
                    self.assertTrue((path.parent/link.split('#')[0]).exists(), f'{path}: {link}')

    def test_evidence_is_terminal_and_tokens_are_redacted(self):
        folder = ROOT/'docs/lanta-runs/2026-09-26-pv915002'
        rows = json.loads((folder/'workflow-status.json').read_text())
        self.assertEqual(sum(r['states'] == 'COMPLETED' for r in rows), 70)
        self.assertEqual(sum(r['states'] == 'FAILED' for r in rows), 3)
        with tarfile.open(folder/'artifacts.tar.gz') as archive:
            for member in archive:
                if member.isfile() and not member.name.endswith('.png'):
                    data = archive.extractfile(member).read().decode('utf-8', errors='replace')
                    self.assertIsNone(re.search(r'(?i)token=[a-z0-9]{16,}', data), member.name)

    def test_extraction_is_idempotent_and_sources_compile(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            command = [sys.executable, str(ROOT/'scripts/extract_tutorial_files.py'), tmp]
            subprocess.run(command, check=True, capture_output=True)
            before = {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            subprocess.run(command, check=True, capture_output=True)
            after = {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            manifest = json.loads((target/'manifest.json').read_text())
            self.assertEqual(sum(len(r['jobs']) for r in manifest), 44)
            for path in target.rglob('*.py'):
                ast.parse(path.read_text(), filename=str(path))
            for path in target.rglob('*.sbatch'):
                subprocess.run(['bash','-n',str(path)], check=True, capture_output=True)
            display = target/'mini-innovation/05-output-display-jupyter-gnuplot'
            subprocess.run([sys.executable,'src/make_display_notebook.py'], cwd=display, check=True, capture_output=True)
            notebook = json.loads((display/'notebooks/mini_innovation_display.ipynb').read_text())
            for cell in notebook['cells']:
                if cell['cell_type'] == 'code':
                    ast.parse(''.join(cell['source']))

    def test_accounting_units(self):
        spec = importlib.util.spec_from_file_location('evidence', ROOT/'scripts/collect_campaign_evidence.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.seconds('1-01:02:03'), 90123)
        self.assertAlmostEqual(module.seconds('00:02.125'), 2.125)
        self.assertEqual(module.rss_kib('1.5G'), 1572864)
        self.assertEqual(module.rss_kib(''), 0)


if __name__ == '__main__':
    unittest.main()
