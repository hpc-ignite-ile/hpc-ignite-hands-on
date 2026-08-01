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

### คำอธิบายเชิงเรื่องเล่า

งาน GPU ไม่ควรเริ่มจาก training ขนาดใหญ่ แต่ควรเริ่มจากการถามระบบอย่างสุภาพว่าได้รับ GPU จริงหรือไม่ Block นี้จึงสร้าง Slurm job ที่ขอ GPU หนึ่งใบ โหลด CUDA หรือ PyTorch เท่าที่ระบบมีให้ แล้วบันทึกทั้ง `nvidia-smi` และผลตรวจ PyTorch ลงใน log

ในเชิงวิธีวิทยา `nvidia-smi` ยืนยันระดับเครื่องและ driver ส่วน `torch.cuda.is_available()` ยืนยันระดับ Python environment ทั้งสองชั้นต้องสัมพันธ์กันจึงจะเริ่มงาน AI ได้อย่างมั่นใจ การใช้ `gpu-devel` และ GPU เพียงหนึ่งใบช่วยลดเวลารอและลดต้นทุนของการ debug ก่อนขยายไปสู่ training จริง

สัญญาณที่ดีคือ log มีตารางจาก `nvidia-smi` และถ้า environment พร้อมจะเห็น `cuda_available True` พร้อมผลคำนวณ matrix บน GPU หาก `nvidia-smi` ผ่านแต่ PyTorch ไม่เห็น CUDA ปัญหามักอยู่ที่ environment ไม่ใช่ allocation หาก submit ถูกปฏิเสธให้ตรวจ `--gpus-per-node=1` และ partition หาก pending นานให้ดู reason ด้วย `squeue` และหาก CUDA module ไม่ตรงกับ PyTorch ให้ใช้ module หรือ environment ที่ ThaiSC แนะนำก่อนเริ่มงานใหญ่

## Next Modification

หลังเห็น `nvidia-smi` และ `cuda_available True` แล้ว ค่อยเปลี่ยน Python block ให้โหลดโมเดลหรือข้อมูลขนาดเล็กของทีม.
