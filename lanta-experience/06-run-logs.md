# 06 Data Summary And Resource Logs

ใช้หลังจากรัน lab ครบแล้ว เพื่อรวมหลักฐานของข้อมูล ผลลัพธ์ และทรัพยากรที่ใช้ไว้ใน `notes/`.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `date`, `tee`, `find`, `head`, `wc`, `sha256sum`, `cut`, `paste`, `sacct`, `sbalance` และ `sbill`

## Copy-Paste

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

if [ -s notes/job-history.tsv ]; then
    JOB_IDS=$(cut -f1 notes/job-history.tsv | paste -sd, -)
    sacct -j "$JOB_IDS" --format=JobID,JobName%24,Partition,Account,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS,AllocTRES%80 -P > "$SPENT_LOG"
else
    echo "No job history yet" > "$SPENT_LOG"
fi

sbalance 2>&1 | tee "notes/balance-${RUN_STAMP}.txt" || true
sbill 2>&1 | tee "notes/bill-${RUN_STAMP}.txt" || true

echo "Data summary: $DATA_LOG"
echo "Resource spent: $SPENT_LOG"
head -30 "$SPENT_LOG"
```

### คำอธิบาย

หลังจากรัน lab หลายงานแล้ว ให้ผู้ใช้รวมหลักฐานไว้ใน `notes/` คำสั่งนี้อ่าน `notes/job-history.tsv`, แสดงรายชื่อไฟล์ใน `results/`, สรุปไฟล์ sensor และ diffusion และสร้าง checksum ให้ผลลัพธ์สำคัญ

จากนั้น block ใช้ `sacct` เพื่อดึงข้อมูลทรัพยากรของ job เช่น partition, state, elapsed time, CPU, memory และ exit code และบันทึก `sbalance` กับ `sbill` พร้อม timestamp

เมื่อสำเร็จ ผู้ใช้จะได้ไฟล์ `notes/data-summary-<เวลา>.txt`, `notes/resource-spent-<เวลา>.tsv`, `notes/balance-<เวลา>.txt`, และ `notes/bill-<เวลา>.txt` เมื่อ resource log ว่าง ให้ตรวจว่า `notes/job-history.tsv` มี job id เมื่อ `sacct` ยังรอข้อมูล job ใหม่ ให้รอสักครู่แล้วรันซ้ำ
