# 00 Readiness

ใช้ก่อนส่งงานจริงเพื่อให้ผู้เรียนเห็น shell, filesystem, quota, account, module และ queue ตามลำดับใน booklet.

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

ก่อนส่งงานแรก ผู้เรียนควรทำความรู้จักสภาพแวดล้อมที่ตนยืนอยู่เสียก่อน Block นี้จึงทำหน้าที่เหมือนการลงทะเบียนภาคสนาม โดยบันทึก workspace วันเวลา ผู้ใช้ เครื่องที่เข้าใช้ และ home directory ลงใน `notes/readiness.txt` จากนั้นจึงเก็บภาพรวมของไฟล์ quota balance queue และ module ลงใน `notes/system-check.txt` พร้อมสร้าง `configs/run-small.env` เป็นตัวอย่างของไฟล์กำกับการทดลอง

ในงาน HPC ความผิดพลาดจำนวนมากไม่ได้เกิดจาก code เพียงอย่างเดียว แต่เกิดจากการอยู่ผิด directory พื้นที่เต็ม account ไม่พร้อม หรือ module ไม่ตรงกับงาน การเก็บหลักฐานเหล่านี้ตั้งแต่ต้นจึงเป็นวิธีวิทยาที่สำคัญ Block นี้ใช้ `tee` เพื่อให้เห็นผลทันทีและเก็บบันทึกพร้อมกัน ส่วน `|| true` ทำให้การตรวจระบบเดินต่อได้แม้คำสั่งบางตัวไม่มีใน environment นั้น

ความสำเร็จของขั้นนี้เห็นได้จากไฟล์ `notes/readiness.txt`, `notes/system-check.txt`, และ `configs/run-small.env` ที่ถูกสร้างครบ พร้อมข้อความ `workspace=...` และค่าของ config ที่อ่านได้ หาก `myquota` หรือ `sbalance` ไม่ทำงาน ให้ถือข้อความ error เป็นข้อมูล ไม่ใช่ความล้มเหลวของบทเรียน แล้วตรวจต่อด้วย `df -h`, `squeue -u "$USER"` หรือสอบถามผู้สอน หากคำสั่ง `module` ไม่ตอบสนอง การ logout แล้ว login ใหม่ด้วย shell ปกติมักช่วยให้ Lmod ถูกโหลดกลับมา

## Check

```bash
find notes configs -maxdepth 2 -type f | sort
tail -40 notes/system-check.txt
```

### คำอธิบายเชิงเรื่องเล่า

หลังจากเก็บหลักฐานแล้ว ผู้เรียนต้องอ่านหลักฐานนั้น ไม่ใช่เพียงเชื่อว่าคำสั่งที่แปะไปทำงานสำเร็จ Block ตรวจสอบนี้จึงให้ `find` แสดงรายชื่อไฟล์ใน `notes` และ `configs` อย่างมีลำดับ แล้วใช้ `tail` อ่านส่วนท้ายของรายงานระบบซึ่งมักมีข้อมูล module หรือข้อความเตือนที่สำคัญ

แนวทางนี้สะท้อนวิธีทำงานของผู้ใช้ HPC ที่ดี กล่าวคือทุกการรันควรมีร่องรอยที่ตรวจซ้ำได้ การใช้ `sort` ทำให้ผลลัพธ์เรียงคงที่และเปรียบเทียบระหว่างรอบได้ง่าย ส่วน `tail` ช่วยหลีกเลี่ยงการเท log ยาวเกินจำเป็นลงหน้าจอ

หากขั้นนี้สมบูรณ์ ผู้เรียนจะเห็น `notes/readiness.txt`, `notes/system-check.txt`, และ `configs/run-small.env` หากไฟล์ไม่ปรากฏ ให้กลับไปตรวจ `pwd` ก่อน เพราะสาเหตุที่พบบ่อยคืออยู่ผิด directory หาก `tail` แจ้งว่าไม่มีไฟล์ แปลว่า block แรกอาจไม่จบหรือถูกแปะในตำแหน่งอื่น ให้กลับไปสร้าง workspace ให้ครบก่อนเดินต่อ
