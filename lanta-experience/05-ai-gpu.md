# 05 AI And GPU Check

ใช้ตรวจว่า job ได้ GPU จริงก่อนเริ่มงาน AI ที่กินทรัพยากรมาก.

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

### คำอธิบายเชิงเรื่องเล่า

งาน GPU ไม่ควรเริ่มจาก training ขนาดใหญ่ แต่ควรเริ่มจากการถามระบบอย่างสุภาพว่าได้รับ GPU จริงหรือไม่ Block นี้จึงสร้าง Slurm job ที่ขอ GPU หนึ่งใบ แล้วเปิดสภาพแวดล้อมของ LANTA ตามแนวทางของบทเรียน AI ด้วย `module load Mamba/23.11.0-0` และ `conda activate pytorch-2.2.2` ก่อนเรียก Python เพื่อให้ผู้เรียนใช้ PyTorch ชุดเดียวกับที่ระบบเตรียมไว้ ไม่ต้องติดตั้งเองบน login node และไม่ต้องเสี่ยงผสม CUDA หลายชุดโดยไม่จำเป็น

ในเชิงวิธีวิทยา `nvidia-smi` ยืนยันระดับเครื่องและ driver ส่วน `torch.cuda.is_available()` ยืนยันระดับ Python environment ทั้งสองชั้นต้องสัมพันธ์กันจึงจะเริ่มงาน AI ได้อย่างมั่นใจ การใช้ `gpu-devel` และ GPU เพียงหนึ่งใบช่วยลดเวลารอและลดต้นทุนของการ debug ก่อนขยายไปสู่ training จริง ส่วนบรรทัด `export PATH` ทำหน้าที่เหมือนเข็มหมุดที่ชี้ไปยัง Python ของ environment `pytorch-2.2.2` โดยตรง แม้ `conda activate` จะตั้งค่าให้แล้วในกรณีปกติ การระบุเส้นทางซ้ำทำให้ตัวอย่างนี้สอดคล้องกับคู่มือ AI หลาย GPU และอ่านย้อนกลับได้ง่ายเมื่อเกิดปัญหา

สัญญาณที่ดีคือ log มีตารางจาก `nvidia-smi` ตามด้วย `torch 2.2.2+cu118`, `cuda_available True`, `gpu_count` มากกว่าศูนย์, ชื่อ GPU และ `status ok` หลังคำนวณ matrix บน GPU สำเร็จ หาก `conda activate pytorch-2.2.2` ล้มเหลวให้ตรวจว่าโหลด `Mamba/23.11.0-0` แล้วจริงหรือไม่และใช้ `conda env list` เพื่อดู environment ที่ระบบมี หาก `nvidia-smi` ผ่านแต่ PyTorch ไม่เห็น CUDA ให้ตรวจว่า job ถูกรันผ่าน `sbatch` ไม่ใช่ `bash jobs/gpu_check.sbatch` และให้ดูว่า Slurm จัด GPU ให้จริงผ่าน `CUDA_VISIBLE_DEVICES` หรือไม่ หาก submit ถูกปฏิเสธให้ตรวจ `--gpus-per-node=1`, partition และ account หาก pending นานให้ดู reason ด้วย `squeue -j <jobid>` ก่อนเพิ่มเวลาหรือขยายจำนวน GPU

## Next Modification

หลังเห็น `nvidia-smi` และ `cuda_available True` แล้ว ค่อยเปลี่ยน Python block ให้โหลดโมเดลหรือข้อมูลขนาดเล็กของทีม.
