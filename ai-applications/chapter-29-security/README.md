# บทที่ 29: Data Security บน HPC

## ก่อนลงมือ

ตรวจสิทธิ์ไฟล์ด้วยข้อมูลสมมติที่เตรียมไว้

- **ใช้เครื่องเท่าไร:** ไม่ต้องใช้ GPU และไม่ควรสแกนพื้นที่ของผู้อื่น
- **ตรวจผลและลองปรับ:** ตรวจว่าไฟล์ลับตัวอย่างอ่านได้เฉพาะเจ้าของ ใช้ข้อมูลสมมติเท่านั้นและไม่ใส่กุญแจจริงในภาพหน้าจอ

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-security` โดยตรง

## เป้าหมาย

1. สร้างไฟล์ตัวอย่างด้าน permission
2. ตรวจ mode และ pattern ของ fake secret
3. ฝึกอ่านผล audit เป็น CSV

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-security"
cd "$HOME/hpc-ignite-standalone/ai-security"
mkdir -p input notes results
```

### ขั้นที่ 2: สร้าง input `input/public.txt`

ขั้นนี้สร้างข้อมูลตัวอย่างขนาดเล็ก เพื่อให้ ขั้นตอนการทำงาน มี input จริงและตรวจ output เทียบได้

```bash
cat > input/public.txt <<'EOF'
public training note
EOF
```

### ขั้นที่ 3: สร้าง input `input/private.env`

ขั้นนี้สร้างข้อมูลตัวอย่างขนาดเล็ก เพื่อให้ ขั้นตอนการทำงาน มี input จริงและตรวจ output เทียบได้

```bash
cat > input/private.env <<'EOF'
API_TOKEN=FAKE_TOKEN_FOR_SECURITY_EXERCISE
EOF
```

### ขั้นที่ 4: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

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

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/ai-security"
cat results/security_audit.csv
```

## การตรวจผล

บทนี้ตรวจไฟล์ตัวอย่างเล็ก ๆ โดยไม่ส่งงาน Slurm จึงไม่มีหมายเลขงานหรือสถิติ `sacct` ตรวจว่า `private.env` มีสิทธิ์ `0o600` และตรวจพบข้อความลับสมมติเป็น `True` ส่วน `public.txt` ต้องเป็น `False` เก็บ `results/security_audit.csv` ไว้เทียบกับการทดลองครั้งถัดไป

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
