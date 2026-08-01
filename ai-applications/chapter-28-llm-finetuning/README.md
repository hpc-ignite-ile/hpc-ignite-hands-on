# บทที่ 28: การ Finetune LLM

Chapter 28: LLM Finetuning

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ LLM Finetuning Methods
2. ใช้ LoRA/QLoRA
3. Prepare Thai Language Data
4. Train และ Evaluate Models

## โครงสร้างไฟล์

```
chapter-28-llm-finetuning/
├── README.md
├── lora_basics.py          # LoRA fundamentals
├── prepare_data.py         # Data preparation
├── finetune_llm.py         # Finetuning script
├── evaluate_model.py       # Model evaluation
└── sbatch/
    └── finetune_multi_gpu.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-llm python=3.9 transformers peft accelerate bitsandbytes
mamba activate hpc-llm

# Prepare data
python prepare_data.py

# Finetune (on GPU nodes)
sbatch sbatch/finetune_multi_gpu.sbatch
```

## Finetuning Methods

| Method | Memory | Speed | Quality |
|--------|--------|-------|---------|
| Full Finetuning | Very High | Slow | Best |
| LoRA | Low | Fast | Good |
| QLoRA | Very Low | Fast | Good |
| Prompt Tuning | Very Low | Very Fast | Limited |

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-ai-applications/chapter-28-llm-finetuning/lora_basics.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=ai-applications/chapter-28-llm-finetuning/lora_basics.py`
