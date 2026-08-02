# บทที่ 4: Deep Learning บน HPC

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/gpu-pytorch` โดยตรง

## เป้าหมาย

1. ขอ GPU หนึ่งใบผ่าน Slurm
2. ตรวจ nvidia-smi และ torch CUDA
3. บันทึกผลคำนวณ tensor ขนาดเล็ก

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/gpu-pytorch"
cd "$HOME/hpc-ignite-standalone/gpu-pytorch"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_GPU_PARTITION:-}" ]; then export LANTA_GPU_PARTITION="gpu-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

cat > src/gpu_torch_smoke.py <<'PYCODE'
from pathlib import Path
import json
import torch
Path("results").mkdir(exist_ok=True)
summary = {"torch": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "gpu_count": torch.cuda.device_count()}
if torch.cuda.is_available():
    x = torch.randn(1024, 1024, device="cuda"); y = x @ x; torch.cuda.synchronize()
    summary["gpu_name"] = torch.cuda.get_device_name(0); summary["matrix_sum"] = float(y.sum().cpu())
Path("results/gpu_torch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/gpu_torch.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gpu-torch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true
conda activate pytorch-2.2.2 2>/dev/null || true
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
nvidia-smi | tee "results/${SLURM_JOB_ID}/nvidia-smi.txt"
python src/gpu_torch_smoke.py | tee "results/${SLURM_JOB_ID}/torch.txt"
cp results/gpu_torch_summary.json "results/${SLURM_JOB_ID}/gpu_torch_summary.json"
SLURM
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_torch.sbatch)
echo "$job_id	gpu_torch	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -80 logs/gpu-torch_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/gpu-pytorch"
find results -maxdepth 2 -type f | sort
tail -80 logs/gpu-torch_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
