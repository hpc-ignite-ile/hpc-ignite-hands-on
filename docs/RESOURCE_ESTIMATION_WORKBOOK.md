# จาก booklet สู่การทดลองจริง: estimate → run → measure → improve

เริ่มจากคำถามที่ตรวจได้ ไม่ใช่จำนวน CPU ที่มากที่สุด: งานเล็กใช้ตรวจระบบ ส่วนงาน benchmark ใช้วัดประสิทธิภาพ และงานวิจัยต้องตรวจความถูกต้องของโมเดลด้วย.

This workbook follows the uploaded [40-page LANTA handbook](lanta-hpc-experience-handbook.pdf), with original [booklet images and provenance](images/booklet/README.md). The source booklet is a teaching artifact: illustrative commands, module names and numerical labels in its pictures are not current system policy. Use the executable tutorial text and live LANTA checks instead.

## Learning sequence

| Booklet pages | Question before proceeding | Tutorial |
|---|---|---|
| 5–11: Linux, files, shell, modules | Can I locate input, code, environment and output? | [Readiness](../lanta-experience/00-readiness.md), [environment](../core-hpc/chapter-02-environment/README.md) |
| 12–18: HPC, access, resource choice, evidence | What is the scientific question and first bounded pilot? | [Foundation](../foundation/lanta-foundation/README.md), this worksheet |
| 19–23: first Slurm job and output checks | Did my program run on a compute node and create the right output? | [First job](../lanta-experience/01-first-slurm-job.md) |
| 24–26: CPU and arrays | Does concurrency improve total throughput at acceptable cost? | [CPU/arrays](../lanta-experience/02-cpu-array.md) |
| 27–32: OpenMP and MPI | Is my input decomposed, and where is communication time spent? | [Parallel programming](../lanta-experience/03-openmp-mpi.md) |
| 33–36: scientific workflows and reproducibility | Is the numerical/scientific result correct at this scale? | [Diffusion](../lanta-experience/04-science-data.md), [reference-building co-simulation](TWINB_REFERENCE_BENCHMARKS.md) |
| 37–38: AI/GPU | Is the GPU doing useful work, at the same accuracy? | [GPU](../lanta-experience/05-ai-gpu.md), [real application experiments](REAL_APPLICATION_EXPERIMENTS.md) |

![The booklet's scientific workflow](images/booklet/Part5-ScientificWorkload.png)

Concept illustration from the booklet, not an observed output. Each tutorial now has its own scope, estimation model, archived measurements (when available), output excerpt and next experiment. Browse the [complete evidence index](tutorial-evidence/README.md).

## Before running: fill in the resource worksheet

| Field | Learner entry |
|---|---|
| Question and correctness criterion | What result must agree, within which tolerance? |
| Inputs | URL/license, checksum, dimensions/agents/atoms/rows, seed |
| Software | Git commit, module versions, package lock/container digest |
| Parallel layout | Nodes, MPI ranks, threads/rank, workers, GPUs |
| Memory model | Input + live state + temporaries + library/runtime + safety margin |
| Time model | Setup + compute + I/O; estimate using two small pilots |
| Storage | Downloads + extracted inputs + checkpoints + retained output |
| Limits | Wall-time ceiling, memory ceiling, array concurrency, maximum repeats |
| Measurement plan | Program time, Slurm elapsed, TotalCPU, RSS, GPU telemetry, output checks |

Requests below are planning examples, not recommendations to enlarge every job. Match the actual code: more reserved cores do not parallelize serial Python. Check current partition limits, account balance and available modules before submission; the campaign used `pv915002`, not the expiring account.

### Worked estimation: separate workload growth from parallel scaling

Suppose **hypothetical** same-environment pilots at 1M and 2M samples take 12 and 22 seconds. The inferred model is 2 seconds startup plus 10 seconds per million samples. A 10M-sample forecast is 102 seconds; a 1.5× margin suggests 153 seconds, rounded up to a 3-minute ceiling. These numbers teach the calculation; they are not LANTA measurements.

For raw numeric arrays, bytes = elements × bytes/element × simultaneously live arrays. Two float64 arrays of 10M elements require at least 160 MB (about 153 MiB), before temporary arrays and runtime overhead. Python object lists are larger. Fit the observed model again after changing algorithm, precision or data structure.

Use measured per-node peaks plus a justified margin when sizing RAM. For MPI, account for all ranks on each node; the largest per-task RSS is not aggregate node memory. For GPU jobs, host RAM and device VRAM are different limits.

## After running: collect evidence

Run this on the login node **after** your job completes, from the lesson workspace. It only queries accounting and saves metadata. Read the [Bash reference](BASH_COMMAND_REFERENCE_TH.md) for shell syntax.

```bash
read -rp "Completed Slurm job or array ID: " JOBID
if [[ "$JOBID" =~ ^[0-9]+(_[0-9]+)?$ ]]; then
    mkdir -p "notes/$JOBID"
    sacct --array -j "$JOBID" --parsable2 \
      --format=JobID,JobName,Account,Partition,State,ExitCode,ElapsedRaw,TotalCPU,AllocCPUS,ReqMem,AllocTRES,MaxRSS,Start,End \
      > "notes/$JOBID/accounting.psv"
    module list 2> "notes/$JOBID/modules-current.txt"
    date -Is > "notes/$JOBID/collected-at.txt"
    cat "notes/$JOBID/accounting.psv"
else
    echo "Enter a numeric job ID (or one array element such as 12345_2)."
fi
```

`modules-current.txt` describes the collection shell, **not necessarily the job environment**. Also save `module list`, program/package versions, input hashes and source commit inside the job log. Save the submitted script and job-specific output before starting another run; a generic `results/summary.json` can otherwise be overwritten.

| Quantity | How to interpret it |
|---|---|
| Program time | Instrument the compute region; separate setup and I/O |
| Slurm elapsed | Allocation duration, including imports and setup; excludes queue wait |
| Reserved CPU-hours | Sum `AllocCPUS × ElapsedRaw / 3600` over allocation rows, once per array element |
| Actual CPU seconds | Allocation-row `TotalCPU`, with day/hour/minute parsing; do not add parent and step totals together |
| CPU efficiency | `100 × TotalCPU_seconds / (AllocCPUS × ElapsedRaw)` for one allocation; use summed numerator/denominator for arrays |
| MaxRSS | Sampled maximum task RSS in a step; inspect step records, not only the parent; not summed node RAM |
| Array makespan | Last element end minus first element start; not the sum of element elapsed times |
| GPU performance | Kernel/step time, throughput, peak VRAM and utilization samples; low CPU efficiency alone is inconclusive |
| Service charge | Site billing (`sbill`); reserved CPU-hours are not SHr |

Accounting availability and sampling depend on the site's collection configuration. Missing measurements are not zero usage. See the official [Slurm sacct field documentation](https://slurm.schedmd.com/sacct.html).

For a GPU experiment, record framework peak VRAM and capture `nvidia-smi` samples **inside the GPU allocation** while the program runs, stopping the sampler when the application ends. A pre-run device listing is not a utilization time series. Do not claim measured energy from a nominal GPU power limit or carbon from CPU-hours.

## Interpret an actual archived run

The [CPU-array evidence viewer](tutorial-evidence/lanta-experience-02-cpu-array.html) shows requested/allocated resources, measured CPU seconds, per-element accounting and stdout from the 2026-09-26 archive. The [Twin-B benchmark report](lanta-runs/2026-09-26-twinb-benchmarks/README.md) supplies a later real coupled scientific workload, including a one-versus-four-CPU comparison. Keep smoke tests, failed original geometry, and successful reference-building tests distinct.

## Improve one variable at a time

1. Establish correctness with the smallest complete input, not just an import check.
2. Increase problem size at fixed resources until application time dominates startup, within the pilot ceiling.
3. Freeze that input and compare 1/2/4 cores or one GPU versus CPU; repeat each variant three times.
4. Report median and spread, throughput, reserved resource-hours and correctness together. Use `T1/Tp` for speedup only with the same work and quality target.
5. Change one bottleneck: vectorization, chunk size, communication, output cadence, batching or transfer overlap. Recheck correctness.
6. Save a screenshot showing job ID, actual accounting and result. Keep raw logs/data beside it so the screenshot is auditable.

Stop escalation on OOM, timeout, non-finite output, failed correctness, unavailable data or incompatible runtime. Diagnose before doubling resources. All new application budgets in the [research-backed catalog](REAL_APPLICATION_EXPERIMENTS.md) are bounded pilot proposals, not completed runs.

## Maintainer reproducibility

`scripts/tutorial_resource_profiles.py` holds reviewed per-topic teaching plans. `python3 scripts/build_tutorial_evidence.py` regenerates marked panels and evidence HTML from the archived campaign, without submitting jobs. Browser screenshots are a separate capture step; recapture them when HTML changes. The source archive and failed-run records remain immutable.
