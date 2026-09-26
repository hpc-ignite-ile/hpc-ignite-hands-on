# 00 เตรียมความพร้อม

## ก่อนลงมือ

รู้จักพื้นที่เก็บไฟล์และโปรแกรมที่ใช้ ก่อนเริ่มส่งงานคำนวณ

- **ใช้เครื่องเท่าไร:** การดูไฟล์และตรวจรายชื่อโปรแกรมไม่ต้องใช้ GPU ส่วนงานคำนวณต้องส่งผ่าน Slurm
- **ตรวจผลและลองปรับ:** ตรวจว่าอยู่ในโฟลเดอร์ที่ต้องการและเปิดไฟล์ได้ แล้วเริ่มจากงานเล็กหนึ่งงาน

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

ใช้ก่อนส่งงานจริงเพื่อให้ผู้ใช้เห็น shell, filesystem, quota, account, module และ queue ตามลำดับใน booklet.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `mkdir -p`, `pwd`, `date`, `whoami`, `hostname`, `find`, `sort`, `myquota`, `sbalance`, `squeue`, `module`, `tee`, `cat` และ `tail`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน ชุดคำสั่ง เตรียมพื้นที่ใน [README.md](README.md) สำหรับ พื้นที่ทำงาน ของกิจกรรม

## ลงมือทำ

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo "host=$(hostname)"
    echo "home=$HOME"
} > notes/readiness.txt
```

### ขั้นที่ 2: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า ขั้นตอนการทำงาน เดินครบ

```bash
{
    echo "== files =="
    find . -maxdepth 2 -type d | sort
    echo
    echo "== quota =="
    myquota 2>&1 || true
    echo
    echo "== balance =="
    sbalance 2>&1 || true
    echo
    echo "== queue =="
    squeue -u "$USER" 2>&1 || true
    echo
    echo "== modules =="
    module list 2>&1 || true
    module avail python 2>&1 | head -80 || true
    echo
    echo "== live module probes for real mini workflows =="
    module avail cray-python Mamba cpeCray WPS WRF WRFchem QuantumESPRESSO GROMACS GDAL BLAST+ Apptainer 2>&1 || true
} | tee notes/system-check.txt
```

### ขั้นที่ 3: สร้าง config `configs/run-small.env`

ขั้นนี้สร้างค่ากำกับการทดลอง เพื่อให้ parameter แยกจาก code และตรวจซ้ำได้

```bash
cat > configs/run-small.env <<'EOF'
INPUT=input/sample.csv
OUTPUT=results/sample-summary.csv
WORKERS=4
MODE=small
EOF
```

### ขั้นที่ 4: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า ขั้นตอนการทำงาน เดินครบ

```bash
cat notes/readiness.txt
cat configs/run-small.env
```

### คำอธิบาย

ก่อนส่งงานแรก ให้ผู้ใช้ตรวจชื่อเครื่อง โฟลเดอร์ปัจจุบัน และสถานะ quota/account คำสั่งนี้จะบันทึกข้อมูลพื้นฐานลงใน `notes/readiness.txt` และบันทึก quota, balance, queue, module ลงใน `notes/system-check.txt`

จากนั้น ชุดคำสั่ง จะสร้าง `configs/run-small.env` เป็นไฟล์กำกับการทดลองตัวอย่าง ผู้ใช้จะเห็นรูปแบบ `KEY=value` ซึ่งใช้ซ้ำได้ในงานวิทยาศาสตร์จริง เช่น input, output, จำนวน worker และ mode ของการรัน

เมื่อสำเร็จ ผู้ใช้ควรเห็นไฟล์ `notes/readiness.txt`, `notes/system-check.txt`, และ `configs/run-small.env` หาก `myquota` หรือ `sbalance` แสดง error ให้เก็บข้อความนั้นไว้ก่อน แล้วตรวจต่อด้วย `df -h` หรือ `squeue -u "$USER"` เมื่อคำสั่ง `module` error ให้ logout แล้ว login ใหม่ก่อนเริ่มส่ง job

## ตรวจผล

```bash
find notes configs -maxdepth 2 -type f | sort
tail -40 notes/system-check.txt
```

### คำอธิบาย

หลังจากรัน ชุดคำสั่ง แรกแล้ว ให้ผู้ใช้ตรวจไฟล์ที่สร้างขึ้นด้วย `find` และอ่านท้ายไฟล์ `notes/system-check.txt` ด้วย `tail`

จุดสำคัญคือผู้ใช้ต้องอ่านหลักฐานในไฟล์นี้ เพราะ quota, account, queue และ module มีผลต่อ job ถัดไปโดยตรง

เมื่อรายการไฟล์ยังขาด ให้ตรวจ `pwd` ก่อน เพราะสาเหตุที่พบบ่อยคือแปะคำสั่งในคนละโฟลเดอร์ หาก `tail` แจ้งว่าไฟล์หาย ให้กลับไปรัน ชุดคำสั่ง เตรียม readiness ใหม่ให้ครบก่อนเดินต่อ
