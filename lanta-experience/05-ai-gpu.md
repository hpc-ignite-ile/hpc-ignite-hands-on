# 05 AI And GPU Check

ใช้ตรวจว่า job ได้ GPU จริงก่อนเริ่มงาน AI ที่กินทรัพยากรมาก.

## Copy-Paste

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"

cat > jobs/gpu_check.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gpu_check
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/gpu_%j.out
#SBATCH --error=logs/gpu_%j.err

set -euo pipefail
module purge
module load CUDA/11.7.0 2>/dev/null || module load cudatoolkit 2>/dev/null || true
module load PyTorch/1.13.1-CUDA-11.7.0 2>/dev/null || module load Mamba/23.11.0-0 2>/dev/null || module load cray-python/3.10.10 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"

echo "job=${SLURM_JOB_ID} node=$(hostname)"
nvidia-smi || true
python - <<'PY'
try:
    import torch
    print("torch", torch.__version__)
    print("cuda_available", torch.cuda.is_available())
    if torch.cuda.is_available():
        x = torch.randn(2000, 2000, device="cuda")
        y = x @ x
        print("matrix_sum", float(y.sum().cpu()))
except Exception as exc:
    print("python_gpu_check_error", repr(exc))
PY
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_check.sbatch)
echo "$job_id	gpu_check	$(date -Is)" >> notes/job-history.tsv
echo "Submitted GPU check: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/gpu_${job_id}.out"
```

## Next Modification

หลังเห็น `nvidia-smi` และ `cuda_available True` แล้ว ค่อยเปลี่ยน Python block ให้โหลดโมเดลหรือข้อมูลขนาดเล็กของทีม.
