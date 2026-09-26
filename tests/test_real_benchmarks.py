import ast
import csv
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/lanta-runs/2026-09-26-real-benchmarks'

class RealBenchmarks(unittest.TestCase):
    def test_script_syntax(self):
        for p in (ROOT/'benchmarks/real').glob('*.py'):
            ast.parse(p.read_text(),filename=str(p))
        for p in (ROOT/'benchmarks/real').glob('*.sbatch'):
            subprocess.run(['bash','-n',str(p)],check=True)

    def test_global_scientific_gates_have_full_matrices(self):
        results=json.loads((EVIDENCE/'validation.json').read_text())
        for name,count in [('athena-6340337',27),('miniweather-6340319',36),('mitgcm-6340345',6)]:
            self.assertEqual(results[name]['gate'],'PASS')
            self.assertEqual(len(results[name]['runs']),count)

    def test_failure_history_and_misleading_zero_exit_are_preserved(self):
        rows={r['JobID']:r for r in csv.DictReader((EVIDENCE/'accounting.psv').read_text().splitlines(),delimiter='|')}
        self.assertEqual(rows['6340324']['State'],'COMPLETED')
        self.assertEqual(rows['6340323']['State'],'FAILED')
        report=(EVIDENCE/'README.md').read_text()
        self.assertIn('scientifically INVALID',report)
        self.assertIn('timing pilot only',report)
        self.assertIn('Neither is billed SHr',report)
        for link in re.findall(r'\]\(([^)]+)\)',report):
            if not link.startswith(('https:','http:','#')):
                self.assertTrue((EVIDENCE/link.split('#')[0]).exists(),link)

if __name__=='__main__': unittest.main()
