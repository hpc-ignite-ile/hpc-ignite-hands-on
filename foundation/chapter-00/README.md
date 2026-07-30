# บทที่ 0: HPC 101 - บทนำสู่การประมวลผลสมรรถนะสูง

Chapter 0: Introduction to High-Performance Computing

## วัตถุประสงค์การเรียนรู้

1. อธิบายความหมายและความสำคัญของ HPC
2. เปรียบเทียบขีดความสามารถของอุปกรณ์ประมวลผลประเภทต่าง ๆ
3. วิเคราะห์หลักการทำงานแบบขนานและกฎของแอมดาห์ล
4. ระบุส่วนประกอบหลักของระบบ LANTA

## โครงสร้างไฟล์

```
chapter-00/
├── README.md                    # ไฟล์นี้
├── hello_lanta.py               # ตัวอย่างแรก - ทดสอบการเชื่อมต่อ
├── hello_lanta.sbatch           # SLURM script สำหรับ hello_lanta.py
├── rice_production_analysis.py  # ตัวอย่างการวิเคราะห์ผลผลิตข้าว
├── amdahl_speedup.py            # แบบฝึกหัด: กฎของแอมดาห์ล
├── wrf_chem_airquality.sbatch   # SLURM script สำหรับ WRF-Chem
└── exercises/
    └── amdahl_exercise.py       # แบบฝึกหัดให้นักศึกษาเติม
```

## การใช้งาน

### 1. Hello LANTA

```bash
# Login to LANTA
ssh username@lanta.nstda.or.th

# Clone repo (ถ้ายังไม่มี)
cd $HOME
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on/foundation/chapter-00

# Run interactively
source ../../slurm/module-loads/base.sh
python hello_lanta.py

# Or submit as job
sbatch hello_lanta.sbatch
```

ถ้าต้องการ flow ที่ทดสอบกับ LANTA ปัจจุบันแล้ว แนะนำเริ่มจากบทใหม่:

```bash
cd $HOME/hpc-ignite-hands-on
export HPC_IGNITE_ACCOUNT=<project-account>
export HPC_IGNITE_PARTITION=compute-limited
bash scripts/lanta_submit_foundation.sh smoke
```

### 2. Rice Production Analysis

```bash
# Run locally (no HPC needed)
python rice_production_analysis.py
```

### 3. Amdahl's Law Exercise

```bash
# View solution
python amdahl_speedup.py

# Or complete the exercise yourself
python exercises/amdahl_exercise.py
```

### 4. WRF-Chem Air Quality (Advanced)

```bash
# This requires WRF-Chem module and data
# For demonstration only
sbatch wrf_chem_airquality.sbatch
```

## แนวคิดหลัก

### กฎของแอมดาห์ล (Amdahl's Law)

$$S = \frac{1}{(1-P) + \frac{P}{N}}$$

- $S$ = Speedup
- $P$ = สัดส่วนงานที่ทำแบบขนานได้
- $N$ = จำนวนหน่วยประมวลผล

### ระบบ LANTA

| รายการ | ข้อมูล |
|--------|-------|
| ความเร็วสูงสุด | 8.15 PetaFLOPS |
| CPU Nodes | 160 nodes (20,480 cores) |
| GPU Nodes | 176 nodes (704 NVIDIA A100) |
| Storage | 10 PB Lustre |

## เอกสารอ้างอิง

- [Curriculum Book - Chapter 0](https://github.com/wdiazcarballo/hpc-curriculum/blob/main/docs/curriculum-book/chapters/chapter-00-hpc-101.md)
- [LANTA User Guide](https://docs.lanta.nstda.or.th)
