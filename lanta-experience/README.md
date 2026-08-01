# LANTA Experience Labs

ลำดับนี้ตาม booklet `LANTA HPC Handbook` สำหรับ LANTA HPC Experience Day: On the Move. จุดประสงค์คือให้ผู้เรียน copy-paste เป็นหลัก แต่ยังเห็นไฟล์จริงที่ตนเองสร้างด้วย heredoc: `src/*.py`, `jobs/*.sbatch`, `configs/*`, `logs/*`, `results/*`, และ `notes/*`

## Event Flow

| ช่วงใน booklet | Lab ใน repo | ผลลัพธ์ที่ควรมี |
|---|---|---|
| Linux, Shell, files | [00-readiness.md](00-readiness.md) | workspace, input/config/log/result folders, environment notes |
| First Slurm job | [01-first-slurm-job.md](01-first-slurm-job.md) | `jobs/hello_lanta.sbatch`, job id, `results/hello_<jobid>.txt` |
| CPU and job array | [02-cpu-array.md](02-cpu-array.md) | CPU baseline, parameter CSV, Slurm array logs |
| OpenMP and MPI | [03-openmp-mpi.md](03-openmp-mpi.md) | compiled C examples launched by `srun` |
| Scientific/data workflow | [04-science-data.md](04-science-data.md) | model/data outputs with run evidence |
| AI/GPU check | [05-ai-gpu.md](05-ai-gpu.md) | GPU allocation log, `nvidia-smi`, optional PyTorch CUDA check |

## Working Pattern

Every activity follows the same visible pattern:

1. `cd` to an event workspace.
2. Create folders with `mkdir -p`.
3. Create small scripts with `cat > file <<'EOF'`.
4. Submit directly with `sbatch`.
5. Read `squeue`, `sacct`, `logs/`, `results/`, and `notes/`.

Use this setup once after SSH to LANTA:

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"

mkdir -p configs input jobs logs notes results src
pwd
```

If your project policy requires a different partition, set it before submitting:

```bash
export LANTA_CPU_PARTITION=compute
export LANTA_GPU_PARTITION=gpu
```
