# Mini Innovation: LANTA EpiSprint

แบบฝึกปฏิบัตินี้เป็น tutorial ภาษาไทยสำหรับกิจกรรมสดประมาณ 40 คน โดยใช้ mini innovation ชื่อ **LANTA EpiSprint**: แบบจำลองโรคระบาดแบบ agent-based simulation ที่มี AI เป็น scaffold ช่วยตั้งคำถาม สร้าง scenario ตรวจ Slurm และอ่านผลลัพธ์

ดูคำอธิบายคำสั่ง Bash, Slurm และ syntax ที่ใช้ใน mini innovation ได้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md)

## บทนำแบบ Verse

ตั้งประชากรให้มีสถานะ กำหนด seed ให้ย้อนรอย<br>
ให้ agent พบกันบน grid แล้วบันทึกวันต่อวัน<br>
ส่ง scenario เป็น array ให้ LANTA กระจายงานสั้นหลายชุด<br>
รวมผลเป็นตาราง เปรียบเทียบ peak, attack rate และความไวของนโยบาย<br>
ผลที่ดีต้องตรวจซ้ำได้ มี log, config, version และ sanity check รองรับ

## คำอธิบายเชิงวิชาการ

LANTA EpiSprint ใช้แบบจำลอง SEIR แบบ agent-based simulation บน Mesa เพื่อศึกษาความสัมพันธ์ระหว่างพฤติกรรมระดับ agent, ค่าพารามิเตอร์ของการแพร่เชื้อ, และผลรวมระดับประชากร เช่น peak infectious agents, peak day และ attack rate

แนวใช้ที่เหมาะสมคือเริ่มจาก smoke job เพื่อยืนยันว่า environment, module, account และ partition ทำงานถูกต้อง จากนั้นใช้ job array เพื่อรันหลาย scenario จาก CSV และใช้ multicore job เพื่อรัน ensemble ภายในหนึ่ง node การออกแบบเช่นนี้ทำให้ผู้ใช้เห็น workflow วิทยาศาสตร์ขนาดจิ๋วที่มี input, code, scheduler evidence, output และ summary แยกกันชัดเจน

ผลลัพธ์ถือว่าน่าเชื่อถือสำหรับการฝึกเมื่อบันทึก seed และพารามิเตอร์ครบ, จำนวน agent ในสถานะ `S + E + I + R` สัมพันธ์กับประชากรที่ตั้งไว้, job จบด้วย `COMPLETED`, ไฟล์ CSV มี header และจำนวนแถวตามจำนวนวัน, และข้อสรุปเชิงนโยบายอ้างอิงหลาย scenario หรือหลาย seed พร้อมตรวจ sensitivity แทนการสรุปจาก run เดียว

## หน้าเรียน

| หน้า | เรื่อง | ใช้เมื่อ |
|---|---|---|
| [00-connect-to-lanta.md](00-connect-to-lanta.md) | เข้า LANTA และเตรียม workspace | เปิดกิจกรรมหรือใช้เป็นหน้าอ้างอิงร่วม |
| [01-custom-python-env-module.md](01-custom-python-env-module.md) | สร้าง Python environment และ Lmod module สำหรับ Mesa | ใช้เมื่อทีมต้องเตรียม environment กลาง |
| [02-jupyter-notebook.md](02-jupyter-notebook.md) | เปิด Jupyter Notebook ผ่าน Slurm allocation | สำรวจผลลัพธ์แบบ interactive |
| [03-epidemic-abs-examples.md](03-epidemic-abs-examples.md) | สร้างและรัน epidemic ABS 3 วิธี | lab หลักของ mini innovation |

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
- AI scaffolding สำหรับตั้งคำถาม ออกแบบ scenario ตรวจ Slurm script และอธิบายผลโดยอ้างอิง code, config, log และ CSV

## Smoke Job ที่อยู่ใน Repo

หลังเตรียม environment/module แล้ว ผู้ใช้ตรวจ Mesa ได้ด้วย job สั้น ๆ:

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel mini-innovation/jobs/epi_smoke.sbatch
```

ถ้า module อยู่คนละ project ให้ตั้ง `EPI_MODULE_ROOT=/project/<project>/modules` ก่อน `sbatch`.

✅ เมื่อสำเร็จ log จะบอก `mesa 2.3.4` และชื่อ API ที่ใช้ใน tutorial

## ขอบเขตความปลอดภัย

แบบจำลองนี้เป็น synthetic educational model เท่านั้น

- ใช้ประชากรและพฤติกรรมจำลองที่สร้างขึ้นเพื่อการสอน
- ใช้สำหรับเรียนรู้ HPC, ABS, uncertainty และการตีความผลลัพธ์
- ใช้ผลลัพธ์เพื่ออภิปรายเชิงวิธีวิทยา เช่น reproducibility, sensitivity และ evidence trail
- แยกงานฝึกออกจากการพยากรณ์โรคและการกำหนดนโยบายสาธารณสุขจริง
