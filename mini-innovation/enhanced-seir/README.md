# แบบจำลอง SEIR ขั้นสูงสำหรับ Performance Clinic

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

folder นี้เป็น reference สำหรับต่อยอด onsite mini innovation ไปสู่ performance practice ตาม booklet หน้า 15-17 ผู้ใช้เริ่มจากคำถามวิทยาศาสตร์ แปลงคำถามเป็นงานคำนวณ เลือกทรัพยากรตามคอขวด แล้วเก็บหลักฐานของ run ให้ตรวจย้อนกลับได้

สำหรับกิจกรรมที่ผู้เรียนแปะคำสั่งบน LANTA โดยตรง ให้ใช้ [TRAINING_SHEET_TH.md](TRAINING_SHEET_TH.md) ซึ่งสร้าง source, data และ Slurm script ด้วย heredoc ครบใน workspace ของผู้เรียน

## งานวิจัยต้นแบบที่นำแนวคิดมาใช้

| งานวิจัย | แนวคิดที่ใช้ในตัวอย่าง |
|---|---|
| [Prem, Cook, and Jit, PLOS Computational Biology 2017](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005697) | contact matrix ตามกลุ่มอายุและโครงสร้างประชากร |
| [Ram and Schaposnik, Scientific Reports 2021](https://www.nature.com/articles/s41598-021-94609-3) | force of infection ที่แยกตามอายุและผลของมาตรการลด contact |
| [Balcan et al., BMC Medicine 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3909360/) | metapopulation, mobility และการผสมของประชากรต่างพื้นที่ |
| [Colizza and Vespignani, Journal of Theoretical Biology 2008](https://www.sciencedirect.com/science/article/pii/S0022519307005991) | การเชื่อม patch ด้วย mobility network |
| [Applied Mathematical Modelling 2023 SEIQRD mobility model](https://www.sciencedirect.com/science/article/abs/pii/S0307904X23002810) | vaccination, seasonality, spatial patches และ policy comparison |
| [Hinch et al., OpenABM-Covid19 preprint 2020](https://www.medrxiv.org/content/10.1101/2020.09.16.20195925v1.full) | disease progression หลายสถานะ ความเสี่ยงตามอายุ และหลักฐานด้าน implementation performance |

## โครงสร้างแบบจำลอง

ทั้ง C++/MPI และ PyTorch GPU/DDP ใช้ข้อมูลขนาดเล็กชุดเดียวกันใน `data/`

- `patches.csv`: พื้นที่จำลอง 3 patch และประชากร 4 กลุ่มอายุ
- `age_contact_4x4.csv`: contact matrix ตามกลุ่มอายุ
- `mobility.csv`: น้ำหนักการเดินทางหรือการผสมระหว่าง patch
- `scenarios.csv`: policy, contact reduction, mobility reduction, vaccination rate และจำนวนวัน

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

## Version 1: C++ Native MPI

ไฟล์หลักคือ `cpp_mpi/seir_mpi.cpp`

รุ่น MPI ใช้ประเมิน performance ของ CPU ensemble แต่ละ rank รับ scenario คนละชุด รันแบบจำลองอายุและ patch ใน memory ของ rank นั้น แล้วรวบรวมผลด้วย native MPI เพื่อเขียน summary CSV เดียว

คำถาม performance:

> เมื่อเพิ่ม MPI rank แล้ว turnaround ของ scenario ensemble ดีขึ้นตาม CPU ที่ขอหรือเห็น overhead จากงานที่เล็กเกินไป

หลักฐานที่ใช้ตัดสิน:

- `sacct`: `Elapsed`, `AllocCPUS`, `MaxRSS`, `ExitCode`
- `/usr/bin/time -v`: wall-clock, CPU และ memory evidence
- `results/seir_mpi_summary_<jobid>.csv`: ผลวิทยาศาสตร์ราย scenario

## Version 2: PyTorch GPU/DDP

ไฟล์หลักคือ `torch_ddp/seir_torch_ddp.py`

รุ่น PyTorch แปลง scenario เป็น tensor batch บน GPU และพร้อมใช้ `torchrun` สำหรับ distributed execution เมื่อใช้หลาย GPU แต่ละ rank รับ scenario subset แล้วรวบรวมผลด้วย `torch.distributed`

คำถาม performance:

> ขนาดงานใหญ่พอสำหรับ GPU/DDP หรือ CPU/MPI ให้ turnaround ดีกว่าสำหรับ mini practical

หลักฐานที่ใช้ตัดสิน:

- `nvidia-smi`: GPU name, memory และ allocation
- `sacct`: elapsed time และ allocated resource
- `/usr/bin/time -v`: host-side timing
- `results/seir_torch_summary_<jobid>.csv`: ผลวิทยาศาสตร์ราย scenario

## การรันบน LANTA

ใช้ folder นี้เป็น prepared source reference จาก folder root ให้ส่ง `jobs/seir_mpi_perf.sbatch` สำหรับ C++/MPI และ `jobs/seir_torch_ddp_gpu.sbatch` สำหรับ PyTorch GPU/DDP ด้วย project account ของรอบอบรม

สำหรับ performance clinic ให้รัน MPI job ที่ `--ntasks=1`, `--ntasks=2` และ `--ntasks=4` แล้วเปรียบเทียบ `elapsed_sec` กับ `AllocCPUS` จากนั้นรัน PyTorch job แล้วเทียบ GPU speed กับ MPI โดยใช้ scenario และ model assumptions ชุดเดียวกัน ชุด scenario ตั้งใจให้มีขนาดเล็กเพื่อให้เห็น GPU startup และ distributed launch overhead เป็นหลักฐานการสอน

## วิธีตรวจความถูกต้อง

1. ทุก summary row มี `ExitCode=0:0` ใน `sacct`
2. `attack_rate` อยู่ระหว่าง `0` และ `1`
3. `peak_infectious` และ `peak_hospitalized` มีค่าเป็นศูนย์หรือบวก
4. policy `combined` ลด peak burden เมื่อเทียบกับ `baseline` ใน scenario ที่ให้มา
5. ผล CPU และ GPU ควรสอดคล้องเชิงแนวโน้ม โดยมีความต่างเชิงตัวเลขเล็กน้อยจาก random perturbation ใน C++ และ deterministic tensor update ใน PyTorch

## Evidence Bundle

แต่ละ Slurm job เขียนหลักฐานต่อไปนี้

- `notes/modules_<jobid>.txt`
- `notes/sacct_<jobid>.txt`
- `logs/<job-name>_<jobid>.out`
- `logs/<job-name>_<jobid>.err`
- `results/*summary_<jobid>.csv`

หลักฐานชุดนี้ใช้ถามคำถามตาม booklet หน้า 15-17 ได้ตรงประเด็น: โจทย์วิทยาศาสตร์คืออะไร ขอ resource แบบใด คอขวดอยู่ที่ CPU, GPU, memory, scheduler หรือ I/O และ run ถัดไปควรเปลี่ยนทีละปัจจัยตรงไหน
