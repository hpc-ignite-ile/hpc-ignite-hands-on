# บทที่ 12: AI Development บน HPC

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-pytorch-train` โดยตรง

## เป้าหมาย

1. ขอ GPU หนึ่งใบ
2. รัน tiny training loop ด้วย PyTorch
3. ตรวจ loss, CUDA และ GPU name

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-pytorch-train"
cd "$HOME/hpc-ignite-standalone/ai-pytorch-train"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_GPU_PARTITION:-}" ]; then export LANTA_GPU_PARTITION="gpu-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

cat > src/tiny_train.py <<'PYCODE'
from pathlib import Path
import json
import torch
Path("results").mkdir(exist_ok=True)
summary = {"torch": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "gpu_count": torch.cuda.device_count()}
if torch.cuda.is_available():
    model = torch.nn.Linear(4, 2).to("cuda"); opt = torch.optim.SGD(model.parameters(), lr=0.1)
    x = torch.randn(64, 4, device="cuda"); target = torch.randint(0, 2, (64,), device="cuda"); loss_fn = torch.nn.CrossEntropyLoss()
    for _ in range(5):
        opt.zero_grad(); loss = loss_fn(model(x), target); loss.backward(); opt.step()
    torch.cuda.synchronize(); summary["gpu_name"] = torch.cuda.get_device_name(0); summary["final_loss"] = float(loss.detach().cpu())
Path("results/tiny_train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/tiny_train.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=tiny-train
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
python src/tiny_train.py | tee "results/${SLURM_JOB_ID}/torch.txt"
cp results/tiny_train_summary.json "results/${SLURM_JOB_ID}/tiny_train_summary.json"
SLURM
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/tiny_train.sbatch)
echo "$job_id	tiny_train	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -80 logs/tiny-train_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/ai-pytorch-train"
cat results/tiny_train_summary.json
tail -80 logs/tiny-train_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
