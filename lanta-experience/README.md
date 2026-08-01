# LANTA Experience Labs

ลำดับนี้ตาม booklet `LANTA HPC Handbook` สำหรับ LANTA HPC Experience Day: On the Move. จุดประสงค์คือให้ผู้เรียน copy-paste เป็นหลัก แต่ยังเห็นไฟล์จริงที่ตนเองสร้างด้วย heredoc: `src/*.py`, `jobs/*.sbatch`, `configs/*`, `logs/*`, `results/*`, และ `notes/*`

## Event Flow

| ช่วงใน booklet | Lab ใน repo | ผลลัพธ์ที่ควรมี |
|---|---|---|
| Linux, Shell, files | [00-readiness.md](00-readiness.md) | workspace, input/config/log/result folders, environment notes |
| First Slurm job | [01-first-slurm-job.md](01-first-slurm-job.md) | `jobs/hello_lanta.sbatch`, job id, `results/hello_<jobid>.txt` |
| CPU and job array | [02-cpu-array.md](02-cpu-array.md) | CPU baseline, parameter CSV, Slurm array logs |
| OpenMP and MPI | [03-openmp-mpi.md](03-openmp-mpi.md) | compiled C examples launched by `srun` |
| Scientific/data workflow | [04-science-data.md](04-science-data.md) | model/data outputs with run evidence |
| AI/GPU check | [05-ai-gpu.md](05-ai-gpu.md) | GPU allocation log, `nvidia-smi`, PyTorch CUDA check |
| Data and resource logs | [06-run-logs.md](06-run-logs.md) | data summary, checksums, Slurm resource-spent report |

## Working Pattern

Every activity follows the same visible pattern:

1. `cd` to an event workspace.
2. Create folders with `mkdir -p`.
3. Create small scripts with `cat > file <<'EOF'`.
4. Submit directly with `sbatch -A "$LANTA_ACCOUNT"`.
5. Read `squeue`, `sacct`, `logs/`, `results/`, and `notes/`.
6. Finish with a data-summary log and a resource-spent log.

Use this setup once after SSH to LANTA:

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

### คำอธิบายเชิงเรื่องเล่า

การเริ่มต้นของงานบน LANTA ควรเริ่มจากพื้นที่ที่มีชื่อและโครงสร้างชัดเจน ผู้เรียนจึงสร้าง `lanta-experience` เป็นสมุดสนามของตนเอง แล้ววางโฟลเดอร์ `configs`, `input`, `jobs`, `logs`, `notes`, `results`, และ `src` ให้เหมือนชั้นเอกสารของการทดลองหนึ่งชุด โครงสร้างนี้ทำให้ code คำขอทรัพยากร ผลลัพธ์ และหลักฐานไม่ปะปนกัน เมื่องานขยายจากคำสั่งแรกไปสู่งานวิทยาศาสตร์จริง ผู้สอนและผู้เรียนจะย้อนดูที่มาได้โดยไม่ต้องเดาว่าไฟล์ใดเกิดจากขั้นตอนใด

ในเชิงปฏิบัติ การเก็บ lab ขนาดเล็กไว้ใน `$HOME` เหมาะกับการเรียนรู้ เพราะเป็นพื้นที่ถาวรสำหรับ script และไฟล์กำกับ ส่วนตัวแปร `LANTA_ACCOUNT`, `LANTA_CPU_PARTITION`, และ `LANTA_GPU_PARTITION` ทำหน้าที่เป็นข้อตกลงร่วมของทุก block ถัดไป การตั้งค่าเป็นตัวแปรดีกว่าการเขียน account ลงในทุกไฟล์ เพราะลดโอกาสแก้ผิดหลายจุด และยังส่งเสริมหลัก reproducibility ที่แยกเงื่อนไขการรันออกจากตัวอย่าง code

เมื่อ block นี้สำเร็จ `pwd` จะพาผู้เรียนมายืนใน path ที่ลงท้ายด้วย `lanta-experience` และโฟลเดอร์มาตรฐานจะปรากฏครบ หากเข้า directory ไม่ได้ ให้ตรวจค่าของ `$HOME` ด้วย `echo "$HOME"` ก่อน หากงานถัดไปถูกปฏิเสธเพราะ account หรือค้างอยู่ใน queue นานผิดปกติ ให้ใช้ `sbalance`, `sinfo`, และ `squeue` เป็นหลักฐานแรกในการตรวจสอบ แล้วปรับ account หรือ partition ให้ตรงกับสิทธิ์ของทีม

If your project policy requires a different partition, set it before submitting:

```bash
export LANTA_CPU_PARTITION=compute
export LANTA_GPU_PARTITION=gpu
```

### คำอธิบายเชิงเรื่องเล่า

เมื่อการทดลองเล็กให้คำตอบที่เชื่อถือได้แล้ว ผู้เรียนจึงค่อยย้ายจากพื้นที่ฝึกซ้อมไปสู่พื้นที่รันงานจริง การเปลี่ยน `LANTA_CPU_PARTITION` เป็น `compute` และ `LANTA_GPU_PARTITION` เป็น `gpu` คือการบอก Slurm ว่างานถัดไปไม่ใช่เพียง smoke test แต่เป็นงานที่อาจต้องใช้เวลาหรือทรัพยากรมากขึ้น

การขยายงานบน HPC ควรมีจังหวะที่รอบคอบ เปลี่ยน partition ก่อน แล้วจึงค่อยเพิ่มเวลา จำนวน CPU หรือจำนวน GPU ทีละด้าน วิธีนี้ทำให้หลักฐานใน log ตอบได้ว่าการเปลี่ยนแปลงใดทำให้เวลารันหรือสถานะงานเปลี่ยนไป หากขยายทุกอย่างพร้อมกัน การวิเคราะห์คอขวดจะคลุมเครือและใช้ทรัพยากรเกินจำเป็น

การตั้งค่าสำเร็จเมื่อ `echo "$LANTA_CPU_PARTITION" "$LANTA_GPU_PARTITION"` แสดงค่าที่ต้องการ และงานถัดไปใน `squeue` อยู่ใน partition นั้นจริง หากงานค้างด้วยเหตุผลด้าน priority หรือ resources ให้กลับไปอ่าน reason ด้วย `squeue -j <job-id> -o "%.18i %.9P %.20j %.8T %.20R"` แล้วลดเวลาหรือทรัพยากร หรือย้อนกลับไปใช้ partition devel เพื่อยืนยันว่า script ยังถูกต้อง
