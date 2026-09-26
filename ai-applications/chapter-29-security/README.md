# บทที่ 29: Data Security บน HPC

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **5–18** of the [LANTA handbook](../../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: security](../../docs/images/booklet/Part1-FirstDayKnowingHPC.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

Small local permissions/fake-secret audit, with no archived Slurm job for this page.

No GPU or parallel allocation is needed to inspect the supplied two fake files. For a larger authorized audit, budget bytes read and file count: metadata work can dominate throughput.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

No page-specific Slurm run is recorded for this setup/reading page. Do not invent usage numbers or a successful-run screenshot. Collect evidence from the next executable lesson using the worksheet.

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Test only a dedicated synthetic fixture directory at 10/100/1000 files. Measure files/second and false positives, not private home/project trees. Capture only synthetic examples.

**Correctness gate:** private.env must have mode 0600; confirm detection of the fake token while preserving public-file access. Never publish real secrets in screenshots.

[Public applications and research-backed experiments](../../docs/REAL_APPLICATION_EXPERIMENTS.md#miniweather) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-security` โดยตรง

## เป้าหมาย

1. สร้างไฟล์ตัวอย่างด้าน permission
2. ตรวจ mode และ pattern ของ fake secret
3. ฝึกอ่านผล audit เป็น CSV

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-security"
cd "$HOME/hpc-ignite-standalone/ai-security"
mkdir -p input notes results
```

### ขั้นที่ 2: สร้าง input `input/public.txt`

ขั้นนี้สร้างข้อมูลตัวอย่างขนาดเล็ก เพื่อให้ workflow มี input จริงและตรวจ output เทียบได้

```bash
cat > input/public.txt <<'EOF'
public training note
EOF
```

### ขั้นที่ 3: สร้าง input `input/private.env`

ขั้นนี้สร้างข้อมูลตัวอย่างขนาดเล็ก เพื่อให้ workflow มี input จริงและตรวจ output เทียบได้

```bash
cat > input/private.env <<'EOF'
API_TOKEN=FAKE_TOKEN_FOR_SECURITY_EXERCISE
EOF
```

### ขั้นที่ 4: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
chmod 600 input/private.env
python - <<'PYCODE'
from pathlib import Path
import csv, stat
Path("results").mkdir(exist_ok=True)
rows = []
for path in sorted(Path("input").glob("*")):
    mode = stat.S_IMODE(path.stat().st_mode); text = path.read_text(encoding="utf-8")
    rows.append([str(path), oct(mode), "TOKEN" in text or "SECRET" in text])
with open("results/security_audit.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["path", "mode", "has_fake_secret_pattern"]); writer.writerows(rows)
print(Path("results/security_audit.csv").read_text(encoding="utf-8"))
PYCODE
find input results -maxdepth 2 -type f -print | sort
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/ai-security"
cat results/security_audit.csv
```

## การตรวจผล

บทนี้เป็นการตรวจไฟล์ขนาดเล็กใน shell ไม่ได้สร้าง Slurm job จึงไม่มี job ID หรือ `sacct` โดยอัตโนมัติ ตรวจว่า `private.env` เป็น `0o600` และมี fake-secret flag เป็น `True`; `public.txt` ต้องเป็น `False` เก็บ `results/security_audit.csv` เป็นหลักฐาน ใน campaign 2026-09-26 ตรวจซ้ำภายในงาน postprocess ด้วย

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
