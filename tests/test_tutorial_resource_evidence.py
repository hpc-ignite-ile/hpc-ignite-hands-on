import hashlib
import importlib.util
import json
import re
import sys
import tarfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import build_tutorial_evidence as evidence


class TutorialEvidenceTests(unittest.TestCase):
    def test_domain_protocols_link_evidence_and_preserve_unexecuted_scope(self):
        tracks = {
            'CFD_CLIMATE_OCEAN_EXPERIMENTS.md': ['OpenFOAM', 'WRF', 'climlab', 'CMIP6', 'MITgcm', 'Oceananigans'],
            'SPACE_ASTRONOMY_EXPERIMENTS.md': ['REBOUND', 'Athena++', 'Astropy', 'SunPy'],
        }
        catalog = (ROOT/'docs/REAL_APPLICATION_EXPERIMENTS.md').read_text()
        for name, applications in tracks.items():
            page = ROOT/'docs'/name
            text = page.read_text()
            self.assertIn(name, catalog)
            self.assertIn('lanta-runs/2026-09-26-real-benchmarks/README.md', text)
            self.assertIn('remain proposed', text)
            self.assertIn('pv915002', text)
            self.assertIn('GiB', text)
            for application in applications:
                self.assertIn(application, text)
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if not target.startswith(('https:', 'http:', '#')):
                    self.assertTrue((page.parent/target.split('#')[0]).is_file(), target)

    def test_all_tutorials_have_scoped_panels_and_valid_local_links(self):
        manifest = json.loads((evidence.OUT/'manifest.json').read_text())
        expected = {str(p.relative_to(ROOT)) for root in evidence.ROOTS for p in (ROOT/root).rglob('*.md')}
        self.assertEqual({m['page'] for m in manifest}, expected)
        for row in manifest:
            page = ROOT/row['page']
            text = page.read_text()
            self.assertEqual(text.count(evidence.START), 1)
            block = text.split(evidence.START)[1].split(evidence.END)[0]
            self.assertIn('Correctness gate:', block)
            self.assertIn('not a new run', block)
            for target in re.findall(r'\]\(([^)]+)\)', block):
                if not target.startswith(('https:', 'http:', '#')):
                    self.assertTrue((page.parent/target.split('#')[0]).is_file(), (page, target))
            if row['jobs']:
                png = ROOT/'docs/images/run-evidence'/row['screenshot']
                self.assertTrue(png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            else:
                self.assertIsNone(row['screenshot'])
                self.assertIn('No page-specific Slurm run', block)

    def test_excerpts_are_traceable_to_archived_bytes(self):
        manifest = json.loads((evidence.OUT/'manifest.json').read_text())
        with tarfile.open(evidence.CAMPAIGN/'artifacts.tar.gz') as archive:
            for row in manifest:
                for sample in row['excerpts']:
                    raw = archive.extractfile(sample['member']).read()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), sample['sha256'])
                    self.assertIn(sample['job'], row['jobs'])

    def test_allocation_rows_do_not_double_count_steps_or_prefix_ids(self):
        rows = [{'JobID': j} for j in ['12', '12.batch', '12_1', '12_1.batch', '123', '123_1']]
        self.assertEqual([r['JobID'] for r in evidence.allocation_rows(rows, '12')], ['12', '12_1'])

    def test_no_match_does_not_invent_evidence_and_failed_jobs_remain(self):
        rows = json.loads((evidence.CAMPAIGN/'workflow-status.json').read_text())
        self.assertEqual(evidence.matching_workflows('lanta-experience/00-readiness.md', rows), [])
        twin = evidence.matching_workflows('mini-innovation/06-twinb-heatlab-repository.md', rows)
        self.assertEqual(sum(r['states'] == 'FAILED' for r in twin), 3)

    def test_original_booklet_assets_and_pdf_hashes(self):
        folder = ROOT/'docs/images/booklet'
        provenance = json.loads((folder/'provenance.json').read_text())
        for asset in provenance['assets']:
            self.assertEqual(hashlib.sha256((folder/asset['file']).read_bytes()).hexdigest(), asset['sha256'])
        self.assertEqual(hashlib.sha256((ROOT/'docs/lanta-hpc-experience-handbook.pdf').read_bytes()).hexdigest(), provenance['handbook_sha256'])

    def test_screenshots_match_captured_html_and_image_hashes(self):
        capture = json.loads((ROOT/'docs/images/run-evidence/capture-manifest.json').read_text())
        for entry in capture['files']:
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(), entry['sha256'], entry['path'])


if __name__ == '__main__':
    unittest.main()
