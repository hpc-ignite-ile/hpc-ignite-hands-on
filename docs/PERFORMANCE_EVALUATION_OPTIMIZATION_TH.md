# การประเมินและปรับสมรรถนะทุก HPC Ignite Hands-On

![ลูปการเรียนรู้: correctness baseline measurement เปลี่ยนหนึ่งอย่าง แล้วทดลองซ้ำพร้อมเก็บหลักฐาน](images/beginners/performance-learning-loop.png)

ภาพแนวคิด ไม่ใช่ผล benchmark: ตรวจความถูกต้อง → เก็บ baseline → วัด → เปลี่ยนทีละอย่าง → ทดลองซ้ำ. ดู [คำอธิบายแบบเริ่มต้น](BEGINNER_VISUAL_GUIDE_TH.md#3-ตรวจให้ถูก-ก่อนถามว่าเร็วขึ้นหรือไม่).

ตัวอย่างจาก [campaign จริง 2026-09-26](lanta-runs/2026-09-26-pv915002/README.md): เก็บผล 70 baseline workflows พร้อม raw accounting, output และ notebook ที่ execute แล้ว รายงานแยก preflight, surrogate, deterministic validation และ coupled failure ไม่ใช้คำว่า `COMPLETED` แทน scientific correctness

ข้อค้นพบสำหรับผู้เรียน: Slurm sampling อาจพลาด peak memory ของงานที่จบเร็ว; GNU time รอบ `srun` อาจวัดเฉพาะ launcher; array task-seconds ไม่ใช่ makespan; ห้ามรวม retry เป็น independent repeat; และ stochastic CPU/GPU models ที่ใช้ noise ต่างกันต้องตรวจ ensemble/inputs ก่อนเทียบ speedup ส่วนค่าความเร็ว 1/2/4 ranks ที่มีเพียงหนึ่ง sample เป็น demonstration ไม่ใช่ข้อสรุปทางสถิติ

หน้านี้เป็นเส้นทางร่วมหลังจากแต่ละ hands-on รันถูกต้องแล้ว เป้าหมายไม่ใช่ทำให้ใช้ CPU หรือ GPU มากที่สุด แต่หาคำตอบว่า **ทรัพยากรแบบใดให้ผลลัพธ์ถูกต้อง เร็ว คุ้มค่า และทำซ้ำได้** บน LANTA

คำสั่ง Bash และ Slurm ที่ใช้ในหน้านี้อธิบายไว้ใน [BASH_COMMAND_REFERENCE_TH.md](BASH_COMMAND_REFERENCE_TH.md)

## หลักการก่อนเริ่ม

1. ตรวจ correctness ก่อน performance ทุกครั้ง
2. เก็บ baseline ด้วย input เดิมอย่างน้อย 3 รอบ
3. เปลี่ยนตัวแปรครั้งละหนึ่งอย่าง เช่น cores, ranks, threads, GPUs, chunk size หรือ array concurrency
4. แยก queue time, startup time, compute time และ I/O time
5. ตรวจ checksum หรือค่าคลาดเคลื่อนของผลลัพธ์หลัง optimization
6. หยุดขยายเมื่อ speedup อิ่มตัว ประสิทธิภาพต่ำ หรือค่าใช้จ่ายเพิ่มโดยไม่ได้ข้อมูลใหม่

สำหรับแคมเปญปัจจุบันใช้:

```bash
export LANTA_ACCOUNT=pv915002
export LANTA_PROJECT=/project/pv915002-hpcign
export PERF_ROOT="$LANTA_PROJECT/wdiazcar/hpc-ignite-performance"
mkdir -p "$PERF_ROOT"/{logs,results,accounting,notes}
```

## เมตริกหลัก

| เมตริก | สูตรหรือแหล่งข้อมูล | ใช้ตอบคำถาม |
|---|---|---|
| elapsed time | `ElapsedRaw` จาก `sacct` หรือ monotonic timer | งานจบเร็วขึ้นจริงหรือไม่ |
| throughput | จำนวนตัวอย่าง ไฟล์ timestep หรือ scenario ต่อวินาที | ทรัพยากรเพิ่มทำงานได้มากขึ้นเท่าใด |
| speedup | `T_baseline / T_variant` | รุ่นใหม่เร็วกว่า baseline กี่เท่า |
| parallel efficiency | `speedup / resource_ratio` | cores/GPUs ที่เพิ่มถูกใช้คุ้มหรือไม่ |
| CPU time/MaxRSS | `TotalCPU`, `MaxRSS` จาก `sacct` | CPU ว่างหรือ memory เป็นคอขวดหรือไม่ |
| GPU utilization/memory | `nvidia-smi` ภายใน allocation | GPU ได้ทำงานจริงหรือรอ CPU/I/O |
| result consistency | checksum หรือ numerical tolerance | ความเร็วแลกกับความถูกต้องหรือไม่ |
| cost proxy | core-hours, GPU-hours และ `sbill` | ผลลัพธ์ต่อ SHr ดีขึ้นหรือไม่ |

## ขั้นที่ 1: บันทึก baseline

สร้างไฟล์กลางหนึ่งแถวต่อการรัน ห้ามรวมค่าจาก input หรือ seed ต่างกันเป็น baseline เดียว

```bash
mkdir -p results/performance
cat > results/performance/runs.csv <<'CSV'
workflow,variant,repeat,problem_size,cpus,gpus,elapsed_s,throughput,result_digest
hello,serial,1,n1000000,1,0,2.10,476190,abc123
hello,serial,2,n1000000,1,0,2.05,487805,abc123
hello,serial,3,n1000000,1,0,2.08,480769,abc123
hello,openmp4,1,n1000000,4,0,0.62,1612903,abc123
hello,openmp4,2,n1000000,4,0,0.60,1666667,abc123
hello,openmp4,3,n1000000,4,0,0.61,1639344,abc123
CSV
```

สรุปค่าเฉลี่ย ความแปรปรวน speedup และ parallel efficiency:

```bash
python scripts/summarize_performance.py \
    results/performance/runs.csv \
    --output results/performance/summary.csv
column -s, -t results/performance/summary.csv
```

คอลัมน์ `result_consistent` ต้องเป็น `true` ถ้าใช้ checksum แบบ exact หากเป็น floating point ให้เปลี่ยนการตรวจเป็น tolerance ของ metric วิทยาศาสตร์ที่สำคัญแทน checksum ไฟล์ทั้งก้อน

## ขั้นที่ 2: เก็บหลักฐานจาก Slurm

หลัง job จบ ให้เก็บ scheduler evidence แยกตาม job ID:

```bash
job_id=<jobid>
sacct -j "$job_id" -P \
    -o JobID,JobName,Account,Partition,State,ExitCode,Elapsed,TotalCPU,UserCPU,SystemCPU,AllocCPUS,ReqCPUS,ReqMem,MaxRSS,MaxVMSize,AveCPU,NodeList \
    > "results/performance/sacct_${job_id}.psv"
scontrol show job "$job_id" > "results/performance/scontrol_${job_id}.txt"
sbill > "results/performance/sbill_after_${job_id}.txt"
```

อย่าใส่ `-X` ในคำสั่งชุดที่ใช้วัด memory เพราะตัวเลือกนั้นตัด job steps ออก และ LANTA มักรายงาน `MaxRSS`, `MaxVMSize` กับ `AveCPU` ในแถว `.batch` ไม่ใช่แถว job หลัก แถว job หลักยังจำเป็นสำหรับ account, partition, requested memory, elapsed และ state อย่าใช้เวลาจาก log เพียงอย่างเดียว เพราะต้องแยกเวลาที่โปรแกรมวัดกับเวลาที่ scheduler เห็น

ตัวอย่างที่บันทึกจริงด้วย `pv915002`:

| Job | Workflow | State | Elapsed | TotalCPU | ReqMem | MaxRSS (`.batch`) | Output สำคัญ |
|---|---|---:|---:|---:|---:|---:|---|
| `6338432` | foundation smoke | `COMPLETED 0:0` | 5 s | 1.040 s | 512M | 22572K | pi error `9.742940e-10` |
| `6338471` | hpc-mesa smoke | `COMPLETED 0:0` | 22 s | 2.227 s | 1G | 114080K | Mesa 3.5.1, MultiGrid/AgentSet |

รายละเอียด stdout, stderr และแถว accounting ทั้งหมดอยู่ใน [run evidence](lanta-runs/2026-09-25-pv915002/README.md) ตัวเลขสองงานนี้ใช้ยืนยัน workflow และวัด startup overhead เท่านั้น ยังไม่ใช่ scaling benchmark

## ขั้นที่ 3: วัดภายในงาน

ใช้ monotonic clock ครอบเฉพาะส่วนที่สนใจ และใช้ `/usr/bin/time -v` เก็บ CPU กับ memory:

```bash
result_dir="results/performance/${SLURM_JOB_ID}"
mkdir -p "$result_dir"

start_ns=$(date +%s%N)
/usr/bin/time -v -o "$result_dir/time_verbose.txt" \
    srun -c "${SLURM_CPUS_PER_TASK:-1}" python src/main.py \
    > "$result_dir/program.out"
end_ns=$(date +%s%N)

python - "$start_ns" "$end_ns" > "$result_dir/elapsed_s.txt" <<'PY'
import sys
print((int(sys.argv[2]) - int(sys.argv[1])) / 1e9)
PY
sha256sum "$result_dir/program.out" > "$result_dir/result.sha256"
```

สำหรับ GPU ให้เก็บ device facts ก่อนและหลัง workload การ sampling ต่อเนื่องควรรันเป็น process ย่อยที่หยุดแน่นอนเมื่อโปรแกรมจบ:

```bash
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total \
    --format=csv > "$result_dir/gpu_inventory.csv"
nvidia-smi dmon -s pucm -d 2 -o DT > "$result_dir/gpu_dmon.txt" &
monitor_pid=$!
srun python src/gpu_workload.py
kill "$monitor_pid" 2>/dev/null || true
wait "$monitor_pid" 2>/dev/null || true
```

## ขั้นที่ 4: ออกแบบ experiment matrix

### Strong scaling

ใช้ input ขนาดเดิมและเพิ่มทรัพยากร เหมาะกับคำถามว่า “งานนี้จะจบเร็วที่สุดอย่างคุ้มค่าได้อย่างไร”

```text
CPU/MPI: 1, 4, 16, 64, 128 cores; แล้ว 2 และ 4 nodes เมื่อหนึ่ง node ยัง scale
GPU:     1, 2, 4 GPUs ภายใน node เดียว ก่อนคิดข้าม node
Repeats: อย่างน้อย 3 รอบต่อจุด
```

### Weak scaling

เพิ่ม problem size ตามทรัพยากร เหมาะกับ ensemble, grid, agent population และ dataset partitions

```text
1 core  = N records/agents/cells
4 cores = 4N
16 cores = 16N
```

### Parameter sweep

งานอิสระควรใช้ job array พร้อมจำกัด concurrency แทนขยาย MPI โดยไม่มี communication:

```bash
#SBATCH --array=0-99%8
```

## แผนประเมินสำหรับทุก hands-on

| Hands-on | Baseline | ตัวแปรที่เปลี่ยน | เมตริก/optimization ที่ต้องทดลอง |
|---|---|---|---|
| readiness/environment | คำสั่งตรวจระบบหนึ่งรอบ | login vs compute node | แยก diagnostic ออกจาก compute; ลดคำสั่งซ้ำ |
| first Slurm job | 1 task, 1 CPU | startup และ I/O | queue/startup ไม่ใช่ compute speed; รวมงานจิ๋วเมื่อเหมาะสม |
| CPU pi/array | serial และ array `%1` | cores, task count, `%N` | throughput, queue pressure, deterministic seeds |
| OpenMP | 1 thread | 2/4/8/16/32/64 threads | speedup, affinity; ใช้ `OMP_PLACES=cores`, `OMP_PROC_BIND=close` |
| MPI/collectives | 1 rank | ranks, nodes, message/problem size | strong/weak scaling, communication fraction, rank placement |
| science diffusion/data | one input | grid size, chunk, threads | compute/I/O split, numerical error, vectorization |
| AI/GPU smoke | CPU or 1 GPU | batch size, warmup, 1/2/4 GPU | samples/s, GPU utilization, memory, synchronization |
| environment/module lab | cold load | cached load, environment choice | reproducibility first; do not optimize away provenance |
| big data | small serial read | partitions, format, compression | records/s, read amplification, spill, inode count |
| visualization | one PNG | resolution, backend, format | render time, memory, file size; use headless `Agg` |
| Dask | one worker | processes/threads/workers/chunks | task overhead, spill, dashboard evidence |
| Spark/preflight | local/small run | executors/partitions if runtime exists | scheduler overhead; use Dask alternative if Spark is unavailable |
| Apptainer | native warm run | native/container, cold/warm cache | startup overhead, bind paths, result equality |
| AI development | 1 GPU | batch, precision, data workers | samples/s, utilization, checkpoint overhead |
| prompts | one fixed prompt set | batching/preprocessing | local preparation throughput and deterministic artifacts; exclude remote API latency from LANTA claims |
| LLM fine-tuning | short fixed steps | batch, accumulation, precision, GPUs | tokens/s, max memory, convergence at equal steps |
| security | one fixed corpus | workers, batch, ruleset | files/s plus false-positive/false-negative checks |
| carbon | baseline job | faster configuration | energy/runtime/SHr per valid result; state measurement limits |
| chemistry preflight | module/input check | startup and input size | distinguish module readiness from solver performance |
| GROMACS | CPU or 1 GPU fixed TPR | threads, ranks, 1/2/4 GPU | ns/day, PME balance, SHr per simulated ns |
| WRF/NetCDF | one fixed file/case | ranks/threads, chunk/compression | timestep or MB/s, restart and output overhead |
| Quantum ESPRESSO | fixed SCF input | ranks, threads, pools, CPU/GPU | seconds/SCF iteration, convergence equivalence |
| GDAL/forest/agriculture | one raster/tile | block size, threads, tile arrays | pixels/s, I/O, CRS/result equality |
| BLAST/bioinformatics | fixed database/query | threads, query arrays | queries/s, memory, hit equivalence |
| hazard/disaster | fixed grid/scenarios | grid, workers, arrays | cells/s or scenarios/s, numerical tolerance |
| EpiSprint/Mesa | one seed/population | agents, days, workers, arrays | agent-steps/s, ensemble throughput, statistical consistency |
| Twin-B MicroCosim | one policy/seed | scenarios, agents, CPU/GPU ranks | timesteps/s, energy/comfort equality, communication overhead |
| enhanced SEIR | serial/1 rank | MPI ranks, nodes, GPU/DDP | solver throughput, roofline evidence, CPU/GPU agreement |
| weather-health HPDS | one dataset partition | Dask workers/chunks/compression | MB/s, task overhead, graph partition balance |
| Jupyter/display | batch render | notebook vs batch, PNG/SVG | kernel startup, render time, file size; no idle allocation |

## Optimization order

ใช้ลำดับนี้เพื่อไม่ให้แก้ผิดชั้น:

1. Algorithm: ลดงานที่ไม่จำเป็นและตรวจ numerical method
2. Data layout/I/O: ลดไฟล์จิ๋ว ใช้ chunk ที่สอดคล้องกับการอ่านจริง
3. Single core/process: profiling, vectorization, compiled kernels
4. Thread/process placement: affinity, ranks, OpenMP threads
5. Node/GPU scale: เพิ่มทรัพยากรเมื่อจุดเล็กยังใช้ได้คุ้ม
6. Workflow: arrays, dependencies, checkpoint/restart และ postprocess แยก job

## เกณฑ์ตัดสิน

รุ่น optimized ผ่านเมื่อครบทุกข้อ:

- งานเป็น `COMPLETED` และ `ExitCode=0:0`
- ผลวิทยาศาสตร์เท่ากันภายใน tolerance ที่ประกาศไว้
- มีอย่างน้อย 3 repeats หรืออธิบายว่าทำไม 2 รอบเพียงพอ
- รายงาน mean และ variability ไม่เลือกเฉพาะรอบเร็วที่สุด
- ระบุ account, partition, modules, commit, input และ seed
- speedup หรือ throughput ดีขึ้นโดยไม่เพิ่ม SHr ต่อผลลัพธ์อย่างไม่มีเหตุผล
- มี stop condition และไม่สรุป scalability จาก smoke input ที่เล็กเกินไป

## ส่งงานวิเคราะห์หลัง experiment

ใช้ dependency เพื่อไม่ให้ postprocess เริ่มก่อน array จบ:

```bash
array_id=$(sbatch -A "$LANTA_ACCOUNT" -p compute --parsable jobs/experiment_array.sbatch)
summary_id=$(sbatch -A "$LANTA_ACCOUNT" -p compute-devel \
    --dependency="afterok:${array_id}" --parsable jobs/summarize_performance.sbatch)
echo "array=$array_id summary=$summary_id"
```

ขั้นสุดท้ายควรเก็บ `runs.csv`, `summary.csv`, `sacct_*.psv`, plot, checksums และคำอธิบายว่าการปรับใดช่วยหรือไม่ช่วย เพื่อให้ผู้เรียนคนถัดไปตัดสินใจจากหลักฐานแทนการเดาค่า resource
