# Workshop: ประเมิน Performance ของ Enhanced SEIR บน LANTA

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

หน้านี้เป็น practical ต่อจาก [TRAINING_SHEET_TH.md](TRAINING_SHEET_TH.md) สำหรับ onsite mini innovation ผู้ใช้เริ่มจากเครื่อง local, เข้า LANTA, สร้าง source และ Slurm script ด้วย heredoc, ส่งงานสั้น, อ่านหลักฐาน และตัดสินใจจากผลจริงใน workspace ของตนเอง

## บทนำแบบ Verse

ตั้งคำถามก่อนตั้งจำนวน core<br>
ให้สมมติฐานเดินนำหน้า benchmark<br>
วัดหนึ่งแกนของระบบ แล้วค่อยขยายแกนนั้น<br>
อ่านเวลา หน่วยความจำ rank และผลวิทยาศาสตร์ในแฟ้มเดียวกัน<br>
เมื่อ overhead ปรากฏ ให้จำแนกเป็น startup, memory, communication, GPU, I/O หรือ scheduler<br>
คำตอบที่ดีคือ run ถัดไปที่มีเหตุผล ชี้ชัดว่าจะเปลี่ยนสิ่งใดและตรวจอะไร

## คำอธิบายเชิงวิชาการ

workshop นี้ยึดแนวคิดจาก `Booklet_LANTA-Experience.pdf` หน้า 15-17 ใน `/home/ubuntu/lanta/AI`: เริ่มจากโจทย์วิทยาศาสตร์ ระบุ input และ model เลือก resource ให้ตรงกับคอขวด เก็บ evidence bundle แล้วใช้หลักฐานเพื่อวาง run ถัดไป

เอกสาร `PerformanceEvaluationOfHPC-AI.pdf` ชี้ให้แยก profiling กับ tracing อย่างมีลำดับ: profiling ให้ภาพรวมว่าค่าเวลาสะสมอยู่ที่ส่วนใด ส่วน tracing ให้ลำดับเหตุการณ์ละเอียดเมื่อมีสมมติฐานแคบพอ ใน practical นี้ผู้ใช้ใช้ timing, Slurm evidence, MPI rank scaling และ CSV summary เป็น profiling ชั้นแรก

เอกสาร Python performance ใน `/home/ubuntu/lanta/AI` เน้นว่า overhead เกิดได้จาก interpreter startup, import, pure Python loop, memory movement และการเรียก subprocess ดังนั้นตัวอย่างท้ายบทจึงวัด Python stack overhead ควบคู่กับ C++/MPI solver และ SEIR GPU/DDP evidence

## แหล่งอ้างอิงจาก `/home/ubuntu/lanta/AI`

| ไฟล์ | หลักคิดที่นำมาใช้ | จุดที่ปรากฏใน practical |
|---|---|---|
| `Booklet_LANTA-Experience.pdf` หน้า 15-17 | เริ่มจากคำถามวิทยาศาสตร์ เลือก resource จากลักษณะงาน และเก็บ evidence bundle | `notes/perf_workshop_evidence.txt`, `sacct`, log, CSV และคำถาม run ถัดไป |
| `PerformanceEvaluationOfHPC-AI.pdf` | แยก profiling, tracing, event-based data, sampling และ instrumentation เป็นระดับคำถาม | timing ชั้นแรก, rank scaling, overhead taxonomy และแนวทางขยายไป IPM, Score-P, Nsight Systems, NVTX |
| `1 Understanding Performant Python  High Performance Python 3rd Edition.pdf` | มองระบบเป็น compute, memory และ interconnect; ใช้ Amdahl อธิบาย serial fraction; ตรวจ GIL และ data movement ของ Python | `amdahl_gustafson.csv`, `solver_roofline_*.csv`, `python_stack_overhead.csv` |
| `2 Profiling to Find Bottlenecks.pdf` | ตั้ง hypothesis, profile ด้วย representative case, ใช้ cProfile เป็นภาพรวม, ใช้ line/memory profiler เมื่อขอบเขตแคบ | ขั้น `cProfile`, report CSV และคำถามสะท้อนผล |
| `ACM_School_Barcelona_2026_Wahib.pptx` | Scientific AI อยู่ในวงจร data, model, use in science; coupling กับ ModSim ต้องมี provenance, correctness, UQ และ throughput | AI scaffolding prompt ใช้เฉพาะ evidence จาก workspace และเชื่อมผล performance กลับสู่ SEIR mini innovation |

## บันไดหลักฐานสำหรับ Performance Evaluation

| ระดับ | คำถาม | หลักฐานที่เก็บใน workshop | เครื่องมือถัดไปเมื่อโจทย์ลึกขึ้น |
|---|---|---|---|
| Scientific question | run นี้ตอบเรื่องโรคระบาดหรือนโยบายใด | `question=...`, `seir_perf_compare.csv`, sanity check ของ policy | เพิ่มข้อมูลจริงหรือ scenario ensemble |
| Resource choice | CPU, MPI, GPU หรือ I/O เป็นแกนทดลองหลัก | Slurm account, partition, ranks, GPU log | job array, multi-node MPI, GPU/DDP |
| Timing profile | เวลารวมอยู่ที่ compute, startup หรือ stack | `/usr/bin/time -v`, elapsed CSV, `cProfile` | line profiler, memory profiler, Scalene |
| Scaling profile | speedup ถูกจำกัดโดย serial fraction หรือ overhead | speedup, efficiency, Karp-Flatt, Amdahl/Gustafson | IPM สำหรับ MPI routine และ min-max spread |
| Solver wall | stencil solver เดินชน compute หรือ memory bandwidth | GFLOP/s, GB/s, arithmetic intensity, residual | hardware counter, memory bandwidth benchmark |
| Communication wall | rank ใดรอ collective หรือ halo exchange | rank scaling, overhead class, elapsed spread | Score-P profile, call path, targeted trace |
| GPU/DDP wall | GPU ทำงานต่อเนื่องหรือมี data movement/NCCL gap | training log, GPU evidence, batch timing | Nsight Systems พร้อม NVTX range |
| AI scaffold | AI ช่วยจัด hypothesis จาก evidence ได้ระดับใด | `notes/ai_perf_review_prompt.md` | เพิ่ม provenance, uncertainty และ model/data checklist |

## แผนภาพความคิด

| แนวคิด | คำถามใน practical | หลักฐาน |
|---|---|---|
| Roofline | งานมี arithmetic intensity สูงพอจะติด compute หรือเดินชน memory bandwidth | `gflop_s`, `gb_s`, `arith_intensity` |
| Amdahl | serial fraction และ overhead จำกัด speedup เมื่อเพิ่ม ranks เท่าใด | `speedup`, `efficiency`, `karp_flatt_serial_fraction` |
| Gustafson | ถ้าขยายขนาดโจทย์พร้อมจำนวน ranks จะคาดหวัง scaled speedup ระดับใด | `amdahl_gustafson.csv` |
| Overhead taxonomy | เวลาที่เพิ่มมาจาก startup, MPI, memory, GPU, I/O, scheduler หรือ Python stack | `overhead_taxonomy.csv`, `/usr/bin/time -v`, `sacct` |
| Solver pattern | stencil, sparse matrix, halo exchange, reduction และ residual มีลักษณะอย่างไร | `solver_roofline_*.csv` |
| Scientific sanity | ผล SEIR ยังสัมพันธ์เชิงนโยบายและค่าช่วงถูกต้อง | `seir_perf_compare.csv` จาก training sheet |

## Copy-Paste จากเครื่อง Local

### ขั้นที่ 1: Login เข้า LANTA

block นี้เปิด shell บน LANTA login node สำหรับสร้าง workspace และส่ง Slurm job

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

## Copy-Paste บน LANTA

### ขั้นที่ 1: เตรียม workspace และตัวแปร

block นี้ใช้ workspace เดียวกับ enhanced SEIR training sheet และสร้าง folder เพิ่มสำหรับ performance practical

```bash
mkdir -p "$HOME/lanta-enhanced-seir"
cd "$HOME/lanta-enhanced-seir"
mkdir -p performance jobs logs notes results figures

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
pwd
```

### ขั้นที่ 2: เปิด evidence note ของ workshop

block นี้บันทึกคำถาม workspace เวลา user และ host เพื่อให้ผลการรันมีบริบทตรวจย้อนกลับ

```bash
{
    echo "workshop=enhanced-seir-performance"
    echo "question=classify overhead and physical wall for miniature SEIR workflow"
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo "host=$(hostname)"
    echo "cpu_partition=$LANTA_CPU_PARTITION"
    echo "gpu_partition=$LANTA_GPU_PARTITION"
} > notes/perf_workshop_evidence.txt
sed -n '1,20p' notes/perf_workshop_evidence.txt
```

### ขั้นที่ 3: สร้างตาราง Amdahl, Gustafson และ taxonomy

block นี้สร้าง script สั้นจาก standard library เพื่อคำนวณ speedup เชิงทฤษฎีและรายการ overhead ที่ต้องตรวจ

ถ้า `performance/perf_theory.py` มีอยู่แล้วใน workspace นี้ ให้ข้ามขั้นนี้และรัน `python performance/perf_theory.py` โดยตรง

```bash
cat > performance/perf_theory.py <<'PY'
from pathlib import Path
import csv
Path("results").mkdir(exist_ok=True)
workers=[1,2,4,8,16,32]
serial=[0.02,0.08,0.18]
rows=[]
for f in serial:
    for p in workers:
        amdahl=1.0/(f+(1.0-f)/p)
        gustafson=p-f*(p-1)
        rows.append({
            "workers":p,
            "serial_fraction":f"{f:.2f}",
            "amdahl_speedup":f"{amdahl:.4f}",
            "gustafson_speedup":f"{gustafson:.4f}",
            "parallel_efficiency":f"{amdahl/p:.4f}",
        })
with open("results/amdahl_gustafson.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
taxonomy=[
    ("startup","Python import, torchrun, MPI initialization","/usr/bin/time -v"),
    ("scheduler","queue wait and allocation size","sbatch, squeue, sacct"),
    ("communication","halo exchange, Allreduce, gather","rank scaling and min/max timing"),
    ("memory","low arithmetic intensity or high MaxRSS","bytes moved and residual"),
    ("gpu","kernel launch, data movement, small batch","GPU elapsed against CPU baseline"),
    ("io","many files, metadata, checkpoint","File system outputs"),
    ("python_stack","interpreter startup, imports, pure Python loop","startup and cProfile"),
]
with open("results/overhead_taxonomy.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["class","typical_source","evidence"])
    w.writerows(taxonomy)
print("wrote results/amdahl_gustafson.csv")
print("wrote results/overhead_taxonomy.csv")
PY
```

### ขั้นที่ 4: รันตารางทฤษฎีบน login node

block นี้ใช้ Python ที่ระบบมีอยู่เพื่อสร้าง CSV ขนาดเล็ก แล้วเปิดอ่านหัวตาราง

```bash
module purge
module load cray-python/3.10.10 2>/dev/null || true
python performance/perf_theory.py
sed -n '1,10p' results/amdahl_gustafson.csv
sed -n '1,10p' results/overhead_taxonomy.csv
```

### ขั้นที่ 5: สร้าง MPI roofline solver ส่วนที่ 1

block นี้สร้าง header และ parser ของ Jacobi stencil solver สำหรับมองภาพ solver ใน HPC

```bash
cat > performance/solver_roofline_mpi.cpp <<'CPP'
#include <mpi.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
struct Args{
    int n_global=1200000;
    int iters=180;
    std::string label="jacobi";
};
Args parse_args(int argc,char** argv){
    Args args;
    for(int i=1;i<argc;++i){
        std::string key=argv[i];
        if(key=="--n" && i+1<argc) args.n_global=std::atoi(argv[++i]);
        else if(key=="--iters" && i+1<argc) args.iters=std::atoi(argv[++i]);
        else if(key=="--label" && i+1<argc) args.label=argv[++i];
    }
    return args;
}
CPP
```

### ขั้นที่ 6: เติม MPI roofline solver ส่วนที่ 2

block นี้เติม domain decomposition, halo exchange และ Jacobi update ซึ่งแทนคุณลักษณะของ sparse/stencil solver

```bash
cat >> performance/solver_roofline_mpi.cpp <<'CPP'
int main(int argc,char** argv){
    MPI_Init(&argc,&argv);
    int rank=0,size=1;
    MPI_Comm_rank(MPI_COMM_WORLD,&rank);
    MPI_Comm_size(MPI_COMM_WORLD,&size);
    Args args=parse_args(argc,argv);
    int base=args.n_global/size;
    int rem=args.n_global%size;
    int n_local=base+(rank<rem?1:0);
    std::vector<double> x(n_local+2,0.0),y(n_local+2,0.0),rhs(n_local+2,1.0);
    int left=rank==0?MPI_PROC_NULL:rank-1;
    int right=rank==size-1?MPI_PROC_NULL:rank+1;
    double residual=0.0;
    MPI_Barrier(MPI_COMM_WORLD);
    double t0=MPI_Wtime();
    for(int it=0;it<args.iters;++it){
        MPI_Sendrecv(&x[1],1,MPI_DOUBLE,left,10,&x[n_local+1],1,MPI_DOUBLE,right,10,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
        MPI_Sendrecv(&x[n_local],1,MPI_DOUBLE,right,20,&x[0],1,MPI_DOUBLE,left,20,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
        double sumsq=0.0;
        for(int i=1;i<=n_local;++i){
            y[i]=0.5*(x[i-1]+x[i+1]-rhs[i]);
            double r=y[i]-x[i];
            sumsq+=r*r;
        }
        x.swap(y);
        if((it+1)%20==0 || it+1==args.iters){
            MPI_Allreduce(&sumsq,&residual,1,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);
        }
    }
CPP
```

### ขั้นที่ 7: เติม MPI roofline solver ส่วนที่ 3

block นี้สรุป elapsed time, flop, byte, arithmetic intensity และ residual ออกเป็น CSV row

```bash
cat >> performance/solver_roofline_mpi.cpp <<'CPP'
    double local_elapsed=MPI_Wtime()-t0;
    double elapsed=0.0;
    MPI_Reduce(&local_elapsed,&elapsed,1,MPI_DOUBLE,MPI_MAX,0,MPI_COMM_WORLD);
    double local_flops=static_cast<double>(n_local)*args.iters*8.0;
    double local_bytes=static_cast<double>(n_local)*args.iters*5.0*sizeof(double);
    double flops=0.0,bytes=0.0;
    MPI_Reduce(&local_flops,&flops,1,MPI_DOUBLE,MPI_SUM,0,MPI_COMM_WORLD);
    MPI_Reduce(&local_bytes,&bytes,1,MPI_DOUBLE,MPI_SUM,0,MPI_COMM_WORLD);
    if(rank==0){
        double denom=std::max(elapsed,1e-12);
        double point_rate=static_cast<double>(args.n_global)*args.iters/denom;
        double gflops=flops/denom/1e9;
        double gbps=bytes/denom/1e9;
        double ai=flops/std::max(bytes,1.0);
        std::cout<<std::fixed<<std::setprecision(6)
                 <<args.label<<","<<size<<","<<args.n_global<<","<<args.iters<<","
                 <<elapsed<<","<<point_rate<<","<<gflops<<","<<gbps<<","<<ai<<","
                 <<std::sqrt(residual)<<"\n";
    }
    MPI_Finalize();
    return 0;
}
CPP
```

### ขั้นที่ 8: สร้าง Slurm script สำหรับ solver

block นี้ขอ 4 MPI tasks บน node เดียว แล้วรัน `srun -n 1`, `srun -n 2` และ `srun -n 4` ภายใน allocation เดียว

```bash
cat > jobs/roofline_solver.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=seir-roof
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:06:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results
module purge
module load cpeCray/25.03 2>/dev/null || true
module list 2> "notes/modules_${SLURM_JOB_ID}.txt"
CC -O3 -std=c++17 performance/solver_roofline_mpi.cpp -o "results/solver_roofline_${SLURM_JOB_ID}"
out="results/solver_roofline_${SLURM_JOB_ID}.csv"
echo "label,ranks,n_global,iters,elapsed_sec,points_per_sec,gflop_s,gb_s,arith_intensity,residual" > "$out"
for ranks in 1 2 4; do
    /usr/bin/time -v srun -n "$ranks" "results/solver_roofline_${SLURM_JOB_ID}" \
        --n 1200000 --iters 180 --label "jacobi_${ranks}" \
        >> "$out" \
        2> "notes/time_solver_${SLURM_JOB_ID}_${ranks}.txt"
done
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
SLURM
sed -n '1,80p' jobs/roofline_solver.sbatch
```

### ขั้นที่ 9: ส่งงาน solver เข้า Slurm

block นี้ส่ง job แล้วบันทึก job id ใน evidence note

```bash
roof_job=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/roofline_solver.sbatch)
echo "roofline_solver_job=$roof_job" | tee -a notes/perf_workshop_evidence.txt
squeue -j "$roof_job"
```

### ขั้นที่ 10: อ่านผล solver หลัง job จบ

block นี้อ่าน `sacct`, log และ CSV เพื่อดู scaling, arithmetic intensity และ residual

```bash
sacct -j "$roof_job" --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
tail -40 "logs/seir-roof_${roof_job}.out"
sed -n '1,8p' "results/solver_roofline_${roof_job}.csv"
sed -n '1,25p' "notes/time_solver_${roof_job}_4.txt"
```

### ขั้นที่ 11: สร้าง report script ส่วนที่ 1

block นี้สร้างตัวอ่าน CSV และสูตร Karp-Flatt สำหรับแปลง timing เป็น overhead evidence

```bash
cat > performance/perf_workshop_report.py <<'PY'
from pathlib import Path
import csv
def read_rows(path):
    with open(path,encoding="utf-8") as f:
        return list(csv.DictReader(f))
def latest(pattern):
    files=sorted(Path("results").glob(pattern),key=lambda p:p.stat().st_mtime)
    return files[-1] if files else None
def karp_flatt(speedup,ranks):
    if ranks<=1 or speedup<=0:
        return 0.0
    return max(0.0,min(1.0,(1.0/speedup-1.0/ranks)/(1.0-1.0/ranks)))
def seir_note():
    compare=latest("seir_perf_compare.csv")
    if compare is None:
        return "run TRAINING_SHEET_TH.md to attach SEIR CPU/GPU evidence."
    rows=read_rows(compare)
    engines=sorted({r.get("engine","") for r in rows})
    return f"SEIR compare found: {compare}; engines={','.join(engines)}."
PY
```

### ขั้นที่ 12: สร้าง report script ส่วนที่ 2

block นี้เขียน Markdown report และ CSV summary สำหรับสรุป overhead และ physical wall

```bash
cat >> performance/perf_workshop_report.py <<'PY'
solver=latest("solver_roofline_*.csv")
if solver is None:
    raise SystemExit("run roofline solver first")
rows=read_rows(solver)
base=next((r for r in rows if int(r["ranks"])==1),rows[0])
t1=float(base["elapsed_sec"])
summary=[]
for r in rows:
    ranks=int(r["ranks"])
    elapsed=float(r["elapsed_sec"])
    speedup=t1/elapsed
    eff=speedup/ranks
    overhead=elapsed-t1/ranks
    ai=float(r["arith_intensity"])
    wall="memory bandwidth"
    if ranks>1 and eff<0.55:
        wall="communication or synchronization"
    elif ai>=1.0:
        wall="compute throughput"
    summary.append([ranks,elapsed,speedup,eff,overhead,karp_flatt(speedup,ranks),wall])
with open("results/perf_workshop_summary.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["ranks","elapsed_sec","speedup","efficiency","overhead_sec","karp_flatt_serial_fraction","observed_wall"])
    w.writerows(summary)
with open("results/perf_workshop_report.md","w",encoding="utf-8") as f:
    f.write("# Performance Workshop Report\n\n")
    f.write(f"source={solver}\n\n")
    f.write("| ranks | elapsed | speedup | efficiency | overhead | serial_fraction | wall |\n")
    f.write("|---:|---:|---:|---:|---:|---:|---|\n")
    for row in summary:
        f.write(f"| {row[0]} | {row[1]:.6f} | {row[2]:.3f} | {row[3]:.3f} | {row[4]:.6f} | {row[5]:.4f} | {row[6]} |\n")
    f.write("\n## Interpretation\n\n")
    f.write("- Low arithmetic intensity points to memory traffic as the first roofline signal.\n")
    f.write("- Efficiency drop across ranks marks synchronization, halo exchange, and Allreduce overhead.\n")
    f.write(f"- {seir_note()}\n")
print("wrote results/perf_workshop_summary.csv")
print("wrote results/perf_workshop_report.md")
PY
```

### ขั้นที่ 13: รัน report และอ่านผล

block นี้แปลง CSV ของ solver เป็นรายงานที่ใช้อภิปรายในห้อง

```bash
python performance/perf_workshop_report.py
sed -n '1,30p' results/perf_workshop_summary.csv
sed -n '1,80p' results/perf_workshop_report.md
```

### ขั้นที่ 14: สร้าง Python stack overhead script

block นี้วัด interpreter startup, import, pure Python loop และ optional tensor/scientific library import

```bash
cat > performance/python_stack_overhead.py <<'PY'
from pathlib import Path
import csv,subprocess,sys,time
def timed_subprocess(label,code):
    t0=time.perf_counter()
    proc=subprocess.run([sys.executable,"-c",code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return {"case":label,"elapsed_sec":f"{time.perf_counter()-t0:.6f}","status":str(proc.returncode)}
def timed_loop():
    t0=time.perf_counter()
    acc=0.0
    for i in range(700000):
        acc+=(i%17)*0.125
    return {"case":"pure_python_loop_700k","elapsed_sec":f"{time.perf_counter()-t0:.6f}","status":f"{acc:.1f}"}
Path("results").mkdir(exist_ok=True)
rows=[
    timed_subprocess("interpreter_startup","pass"),
    timed_subprocess("stdlib_imports","import csv,json,math,statistics"),
    timed_subprocess("torch_import","import torch"),
    timed_loop(),
    timed_subprocess("numpy_import_and_vector_op","import numpy as np; x=np.arange(700000,dtype=np.float64); float((x%17).sum())"),
]
with open("results/python_stack_overhead.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["case","elapsed_sec","status"])
    w.writeheader()
    w.writerows(rows)
for row in rows:
    print(row)
PY
```

### ขั้นที่ 15: รัน Python overhead และ cProfile

block นี้ดู runtime ของ stack สั้น ๆ และใช้ `cProfile` เพื่อให้เห็น call-level timing ของ script
ค่า `status=0` หมายถึง import หรือ subprocess สำเร็จ ค่าอื่นเป็นหลักฐานว่า package นั้นยังอยู่นอก Python environment ปัจจุบัน

```bash
python -m cProfile -s cumulative performance/python_stack_overhead.py > notes/python_stack_cprofile.txt
/usr/bin/time -v python performance/python_stack_overhead.py
sed -n '1,10p' results/python_stack_overhead.csv
sed -n '1,35p' notes/python_stack_cprofile.txt
```

### ขั้นที่ 16: สร้าง Python performance summary display ส่วนที่ 1

block นี้สร้าง helper สำหรับวาด SVG ด้วย Python standard library จึงใช้ได้แม้ environment ยังมีเฉพาะ `cray-python`

```bash
cat > performance/perf_summary_plot.py <<'PY'
from pathlib import Path
from xml.sax.saxutils import escape
import csv
WIDTH=900
HEIGHT=560
PAD_L=76
PAD_R=28
PAD_T=42
PAD_B=68
def read_csv(path):
    with open(path,encoding="utf-8") as f:
        return list(csv.DictReader(f))
def sx(x,xmin,xmax):
    return PAD_L if xmax==xmin else PAD_L+(x-xmin)*(WIDTH-PAD_L-PAD_R)/(xmax-xmin)
def sy(y,ymin,ymax):
    return HEIGHT-PAD_B if ymax==ymin else HEIGHT-PAD_B-(y-ymin)*(HEIGHT-PAD_T-PAD_B)/(ymax-ymin)
def line_chart(path,title,xlabel,ylabel,xs,series):
    xmin,xmax=min(xs),max(xs)
    ymax=max(max(vals) for _,vals,_ in series)*1.12
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">',
           '<rect width="100%" height="100%" fill="#ffffff"/>',
           f'<text x="{WIDTH/2}" y="26" text-anchor="middle" font-size="22" font-family="sans-serif">{escape(title)}</text>',
           f'<line x1="{PAD_L}" y1="{HEIGHT-PAD_B}" x2="{WIDTH-PAD_R}" y2="{HEIGHT-PAD_B}" stroke="#222"/>',
           f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{HEIGHT-PAD_B}" stroke="#222"/>']
    for tick in range(6):
        yv=ymax*tick/5.0
        yp=sy(yv,0,ymax)
        lines.append(f'<line x1="{PAD_L-5}" y1="{yp:.1f}" x2="{WIDTH-PAD_R}" y2="{yp:.1f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{PAD_L-10}" y="{yp+4:.1f}" text-anchor="end" font-size="12" font-family="monospace">{yv:.2f}</text>')
    for x in xs:
        xp=sx(x,xmin,xmax)
        lines.append(f'<text x="{xp:.1f}" y="{HEIGHT-PAD_B+24}" text-anchor="middle" font-size="12" font-family="monospace">{x:g}</text>')
    for idx,(name,vals,color) in enumerate(series):
        pts=" ".join(f"{sx(x,xmin,xmax):.1f},{sy(y,0,ymax):.1f}" for x,y in zip(xs,vals))
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{pts}"/>')
        lines.append(f'<text x="{WIDTH-PAD_R-170}" y="{PAD_T+22*idx}" font-size="13" font-family="sans-serif">{escape(name)}</text>')
    lines.append(f'<text x="{WIDTH/2}" y="{HEIGHT-18}" text-anchor="middle" font-size="14" font-family="sans-serif">{escape(xlabel)}</text>')
    lines.append("</svg>")
    Path(path).write_text("\n".join(lines),encoding="utf-8")
PY
```

### ขั้นที่ 17: สร้าง Python performance summary display ส่วนที่ 2

block นี้เติม bar chart และ main routine ที่อ่าน CSV แล้วสร้าง SVG กับ Markdown summary

```bash
cat >> performance/perf_summary_plot.py <<'PY'
def bar_chart(path,title,ylabel,labels,values):
    ymax=max(values+[1e-9])*1.18
    gap=12
    area=WIDTH-PAD_L-PAD_R
    bar=max(18,(area-gap*(len(labels)+1))/max(1,len(labels)))
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">',
           '<rect width="100%" height="100%" fill="#ffffff"/>',
           f'<text x="{WIDTH/2}" y="26" text-anchor="middle" font-size="22" font-family="sans-serif">{escape(title)}</text>',
           f'<line x1="{PAD_L}" y1="{HEIGHT-PAD_B}" x2="{WIDTH-PAD_R}" y2="{HEIGHT-PAD_B}" stroke="#222"/>']
    for i,(label,value) in enumerate(zip(labels,values)):
        x=PAD_L+gap+i*(bar+gap)
        y=sy(value,0,ymax)
        h=HEIGHT-PAD_B-y
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h:.1f}" fill="#0f766e"/>')
        lines.append(f'<text x="{x+bar/2:.1f}" y="{y-7:.1f}" text-anchor="middle" font-size="12" font-family="monospace">{value:.3f}</text>')
        lines.append(f'<text x="{x+bar/2:.1f}" y="{HEIGHT-PAD_B+23}" text-anchor="middle" font-size="11" font-family="sans-serif">{escape(label)}</text>')
    lines.append("</svg>")
    Path(path).write_text("\n".join(lines),encoding="utf-8")
Path("figures").mkdir(exist_ok=True)
summary=read_csv(Path("results/perf_workshop_summary.csv"))
ranks=[float(r["ranks"]) for r in summary]
speed=[float(r["speedup"]) for r in summary]
eff=[float(r["efficiency"]) for r in summary]
over=[max(0.0,float(r["overhead_sec"])) for r in summary]
line_chart("figures/perf_summary_speedup.svg","MPI Solver Speedup","MPI ranks","speedup",ranks,[("observed",speed,"#2563eb"),("ideal",ranks,"#94a3b8")])
line_chart("figures/perf_summary_efficiency.svg","Parallel Efficiency","MPI ranks","efficiency",ranks,[("efficiency",eff,"#7c3aed")])
bar_chart("figures/perf_summary_overhead.svg","Estimated Overhead","seconds",[r["ranks"] for r in summary],over)
note="Python stack CSV is pending."
if Path("results/python_stack_overhead.csv").exists():
    rows=read_csv(Path("results/python_stack_overhead.csv"))
    bar_chart("figures/perf_summary_python_stack.svg","Python Stack Cost","seconds",[r["case"].replace("_"," ")[:15] for r in rows],[float(r["elapsed_sec"]) for r in rows])
    note="figures/perf_summary_python_stack.svg"
Path("results/perf_summary_display.md").write_text("\n".join(["# Performance Summary Display","","- figures/perf_summary_speedup.svg","- figures/perf_summary_efficiency.svg","- figures/perf_summary_overhead.svg",f"- {note}",""]) ,encoding="utf-8")
print("wrote SVG figures and results/perf_summary_display.md")
PY
```

### ขั้นที่ 18: รัน Python performance summary display

block นี้สร้างรูป SVG ที่เปิดดูใน JupyterLab, browser หรือ download ไปใส่ slide ได้

```bash
python performance/perf_summary_plot.py
sed -n '1,20p' results/perf_summary_display.md
ls -lh figures/perf_summary_*.svg
```

### ขั้นที่ 19: สร้าง gnuplot dashboard รวมทุก analysis ส่วนที่ 1

block นี้สร้างส่วนตั้งค่าของ gnuplot dashboard และ panel ชุดแรกสำหรับ speedup, efficiency, overhead และ roofline signal ผู้ใช้เปิดอ่าน syntax ได้ทันที ส่วนการรันจริงเกิดในขั้นถัดไปเมื่อ environment มี `gnuplot`

```bash
cat > performance/plot_perf_dashboard.gp <<'GP'
set datafile separator ","
set terminal pngcairo size 1800,1200 enhanced font "Arial,12"
set output "figures/perf_workshop_dashboard.png"
summary_csv = "results/perf_workshop_summary.csv"
theory_csv = "results/amdahl_gustafson.csv"
python_csv = "results/python_stack_overhead.csv"
solver_csv = system("ls -t results/solver_roofline_*.csv 2>/dev/null | head -1")
if (strlen(solver_csv) == 0) solver_csv = "results/solver_roofline_latest.csv"
set print "results/perf_workshop_gnuplot_summary.txt"
print "dashboard=figures/perf_workshop_dashboard.png"
print "summary_csv=".summary_csv
print "theory_csv=".theory_csv
print "solver_csv=".solver_csv
print "python_csv=".python_csv
set print
set style line 1 lc rgb "#2563eb" lw 3 pt 7 ps 1.1
set style line 2 lc rgb "#94a3b8" lw 2 dt 2
set style line 3 lc rgb "#7c3aed" lw 3 pt 5 ps 1.1
set style line 4 lc rgb "#0f766e" lw 2 pt 9 ps 1.1
set style line 5 lc rgb "#dc2626" lw 2 pt 11 ps 1.1
set style fill solid 0.82 border rgb "#374151"
set boxwidth 0.65
set grid
set key outside right top
set multiplot layout 2,3 title "Enhanced SEIR Performance Evaluation Dashboard"
set title "MPI Solver Speedup"
set xlabel "MPI ranks"
set ylabel "speedup"
set key left top
set yrange [0:*]
plot summary_csv every ::1 using 1:3 with linespoints ls 1 title "observed", \
     summary_csv every ::1 using 1:1 with lines ls 2 title "ideal"
set title "Efficiency and Serial Fraction"
set ylabel "fraction"
set yrange [0:1.1]
plot summary_csv every ::1 using 1:4 with linespoints ls 3 title "efficiency", \
     summary_csv every ::1 using 1:6 with linespoints ls 5 title "Karp-Flatt serial"
set title "Estimated Overhead"
set ylabel "seconds"
set style data boxes
plot summary_csv every ::1 using 1:5 with boxes lc rgb "#0f766e" title "overhead_sec"
set style data linespoints
set title "Roofline Signal from Solver"
set xlabel "observed GB/s"
set ylabel "observed GFLOP/s"
plot solver_csv every ::1 using 8:7 with linespoints ls 4 title "bandwidth vs flops", \
     solver_csv every ::1 using 8:7:2 with labels offset 1,1 title "ranks"
GP
sed -n '1,45p' performance/plot_perf_dashboard.gp
```

### ขั้นที่ 20: เติม gnuplot dashboard รวมทุก analysis ส่วนที่ 2

block นี้เติม panel สำหรับ Amdahl/Gustafson, Python stack cost และรูปแยกสำหรับใช้ใน slide

```bash
cat >> performance/plot_perf_dashboard.gp <<'GP'
set title "Amdahl and Gustafson, f=0.08"
set xlabel "workers"
set ylabel "speedup"
plot theory_csv every ::1 using 1:(strcol(2) eq "0.08" ? $3 : 1/0) with linespoints ls 1 title "Amdahl", \
     theory_csv every ::1 using 1:(strcol(2) eq "0.08" ? $4 : 1/0) with linespoints ls 4 title "Gustafson"
set title "Python Stack Cost"
set xlabel "case"
set ylabel "seconds"
set xtics rotate by -35 right
set style data histograms
plot python_csv every ::1 using 2:xtic(1) lc rgb "#f59e0b" title "elapsed_sec"
unset multiplot
set terminal pngcairo size 1100,720 enhanced font "Arial,12"
set output "figures/perf_workshop_speedup_efficiency.png"
set title "Enhanced SEIR Performance Summary"
set xlabel "MPI ranks"
set ylabel "speedup / efficiency"
set style data linespoints
set xtics norotate
plot summary_csv every ::1 using 1:3 with linespoints ls 1 title "speedup", \
     summary_csv every ::1 using 1:4 with linespoints ls 3 title "efficiency", \
     summary_csv every ::1 using 1:1 with lines ls 2 title "ideal speedup"
set output "figures/perf_workshop_python_stack.png"
set title "Python Stack Cost"
set xlabel "case"
set ylabel "seconds"
set xtics rotate by -35 right
set style data histograms
plot python_csv every ::1 using 2:xtic(1) lc rgb "#f59e0b" title "elapsed_sec"
GP
sed -n '46,120p' performance/plot_perf_dashboard.gp
```

### ขั้นที่ 21: รัน gnuplot dashboard ด้วย native command หรือ Apptainer

block นี้สร้างรูป PNG รวมทุก analysis และไฟล์ summary ที่บอกว่า gnuplot ใช้ CSV ใด ถ้า shell พบ `gnuplot` จะใช้ command ตรง ๆ ถ้า environment ปัจจุบันมีเฉพาะ Apptainer จะดึง image `gitrust/gnuplot:latest` เป็น `containers/gnuplot.sif` แล้วรันผ่าน container

```bash
mkdir -p containers
GNUPLOT_RUNNER=()
if command -v gnuplot >/dev/null 2>&1; then
    GNUPLOT_RUNNER=(gnuplot)
    echo "gnuplot_source=native" | tee results/perf_workshop_gnuplot_runner.txt
else
    module load Apptainer/1.1.6 2>/dev/null || module load Apptainer 2>/dev/null || true
    if [ ! -f containers/gnuplot.sif ]; then
        apptainer pull containers/gnuplot.sif docker://gitrust/gnuplot:latest
    fi
    GNUPLOT_RUNNER=(apptainer exec containers/gnuplot.sif gnuplot)
    echo "gnuplot_source=apptainer:gitrust/gnuplot:latest" | tee results/perf_workshop_gnuplot_runner.txt
fi
"${GNUPLOT_RUNNER[@]}" --version | tee notes/gnuplot_version.txt
"${GNUPLOT_RUNNER[@]}" performance/plot_perf_dashboard.gp
sed -n '1,20p' results/perf_workshop_gnuplot_summary.txt
ls -lh figures/perf_workshop_dashboard.png figures/perf_workshop_speedup_efficiency.png figures/perf_workshop_python_stack.png
```

### ขั้นที่ 22: สร้าง AI scaffolding prompt จาก evidence จริง

block นี้สร้าง prompt สำหรับให้ AI ช่วยจัดลำดับสมมติฐาน โดยยึดเฉพาะไฟล์ evidence ที่ผู้ใช้สร้างเอง

```bash
{
    echo "# AI Performance Review Prompt"
    echo
    echo "Use only the evidence below. Classify the dominant overhead, name the physical wall, and propose one next run."
    echo
    echo "## Evidence Files"
    find notes results -maxdepth 1 -type f | sort
    echo
    echo "## Solver Summary"
    sed -n '1,20p' results/perf_workshop_summary.csv
    echo
    echo "## Python Stack"
    sed -n '1,20p' results/python_stack_overhead.csv
    echo
    echo "## Display Summary"
    sed -n '1,20p' results/perf_summary_display.md
    if [ -f results/perf_workshop_gnuplot_summary.txt ]; then
        echo
        echo "## Gnuplot Dashboard"
        sed -n '1,20p' results/perf_workshop_gnuplot_runner.txt
        sed -n '1,20p' results/perf_workshop_gnuplot_summary.txt
    fi
} > notes/ai_perf_review_prompt.md
sed -n '1,80p' notes/ai_perf_review_prompt.md
```

## วิธีอภิปรายผลในห้อง

อ่านจากหลักฐานตามลำดับนี้

1. `sacct` แสดง `COMPLETED`, `AllocCPUS`, `Elapsed` และ `MaxRSS`
2. `solver_roofline_<jobid>.csv` มี 3 แถวสำหรับ 1, 2 และ 4 ranks
3. `speedup` และ `efficiency` ชี้ว่า scaling ได้ตามทรัพยากรที่ขอเพียงใด
4. `arith_intensity` ต่ำมักชี้ไปที่ memory bandwidth ใน stencil solver
5. `overhead_sec` สูงขึ้นเมื่อเพิ่ม rank ชี้ไปที่ communication, synchronization หรือ load imbalance
6. `python_stack_overhead.csv` แยกเวลา startup/import ออกจากงานคำนวณจริงของ Python
7. `perf_summary_display.md` และ `figures/perf_summary_*.svg` ใช้สื่อสาร speedup, efficiency, overhead และ Python stack cost
8. `perf_workshop_dashboard.png` รวม speedup, efficiency, overhead, roofline signal, Amdahl/Gustafson และ Python stack cost ในรูปเดียว
9. `seir_perf_compare.csv` จาก training sheet ใช้เชื่อมกลับไปยัง innovation หลัก C++/MPI เทียบ PyTorch GPU/DDP

## เกณฑ์ตัดสินว่าผลดีและถูกต้อง

- job จบด้วย `COMPLETED` และ `ExitCode=0:0`
- CSV มี header และจำนวนแถวตรงกับจำนวน rank หรือ case ที่ตั้งไว้
- `residual` เป็นค่าจำนวนจริงและอยู่ในช่วงบวกจำกัด
- `speedup` เพิ่มเมื่อเพิ่ม rank ในทิศทางที่อธิบายได้
- `efficiency` ลดลงพร้อมหลักฐาน overhead ที่ชี้แหล่งกำเนิดได้
- ค่า SEIR เช่น `attack_rate`, `peak_infectious` และ policy ordering ผ่าน sanity check จาก training sheet

## คำถามสะท้อนผล

1. ถ้า `arith_intensity` ต่ำกว่า `1.0` ผู้ใช้จะเพิ่ม flop ต่อ byte หรือปรับ data locality ตรงไหน
2. ถ้า 4 ranks เร็วกว่า 2 ranks เพียงเล็กน้อย ผู้ใช้ควรตรวจ halo exchange, Allreduce หรือ load balance ด้วยหลักฐานใด
3. ถ้า `torch_import` ใช้เวลาสูงเมื่อเทียบกับ mini workload ผู้ใช้จะรวบ scenario เป็น batch หรือย้ายงานไป CPU/MPI อย่างไร
4. ถ้าต้องสอนผู้บริหารด้วยรูปเดียว ผู้ใช้จะเลือกกราฟ speedup, efficiency หรือ roofline signal เพราะเหตุใด
