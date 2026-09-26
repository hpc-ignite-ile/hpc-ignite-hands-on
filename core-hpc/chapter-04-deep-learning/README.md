# บทที่ 4: Deep Learning บน HPC

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **37–38** of the [LANTA handbook](../../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: gpu](../../docs/images/booklet/Part7-AIforScience.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

GPU/framework smoke or tiny tensor workload; device visibility is not GPU utilization or training quality.

Separate host RAM from GPU VRAM. Dense float32 n×n matrices occupy 4n² bytes each; three 4096² tensors alone need 192 MiB, excluding library workspace. Start on one GPU and measure peak allocated/reserved VRAM before increasing tensor or batch size.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6339640 | COMPLETED | 1 | 6 | 3.548 | 0.006667 | 2.54 |

Elapsed is summed across array elements, not array makespan. CPU used is `TotalCPU`; reserved CPU-hours include idle allocation time. MaxRSS is the largest sampled task/step value, **not total node RAM**. Missing GPU/energy telemetry must not be interpreted as zero.

![Screenshot of archived job accounting and stdout](../../docs/images/run-evidence/core-hpc-chapter-04-deep-learning-readme.png)

Browser screenshot of the [archived evidence viewer](../../docs/tutorial-evidence/core-hpc-chapter-04-deep-learning-readme.html); not a live terminal capture. Open the viewer for exact requested/allocated resources and job-specific log excerpts.

**Read the numbers:** job `6339640` used 3.548 CPU-seconds over 6 summed elapsed seconds: about **0.59 busy CPU cores per running element on average**. This describes CPU work across the whole allocation, including setup; it does not measure GPU utilization. For a seconds-long run, startup and coarse memory sampling can dominate. Do not reduce RAM to the displayed RSS or claim scaling without a longer pilot.

<details><summary>ตัวอย่าง output ที่บันทึกจริง / archived stdout excerpt</summary>

Job `6339640` · archive member `tutorials/core-hpc/chapter-04-deep-learning/README/logs/gpu-torch_6339640.out`

```text
Sat Sep 26 08:12:17 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 565.57.01              Driver Version: 565.57.01      CUDA Version: 12.7     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
[... excerpt; full log in archive ...]
{
  "torch": "2.2.2+cu118",
  "cuda_version": "11.8",
  "cuda_available": true,
  "gpu_count": 1,
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "matrix_sum": 20055.033203125
}
```

</details>

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Warm up kernels, synchronize CUDA around timing, and measure repeated fixed-size kernels separately from imports and transfers. Compare CPU and GPU at identical precision and input. Increase problem size until compute is measurable, without exceeding measured VRAM headroom.

**Correctness gate:** Require CUDA availability, the expected device and a numerical comparison with CPU output. nvidia-smi showing a device does not demonstrate sustained utilization.

[Public applications and research-backed experiments](../../docs/REAL_APPLICATION_EXPERIMENTS.md#nvidia-and-ai) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/gpu-pytorch` โดยตรง

## เป้าหมาย

1. ขอ GPU หนึ่งใบผ่าน Slurm
2. ตรวจ nvidia-smi และ torch CUDA
3. บันทึกผลคำนวณ tensor ขนาดเล็ก

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/gpu-pytorch"
cd "$HOME/hpc-ignite-standalone/gpu-pytorch"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_GPU_PARTITION:-}" ]; then export LANTA_GPU_PARTITION="gpu-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi
```

### ขั้นที่ 2: สร้าง source code `src/gpu_torch_smoke.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/gpu_torch_smoke.py <<'PYCODE'
from pathlib import Path
import json
import torch
Path("results").mkdir(exist_ok=True)
summary = {"torch": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "gpu_count": torch.cuda.device_count()}
if torch.cuda.is_available():
    x = torch.randn(1024, 1024, device="cuda"); y = x @ x; torch.cuda.synchronize()
    summary["gpu_name"] = torch.cuda.get_device_name(0); summary["matrix_sum"] = float(y.sum().cpu())
Path("results/gpu_torch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PYCODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/gpu_torch.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/gpu_torch.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gpu-torch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true
conda activate pytorch-2.2.2 2>/dev/null || true
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
nvidia-smi | tee "results/${SLURM_JOB_ID}/nvidia-smi.txt"
python src/gpu_torch_smoke.py | tee "results/${SLURM_JOB_ID}/torch.txt"
cp results/gpu_torch_summary.json "results/${SLURM_JOB_ID}/gpu_torch_summary.json"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_torch.sbatch)
echo "$job_id	gpu_torch	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -80 logs/gpu-torch_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/gpu-pytorch"
find results -maxdepth 2 -type f | sort
tail -80 logs/gpu-torch_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง

<!-- performance-rerun:start -->
## Fresh measured rerun — 26 September 2026

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6340165 | COMPLETED | 1 | 33 | 4.484 | 0.036667 | 536.91 |

These are new measured jobs, not estimates. One campaign pass does not establish scaling or runtime variance. Allocated CPU-hours are not billed SHr; sampled RSS is not total node memory.

[Accounting, output archive and measurement limitations](../../docs/lanta-runs/2026-09-26-performance/README.md)

![Browser capture of fresh measured accounting and recorded output](../../docs/lanta-runs/2026-09-26-performance/core-hpc-chapter-04-deep-learning-readme.png)
<!-- performance-rerun:end -->
