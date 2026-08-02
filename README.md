# HPC Ignite Hands-On Labs

[![LANTA Compatible](https://img.shields.io/badge/LANTA-Compatible-blue.svg)](https://docs.lanta.nstda.or.th)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Runnable copy-paste labs for Thailand's LANTA supercomputer. The main path now follows the event booklet `LANTA HPC Handbook` for **LANTA HPC Experience Day: On the Move**.

## Quick Start On LANTA

```bash
cd "$HOME"
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on

# Start with the booklet-aligned event flow.
sed -n '1,120p' lanta-experience/README.md
```

For the first real job, open [lanta-experience/01-first-slurm-job.md](lanta-experience/01-first-slurm-job.md) and paste the block on LANTA. It creates `src/hello_lanta.py` and `jobs/hello_lanta.sbatch` with heredoc, then submits directly with `sbatch`.

## Booklet-Aligned Structure

```text
hpc-ignite-hands-on/
├── lanta-experience/        # Main event path from the booklet
│   ├── 00-readiness.md      # Linux, shell, files, quota, modules
│   ├── 01-first-slurm-job.md
│   ├── 02-cpu-array.md
│   ├── 03-openmp-mpi.md
│   ├── 04-science-data.md
│   └── 05-ai-gpu.md
├── foundation/              # Reusable foundation scripts and older chapter material
├── core-hpc/                # Reference chapters: environment, parallel, data, MPI, GPU
├── ai-applications/         # Reference AI chapters
├── domain-science/          # Reference science/domain chapters
├── mini-innovation/         # Scaffolded epidemic ABS innovation labs
├── environments/            # Optional Conda/Mamba environment files
├── slurm/                   # Reusable Slurm templates and module-load snippets
├── docs/                    # Authoring guide and copy-paste conventions
├── requirements/            # Optional pip requirements
└── tests/                   # Local validation
```

## Event Flow

| Booklet section | Repo guide | Main activity |
|---|---|---|
| Linux, shell, files | [00-readiness.md](lanta-experience/00-readiness.md) | Create folders, configs, and system notes |
| First Slurm job | [01-first-slurm-job.md](lanta-experience/01-first-slurm-job.md) | Write `hello_lanta.py` and `hello_lanta.sbatch` using heredoc |
| CPU and arrays | [02-cpu-array.md](lanta-experience/02-cpu-array.md) | Run CPU pi baseline and a small job array |
| OpenMP and MPI | [03-openmp-mpi.md](lanta-experience/03-openmp-mpi.md) | Compile C examples and launch with `srun` |
| Science/data | [04-science-data.md](lanta-experience/04-science-data.md) | Run diffusion/data examples and capture evidence |
| AI/GPU | [05-ai-gpu.md](lanta-experience/05-ai-gpu.md) | Request one GPU and verify CUDA/PyTorch |

## Mini Innovation Path

For a short live training activity with a scientific model, agent-based simulation, and AI scaffolding, use [mini-innovation/README.md](mini-innovation/README.md). The first mini innovation is **LANTA EpiSprint**, a Thai tutorial for epidemic ABS with Mesa, custom Python environments, Jupyter on Slurm, single jobs, job arrays, and multicore ensembles.

## Real Mini Workflow Audit

For a repo-wide evaluation of how to make the examples more LANTA-native, module-backed, and closer to real miniature scientific/developer workflows, see [docs/LANTA_REAL_MINI_WORKFLOW_AUDIT_TH.md](docs/LANTA_REAL_MINI_WORKFLOW_AUDIT_TH.md).

## Copy-Paste Style

Learner-facing labs should avoid hidden submit helpers. A good activity is still mostly copy-paste, but the pasted block should create simple visible files:

```bash
mkdir -p jobs logs results src

cat > src/main.py <<'PY'
print("Hello from LANTA")
PY

cat > jobs/main.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
python src/main.py
SLURM

sbatch -p compute-devel jobs/main.sbatch
```

See [docs/LAB_AUTHORING_GUIDE_TH.md](docs/LAB_AUTHORING_GUIDE_TH.md) for the authoring checklist.

## LANTA Notes

- SSH login host: `lanta.nstda.or.th`
- Transfer host: `transfer.lanta.nstda.or.th`
- Use login nodes for editing, small checks, and job submission only.
- Start with `compute-devel` or `gpu-devel` smoke tests when available, then scale after the result is correct.
- Set `LANTA_ACCOUNT` only if your project requires explicit `sbatch -A`.

## Optional Reference Chapters

The older chapter directories remain useful as source examples and extension material after the event path:

| Track | Topics |
|---|---|
| `foundation/` | HPC basics and first runnable scripts |
| `core-hpc/` | Environment, parallel Python, Dask, MPI, Spark, GPU |
| `ai-applications/` | Containers, AI development, prompts, fine-tuning, security, carbon |
| `domain-science/` | Chemistry, MD, climate, materials, bioinformatics, agriculture, disaster |

## Related Resources

- LANTA User Guide: https://docs.lanta.nstda.or.th
- ThaiSC: https://www.thaisc.io
- Slurm: https://slurm.schedmd.com/documentation.html

## License

MIT License - See [LICENSE](LICENSE) for details.
