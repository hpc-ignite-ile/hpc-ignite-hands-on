# Mini Innovation: LANTA EpiSprint และ Twin-B MicroCosim

แบบฝึกปฏิบัตินี้เป็น tutorial ภาษาไทยสำหรับกิจกรรมสดประมาณ 40 คน โดยมีสอง innovation track ขนาดจิ๋วบน LANTA: **LANTA EpiSprint** สำหรับ epidemic ABS และ **Twin-B MicroCosim** สำหรับ co-simulation ระหว่าง scientific thermal model กับ Mesa occupant agents

ดูคำอธิบายคำสั่ง Bash, Slurm และ syntax ที่ใช้ใน mini innovation ได้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md)

เริ่มจาก SSH และ workspace ตาม [00-connect-to-lanta.md](00-connect-to-lanta.md) แล้วเลือกหน้าถัดไปตามลำดับกิจกรรม

## บทนำแบบ Verse

ตั้งประชากรให้มีสถานะ กำหนด seed ให้ย้อนรอย<br>
ให้ agent พบกันบน grid แล้วบันทึกวันต่อวัน<br>
ส่ง scenario เป็น array ให้ LANTA กระจายงานสั้นหลายชุด<br>
รวมผลเป็นตาราง เปรียบเทียบ peak, attack rate และความไวของนโยบาย<br>
ผลที่ดีต้องตรวจซ้ำได้ มี log, config, version และ sanity check รองรับ

อ่านอุณหภูมิราย zone จาก model อาคาร ส่งให้ agent ประเมิน comfort<br>
รวม setpoint request กลับไปปรับ cooling แล้วเดิน timestep ถัดไป<br>
ให้ LANTA กระจาย policy และ seed เป็น array สั้นหลายชุด<br>
ผลที่ดีต้องอธิบาย trade-off ระหว่าง energy, comfort และหลักฐานจาก CSV ได้

## คำอธิบายเชิงวิชาการ

LANTA EpiSprint ใช้แบบจำลอง SEIR แบบ agent-based simulation บน Mesa เพื่อศึกษาความสัมพันธ์ระหว่างพฤติกรรมระดับ agent, ค่าพารามิเตอร์ของการแพร่เชื้อ, และผลรวมระดับประชากร เช่น peak infectious agents, peak day และ attack rate

Twin-B MicroCosim ย่อแนวคิดจาก building digital twin ที่ใช้ scientific model ส่ง zone temperature ให้ ABS และรับ setpoint request กลับไปคำนวณ cooling energy การย่อเป็น thermal surrogate ทำให้ผู้ใช้เห็น coupling contract และ sensitivity ของ policy ในเวลาอบรมสั้น

แนวใช้ที่เหมาะสมคือเริ่มจาก smoke job เพื่อยืนยันว่า environment, module, account และ partition ทำงานถูกต้อง จากนั้นใช้ job array เพื่อรันหลาย scenario จาก CSV และใช้ multicore job เพื่อรัน ensemble ภายในหนึ่ง node การออกแบบเช่นนี้ทำให้ผู้ใช้เห็น workflow วิทยาศาสตร์ขนาดจิ๋วที่มี input, code, scheduler evidence, output และ summary แยกกันชัดเจน

ผลลัพธ์ถือว่าน่าเชื่อถือสำหรับการฝึกเมื่อบันทึก seed และพารามิเตอร์ครบ, จำนวน agent ในสถานะ `S + E + I + R` สัมพันธ์กับประชากรที่ตั้งไว้, job จบด้วย `COMPLETED`, ไฟล์ CSV มี header และจำนวนแถวตามจำนวนวัน, และข้อสรุปเชิงนโยบายอ้างอิงหลาย scenario หรือหลาย seed พร้อมตรวจ sensitivity แทนการสรุปจาก run เดียว

## หน้าเรียน

| หน้า | เรื่อง | ใช้เมื่อ |
|---|---|---|
| [00-connect-to-lanta.md](00-connect-to-lanta.md) | เข้า LANTA และเตรียม workspace | เปิดกิจกรรมหรือใช้เป็นหน้าอ้างอิงร่วม |
| [01-custom-python-env-module.md](01-custom-python-env-module.md) | สร้าง Python environment และ Lmod module สำหรับ Mesa | ใช้เมื่อทีมต้องเตรียม environment กลาง |
| [02-jupyter-notebook.md](02-jupyter-notebook.md) | เปิด Jupyter Notebook ผ่าน Slurm allocation | สำรวจผลลัพธ์แบบ interactive |
| [03-epidemic-abs-examples.md](03-epidemic-abs-examples.md) | สร้างและรัน epidemic ABS 3 วิธี | lab หลักของ mini innovation |
| [04-building-cosimulation-twinb.md](04-building-cosimulation-twinb.md) | สร้าง co-simulation แบบ Twin-B MicroCosim | แสดงการทำงานร่วมกันของ scientific model และ ABS |

ทุกหน้าเริ่มจากเครื่อง local ด้วย `ssh` เข้า LANTA หรือมี link กลับไปยังหน้าเชื่อมต่อกลาง ผู้ใช้จึงเปิดหน้าใดหน้าหนึ่งแล้วเริ่มทำต่อได้ทันที

## รูปแบบกิจกรรมสดที่แนะนำ

- แบ่งผู้ใช้ 40 คนเป็น 10 ทีม ทีมละ 4 คน
- ทีมจัดกิจกรรมเตรียม environment ตามหน้า 01 ไว้ล่วงหน้า
- ผู้ใช้แต่ละทีมรัน smoke job และ job array ขนาดเล็ก
- จำกัด concurrency ของ array ด้วย `%4` หรือ `%8`
- ใช้ `compute-devel` เป็นค่าเริ่มต้น
- งานแต่ละ scenario ควรจบภายใน 30-120 วินาที

## สิ่งที่ mini innovation นี้สอน

- Login, workspace, quota, account และ module
- การสร้าง Python environment ที่ใช้ร่วมกันใน project space
- การทำ module ส่วนตัวด้วย Lmod
- Jupyter บน compute node ผ่าน Slurm และ SSH tunnel
- Slurm single job
- Slurm job array
- Multicore Python ภายในหนึ่ง node
- การออกแบบ experiment แบบ reproducible
- การออกแบบ co-simulation และ data contract ระหว่าง model
- AI scaffolding สำหรับตั้งคำถาม ออกแบบ scenario ตรวจ Slurm script และอธิบายผลโดยอ้างอิง code, config, log และ CSV

## Standalone Smoke Job

หลังเตรียม environment/module แล้ว ผู้ใช้ตรวจ Mesa ได้ด้วย job สั้น ๆ:

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/lanta-episprint"/{jobs,logs,results}
cd "$HOME/lanta-episprint"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น ltXXXXXX หรือ tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-/project/<project>/modules}"
```

### ขั้นที่ 2: สร้าง Slurm script `jobs/epi_smoke.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/epi_smoke.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-smoke
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python - <<'PY' | tee "results/${SLURM_JOB_ID}/mesa_check.txt"
import mesa
from mesa.space import MultiGrid
from mesa.time import RandomActivation
print("mesa", mesa.__version__)
print("api", "RandomActivation MultiGrid")
PY
SLURM
```

### ขั้นที่ 3: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_smoke.sbatch)
echo "Submitted smoke job: $job_id"
echo "Read: tail -50 logs/epi-smoke_${job_id}.out"
```

ถ้า module อยู่คนละ project ให้ตั้ง `EPI_MODULE_ROOT=/project/<project>/modules` ก่อน `sbatch`.

✅ เมื่อสำเร็จ log จะบอก `mesa 2.3.4` และชื่อ API ที่ใช้ใน tutorial

## ขอบเขตความปลอดภัย

แบบจำลองนี้เป็น synthetic educational model เท่านั้น

- ใช้ประชากรและพฤติกรรมจำลองที่สร้างขึ้นเพื่อการสอน
- ใช้สำหรับเรียนรู้ HPC, ABS, uncertainty และการตีความผลลัพธ์
- ใช้ผลลัพธ์เพื่ออภิปรายเชิงวิธีวิทยา เช่น reproducibility, sensitivity และ evidence trail
- แยกงานฝึกออกจากการพยากรณ์โรคและการกำหนดนโยบายสาธารณสุขจริง
