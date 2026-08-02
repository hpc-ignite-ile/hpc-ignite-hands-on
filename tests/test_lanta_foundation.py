from __future__ import annotations

import csv
import json
import re
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

    def test_chapter_02_environment_json(self) -> None:
        chapter = REPO_ROOT / "core-hpc" / "chapter-02-environment"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "system.json"
            result = subprocess.run(
                [sys.executable, "check_environment.py", "--write-json", str(output)],
                cwd=chapter,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("Environment check complete", result.stdout)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["python"]["version"])
            self.assertIn("packages", data)

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

    def test_bash_command_reference_is_linked_from_command_docs(self) -> None:
        reference = REPO_ROOT / "docs" / "BASH_COMMAND_REFERENCE_TH.md"
        self.assertTrue(reference.exists())
        for path in REPO_ROOT.rglob("*.md"):
            if path == reference or ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "```bash" in text:
                self.assertIn("BASH_COMMAND_REFERENCE_TH.md", text, f"missing command reference link in {path}")

    def test_bash_blocks_are_short_semantic_tasks(self) -> None:
        max_lines = 60
        for path in REPO_ROOT.rglob("*.md"):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"```bash\n(.*?)\n```", text, flags=re.DOTALL):
                block = match.group(1)
                lines = block.splitlines()
                self.assertTrue(any(line.strip() for line in lines), f"empty bash block in {path}")
                self.assertLessEqual(
                    len(lines),
                    max_lines,
                    f"bash block in {path} has {len(lines)} lines; split into one semantic task per block",
                )

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

    def test_learner_markdown_submits_standalone_jobs(self) -> None:
        learner_roots = [
            REPO_ROOT / "foundation",
            REPO_ROOT / "core-hpc",
            REPO_ROOT / "ai-applications",
            REPO_ROOT / "domain-science",
            REPO_ROOT / "lanta-experience",
            REPO_ROOT / "mini-innovation",
        ]
        forbidden_patterns = {
            r"source\s+(?:['\"])?(?:\./|\.\./)*slurm/module-loads/": "sources repo module wrapper",
            r"sbatch[^\n]*(?:foundation|core-hpc|ai-applications|domain-science|mini-innovation|lanta-experience)/": "submits repo-relative job path",
            r"cd\s+['\"]?\$HOME/hpc-ignite-hands-on": "requires cloned repo directory",
        }
        for root in learner_roots:
            for path in root.rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                for pattern, reason in forbidden_patterns.items():
                    self.assertIsNone(re.search(pattern, text), f"{path} {reason}")
                if re.search(r"^\s*(?:job_id=\$\(sbatch|sbatch\s)", text, flags=re.MULTILINE):
                    self.assertRegex(
                        text,
                        r"cat\s+>\s+jobs/[^`\n]+\.sbatch\s+<<",
                        f"{path} should create a local jobs/*.sbatch file in the page",
                    )
                    self.assertRegex(
                        text,
                        r"sbatch[^\n]*jobs/[^`\n]+\.sbatch",
                        f"{path} should submit the local jobs/*.sbatch file",
                    )

    def test_lanta_module_wrappers_exist(self) -> None:
        module_dir = REPO_ROOT / "slurm" / "module-loads"
        for name in [
            "base.sh",
            "netcdf-python.sh",
            "pytorch-shared.sh",
            "cpe-mpi.sh",
            "qe.sh",
            "gromacs.sh",
            "geodata.sh",
            "bio.sh",
            "apptainer.sh",
        ]:
            path = module_dir / name
            self.assertTrue(path.exists(), f"missing module wrapper {path}")

    def test_no_stale_lanta_module_names_in_live_materials(self) -> None:
        stale_markers = [
            "Miniconda3",
            "PyTorch/2.0.1-CUDA-11.7.0",
            "CUDA/11.7.0",
            "TensorFlow/2.11.0-CUDA-11.7.0",
            "Singularity/3.8.3",
            "WRF-Chem/4.4",
            "Spark/3.3.0",
            "OpenMPI/4.1.2",
            "hpc-ignite-base",
            "pip install cupy-cuda11x",
        ]
        excluded = {
            REPO_ROOT / "docs" / "LANTA_REAL_MINI_WORKFLOW_AUDIT_TH.md",
            REPO_ROOT / "tests" / "test_lanta_foundation.py",
        }
        suffixes = {".md", ".py", ".sh", ".sbatch", ".txt", ".yaml", ".yml"}
        for path in REPO_ROOT.rglob("*"):
            if path in excluded or path.suffix not in suffixes or ".git" in path.parts:
                continue
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in stale_markers:
                self.assertNotIn(marker, text, f"{marker} found in {path}")

    def test_real_mini_workflow_jobs_exist(self) -> None:
        expected_jobs = [
            "core-hpc/chapter-02-environment/jobs/environment_audit.sbatch",
            "core-hpc/chapter-03-parallel/jobs/mpi_rank_smoke.sbatch",
            "core-hpc/chapter-04-deep-learning/jobs/gpu_smoke.sbatch",
            "core-hpc/chapter-08-mpi/jobs/mpi_collective_smoke.sbatch",
            "core-hpc/chapter-10-gpu/jobs/gpu_smoke.sbatch",
            "ai-applications/chapter-11-containers/jobs/apptainer_smoke.sbatch",
            "ai-applications/chapter-12-ai-development/jobs/pytorch_gpu_smoke.sbatch",
            "mini-innovation/jobs/epi_smoke.sbatch",
            "domain-science/chapter-20-computational-chemistry/jobs/chemistry_preflight.sbatch",
            "domain-science/chapter-21-molecular-dynamics/jobs/gromacs_gpu_smoke.sbatch",
            "domain-science/chapter-22-climate-modeling/jobs/netcdf_wrf_summary.sbatch",
            "domain-science/chapter-23-materials-science/jobs/qe_scf_smoke.sbatch",
            "domain-science/chapter-24-ai-forest/jobs/gdal_forest_smoke.sbatch",
            "domain-science/chapter-25-bioinformatics/jobs/blast_cli_smoke.sbatch",
            "domain-science/chapter-26-smart-agriculture/jobs/agri_geodata_smoke.sbatch",
            "domain-science/chapter-27-disaster-prevention/jobs/hazard_grid_smoke.sbatch",
        ]
        for rel in expected_jobs:
            path = REPO_ROOT / rel
            self.assertTrue(path.exists(), f"missing workflow job {rel}")
            text = path.read_text(encoding="utf-8")
            self.assertIn("results/", text, f"job should write job-scoped results: {rel}")

    def test_gpu_jobs_use_gpu_devel_for_smoke_tests(self) -> None:
        gpu_jobs = [
            REPO_ROOT / "core-hpc/chapter-04-deep-learning/jobs/gpu_smoke.sbatch",
            REPO_ROOT / "core-hpc/chapter-10-gpu/jobs/gpu_smoke.sbatch",
            REPO_ROOT / "ai-applications/chapter-12-ai-development/jobs/pytorch_gpu_smoke.sbatch",
            REPO_ROOT / "domain-science/chapter-21-molecular-dynamics/jobs/gromacs_gpu_smoke.sbatch",
            REPO_ROOT / "slurm/templates/single-gpu.sbatch",
            REPO_ROOT / "slurm/templates/multi-gpu.sbatch",
            REPO_ROOT / "slurm/templates/gromacs-gpu-smoke.sbatch",
        ]
        for path in gpu_jobs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("#SBATCH --partition=gpu-devel", text, f"GPU smoke should use gpu-devel: {path}")

    def test_mpi_jobs_use_srun_with_multiple_tasks(self) -> None:
        for rel in [
            "core-hpc/chapter-03-parallel/jobs/mpi_rank_smoke.sbatch",
            "core-hpc/chapter-08-mpi/jobs/mpi_collective_smoke.sbatch",
        ]:
            path = REPO_ROOT / rel
            text = path.read_text(encoding="utf-8")
            self.assertIn("#SBATCH --ntasks=4", text)
            self.assertIn("srun -n", text)

    def test_mini_innovation_jupyter_env_is_declared(self) -> None:
        setup = (REPO_ROOT / "mini-innovation" / "01-custom-python-env-module.md").read_text(encoding="utf-8")
        notebook = (REPO_ROOT / "mini-innovation" / "02-jupyter-notebook.md").read_text(encoding="utf-8")
        for marker in [
            '"jupyterlab>=4,<5"',
            '"notebook>=7,<8"',
            "ipykernel",
            "jupyter lab --version",
            "python -m ipykernel install --user --name hpc-mesa",
            "jupyter kernelspec list",
        ]:
            self.assertIn(marker, setup)
        self.assertIn("jupyter lab --no-browser", notebook)
        self.assertIn('JUPYTER_SERVER_SOURCE:-hpc-mesa', notebook)
        self.assertIn("LANTA_JUPYTER_MODULE", notebook)

    def test_epidemic_tutorial_uses_model_rng_and_small_training_load(self) -> None:
        text = (REPO_ROOT / "mini-innovation" / "03-epidemic-abs-examples.md").read_text(encoding="utf-8")
        self.assertNotIn("other.state == S and self.model.random.random()", text)
        self.assertIn("self.random.random()", text)
        self.assertIn("#SBATCH --array=1-8%2", text)
        self.assertIn("--agents 1500", text)
        self.assertIn("--days 45", text)


if __name__ == "__main__":
    unittest.main()
