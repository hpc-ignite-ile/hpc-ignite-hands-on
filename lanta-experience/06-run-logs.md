# 06 สรุปข้อมูลและทรัพยากรที่ใช้

## ก่อนลงมือ

รู้จักพื้นที่เก็บไฟล์และโปรแกรมที่ใช้ ก่อนเริ่มส่งงานคำนวณ

- **ใช้เครื่องเท่าไร:** การดูไฟล์และตรวจรายชื่อโปรแกรมไม่ต้องใช้ GPU ส่วนงานคำนวณต้องส่งผ่าน Slurm
- **ตรวจผลและลองปรับ:** ตรวจว่าอยู่ในโฟลเดอร์ที่ต้องการและเปิดไฟล์ได้ แล้วเริ่มจากงานเล็กหนึ่งงาน

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

ใช้หลังจากรัน lab ครบแล้ว เพื่อรวมหลักฐานของข้อมูล ผลลัพธ์ และทรัพยากรที่ใช้ไว้ใน `notes/`.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `date`, `tee`, `find`, `head`, `wc`, `sha256sum`, `cut`, `paste`, `sacct`, `sbalance` และ `sbill`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน ชุดคำสั่ง เตรียมพื้นที่ใน [README.md](README.md) สำหรับ พื้นที่ทำงาน ของกิจกรรม

## ลงมือทำ

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-experience"
mkdir -p notes results

RUN_STAMP=$(date +%Y%m%d-%H%M%S)
DATA_LOG="notes/data-summary-${RUN_STAMP}.txt"
SPENT_LOG="notes/resource-spent-${RUN_STAMP}.tsv"

{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo
    echo "job history"
    cat notes/job-history.tsv 2>/dev/null || echo "notes/job-history.tsv not found"
    echo
    echo "result files"
    find results -maxdepth 2 -type f | sort
    echo
    echo "sensor summary"
    if [ -f results/sensor_summary.csv ]; then
        cat results/sensor_summary.csv
    else
        echo "missing results/sensor_summary.csv"
    fi
```

### ขั้นที่ 2: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า ขั้นตอนการทำงาน เดินครบ

```bash
    echo
    echo "diffusion summaries"
    for file in results/diffusion_*.csv; do
        [ -f "$file" ] || continue
        echo "$file"
        head -5 "$file"
        echo "lines=$(wc -l < "$file")"
    done
    echo
    echo "checksums"
    sha256sum input/sensor.csv results/sensor_summary.csv 2>/dev/null || true
    sha256sum results/hello_*.txt results/pi_*.txt results/diffusion_*.csv 2>/dev/null || true
} | tee "$DATA_LOG"
```

### ขั้นที่ 3: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า ขั้นตอนการทำงาน เดินครบ

```bash
if [ -s notes/job-history.tsv ]; then
    JOB_IDS=$(cut -f1 notes/job-history.tsv | paste -sd, -)
    sacct -j "$JOB_IDS" --format=JobID,JobName%24,Partition,Account,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS,AllocTRES%80 -P > "$SPENT_LOG"
else
    echo "No job history yet" > "$SPENT_LOG"
fi

sbalance 2>&1 | tee "notes/balance-${RUN_STAMP}.txt" || true
sbill 2>&1 | tee "notes/bill-${RUN_STAMP}.txt" || true
```

### ขั้นที่ 4: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า ขั้นตอนการทำงาน เดินครบ

```bash
echo "Data summary: $DATA_LOG"
echo "Resource spent: $SPENT_LOG"
head -30 "$SPENT_LOG"
```

### คำอธิบาย

หลังจากรัน lab หลายงานแล้ว ให้ผู้ใช้รวมหลักฐานไว้ใน `notes/` คำสั่งนี้อ่าน `notes/job-history.tsv`, แสดงรายชื่อไฟล์ใน `results/`, สรุปไฟล์ sensor และ diffusion และสร้าง checksum ให้ผลลัพธ์สำคัญ

จากนั้น ชุดคำสั่ง ใช้ `sacct` เพื่อดึงข้อมูลทรัพยากรของ job เช่น partition, state, elapsed time, CPU, memory และ exit code และบันทึก `sbalance` กับ `sbill` พร้อม timestamp

เมื่อสำเร็จ ผู้ใช้จะได้ไฟล์ `notes/data-summary-<เวลา>.txt`, `notes/resource-spent-<เวลา>.tsv`, `notes/balance-<เวลา>.txt`, และ `notes/bill-<เวลา>.txt` เมื่อ resource log ว่าง ให้ตรวจว่า `notes/job-history.tsv` มี หมายเลขงาน เมื่อ `sacct` ยังรอข้อมูล job ใหม่ ให้รอสักครู่แล้วรันซ้ำ
