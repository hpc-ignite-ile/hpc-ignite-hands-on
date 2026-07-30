# บทที่ 5: การประมวลผล Big Data

Chapter 5: Big Data Processing

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ 5V ของ Big Data
2. ใช้ Pandas สำหรับข้อมูลขนาดกลาง
3. ประยุกต์ Chunk Processing สำหรับข้อมูลใหญ่
4. ใช้ Out-of-Core Computing

## โครงสร้างไฟล์

```
chapter-05-big-data/
├── README.md
├── pandas_basics.py         # Pandas fundamentals
├── chunk_processing.py      # Processing large files in chunks
├── memory_efficient.py      # Memory-efficient techniques
├── generate_large_data.py   # Generate test data
└── sbatch/
    └── big_data_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba env create -f ../../environments/base.yaml
mamba activate hpc-ignite-base

# Generate sample data
python generate_large_data.py --size 1000000

# Run examples
python pandas_basics.py
python chunk_processing.py

# On SLURM
sbatch sbatch/big_data_job.sbatch
```

## แนวคิดหลัก: 5V ของ Big Data

1. **Volume** - ปริมาณข้อมูล
2. **Velocity** - ความเร็วในการสร้างข้อมูล
3. **Variety** - ความหลากหลายของข้อมูล
4. **Veracity** - ความถูกต้องของข้อมูล
5. **Value** - มูลค่าของข้อมูล

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA แล้วเลือกหมายเลข script ที่ต้องการส่งเข้า Slurm:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-05-big-data.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LABS=(
    "core-hpc/chapter-05-big-data/chunk_processing.py"
    "core-hpc/chapter-05-big-data/pandas_basics.py"
)

echo "เลือก script ของบท core-hpc/chapter-05-big-data:"
select LAB_SCRIPT in "${LABS[@]}"; do
    if [ -n "${LAB_SCRIPT:-}" ]; then
        bash scripts/lanta_submit_python_lab.sh "$LAB_SCRIPT"
        break
    fi
    echo "กรุณาเลือกหมายเลขจากรายการ"
done

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-05-big-data.sh
```
