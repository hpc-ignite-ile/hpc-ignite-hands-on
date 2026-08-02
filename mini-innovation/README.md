# Mini Innovation: LANTA EpiSprint

ชุดนี้เป็น tutorial ภาษาไทยสำหรับกิจกรรมสดประมาณ 40 คน โดยใช้ mini innovation ชื่อ **LANTA EpiSprint**: แบบจำลองโรคระบาดแบบ agent-based simulation ที่มี AI เป็น scaffold ช่วยตั้งคำถาม สร้าง scenario ตรวจ Slurm และอ่านผลลัพธ์

แนวคิดหลักคือให้ผู้เรียนเห็นว่า HPC ไม่ได้มีพลังเพราะรันกราฟโรคระบาดหนึ่งเส้นได้ แต่มีพลังเพราะรัน scenario จำนวนมากภายในเวลาสั้น แล้วเปรียบเทียบความไม่แน่นอนของพฤติกรรมและนโยบายได้

## หน้าเรียน

| หน้า | เรื่อง | ใช้เมื่อ |
|---|---|---|
| [00-connect-to-lanta.md](00-connect-to-lanta.md) | เข้า LANTA และเตรียม workspace | เปิดกิจกรรมหรือใช้เป็นหน้าอ้างอิงร่วม |
| [01-custom-python-env-module.md](01-custom-python-env-module.md) | สร้าง Python environment และ Lmod module สำหรับ Mesa | ผู้สอนหรือทีมที่ต้องเตรียม environment กลาง |
| [02-jupyter-notebook.md](02-jupyter-notebook.md) | เปิด Jupyter Notebook ผ่าน Slurm allocation | สำรวจผลลัพธ์แบบ interactive |
| [03-epidemic-abs-examples.md](03-epidemic-abs-examples.md) | สร้างและรัน epidemic ABS 3 วิธี | lab หลักของ mini innovation |

ทุกหน้าถูกออกแบบให้เริ่มจากเครื่อง local ด้วย `ssh` เข้า LANTA หรือมี link กลับไปยังหน้าเชื่อมต่อกลาง ผู้เรียนจึงเปิดหน้าใดหน้าหนึ่งแล้วเริ่มทำต่อได้โดยไม่ต้องอ่านทั้งชุดก่อน

## รูปแบบกิจกรรมสดที่แนะนำ

- แบ่งผู้เรียน 40 คนเป็น 10 ทีม ทีมละ 4 คน
- ผู้สอนเตรียม environment ตามหน้า 01 ไว้ล่วงหน้า
- ผู้เรียนแต่ละทีมรัน smoke job และ job array ขนาดเล็ก
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
- AI scaffolding สำหรับถาม ออกแบบ และอธิบายผล ไม่ใช่แทนที่วิทยาศาสตร์

## ขอบเขตความปลอดภัย

แบบจำลองนี้เป็น synthetic educational model เท่านั้น

- ไม่ใช้ข้อมูลผู้ป่วยจริง
- ไม่ใช้เพื่อพยากรณ์โรคจริง
- ไม่ใช้เพื่อออกคำแนะนำทางสาธารณสุข
- ใช้เพื่อเรียนรู้ HPC, ABS, uncertainty และการตีความผลลัพธ์
