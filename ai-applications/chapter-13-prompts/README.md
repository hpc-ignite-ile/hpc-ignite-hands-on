# บทที่ 13: Prompt Engineering

Chapter 13: Prompt Engineering for HPC

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ Prompt Engineering
2. สร้าง Effective Prompts
3. ใช้ LLM APIs
4. ประยุกต์กับงาน HPC

## โครงสร้างไฟล์

```
chapter-13-prompts/
├── README.md
├── prompt_basics.py        # Prompt fundamentals
├── few_shot_learning.py    # Few-shot examples
├── chain_of_thought.py     # CoT prompting
├── code_generation.py      # Code generation prompts
└── hpc_assistant.py        # HPC-specific prompts
```

## การใช้งาน

```bash
# Install dependencies
pip install openai anthropic

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run examples
python prompt_basics.py
python chain_of_thought.py
```

## Prompt Structure

```
[System instruction]
[Context / Background]
[Task description]
[Input data]
[Output format specification]
[Examples (optional)]
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
export LAB_SCRIPT="${LAB_SCRIPT:-ai-applications/chapter-13-prompts/prompt_basics.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=ai-applications/chapter-13-prompts/prompt_basics.py`
