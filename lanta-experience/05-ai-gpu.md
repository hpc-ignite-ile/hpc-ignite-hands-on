# 05 AI And GPU Check

ใช้ตรวจว่า job ได้ GPU จริงก่อนเริ่มงาน AI ที่กินทรัพยากรมาก.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `nvidia-smi`, `conda activate`, `python - <<'PY'`, `sbatch`, `squeue`, `tail` และ `CUDA_VISIBLE_DEVICES`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน block เตรียมพื้นที่ใน [README.md](README.md) สำหรับ workspace ของกิจกรรม

## Copy-Paste

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
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
module load Mamba/23.11.0-0
conda activate pytorch-2.2.2
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
cd "$SLURM_SUBMIT_DIR"

echo "job=${SLURM_JOB_ID} node=$(hostname)"
nvidia-smi
python - <<'PY'
import torch

print("torch", torch.__version__)
print("cuda_version", torch.version.cuda)
print("cuda_available", torch.cuda.is_available())
print("gpu_count", torch.cuda.device_count())
if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
    raise SystemExit("PyTorch cannot see the allocated GPU")

x = torch.randn(2000, 2000, device="cuda")
y = x @ x
torch.cuda.synchronize()
print("gpu_name", torch.cuda.get_device_name(0))
print("matrix_sum", float(y.sum().cpu()))
print("status", "ok")
PY
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_check.sbatch)
echo "$job_id	gpu_check	$(date -Is)" >> notes/job-history.tsv
echo "Submitted GPU check: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/gpu_${job_id}.out"
```

### คำอธิบาย

ก่อนรัน training จริง ให้ผู้ใช้ตรวจว่า job ได้ GPU จริงก่อน คำสั่งนี้สร้าง Slurm job ที่ขอ GPU หนึ่งใบ แล้วโหลด `Mamba/23.11.0-0` และ activate environment `pytorch-2.2.2`

ใน job นี้ `nvidia-smi` ใช้ตรวจระดับเครื่อง ส่วน `torch.cuda.is_available()` ใช้ตรวจระดับ Python หากสองคำสั่งนี้ผ่าน ผู้ใช้จึงค่อยขยายไปสู่ model training

เมื่อสำเร็จ log จะมีตารางจาก `nvidia-smi`, ค่า `cuda_available True`, จำนวน GPU มากกว่าศูนย์ และ `status ok` หลังคำนวณ matrix บน GPU เมื่อ `conda activate pytorch-2.2.2` error ให้ใช้ `conda env list` ตรวจ environment เมื่อ `nvidia-smi` ผ่านแต่ PyTorch ยังรายงาน CUDA unavailable ให้ตรวจว่า job ส่งผ่าน `sbatch` และ log มี `CUDA_VISIBLE_DEVICES`

## Next Modification

หลังเห็น `nvidia-smi` และ `cuda_available True` แล้ว ค่อยเปลี่ยน Python block ให้โหลดโมเดลหรือข้อมูลขนาดเล็กของทีม.
