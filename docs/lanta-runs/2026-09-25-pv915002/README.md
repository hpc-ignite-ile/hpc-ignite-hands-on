# หลักฐาน LANTA: pv915002 วันที่ 2026-09-25

หน้านี้บันทึกผลจากงานจริงบน LANTA ไม่ใช่ค่าจำลอง ภาพใน tutorial เป็นภาพประกอบ “expected result” ที่สร้างจากข้อมูลชุดนี้ ส่วนข้อความ `stdout`, `stderr` และ `sacct` ด้านล่างคือหลักฐานอ้างอิงที่ต้องใช้เมื่อตรวจความถูกต้อง

คำสั่ง Bash และ Slurm ที่ใช้บันทึกหลักฐานอธิบายไว้ใน [BASH command reference](../../BASH_COMMAND_REFERENCE_TH.md)

พื้นที่แคมเปญ:

```text
/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260925
```

## Foundation smoke: job 6338432

สถานะและการใช้ทรัพยากร:

```text
JobID|JobName|Account|Partition|State|ExitCode|Elapsed|TotalCPU|UserCPU|SystemCPU|AllocCPUS|ReqCPUS|ReqMem|MaxRSS|MaxVMSize|AveCPU|NodeList
6338432|hpcig-foundation-smoke|pv915002|compute-devel|COMPLETED|0:0|00:00:05|00:01.040|00:00.619|00:00.420|1|1|512M||||lanta-c-156
6338432.batch|batch|pv915002||COMPLETED|0:0|00:00:05|00:01.039|00:00.618|00:00.420|1|1||22572K|0|00:00:01|lanta-c-156
6338432.extern|extern|pv915002||COMPLETED|0:0|00:00:05|00:00.001|00:00.001|00:00:00|1|1||0|0|00:00:00|lanta-c-156
```

ตัวอย่าง `stdout` ที่ได้จริง:

```text
Base modules loaded for HPC Ignite:
Currently Loaded Modules:
  1) cray-python/3.10.10   2) Mamba/23.11.0-0

Repository : /project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260925/repo
Job ID     : 6338432
Node       : x1001c3s6b1n1
Start      : 2026-09-25T22:42:41+07:00
========================================================================
HPC Ignite: LANTA Foundation Smoke Test
========================================================================
Python          : 3.10.13 (/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/bin/python)
ดูเหมือน LANTA  : True
SLURM_JOB_ID           6338432
SLURM_JOB_NAME         hpcig-foundation-smoke
SLURM_NODELIST         lanta-c-156
SLURM_NTASKS           1
SLURM_CPUS_PER_TASK    1
SLURM_MEM_PER_NODE     512
SLURM_JOB_PARTITION    compute-devel
SLURM_JOB_ACCOUNT      pv915002
Wrote JSON report: results/foundation/6338432/system.json
CPU baseline workload
n          : 500000
pi estimate: 3.141592654564
abs error  : 9.742940e-10
elapsed sec: 0.0632
Finish     : 2026-09-25T22:42:42+07:00
```

`stderr` ว่าง ค่า `MaxRSS` ของขั้น `batch` คือ `22572K` และเวลางานที่ Slurm เห็นคือ 5 วินาที จึงไม่ควรใช้ smoke ขนาดนี้สรุป scalability เพราะ startup มีสัดส่วนสูงกว่า workload 0.0632 วินาที

## HPC-Mesa smoke: job 6338471

สภาพแวดล้อมถูกสร้างใน project space ด้วย Python 3.12.14 และ Mesa 3.5.1 แล้วโหลดผ่าน [modulefile](modulefiles/hpc-mesa/3.5.1.lua)

สถานะและการใช้ทรัพยากร:

```text
JobID|JobName|Account|Partition|State|ExitCode|Elapsed|TotalCPU|UserCPU|SystemCPU|AllocCPUS|ReqCPUS|ReqMem|MaxRSS|MaxVMSize|AveCPU|NodeList
6338471|epi-abs-smoke|pv915002|compute-devel|COMPLETED|0:0|00:00:22|00:02.227|00:01.037|00:01.189|1|1|1G||||lanta-c-156
6338471.batch|batch|pv915002||COMPLETED|0:0|00:00:22|00:02.225|00:01.036|00:01.189|1|1||114080K|0|00:00:02|lanta-c-156
6338471.extern|extern|pv915002||COMPLETED|0:0|00:00:22|00:00.001|00:00.001|00:00:00|1|1||0|0|00:00:00|lanta-c-156
```

ตัวอย่าง `stdout` ที่ได้จริง:

```text
mesa 3.5.1
api MultiGrid AgentSet
```

`stderr` ว่าง ค่า `MaxRSS` ของขั้น `batch` คือ `114080K` งานใช้ CPU รวมประมาณ 2.227 วินาที แต่ elapsed 22 วินาที แสดงว่า environment/module/import startup ครองเวลาส่วนใหญ่ การ optimize โมเดลต้องวัดช่วง simulation แยกและใช้ input ใหญ่กว่านี้

## คำสั่งเก็บสถิติแบบเดียวกัน

```bash
job_id=<jobid>
sacct -j "$job_id" -P \
  -o JobID,JobName,Account,Partition,State,ExitCode,Elapsed,TotalCPU,UserCPU,SystemCPU,AllocCPUS,ReqCPUS,ReqMem,MaxRSS,MaxVMSize,AveCPU,NodeList
```

ต้องเก็บแถว `.batch` เพราะ LANTA รายงาน `MaxRSS`, `MaxVMSize` และ `AveCPU` ของ process step ในแถวนี้ ส่วนแถว job หลักใช้ตรวจ account, partition, state, requested memory และ elapsed รวม
