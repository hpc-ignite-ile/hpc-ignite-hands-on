# Weather-Health ABS: High Performance Data Science บน LANTA

folder นี้เป็น mini innovation สำหรับสอน High Performance Data Science หรือ HPDS ผ่าน workflow ข้อมูลอากาศจริง, scientific building model, agent-based simulation และ evidence bundle บน LANTA

ในชุมชน HPC คำที่พบมากคือ High Performance Data Analytics หรือ HPDA ส่วนชื่อ HPDS ใช้ในบทเรียนนี้เพื่อเน้นทักษะของผู้ปฏิบัติ data science ที่ต้องทำงานกับ scheduler, parallel filesystem, data transfer, chunking, provenance และ performance evidence

## เป้าหมายของบทเรียน

- ดึงข้อมูลจากแหล่ง HTTP เข้าสู่ LANTA ด้วย `curl` และ `wget`
- ฝึก `rsync` ผ่าน SSH สำหรับย้ายข้อมูลจากเครื่อง local ไปยัง LANTA
- ใช้ `zip`, `unzip`, `tar`, `gzip`, `pigz` เพื่อจัดการ archive และปัญหา many-small-files
- อ่านหลักฐานของ Lustre parallel filesystem ด้วย `df`, `lfs getstripe`, `du`, `find`
- สร้าง Dask overlay environment โดยอิง project `hpc-mesa` แล้วเพิ่ม `dask` และ `distributed`
- รัน Dask `LocalCluster` ภายใน Slurm allocation หนึ่ง node
- สร้าง weather-derived features แล้วป้อนให้ reduced building model และ ABS
- สรุปผลเป็น CSV, รูปภาพ, Slurm evidence และ AI review prompt
- เชื่อมแนวคิด graph partitioning จาก METIS/ParMETIS เข้ากับ mobility graph และ communication cost

## โครงสร้าง workflow

`HTTP/rsync data source -> manifest/checksum -> archive/staging -> Dask tasks -> building model -> ABS -> Slurm evidence -> summary display -> AI scaffold`

## ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
|---|---|
| [TRAINING_SHEET_TH.md](TRAINING_SHEET_TH.md) | หน้า copy-paste standalone สำหรับผู้เรียน |
| [DATA_RESCUE_CADC_TH.md](DATA_RESCUE_CADC_TH.md) | หน้า data-rescue สำหรับ host timeout, resumable download, checksum, manifest และ `rsync --append-verify` |
| `src/stage_weather_data.py` | แปลง NASA POWER CSV เป็น weather chunks หลายพื้นที่และ manifest |
| `src/cadc_resumable_fetch.py` | helper สำหรับ CADC/public-data probe, resumable download, checksum และ manifest |
| `src/hpds_weather_abs.py` | Dask workflow ที่รัน building model และ ABS หลาย scenario |
| `src/plot_hpds_summary.py` | สร้าง policy summary และรูป PNG |
| `src/partition_mobility_graph.py` | เปรียบเทียบ partition แบบง่ายเพื่ออธิบาย METIS/ParMETIS |
| `jobs/hpds_weather_abs.sbatch` | Slurm job สำหรับรัน Dask workflow |
| `plots/hpds_dashboard.gp` | gnuplot dashboard จาก CSV summary |

## หลักฐานที่ผู้เรียนควรส่ง

- `data/weather_manifest.csv`
- `logs/lanta_cadc_probe.txt` หรือ `manifest/cadc_manifest.csv` เมื่อใช้ data-rescue sheet
- `notes/filesystem_evidence.txt`
- `notes/environment_<jobid>.txt`
- `notes/time_hpds_weather_abs_<jobid>.txt`
- `notes/sacct_<jobid>.txt`
- `results/hpds_weather_abs_summary.csv`
- `results/hpds_policy_summary.csv`
- `results/mobility_partition_summary.csv`
- `figures/hpds_weather_abs_summary.png`
- `notes/ai_hpds_review_prompt.md`

## เกณฑ์ตัดสินผล

1. transfer สำเร็จ มีขนาดไฟล์และ checksum ใน manifest
2. staged CSV ทุกไฟล์มี header, จำนวนแถว และค่า temperature/humidity อยู่ในช่วงสมเหตุสมผล
3. Slurm job จบด้วย `COMPLETED` และ `ExitCode=0:0`
4. Dask report ระบุจำนวน tasks และ workers
5. policy summary แสดง trade-off ระหว่าง exposure, cooling และ risk proxy
6. partition summary ชี้ให้เห็น load balance และ edge cut จาก mobility graph
