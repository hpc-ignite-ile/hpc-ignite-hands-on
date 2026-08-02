# 00 Readiness

ใช้ก่อนส่งงานจริงเพื่อให้ผู้ใช้เห็น shell, filesystem, quota, account, module และ queue ตามลำดับใน booklet.

## Copy-Paste

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

cat > configs/run-small.env <<'EOF'
INPUT=input/sample.csv
OUTPUT=results/sample-summary.csv
WORKERS=4
MODE=small
EOF

cat notes/readiness.txt
cat configs/run-small.env
```

### คำอธิบาย

ก่อนส่งงานแรก ให้ผู้ใช้ตรวจว่าอยู่ที่เครื่องใด อยู่ในโฟลเดอร์ใด และมี quota/account พร้อมหรือไม่ คำสั่งนี้จะบันทึกข้อมูลพื้นฐานลงใน `notes/readiness.txt` และบันทึก quota, balance, queue, module ลงใน `notes/system-check.txt`

จากนั้น block จะสร้าง `configs/run-small.env` เป็นไฟล์กำกับการทดลองตัวอย่าง ผู้ใช้จะเห็นรูปแบบ `KEY=value` ซึ่งใช้ซ้ำได้ในงานวิทยาศาสตร์จริง เช่น input, output, จำนวน worker และ mode ของการรัน

เมื่อสำเร็จ ผู้ใช้ควรเห็นไฟล์ `notes/readiness.txt`, `notes/system-check.txt`, และ `configs/run-small.env` หาก `myquota` หรือ `sbalance` แสดง error ให้เก็บข้อความนั้นไว้ก่อน แล้วตรวจต่อด้วย `df -h` หรือ `squeue -u "$USER"` หากคำสั่ง `module` ไม่ทำงาน ให้ logout แล้ว login ใหม่ก่อนเริ่มส่ง job

## Check

```bash
find notes configs -maxdepth 2 -type f | sort
tail -40 notes/system-check.txt
```

### คำอธิบาย

หลังจากรัน block แรกแล้ว ให้ผู้ใช้ตรวจไฟล์ที่สร้างขึ้นด้วย `find` และอ่านท้ายไฟล์ `notes/system-check.txt` ด้วย `tail`

จุดสำคัญคือผู้ใช้ต้องอ่านหลักฐาน ไม่ใช่ดูเพียงว่าคำสั่งไม่มี error เพราะในไฟล์นี้อาจมีข้อมูล quota, account, queue หรือ module ที่จะมีผลต่อ job ถัดไป

ถ้าไม่พบไฟล์ ให้ตรวจ `pwd` ก่อน เพราะสาเหตุที่พบบ่อยคือแปะคำสั่งในคนละโฟลเดอร์ หาก `tail` แจ้งว่าไม่มีไฟล์ ให้กลับไปรัน block เตรียม readiness ใหม่ให้ครบก่อนเดินต่อ
