# LANTA Setup Guide

คู่มือเริ่มต้นสำหรับใช้ repo นี้บน LANTA ตาม booklet ของงาน LANTA HPC Experience Day: On the Move.

คำสั่งและ syntax ในหน้านี้อธิบายรวมไว้ที่ [docs/BASH_COMMAND_REFERENCE_TH.md](docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `scp`, `rsync`, `git clone`, `module`, `sbatch`, `squeue`, `sacct`, heredoc และ `#SBATCH`

## 1. SSH To LANTA

```bash
ssh <username>@lanta.nstda.or.th
```

ใช้ transfer host สำหรับย้ายไฟล์ขนาดใหญ่:

```bash
scp local-file <username>@transfer.lanta.nstda.or.th:/project/<project-id>/
rsync -rvz ./local-folder/ <username>@transfer.lanta.nstda.or.th:/project/<project-id>/local-folder/
```

หลัง login แล้ว prompt ที่เห็นคือ shell บน LANTA. ใช้ login node สำหรับแก้ไฟล์ ตรวจระบบ และส่งงานเท่านั้น.

## 2. Clone Repository

```bash
cd "$HOME"
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on
```

## 3. Create The Event Workspace

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
```

Then follow [lanta-experience/README.md](lanta-experience/README.md).

## 4. First Job Pattern

Teaching pattern นี้ให้ผู้ใช้เห็นไฟล์ที่สร้างจริงด้วย heredoc และเห็น `.sbatch` ที่ส่งด้วย `sbatch` โดยตรง:

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs results src

cat > src/main.py <<'PY'
from pathlib import Path
Path("results").mkdir(exist_ok=True)
Path("results/main.txt").write_text("hello from LANTA\n", encoding="utf-8")
print("results/main.txt")
PY

cat > jobs/main.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
python src/main.py
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "${LANTA_CPU_PARTITION:-compute-devel}" --parsable jobs/main.sbatch)
echo "Submitted: $job_id"
squeue -j "$job_id"
```

## Storage

Official LANTA training material describes these common storage areas:

| Path | Typical use |
|---|---|
| `/home/<username>` | Personal scripts, small source trees, configs |
| `/project/<project-id>` | Shared project data, builds, job output |
| `/scratch/<project-id>` | Temporary high-throughput work files |

Check live quota before large work:

```bash
myquota
sbalance
df -h "$HOME" "$PWD"
```

## Partitions

Use `sinfo` for live partition status. For teaching:

```bash
sinfo -o "%P %a %l %D %t %N"
```

Start small:

| Workload | First partition to try | Notes |
|---|---|---|
| CPU smoke test | `compute-devel` | short job, small memory |
| CPU full run | `compute` | scale only after output is correct |
| GPU smoke test | `gpu-devel` | one GPU check first |
| GPU full run | `gpu` | request only the GPUs you use |
| High-memory work | `memory` | use when compute memory is insufficient |

## Modules

```bash
module avail
module spider python
module spider Mamba
module spider Apptainer
module spider QuantumESPRESSO
module spider GROMACS
module spider GDAL
module spider BLAST+
module list
```

Load modules inside the Slurm script so the job is reproducible. For this repo, prefer the wrappers in `slurm/module-loads/`: `base.sh`, `netcdf-python.sh`, `pytorch-shared.sh`, `cpe-mpi.sh`, `qe.sh`, `gromacs.sh`, `geodata.sh`, `bio.sh`, and `apptainer.sh`.

## Monitoring

```bash
squeue -u "$USER"
squeue -j <job-id> -o "%.18i %.9P %.20j %.8T %.20R"
sacct -j <job-id> --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
tail -50 logs/<name>_<job-id>.out
tail -50 logs/<name>_<job-id>.err
scancel <job-id>
```

## Next

Use the booklet-aligned labs:

```bash
sed -n '1,160p' "$HOME/hpc-ignite-hands-on/lanta-experience/README.md"
```

อ่านคำอธิบาย `sed -n '1,160p' ...` ได้ที่ [docs/BASH_COMMAND_REFERENCE_TH.md#sed](docs/BASH_COMMAND_REFERENCE_TH.md#sed)
