# 06 Data Summary And Resource Logs

ใช้หลังจากรัน lab ครบแล้ว เพื่อรวมหลักฐานของข้อมูล ผลลัพธ์ และทรัพยากรที่ใช้ไว้ใน `notes/`.

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

### คำอธิบายเชิงเรื่องเล่า

เมื่อการทดลองทั้งหมดผ่านพ้นแล้ว หลักฐานไม่ควรกระจัดกระจายอยู่เพียงใน log หลายไฟล์เหมือนเศษกระดาษหลังงานภาคสนาม Block นี้จึงกลับมาอ่านพื้นที่เดิมอย่างเป็นระบบ เริ่มจาก `notes/job-history.tsv` เพื่อรู้ว่า job ใดถูกส่งไปแล้ว อ่านรายชื่อไฟล์ใน `results/` เพื่อเห็นผลลัพธ์ที่เกิดขึ้นจริง และเปิด `results/sensor_summary.csv` กับไฟล์ diffusion เพื่อสรุปข้อมูลที่ lab สร้างไว้ จากนั้นจึงทำ checksum ให้ผลลัพธ์สำคัญ เพื่อให้การตรวจซ้ำในภายหลังรู้ว่าไฟล์ยังเป็นชุดเดียวกับวันที่สรุปหรือไม่

ในเชิงวิชาการ การสรุปข้อมูลกับการสรุปทรัพยากรเป็นหลักฐานคนละชั้นแต่ต้องเดินคู่กัน ข้อมูลบอกว่างานให้คำตอบอะไร ส่วน `sacct` บอกว่างานใช้ partition ใด ใช้เวลาเท่าใด ขอ CPU และ memory เท่าใด และจบด้วยสถานะใด การเรียก `sbalance` และ `sbill` เพิ่มเติมทำให้ผู้เรียนเห็นภาพของบัญชีโครงการหลังการทดลอง แม้รูปแบบผลลัพธ์ของคำสั่งเหล่านี้อาจเปลี่ยนตามนโยบายของระบบ แต่การบันทึกไว้พร้อม timestamp ทำให้การสนทนากับผู้สอนหรือผู้ดูแลระบบมีหลักฐานชัดเจน

ความสำเร็จของขั้นนี้เห็นได้จากไฟล์ `notes/data-summary-<เวลา>.txt`, `notes/resource-spent-<เวลา>.tsv`, `notes/balance-<เวลา>.txt`, และ `notes/bill-<เวลา>.txt` โดยใน resource log ควรเห็นสถานะ `COMPLETED` สำหรับ job ที่รันจบสมบูรณ์ หาก resource log ว่าง ให้ตรวจว่า `notes/job-history.tsv` มี job id หรือไม่ หาก `sacct` ยังไม่เห็น job ใหม่ ให้รอสักครู่เพราะ accounting อาจตามหลังการจบงานเล็กน้อย หาก checksum แจ้งว่าไม่มีไฟล์ ให้กลับไปดูว่า lab ก่อนหน้าสร้างผลลัพธ์ใน workspace เดียวกันหรือไม่
