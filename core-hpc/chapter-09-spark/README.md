# บทที่ 9: Apache Spark

## ก่อนลงมือ

ฝึกนับคำก่อนต่อยอดสู่ระบบประมวลผลข้อมูลขนาดใหญ่

- **ใช้เครื่องเท่าไร:** ตัวอย่างนับคำสั้น ๆ ใช้ CPU 1 คอร์ ไม่ได้เปิดระบบ Spark เต็มรูปแบบ
- **ตรวจผลและลองปรับ:** ตรวจจำนวนคำด้วยมือก่อน หากทดลอง Spark จริงต้องวัดทั้งเวลาอ่านและแลกเปลี่ยนข้อมูล ไม่ใช้ตัวเลขจากตัวอย่างเล็กแทน

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-spark-shape` โดยตรง

## เป้าหมาย

1. ตรวจแนวคิด partitioned word count
2. บันทึกผลแบบ Spark-shaped ขั้นตอนการทำงาน
3. เตรียมหลักฐานก่อนขยายสู่ Spark module จริง

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-spark-shape"
cd "$HOME/hpc-ignite-standalone/core-spark-shape"
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

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/spark_shape.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/spark_shape.py <<'PYCODE'
from pathlib import Path
from collections import Counter
import json
Path("input").mkdir(exist_ok=True); Path("results").mkdir(exist_ok=True)
text = "lanta spark hpc data lanta hpc ignite spark data data"
Path("input/words.txt").write_text(text + "\n", encoding="utf-8")
counts = Counter(text.split())
out = Path("results/spark_shaped_wordcount.json"); out.write_text(json.dumps(dict(sorted(counts.items())), indent=2), encoding="utf-8"); print(out.read_text(encoding="utf-8"))
PYCODE
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/spark-shape.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
cat > jobs/spark-shape.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=spark-shape
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
python src/spark_shape.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/spark-shape.sbatch)
echo "$job_id	spark-shape	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/spark-shape_${job_id}.out"
```

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/core-spark-shape"
cat results/spark_shaped_wordcount.json
tail -50 logs/spark-shape_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี ข้อความผลและข้อผิดพลาด ของ หมายเลขงาน นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
