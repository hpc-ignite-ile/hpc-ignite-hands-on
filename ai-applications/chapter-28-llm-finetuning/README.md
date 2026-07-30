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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-28-llm-finetuning.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "ai-applications/chapter-28-llm-finetuning/lora_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-28-llm-finetuning.sh
```
