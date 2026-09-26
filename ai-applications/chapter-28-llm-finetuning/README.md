# บทที่ 28: การ Finetune LLM

## ก่อนลงมือ

เข้าใจการปรับเมทริกซ์ขนาดเล็กซึ่งเป็นแนวคิดพื้นฐานของ LoRA

- **ใช้เครื่องเท่าไร:** เมทริกซ์ที่ใหญ่ขึ้นใช้หน่วยความจำเพิ่ม ตัวอย่างนี้ยังไม่โหลดหรือฝึกโมเดลภาษาขนาดใหญ่
- **ตรวจผลและลองปรับ:** เปรียบเทียบจำนวนค่าที่ต้องปรับและผลลัพธ์ก่อนเพิ่มขนาด อย่านำเวลาตัวอย่างนี้ไปคาดเวลาฝึกโมเดลจริง

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-lora-math` โดยตรง

## เป้าหมาย

1. สาธิต LoRA parameter update ด้วยคณิตศาสตร์ขนาดเล็ก
2. บันทึกจำนวน trainable parameters
3. เตรียมหลักฐานก่อนใช้ model cache จริง

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-lora-math"
cd "$HOME/hpc-ignite-standalone/ai-lora-math"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then
    export LANTA_CPU_PARTITION="compute-devel"
fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
```

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/lora_math.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/lora_math.py <<'PYCODE'
from pathlib import Path
import json, math, random
Path("results").mkdir(exist_ok=True); random.seed(7)
base_dim, rank = 6, 2
A = [[random.uniform(-0.02, 0.02) for _ in range(rank)] for _ in range(base_dim)]
B = [[random.uniform(-0.02, 0.02) for _ in range(base_dim)] for _ in range(rank)]
updates = [[sum(A[i][k] * B[k][j] for k in range(rank)) for j in range(base_dim)] for i in range(base_dim)]
summary = {"base_dim": base_dim, "lora_rank": rank, "trainable_parameters": base_dim * rank + rank * base_dim, "update_frobenius_norm": math.sqrt(sum(x*x for row in updates for x in row))}
out = Path("results/lora_math_summary.json"); out.write_text(json.dumps(summary, indent=2), encoding="utf-8"); print(json.dumps(summary, indent=2))
PYCODE
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/lora-math.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
cat > jobs/lora-math.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=lora-math
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/lora_math.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/lora-math.sbatch)
echo "$job_id	lora-math	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/lora-math_${job_id}.out"
```

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/ai-lora-math"
cat results/lora_math_summary.json
tail -50 logs/lora-math_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี ข้อความผลและข้อผิดพลาด ของ หมายเลขงาน นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
