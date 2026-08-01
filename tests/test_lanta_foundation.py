from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = REPO_ROOT / "foundation" / "lanta-foundation"


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=FOUNDATION,
        check=True,
        text=True,
        capture_output=True,
    )


class LantaFoundationTests(unittest.TestCase):
    def test_verify_lanta_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "system.json"
            result = run_python("verify_lanta.py", "--write-json", str(output))
            self.assertIn("HPC Ignite: LANTA Foundation Smoke Test", result.stdout)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["python"]["version"])
            self.assertIn("SLURM_JOB_ID", data["slurm"])

    def test_serial_sum_runs(self) -> None:
        result = run_python("serial_sum.py", "--n", "1000")
        self.assertIn("pi estimate", result.stdout)
        self.assertIn("abs error", result.stdout)

    def test_array_task_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "task.csv"
            run_python("array_task.py", "--task-id", "2", "--task-count", "4", "--output", str(output))
            with output.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["task_id"], "2")
            self.assertEqual(rows[0]["task_count"], "4")
            self.assertEqual(rows[0]["n"], "100000")
            self.assertTrue(rows[0]["pi_estimate"])

    def test_sbatch_files_exist(self) -> None:
        for name in ["00-smoke-cpu.sbatch", "01-array-foundation.sbatch", "02-env-report.sbatch"]:
            self.assertTrue((FOUNDATION / "jobs" / name).exists())

    def test_event_guides_exist(self) -> None:
        event_dir = REPO_ROOT / "lanta-experience"
        for name in [
            "README.md",
            "00-readiness.md",
            "01-first-slurm-job.md",
            "02-cpu-array.md",
            "03-openmp-mpi.md",
            "04-science-data.md",
            "05-ai-gpu.md",
        ]:
            self.assertTrue((event_dir / name).exists())

    def test_learner_docs_do_not_use_hidden_submit_helpers(self) -> None:
        learner_docs = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "LANTA_SETUP.md",
            REPO_ROOT / "docs" / "COPY_PASTE_ONLY_LABS_TH.md",
            REPO_ROOT / "docs" / "LAB_AUTHORING_GUIDE_TH.md",
            FOUNDATION / "README.md",
        ]
        forbidden = ["lanta" + "_submit_", "/tmp/hpc" + "_ignite_", "bash /tmp/hpc" + "_ignite"]
        for doc in learner_docs:
            text = doc.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} found in {doc}")


if __name__ == "__main__":
    unittest.main()
