# Weather-Health ABS: วิทยาการข้อมูลสมรรถนะสูงบน LANTA

โฟลเดอร์นี้เป็นนวัตกรรมย่อยสำหรับสอน High Performance Data Science หรือ HPDS ผ่านกระบวนการข้อมูลอากาศจริง แบบจำลองอาคารเชิงวิทยาศาสตร์ แบบจำลองเชิงตัวแทน และชุดหลักฐานที่รันบน LANTA

ในชุมชน HPC มักใช้คำว่า High Performance Data Analytics หรือ HPDA บทเรียนนี้ใช้คำว่า HPDS เพื่อเน้นทักษะของผู้ทำงานวิทยาการข้อมูลที่ต้องเข้าใจระบบจัดคิว ระบบแฟ้มขนาน การย้ายข้อมูล การแบ่งข้อมูลเป็นก้อน ประวัติที่มาของข้อมูล และหลักฐานด้านสมรรถนะ

## เป้าหมายของบทเรียน

- ดึงข้อมูลจากแหล่ง HTTP เข้าสู่ LANTA ด้วย `curl` และ `wget`
- ฝึก `rsync` ผ่าน SSH สำหรับย้ายข้อมูลจากเครื่องผู้ใช้ไปยัง LANTA
- ใช้ `zip`, `unzip`, `tar`, `gzip`, `pigz` เพื่อจัดแฟ้มรวมและลดปัญหาไฟล์ย่อยจำนวนมาก
- อ่านหลักฐานของระบบแฟ้มขนาน Lustre ด้วย `df`, `lfs getstripe`, `du`, `find`
- สร้างสภาพแวดล้อม Dask เพิ่มเติมบนฐานของโครงการ `hpc-mesa` แล้วติดตั้ง `dask` และ `distributed`
- รัน Dask `LocalCluster` ภายในทรัพยากรหนึ่งโหนดที่ Slurm จัดให้
- สร้างตัวแปรจากข้อมูลอากาศ แล้วส่งต่อให้แบบจำลองอาคารขนาดย่อและ ABS
- สรุปผลเป็น CSV รูปภาพ หลักฐานจาก Slurm และ prompt สำหรับให้ AI ช่วยตรวจหลักฐาน
- เชื่อมแนวคิดการแบ่งกราฟจาก METIS/ParMETIS เข้ากับกราฟการเดินทางและต้นทุนการสื่อสาร

## ลำดับการทำงาน

`แหล่งข้อมูล HTTP/rsync -> manifest/checksum -> แฟ้มรวมและพื้นที่พักข้อมูล -> งานย่อยของ Dask -> แบบจำลองอาคาร -> ABS -> หลักฐานจาก Slurm -> การแสดงผลสรุป -> นั่งร้านการเรียนรู้ด้วย AI`

## ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
|---|---|
| [TRAINING_SHEET_TH.md](TRAINING_SHEET_TH.md) | หน้าเรียนแบบคัดลอกคำสั่งทีละขั้นสำหรับผู้เรียน |
| [DATA_RESCUE_CADC_TH.md](DATA_RESCUE_CADC_TH.md) | หน้าเรียนกู้ข้อมูลเมื่อปลายทางหมดเวลา ครอบคลุมการดาวน์โหลดต่อจากไฟล์ค้าง checksum, manifest และ `rsync --append-verify` |
| `src/stage_weather_data.py` | แปลง NASA POWER CSV เป็นชุดข้อมูลอากาศหลายพื้นที่พร้อม manifest |
| `src/cadc_resumable_fetch.py` | ตัวช่วยสำหรับตรวจ CADC/ข้อมูลสาธารณะ ดาวน์โหลดต่อจากไฟล์ค้าง สร้าง checksum และ manifest |
| `src/hpds_weather_abs.py` | กระบวนการ Dask ที่รันแบบจำลองอาคารและ ABS หลายสถานการณ์ |
| `src/plot_hpds_summary.py` | สร้างตารางสรุปเชิงนโยบายและรูป PNG |
| `src/partition_mobility_graph.py` | เปรียบเทียบการแบ่งกราฟแบบง่ายเพื่ออธิบาย METIS/ParMETIS |
| `jobs/hpds_weather_abs.sbatch` | ไฟล์ Slurm สำหรับรันกระบวนการ Dask |
| `plots/hpds_dashboard.gp` | แดชบอร์ดของ gnuplot จาก CSV สรุป |

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

1. การย้ายข้อมูลสำเร็จ มีขนาดไฟล์และ checksum ใน manifest
2. CSV ที่พักข้อมูลไว้ทุกไฟล์มีหัวตาราง จำนวนแถว และค่าอุณหภูมิ/ความชื้นอยู่ในช่วงสมเหตุสมผล
3. งาน Slurm จบด้วย `COMPLETED` และ `ExitCode=0:0`
4. รายงาน Dask ระบุจำนวนงานย่อยและจำนวน worker
5. ตารางสรุปเชิงนโยบายแสดงการแลกเปลี่ยนระหว่างการสัมผัสความร้อน การทำความเย็น และตัวแทนความเสี่ยง
6. ตารางสรุปการแบ่งกราฟชี้ให้เห็นสมดุลภาระงานและน้ำหนักขอบที่ถูกตัดจากกราฟการเดินทาง
