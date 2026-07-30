# บทที่ 22: การจำลองภูมิอากาศ

Chapter 22: Climate Modeling

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ Climate Models
2. ใช้ข้อมูล NetCDF
3. วิเคราะห์ข้อมูล Climate
4. สร้าง Visualizations

## โครงสร้างไฟล์

```
chapter-22-climate-modeling/
├── README.md
├── netcdf_basics.py        # Working with NetCDF
├── climate_analysis.py     # Climate data analysis
├── temperature_trends.py   # Temperature trend analysis
├── thai_rainfall.py        # Thailand rainfall analysis
└── sbatch/
    └── climate_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-climate python=3.9 netcdf4 xarray cartopy matplotlib
mamba activate hpc-climate

# Run examples
python netcdf_basics.py
python thai_rainfall.py
```

## Climate Data Sources

- ERA5: ECMWF Reanalysis
- CMIP6: Coupled Model Intercomparison Project
- Thai Meteorological Department

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-22-climate-modeling.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-22-climate-modeling/climate_analysis.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-22-climate-modeling.sh
```
