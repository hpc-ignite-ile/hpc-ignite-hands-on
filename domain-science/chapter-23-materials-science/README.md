# บทที่ 23: วัสดุศาสตร์

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

Chapter 23: Materials Science

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel domain-science/chapter-23-materials-science/jobs/qe_scf_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น input Si SCF ขนาดเล็ก, output จาก `pw.x`, และไฟล์สรุป energy/convergence หาก pseudopotential shared พร้อม

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ DFT Calculations
2. วิเคราะห์ Crystal Structures
3. คำนวณ Electronic Properties
4. ศึกษา Material Databases

## โครงสร้างไฟล์

```
chapter-23-materials-science/
├── README.md
├── crystal_structures.py   # Crystal structure analysis
├── band_structure.py       # Band structure concepts
├── material_properties.py  # Calculate properties
└── sbatch/
    └── dft_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-materials python=3.9 ase pymatgen numpy matplotlib
mamba activate hpc-materials

# Run examples
python crystal_structures.py
python material_properties.py
```

## Key Concepts

- **DFT**: Density Functional Theory
- **Band Gap**: Energy gap between valence and conduction bands
- **Crystal Systems**: Cubic, hexagonal, tetragonal, etc.

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-23-materials-science/crystal_structures.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-23-materials-science/crystal_structures.py`
