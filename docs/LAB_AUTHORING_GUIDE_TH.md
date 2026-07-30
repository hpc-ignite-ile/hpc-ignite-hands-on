# แนวทางเขียน Lab แบบ Heredoc-First

ทุก lab ใหม่ควรมีหัวข้อ `Copy-paste only` เพื่อให้ผู้เรียนที่ยังไม่ถนัด Linux CLI สามารถเริ่มได้โดยไม่ต้องเปิด editor

## โครงสร้างที่แนะนำ

1. บอกเป้าหมายของ lab ใน 2-3 บรรทัด
2. ให้ copy-paste block เดียวก่อนคำอธิบายละเอียด
3. ใน block ให้สร้างไฟล์ด้วย heredoc
4. ส่งงานด้วย `sbatch`
5. พิมพ์คำสั่งดูคิวและดูผลลัพธ์
6. หลัง block ค่อยอธิบายว่าแต่ละไฟล์ทำอะไร

## Template

```bash
cat > /tmp/hpc_ignite_<lab-id>.sh <<'BASH'
#!/bin/bash
set -euo pipefail

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LAB_DIR="$HOME/hpc-ignite-copy-paste/<lab-id>"
mkdir -p "$LAB_DIR/logs" "$LAB_DIR/results"
cd "$LAB_DIR"

cat > main.py <<'PY'
print("Hello from HPC Ignite")
PY

cat > run.sbatch <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=hpcig-<lab-id>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:03:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

module purge
module load cray-python/3.10.10 2>/dev/null || true
module load Mamba/23.11.0-0 2>/dev/null || true

python main.py | tee "results/output_${SLURM_JOB_ID}.txt"
SBATCH

job_id=$(sbatch -A "$HPC_IGNITE_ACCOUNT" -p "$HPC_IGNITE_PARTITION" --parsable run.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Output : tail -n +1 $LAB_DIR/logs/hpcig-<lab-id>_${job_id}.out"
BASH

bash /tmp/hpc_ignite_<lab-id>.sh
```

## Checklist ก่อน merge lab ใหม่

- มีหัวข้อ `Copy-paste only`
- ไม่มีขั้นตอนที่ต้อง `nano`, `vim`, หรือแก้ไฟล์ด้วยมือ
- heredoc marker ใช้ quoted form เช่น `<<'PY'` เพื่อกัน shell expand โค้ด
- มี `set -euo pipefail` ใน shell script
- ใช้ partition devel/limited เป็นค่าเริ่มต้นสำหรับ smoke test
- ไม่ hard-code account project ของผู้สอน
- ไม่ hard-code token, password, SSH key หรือ secret
- มีคำสั่งดูคิวและดูผลลัพธ์หลัง submit
- ถ้า lab ต้องใช้ package เฉพาะ ให้บอก environment ที่ต้อง activate อย่างชัดเจน
