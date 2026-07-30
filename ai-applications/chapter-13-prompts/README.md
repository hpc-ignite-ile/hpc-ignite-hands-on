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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-13-prompts.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "ai-applications/chapter-13-prompts/prompt_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-13-prompts.sh
```
