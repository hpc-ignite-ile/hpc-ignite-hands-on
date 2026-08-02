# บทที่ 29: Data Security บน HPC

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-security` โดยตรง

## เป้าหมาย

1. สร้างไฟล์ตัวอย่างด้าน permission
2. ตรวจ mode และ pattern ของ fake secret
3. ฝึกอ่านผล audit เป็น CSV

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-security"
cd "$HOME/hpc-ignite-standalone/ai-security"
mkdir -p input notes results
cat > input/public.txt <<'EOF'
public training note
EOF
cat > input/private.env <<'EOF'
API_TOKEN=FAKE_TOKEN_FOR_SECURITY_EXERCISE
EOF
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

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
