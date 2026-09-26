# เริ่มต้น HPC IGNITE ด้วยภาพ: จาก laptop ถึงผลทดลอง

ถ้าเพิ่งใช้ HPC ครั้งแรก ให้เริ่มจากหน้านี้ คุณไม่จำเป็นต้องรู้ MPI, GPU หรือ Mesa ทั้งหมดก่อน เป้าหมายแรกคือส่งงานเล็กหนึ่งงาน แล้วตอบได้ว่า **รันที่ไหน ใช้ทรัพยากรอะไร และรู้ได้อย่างไรว่าผลถูกต้อง**

ภาพทั้งสี่เป็นภาพอธิบายแนวคิดที่สร้างด้วย AI ไม่ใช่ screenshot ของ LANTA และไม่ใช่หลักฐานว่าการทดลองผ่าน ดู [ผลรันจริงและข้อจำกัด](lanta-runs/2026-09-26-pv915002/README.md) แยกต่างหาก ภาพมีข้อความภาษาอังกฤษเพื่อจับคู่กับคำสั่งจริง; คำอธิบายไทยและลำดับแบบข้อความอยู่ใต้ภาพ

## 1. Tutorial นี้พาเราไปทำอะไร

![เส้นทางหกขั้น: เชื่อมต่อ เตรียมไฟล์ ส่ง Slurm job รันบน compute node ตรวจผล แล้ววัดและปรับปรุง](images/beginners/tutorial-overview.png)

เริ่มจาก **Connect → Prepare → Submit → Run → Check → Improve**: เข้าเครื่องด้วย SSH, เตรียม code/data/environment, ขอทรัพยากรด้วย Slurm, รอให้ compute node ทำงาน, ตรวจ log กับ output แล้วค่อยเปลี่ยนการตั้งค่าเพื่อให้เร็วหรือคุ้มขึ้น

ตัวอย่างในหลักสูตรมีทั้งงานตัวเลข CPU/MPI, GPU/AI, วิทยาศาสตร์ และ agent-based models ที่จำลองคนหรือพฤติกรรม เรียน workflow เดียวให้คล่องก่อน แล้วนำไปใช้กับโมเดลที่สนใจ

**ทำต่อ:** [ตั้งค่า LANTA](../LANTA_SETUP.md) แล้วรัน [First Job](../foundation/chapter-00/README.md). จุดตรวจแรกคือมี job ID, log และ output ของงานตัวเอง ไม่ใช่เพียงเห็นข้อความตัวอย่างในคู่มือ

## 2. คำสั่งกับข้อมูลเดินทางคนละเส้น

![เส้นคำสั่ง laptop ไป login node ไป Slurm queue ไป compute node; เส้นข้อมูลผ่าน transfer host ไป project storage ซึ่ง compute node อ่านและเขียน](images/beginners/lanta-job-workflow.png)

**เส้นคำสั่ง:** laptop → SSH → login node → `sbatch` → scheduler → compute node. Login node ใช้ตรวจไฟล์และส่งงาน ไม่ใช่ที่รันการคำนวณหนัก

**เส้นข้อมูล:** laptop → `rsync`/`scp` → transfer host → project storage. Compute node อ่าน input และเขียน output ที่ storage. การ upload สำเร็จยังไม่ใช่การรัน simulation

`PENDING` หมายถึงกำลังรอทรัพยากรหรือ dependency; `RUNNING` หมายถึงกำลังทำงาน. เมื่อจบอาจสำเร็จหรือล้มเหลว จึงต้องดู `sacct`, exit code, stderr และไฟล์ผลลัพธ์ ภาพย่อไม่ได้แสดงสถานะล้มเหลวทุกแบบ

**ทำต่อ:** [Foundation lab](../foundation/lanta-foundation/README.md). ใช้บัญชีโครงการที่ยังมีสิทธิ์และ allocation; `pv915002` คือบัญชีที่ใช้ใน campaign นี้ ไม่ใช่บัญชีถาวรของผู้เรียนทุกคน

## 3. ตรวจให้ถูก ก่อนถามว่าเร็วขึ้นหรือไม่

![ตรวจ correctness บันทึก baseline วัดเวลา CPU memory GPU เปลี่ยนหนึ่งอย่าง แล้วทดลองซ้ำ โดยเก็บ job ID log output และ resource statistics](images/beginners/performance-learning-loop.png)

1. **Check correctness:** ผลมีจำนวนแถว รูปร่าง ค่า และสมบัติที่คาดไว้หรือไม่? เปรียบเทียบกับ reference หรือตรวจ tolerance
2. **Record a baseline:** จด input, seed, software version และทรัพยากรของรันตั้งต้น
3. **Measure:** แยก queue wait, เวลารัน, CPU time, memory และ GPU usage. ค่าที่ไม่ได้วัดต้องระบุว่าไม่มี ไม่ใส่ศูนย์แทน
4. **Change one thing:** เช่นจำนวน threads/ranks หรือ batch size โดยใช้ input เดิม
5. **Repeat:** รันซ้ำอย่างน้อยสามครั้งต่อ configuration เพื่อเริ่มเห็นความแปรปรวน. Retry ของ seed เดิมไม่ใช่ independent scientific sample

ตัวอย่างจริงใน campaign มีงานที่ `COMPLETED` แต่ไม่ได้รัน scientific application เต็มรูปแบบ และโมเดล C++/GPU บางคู่ใช้ noise ต่างกัน จึงห้ามแปลสถานะสำเร็จเป็น “ผลวิทยาศาสตร์เท่ากัน” หรือ “GPU เร็วกว่า” โดยอัตโนมัติ

**ทำต่อ:** [Performance evaluation ของทุก hands-on](PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md) และ [ดู plot/table ใน notebook](../mini-innovation/05-output-display-jupyter-gnuplot.md).

## 4. Mesa, thermal surrogate และ EnergyPlus ต่างกันอย่างไร

![Mesa agents รับอุณหภูมิจาก building model และส่งคำขอ setpoint กลับ; weather ป้อนเข้า building; thermal surrogate เป็นแบบฝึกเริ่มต้น ส่วน EnergyPlus เป็น advanced integration](images/beginners/mesa-twinb-learning-map.png)

**Mesa** จัดการ agents เช่นคนและพฤติกรรม; **thermal surrogate** เป็นโมเดลความร้อนแบบย่อสำหรับฝึกการส่งข้อมูลกลับไปมา; **EnergyPlus** เป็นอีกตัวเลือกสำหรับฟิสิกส์อาคาร ไม่ใช่ชื่อใหม่ของ surrogate

ลูปที่ตั้งใจคือ weather → building → indoor temperature → agents → setpoint requests → building. จากนั้นจึงเปรียบเทียบ energy, comfort และ runtime. ต้องตรวจ timestamp, warmup, actuator และ synchronization ก่อนเชื่อผลจากลูปจริง

**เริ่มตามลำดับ:** [environment Mesa](../mini-innovation/01-custom-python-env-module.md) → [epidemic agents](../mini-innovation/03-epidemic-abs-examples.md) → [Twin-B surrogate](../mini-innovation/04-building-cosimulation-twinb.md) → [Twin-B repository/HeatLab](../mini-innovation/06-twinb-heatlab-repository.md).

**สถานะสำคัญ:** Mesa-only และ surrogate ผ่าน baseline แต่ EnergyPlus/Mesa coupled integration ยังไม่ผ่านใน campaign 2026-09-26. ภาพนี้อธิบาย architecture ที่ตั้งใจ ไม่ได้ยืนยันว่าระบบ coupled พร้อมใช้หรือถูกต้องทางวิทยาศาสตร์

## ก่อนขยับไปบทถัดไป

คุณควรบอกได้ว่าใช้ input ชุดไหน, job ID อะไร, รันบน node/partition ไหน, ผลอยู่ที่ใด, correctness ผ่านเกณฑ์อะไร และใช้เวลา/ทรัพยากรเท่าไร ถ้าข้อใดตอบไม่ได้ ให้กลับไปเก็บหลักฐานก่อนเพิ่มจำนวน CPU/GPU

อ่านเพิ่มเติม: [คำศัพท์และคำสั่ง Bash](BASH_COMMAND_REFERENCE_TH.md) · [ผลรันจริง](lanta-runs/2026-09-26-pv915002/README.md) · [ที่มาและ prompts ของภาพ](images/beginners/PROMPTS.md).
