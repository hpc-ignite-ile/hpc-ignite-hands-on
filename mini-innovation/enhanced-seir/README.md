# แบบจำลอง SEIR ขั้นสูงสำหรับคลินิกสมรรถนะ

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

โฟลเดอร์นี้เป็นแหล่งอ้างอิงสำหรับต่อยอดนวัตกรรมย่อยในห้องอบรมไปสู่การฝึกประเมินสมรรถนะตาม booklet หน้า 15-17 ผู้ใช้เริ่มจากคำถามวิทยาศาสตร์ แปลงคำถามเป็นงานคำนวณ เลือกทรัพยากรตามคอขวด แล้วเก็บหลักฐานของการรันให้ตรวจย้อนกลับได้

สำหรับกิจกรรมที่ผู้เรียนคัดลอกคำสั่งบน LANTA โดยตรง ให้ใช้ [TRAINING_SHEET_TH.md](TRAINING_SHEET_TH.md) ซึ่งสร้างโค้ด ข้อมูล และสคริปต์ Slurm ด้วย heredoc ครบในพื้นที่ทำงานของผู้เรียน

สำหรับ workshop ประเมินสมรรถนะ ให้ใช้ [PERFORMANCE_WORKSHOP_TH.md](PERFORMANCE_WORKSHOP_TH.md) หลังจากรัน training sheet หรือใช้เป็นหน้าเดียวจบเพื่อสร้าง MPI roofline solver, ตัวตรวจ Python overhead, รายงาน, รูปแสดงผลด้วย SVG/gnuplot และ prompt จากหลักฐานในพื้นที่ทำงานเดียวกัน

## งานวิจัยต้นแบบที่นำแนวคิดมาใช้

| งานวิจัย | แนวคิดที่ใช้ในตัวอย่าง |
|---|---|
| [Prem, Cook, and Jit, PLOS Computational Biology 2017](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005697) | contact matrix ตามกลุ่มอายุและโครงสร้างประชากร |
| [Ram and Schaposnik, Scientific Reports 2021](https://www.nature.com/articles/s41598-021-94609-3) | force of infection ที่แยกตามอายุและผลของมาตรการลดการสัมผัส |
| [Balcan et al., BMC Medicine 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3909360/) | metapopulation, mobility และการผสมของประชากรต่างพื้นที่ |
| [Colizza and Vespignani, Journal of Theoretical Biology 2008](https://www.sciencedirect.com/science/article/pii/S0022519307005991) | การเชื่อมพื้นที่ย่อยด้วย mobility network |
| [Applied Mathematical Modelling 2023 SEIQRD mobility model](https://www.sciencedirect.com/science/article/abs/pii/S0307904X23002810) | การฉีดวัคซีน ฤดูกาล พื้นที่ย่อย และการเปรียบเทียบนโยบาย |
| [Hinch et al., OpenABM-Covid19 preprint 2020](https://www.medrxiv.org/content/10.1101/2020.09.16.20195925v1.full) | ลำดับการดำเนินโรคหลายสถานะ ความเสี่ยงตามอายุ และหลักฐานด้านสมรรถนะของการทำให้รันได้จริง |

## โครงสร้างแบบจำลอง

ทั้ง C++/MPI และ PyTorch GPU/DDP ใช้ข้อมูลขนาดเล็กชุดเดียวกันใน `data/`

- `patches.csv`: พื้นที่จำลอง 3 patch และประชากร 4 กลุ่มอายุ
- `age_contact_4x4.csv`: contact matrix ตามกลุ่มอายุ
- `mobility.csv`: น้ำหนักการเดินทางหรือการผสมระหว่างพื้นที่ย่อย
- `scenarios.csv`: นโยบาย การลดการสัมผัส การลดการเดินทาง อัตราฉีดวัคซีน และจำนวนวัน

สถานะโรคคือ `S, V, E, Ip, Ia, Is, H, R, D`

- `S`: susceptible
- `V`: vaccinated และมีความเสี่ยงติดเชื้อลดลง
- `E`: exposed หรือ latent
- `Ip`: pre-symptomatic infectious
- `Ia`: asymptomatic infectious
- `Is`: symptomatic infectious
- `H`: hospitalized หรือ severe isolated
- `R`: recovered
- `D`: deaths

## รุ่นที่ 1: C++ Native MPI

ไฟล์หลักคือ `cpp_mpi/seir_mpi.cpp`

รุ่น MPI ใช้ประเมินสมรรถนะของชุดทดลองบน CPU แต่ละ rank รับสถานการณ์ทดลองคนละชุด รันแบบจำลองอายุและพื้นที่ย่อยในหน่วยความจำของ rank นั้น แล้วรวบรวมผลด้วย native MPI เพื่อเขียน CSV สรุปไฟล์เดียว

คำถามด้านสมรรถนะ:

> เมื่อเพิ่ม MPI rank แล้วเวลาจบงานของชุดสถานการณ์ทดลองดีขึ้นตาม CPU ที่ขอ หรือเห็น overhead จากงานที่เล็กเกินไป

หลักฐานที่ใช้ตัดสิน:

- `sacct`: `Elapsed`, `AllocCPUS`, `MaxRSS`, `ExitCode`
- `/usr/bin/time -v`: wall-clock, CPU และหลักฐานหน่วยความจำ
- `results/seir_mpi_summary_<jobid>.csv`: ผลวิทยาศาสตร์รายสถานการณ์ทดลอง

## รุ่นที่ 2: PyTorch GPU/DDP

ไฟล์หลักคือ `torch_ddp/seir_torch_ddp.py`

รุ่น PyTorch แปลงสถานการณ์ทดลองเป็น tensor batch บน GPU และพร้อมใช้ `torchrun` สำหรับการรันกระจายงานเมื่อใช้หลาย GPU แต่ละ rank รับชุดย่อยของสถานการณ์ทดลอง แล้วรวบรวมผลด้วย `torch.distributed`

คำถามด้านสมรรถนะ:

> ขนาดงานใหญ่พอสำหรับ GPU/DDP หรือ CPU/MPI ให้เวลาจบงานดีกว่าสำหรับแบบฝึกขนาดเล็ก

หลักฐานที่ใช้ตัดสิน:

- `nvidia-smi`: ชื่อ GPU, หน่วยความจำ และการจัดสรรอุปกรณ์
- `sacct`: เวลาที่ใช้และทรัพยากรที่จัดสรร
- `/usr/bin/time -v`: host-side timing
- `results/seir_torch_summary_<jobid>.csv`: ผลวิทยาศาสตร์รายสถานการณ์ทดลอง

## การรันบน LANTA

ใช้โฟลเดอร์นี้เป็นแหล่งอ้างอิงของโค้ดที่เตรียมไว้ จากโฟลเดอร์รากให้เรียก `sbatch` กับ `jobs/seir_mpi_perf.sbatch` สำหรับ C++/MPI และ `jobs/seir_torch_ddp_gpu.sbatch` สำหรับ PyTorch GPU/DDP ด้วยบัญชีโครงการของรอบอบรม

สำหรับคลินิกสมรรถนะ ให้รันงาน MPI ที่ `--ntasks=1`, `--ntasks=2` และ `--ntasks=4` แล้วเปรียบเทียบ `elapsed_sec` กับ `AllocCPUS` จากนั้นรันงาน PyTorch แล้วเทียบความเร็วของ GPU กับ MPI โดยใช้สถานการณ์ทดลองและสมมติฐานของแบบจำลองชุดเดียวกัน ชุดสถานการณ์ตั้งใจให้มีขนาดเล็กเพื่อให้เห็นเวลาเริ่ม GPU และ overhead จากการเปิดงานแบบกระจายเป็นหลักฐานการสอน

สำหรับ workshop ด้านประเมินสมรรถนะ ให้รัน [PERFORMANCE_WORKSHOP_TH.md](PERFORMANCE_WORKSHOP_TH.md) เพื่อเชื่อม roofline analysis, Amdahl's law, Gustafson's law, overhead taxonomy, stencil solver pattern และ Python stack overhead เข้ากับหลักฐานจาก LANTA

## วิธีตรวจความถูกต้อง

1. ทุกแถวสรุปมี `ExitCode=0:0` ใน `sacct`
2. `attack_rate` อยู่ระหว่าง `0` และ `1`
3. `peak_infectious` และ `peak_hospitalized` มีค่าเป็นศูนย์หรือบวก
4. นโยบาย `combined` ลดภาระสูงสุดเมื่อเทียบกับ `baseline` ในสถานการณ์ทดลองที่ให้มา
5. ผล CPU และ GPU ควรสอดคล้องเชิงแนวโน้ม โดยมีความต่างเชิงตัวเลขเล็กน้อยจาก random perturbation ใน C++ และ deterministic tensor update ใน PyTorch

## ชุดหลักฐาน

แต่ละงาน Slurm เขียนหลักฐานต่อไปนี้

- `notes/modules_<jobid>.txt`
- `notes/sacct_<jobid>.txt`
- `logs/<job-name>_<jobid>.out`
- `logs/<job-name>_<jobid>.err`
- `results/*summary_<jobid>.csv`

หลักฐานชุดนี้ใช้ถามคำถามตาม booklet หน้า 15-17 ได้ตรงประเด็น: โจทย์วิทยาศาสตร์คืออะไร ขอทรัพยากรแบบใด คอขวดอยู่ที่ CPU, GPU, หน่วยความจำ, scheduler หรือ I/O และการรันถัดไปควรเปลี่ยนทีละปัจจัยตรงไหน
