# กิจกรรมเรียนรู้ LANTA

## ก่อนลงมือ

รู้จักพื้นที่เก็บไฟล์และโปรแกรมที่ใช้ ก่อนเริ่มส่งงานคำนวณ

- **ใช้เครื่องเท่าไร:** การดูไฟล์และตรวจรายชื่อโปรแกรมไม่ต้องใช้ GPU ส่วนงานคำนวณต้องส่งผ่าน Slurm
- **ตรวจผลและลองปรับ:** ตรวจว่าอยู่ในโฟลเดอร์ที่ต้องการและเปิดไฟล์ได้ แล้วเริ่มจากงานเล็กหนึ่งงาน

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

![ภาพรวมการเรียนจากเชื่อมต่อจนถึงประเมินผล](../docs/images/beginners/tutorial-overview.png)

ภาพแนวคิดสำหรับผู้เริ่มต้น: Connect → Prepare → Submit → Run → Check → Improve ทำงานเล็กให้ครบวงจรก่อนเพิ่มขนาด. อ่าน [คู่มือเริ่มต้นด้วยภาพ](../docs/BEGINNER_VISUAL_GUIDE_TH.md) สำหรับคำอธิบายทีละขั้น


ลำดับนี้ตาม booklet `LANTA HPC Handbook` สำหรับ LANTA HPC Experience Day: On the Move ให้ผู้ใช้แปะคำสั่งทีละ ชุดคำสั่ง และตรวจไฟล์จริงที่สร้างขึ้น เช่น `src/*.py`, `jobs/*.sbatch`, `configs/*`, `logs/*`, `results/*`, และ `notes/*`

คำสั่งและ รูปแบบคำสั่ง ใน lab ชุดนี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `cd`, `mkdir -p`, heredoc, `export`, `sbatch`, `squeue`, `sacct`, `srun`, `tail` และตัวแปร `SLURM_*`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน setup ชุดคำสั่ง ด้านล่างเพื่อเตรียม พื้นที่ทำงาน กลางของกิจกรรม

## ลำดับการเรียน

| ช่วงใน booklet | Lab ใน repo | ผลลัพธ์ที่ควรมี |
|---|---|---|
| ไฟล์และคำสั่งพื้นฐาน | [เตรียมพร้อม](00-readiness.md) | โฟลเดอร์ข้อมูล คำสั่ง และผลลัพธ์ |
| งานแรก | [ส่งงาน](01-first-slurm-job.md) | ไฟล์งาน หมายเลขงาน และข้อความผล |
| CPU และชุดงานย่อย | [แบ่งการทดลอง](02-cpu-array.md) | ผลหลายชุดที่เปรียบเทียบกันได้ |
| OpenMP และ MPI | [แบ่งงานหลายคอร์](03-openmp-mpi.md) | โปรแกรม C ที่รันผ่าน `srun` |
| วิทยาศาสตร์และข้อมูล | [จำลองและอ่านผล](04-science-data.md) | ไฟล์ตัวเลขที่ตรวจคำตอบได้ |
| AI และ GPU | [ลองใช้การ์ดคำนวณ](05-ai-gpu.md) | ผลตรวจว่าโปรแกรมใช้ GPU ได้ |
| สรุปการทดลอง | [อ่านทรัพยากร](06-run-logs.md) | สรุปคำตอบ เวลา และหน่วยความจำ |

## วิธีทำกิจกรรม

แต่ละกิจกรรมทำตามลำดับเดียวกัน:

1. ใช้ `cd` เข้าโฟลเดอร์ของบทเรียน
2. สร้างโฟลเดอร์ด้วย `mkdir -p`
3. สร้างไฟล์คำสั่งด้วย `cat > file <<'EOF'` ตามตัวอย่าง
4. ส่งงานด้วย `sbatch -A "$LANTA_ACCOUNT"`
5. ดูคิวด้วย `squeue` ดูสถิติด้วย `sacct` แล้วเปิดไฟล์ผลลัพธ์
6. สรุปคำตอบและทรัพยากรที่ใช้ด้วยคำพูดของคุณเอง

หลังเชื่อมต่อ LANTA ให้เตรียมพื้นที่ครั้งแรกดังนี้:

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"

mkdir -p configs input jobs logs notes results src
pwd
```

### คำอธิบาย

ก่อนเริ่ม lab ให้ผู้ใช้สร้างโฟลเดอร์ `lanta-experience` ไว้เป็นพื้นที่ทำงานหลัก จากนั้นสร้างโฟลเดอร์ย่อย `configs`, `input`, `jobs`, `logs`, `notes`, `results`, และ `src` ให้ครบ เพื่อแยกไฟล์คำสั่ง ไฟล์งาน ผลลัพธ์ และบันทึกออกจากกัน

ในขั้นตอนนี้ ผู้ใช้ตั้งค่า `LANTA_ACCOUNT`, `LANTA_CPU_PARTITION`, และ `LANTA_GPU_PARTITION` ให้พร้อมก่อนส่ง job ตัวแปรเหล่านี้จะถูกใช้ซ้ำใน lab ถัดไป ทำให้ account และ partition คงที่ตลอดกิจกรรม

เมื่อตรวจสอบ ให้ใช้ `pwd` เพื่อดูว่าผู้ใช้อยู่ใน path ที่ลงท้ายด้วย `lanta-experience` และใช้ `ls` หรือ `find . -maxdepth 1 -type d` เพื่อดูว่าโฟลเดอร์มาตรฐานถูกสร้างครบ หาก path คลาดจากที่ตั้งใจ ให้กลับไปตรวจ `$HOME` ด้วย `echo "$HOME"` แล้วรัน ชุดคำสั่ง เตรียมพื้นที่ใหม่อีกครั้ง

หากโครงการให้ใช้กลุ่มเครื่องอื่น ให้กำหนดก่อนส่งงาน:

```bash
export LANTA_CPU_PARTITION=compute
export LANTA_GPU_PARTITION=gpu
```

### คำอธิบาย

หลังจาก การทดสอบเบื้องต้น สำเร็จแล้ว ผู้ใช้สามารถเปลี่ยน partition จาก `compute-devel` เป็น `compute` หรือจาก `gpu-devel` เป็น `gpu` ได้ ควรเปลี่ยนเฉพาะเมื่อ job เล็กทำงานถูกต้องแล้ว

ให้ผู้ใช้เพิ่มขนาดงานทีละอย่าง เช่น เปลี่ยน partition ก่อน แล้วค่อยเพิ่มเวลา CPU หรือ GPU ในรอบถัดไป วิธีนี้ช่วยให้รู้ว่าการเปลี่ยนค่าใดทำให้เวลารันหรือสถานะงานเปลี่ยนไป

การตั้งค่าสำเร็จเมื่อ `echo "$LANTA_CPU_PARTITION" "$LANTA_GPU_PARTITION"` แสดงค่าที่ต้องการ และ job ถัดไปปรากฏใน partition นั้นจริงจาก `squeue` หาก job ค้าง ให้ดู reason ด้วย `squeue -j <job-id> -o "%.18i %.9P %.20j %.8T %.20R"` ก่อนเพิ่มทรัพยากร
