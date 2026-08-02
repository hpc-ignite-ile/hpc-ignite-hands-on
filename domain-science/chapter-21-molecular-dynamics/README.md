# บทที่ 21: Molecular Dynamics

Chapter 21: Molecular Dynamics Simulations

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p gpu-devel domain-science/chapter-21-molecular-dynamics/jobs/gromacs_gpu_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น version ของ GROMACS, path ของ shared `benchPEP.tpr` ถ้ามี และ performance summary จาก `gmx mdrun`

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ MD Simulation
2. ใช้ OpenMM สำหรับ MD บน GPU
3. วิเคราะห์ Trajectory Data
4. คำนวณ Properties จาก Simulation

## โครงสร้างไฟล์

```
chapter-21-molecular-dynamics/
├── README.md
├── md_basics.py            # MD fundamentals
├── lennard_jones.py        # Simple LJ simulation
├── water_simulation.py     # Water box simulation
├── trajectory_analysis.py  # Analyze MD trajectories
└── sbatch/
    └── md_gpu.sbatch
```

## การใช้งาน

```bash
# On LANTA, start with the real GROMACS GPU smoke job
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p gpu-devel domain-science/chapter-21-molecular-dynamics/jobs/gromacs_gpu_smoke.sbatch

# Concept scripts can still run as lightweight Python examples
python md_basics.py
python lennard_jones.py
```

## MD Simulation Loop

```
1. Initialize positions and velocities
2. Calculate forces: F = -∇U(r)
3. Integrate equations of motion
4. Update positions and velocities
5. Apply constraints/thermostats
6. Repeat for desired time
```

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-21-molecular-dynamics/lennard_jones.py}"

mkdir -p jobs logs results/python-labs

cat > jobs/run_python_lab.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-python-lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi
mkdir -p "results/python-labs/${SLURM_JOB_ID}"
echo "script=${LAB_SCRIPT}"
python "$LAB_SCRIPT" | tee "results/python-labs/${SLURM_JOB_ID}/output.txt"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --export=ALL,LAB_SCRIPT="$LAB_SCRIPT" --parsable jobs/run_python_lab.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Results: find results/python-labs/${job_id} -type f -maxdepth 2 -print"
```

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-21-molecular-dynamics/lennard_jones.py`
