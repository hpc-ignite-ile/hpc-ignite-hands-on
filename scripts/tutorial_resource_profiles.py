"""Reviewed teaching plans; proposed experiments are NOT recorded measurements."""

# scope, estimate, controlled next experiment, correctness gate
PROFILES = {
    "orientation": (
        "Access, filesystem and environment checks; not a compute benchmark.",
        "No GPU is needed. File/module checks need no compute allocation; use the existing one-CPU Slurm smoke job to prove compute-node access. Budget storage from input + output + checkpoints, not input alone.",
        "Record account, quota, module versions and a small job ID before moving to CPU scaling. Do not run a CPU stress test on a login node.",
        "Confirm the compute hostname, intended account, output file and exit status. Redact tokens and private keys from evidence."),
    "hello": (
        "Small Slurm/environment smoke test; startup dominates its elapsed time.",
        "One task and one CPU are sufficient for printing context and writing a small file. A 1 GiB / 5 minute initial ceiling is a teaching budget, not measured need. Reserved capacity at that ceiling is 1 × 300 / 3600 = 0.0833 CPU-hours.",
        "Run the unchanged job three times. Compare queue wait, job elapsed and program time separately; do not infer parallel speedup from a hello-world job.",
        "Match the job ID and compute hostname in the log and result. COMPLETED alone does not prove the intended program ran."),
    "pi": (
        "Monte Carlo CPU workers and parameter arrays; short examples emphasize scheduling, not speedup.",
        "Work is proportional to samples N; streaming samples avoids storing N points. Workers each need their own Python runtime. Pilot 0.5M samples, then 5M and 50M only if the previous budget permits. Estimate T(N)=startup + N/rate from two pilots. For K array elements, sum each element's CPU-seconds; concurrency changes makespan, not total reserved work.",
        "Hold N fixed and compare 1, 2, 4 workers with three repeats. Set workers no larger than allocated CPUs and cap array concurrency. This code changes random streams with worker count, so compare error distributions, not byte-identical pi values.",
        "Check exact sample count, finite pi near 3.14, unique array output paths and every array exit code. Monte Carlo uncertainty decreases approximately as 1/sqrt(N)."),
    "mpi": (
        "Rank/collective or thread-hello validation; a greeting does not measure useful parallel scaling.",
        "MPI: requested CPUs = ranks × threads/rank; OpenMP: one rank with cpus-per-task equal to OMP_NUM_THREADS. For replicated arrays, node RAM grows with ranks; for decomposed arrays estimate local cells × bytes/field × fields plus halos and runtime overhead.",
        "After hello/collective checks, implement a fixed-size reduction or stencil lasting at least about 60 seconds. Compare 1, 2, 4 ranks or threads with three repeats, then a two-node run at the same total rank count to expose communication cost. Do not change input size in a strong-scaling comparison.",
        "Require all ranks/threads to appear and collective sums to match a serial reference. Preserve reduction tolerances because floating-point summation order can change."),
    "stream": (
        "50,000-row generated CSV and serial streaming group aggregation; not a distributed Big Data engine.",
        "Memory is mainly the parser and group dictionary, O(number of groups), rather than O(rows), because the loop streams records. Disk grows with row count × measured bytes/row. Measure generation, read/aggregate and write separately; use rows/second for throughput.",
        "Change the generator's row count from 50k to 500k to 5M, updating the printed count too. Keep eight groups and seed 42 fixed. Compare streaming to a bounded in-memory version only after estimating memory. Extra CPUs will not accelerate this serial loop automatically.",
        "Sum group counts to the input row count; compare group means to the baseline within the printed rounding tolerance."),
    "plot": (
        "Batch plotting and notebook/output inspection; rendering is distinct from simulation time.",
        "Budget arrays separately from figure buffers. A W × H pixel RGBA canvas needs at least 4WH bytes, before renderer overhead; two float64 coordinate arrays need 16N bytes, while Python lists use more. A single plot normally starts with one CPU and no GPU.",
        "Compare 120, 12k and 120k points while holding figure size fixed; then vary DPI alone. Record render seconds, peak RSS and PNG size. Downsample only the display, retaining the raw scientific output.",
        "Open the generated image, verify axis units and that plotted values correspond to the source CSV. An existing PNG alone is not a successful scientific run."),
    "dask": (
        "A 16-task local Dask thread graph, with a serial fallback; neither branch establishes distributed scaling.",
        "Peak RAM includes concurrently live chunks, temporary arrays, scheduler and workers. For float64 chunks estimate chunk_elements × 8 × live_chunks × temporary_factor. Current Python math loops can be limited by the GIL; more threads are not guaranteed to help.",
        "First require dask_available=true in the output. Enlarge work per task, compare serial and 1/2/4 workers at fixed total work, and record scheduler overhead. A process-based version needs a main guard and its own memory budget. Distributed execution is a separate implementation step.",
        "Compare totals with serial output to a declared tolerance. A fallback result is environment evidence, not a successful Dask benchmark."),
    "spark": (
        "Python Counter over ten words; no Spark session, executors or shuffle are started.",
        "The current exercise needs one CPU and little memory. A future Spark benchmark must budget driver + executors + shuffle/spill storage; the ten-word result cannot size that system.",
        "Implement a real Spark session as a separate extension, then compare 10 MB, 100 MB and 1 GB of fixed-source text. Record executor count, heap, input partitions, shuffle bytes and words/second. Compare to the same serial Counter result before claiming speedup.",
        "Expected counts are data=3, hpc=2, ignite=1, lanta=2, spark=2; require actual Spark event logs before reporting Spark performance."),
    "gpu": (
        "GPU/framework smoke or tiny tensor workload; device visibility is not GPU utilization or training quality.",
        "Separate host RAM from GPU VRAM. Dense float32 n×n matrices occupy 4n² bytes each; three 4096² tensors alone need 192 MiB, excluding library workspace. Start on one GPU and measure peak allocated/reserved VRAM before increasing tensor or batch size.",
        "Warm up kernels, synchronize CUDA around timing, and measure repeated fixed-size kernels separately from imports and transfers. Compare CPU and GPU at identical precision and input. Increase problem size until compute is measurable, without exceeding measured VRAM headroom.",
        "Require CUDA availability, the expected device and a numerical comparison with CPU output. nvidia-smi showing a device does not demonstrate sustained utilization."),
    "training": (
        "Five optimizer updates of a tiny Linear(4,2) network on random data; not model-quality training.",
        "Runtime approximately follows epochs × ceil(samples/batch) × seconds/step after warmup. Host data, parameters, gradients, optimizer state and activations all need separate budgets. Activation memory often grows with batch size; pilot it rather than sizing from parameter count alone.",
        "Fix train/validation data and seeds, increase updates to 100 then 1000, and compare batch sizes 64/128/256 on one GPU. Report examples/second, VRAM, validation metric and time to the same quality target. This extension requires replacing the random-data demonstration.",
        "Check finite losses, actual parameter updates and held-out quality. The archived unseeded final loss is an example, not an exact expected value."),
    "container": (
        "Apptainer environment/payload validation; distinguish version checks from an actual container execution.",
        "Budget image storage + unpack/cache space separately from job RAM. Use the same CPU, memory and input for native and container pilots; image pull/build time is setup, not kernel time. Download on the transfer host.",
        "Pin the image digest, run the same bounded payload natively and in the container three times, and separate first-read/cold-cache from warm execution. No GPU request is needed for a CPU-only payload.",
        "Compare payload outputs and image digest; a version string alone does not prove the payload ran inside the container."),
    "prompts": (
        "Local prompt/checklist scaffold; no remote model inference is established by this exercise.",
        "Current text generation/checking is a one-CPU task. For a future model, budget prompt + generated tokens, batching and KV cache separately; this scaffold supplies no tokens/second or inference-memory measurement.",
        "Create a fixed set of valid and invalid Slurm examples, score detected errors and false positives, and only then compare inference implementations on the same set. Do not send credentials or private research data to an external model.",
        "Check that account, partition, resources and output paths are represented; report quality alongside any future latency improvement."),
    "lora": (
        "6×6 low-rank update arithmetic with rank 2; no language model is loaded or fine-tuned.",
        "Adapter parameters = r(d_in+d_out), versus d_in×d_out dense weights. Here 2(6+6)=24. This saving does not remove base-model, activation, gradient or optimizer memory in real training.",
        "For the arithmetic exercise vary dimension 6/60/600 and rank 2/4/8, recording update norm and time. A real fine-tuning extension must specify model, dataset, sequence length, precision and quality target before requesting GPUs.",
        "Check parameter counts and finite matrix values. Do not describe this result as LLM fine-tuning throughput or accuracy."),
    "security": (
        "Small local permissions/fake-secret audit, with no archived Slurm job for this page.",
        "No GPU or parallel allocation is needed to inspect the supplied two fake files. For a larger authorized audit, budget bytes read and file count: metadata work can dominate throughput.",
        "Test only a dedicated synthetic fixture directory at 10/100/1000 files. Measure files/second and false positives, not private home/project trees. Capture only synthetic examples.",
        "private.env must have mode 0600; confirm detection of the fake token while preserving public-file access. Never publish real secrets in screenshots."),
    "carbon": (
        "CPU work and reserved-resource proxy; no measured joules or carbon emissions.",
        "Reserved CPU-hours = AllocCPUS × elapsed_seconds / 3600. This is not kWh or SHr. Energy requires time-integrated power; emissions additionally require a documented carbon-intensity source and time/location assumptions.",
        "Run identical work on 1/2/4 reserved CPUs and explain why a serial loop may reserve more resources without finishing faster. Compare reserved CPU-hours and measured TotalCPU; use power telemetry only if actually available.",
        "Preserve the numerical checksum. Label energy/carbon unavailable when not measured; do not multiply CPU-hours by an invented emissions factor."),
    "chemistry": (
        "Molecular-mass arithmetic and software preflight; not an electronic-structure calculation.",
        "Current arithmetic needs one CPU. A real chemistry job must specify atoms, basis, method, convergence and scratch needs; mass-calculation timings cannot predict SCF memory or runtime.",
        "After authorized software access, choose a documented small reference molecule and compare basis sizes separately from 1/2/4-core scaling. Record SCF iterations, energy tolerance, peak memory and scratch bytes. This is a new scientific workload, not an already validated tutorial result.",
        "Check masses/units for this exercise. A future SCF benchmark must show convergence and energy agreement, not only a software version."),
    "md": (
        "GROMACS/GPU preflight; a version/device check is not a molecular-dynamics trajectory.",
        "For the existing preflight, the requested GPU time is mostly software startup. Real MD requires atom count, timestep, steps, neighbor settings and output cadence; estimate time from a pilot's ns/day and trajectory storage from frames × atoms × bytes/coordinate.",
        "Prepare a public, documented GROMACS input as a separate extension. After equilibration, compare CPU and one-GPU runs for identical steps and output cadence; report ns/day, energy stability and CPU/GPU balance. Do not extrapolate production speed from this preflight.",
        "Require a trajectory, mdrun performance report and physical checks before claiming MD completion. The current version output proves installation only."),
    "climate": (
        "Synthetic climate grid / NetCDF summary; not a WRF forecast.",
        "Array storage lower bound = Nx×Ny×Nz×variables×bytes/value, multiplied by simultaneously live time levels and temporaries. Output volume adds retained timesteps. Python object grids need more than raw numeric-array bytes.",
        "Scale the synthetic grid side length by 2 then 4 (2-D cells grow 4× then 16×). Time read, compute and write separately. A real WRF benchmark additionally needs matching WPS inputs, domain/nesting and timestep-stability validation.",
        "Check dimensions, units, finite values and known synthetic statistics. A valid NetCDF file does not establish a valid weather forecast."),
    "qe": (
        "Small silicon SCF/preflight path; verify that pw.x actually ran rather than stopping at input/software checks.",
        "Plane-wave memory depends on cell volume, energy cutoff, bands and k-points; doubling atoms is not a reliable linear memory estimate. Pilot the provided small system, record QE's memory estimates and iterations, then tune ranks.",
        "Hold cell, pseudopotential hash, cutoffs and k-grid fixed for 1/2/4-rank timing. Treat cutoff/k-point convergence as a separate accuracy study. Record total energy, iterations, elapsed and per-rank memory; reject unconverged faster runs.",
        "Require convergence and JOB DONE in the scientific output, plus energy agreement within a stated tolerance. A successful module/preflight step alone is insufficient."),
    "raster": (
        "Small synthetic raster/index/risk calculation; not a validated forest, crop or disaster product.",
        "For B float32 bands, a raw H×W image needs 4BHW bytes before masks, output and temporaries. Three 4096² bands alone need 192 MiB. Tiling can bound RAM; output and nodata masks still consume storage.",
        "Increase grid width/height 2× then 4× and compare full-grid versus tiled computation on identical data. Record cells/second, read/write bytes and peak RSS. Keep spatial resolution and thresholds fixed when comparing implementations.",
        "Verify bounds, nodata handling, coordinate reference system for real rasters, and exact/tolerance agreement of tiled and untiled results. Synthetic risk scores are not operational warnings."),
    "bio": (
        "Tiny BLAST query/database smoke test, not a realistic search-throughput study.",
        "Database/index residency may dominate RAM; query bytes alone are insufficient. Pilot a bounded database subset with fixed version and checksum; record queries, total bases, hits and database size.",
        "At fixed database and query set, compare 1/2/4 threads with three repeats. Then scale query count 10× without changing search sensitivity. Include cold/warm database-cache effects and separate database construction from query time.",
        "Compare hit IDs, scores and E-values at fixed settings. A no-hit result can be valid, but software --version alone is not a search."),
    "diffusion": (
        "Explicit 1-D diffusion in serial Python; a real numerical update on a small synthetic problem.",
        "Work is O(N×steps), memory O(N) for two fields (Python lists use more than 16N raw bytes). Pilot N=200, steps=500; grow N to 2000 and then steps to 5000 separately. Estimate from measured cell-updates/second.",
        "Compare a vectorized two-buffer implementation to the serial loop at identical N, steps and alpha. For this stencil alpha is the nondimensional diffusion coefficient; keep it between 0 and 0.5. Refining a fixed physical domain/time requires adjusting dt/steps, not just N.",
        "Check finite values, fixed endpoints, symmetry and agreement to a reference within tolerance. Distinguish code speedup from changing the physical simulation."),
    "jupyter": (
        "Allocated notebook service and HTTP probe; service uptime is not numerical compute time.",
        "Request resources for the notebook kernels' actual workload, not the browser. An idle 4-CPU session for 30 minutes reserves 2 CPU-hours even when TotalCPU is small. Leave RAM headroom for kernels and copies of data.",
        "Compare import-only and an explicitly timed cell, record kernel RSS and service duration, then stop the allocation when done. Do not improve apparent efficiency by leaving an idle notebook running.",
        "Verify the intended kernel and compute node, successful saved output, and tunnel connectivity. Redact notebook tokens in every captured image."),
    "agents": (
        "Synthetic epidemic/agent ensemble; performance evidence does not validate epidemiological predictions.",
        "For local interactions, start with work proportional to agents × steps × repeats; all-pairs interactions can instead grow quadratically. Memory grows with agent state plus retained history. Pilot one seed before multiplying by scenarios.",
        "Compare fixed-size 1/2/4-worker or rank runs with three repeats, preserving seeds and input. Then vary agent count 10× separately. Limit concurrent array tasks and aggregate throughput only after checking every task.",
        "Check population conservation, finite/non-negative compartments and seed-specific output agreement. Compare stochastic distributions when implementations change random-stream ordering."),
    "twinb": (
        "Older synthetic Twin-B / Heatlab runs are distinct from the later real EnergyPlus + Mesa reference-building benchmarks. Original student geometry failures remain recorded.",
        "The synchronous reference adapter advances Mesa once per EnergyPlus zone interval: 96 intervals/day at four timesteps/hour. Agent-side work scales roughly with agents × intervals; EnergyPlus sizing/warmup and HVAC solves add non-linear overhead. Pilot one day before three days or a year.",
        "Use the qualified five-zone (50 agents) and school (1875 synthetic request agents) benchmarks. Compare one versus four allocated CPUs at identical input, then one versus three days separately. The serial adapter cannot use four cores merely because Slurm reserves them. See the reference-building guide for exact commands and newer evidence.",
        "Require zero severe/fatal EnergyPlus errors, valid handles, one Mesa step per zone interval, read-only/reset equivalence, intervention response and reproducible traces. School warnings and lack of Thai calibration remain limitations."),
    "weather": (
        "Weather-data preparation and synthetic health-agent modelling; downloaded data and model validity are different checks.",
        "Budget source archive + extracted data + intermediate tables + outputs. Model cost scales with agents, steps and seeds; preprocessing cost scales with input records and parsing. Record both phases separately.",
        "Pilot one weather file and one seed, then 10 files or seeds with bounded array concurrency. Compare chunk sizes without changing missing-value handling, dates or units. Do not silently replace failed data downloads with synthetic input.",
        "Verify source manifest/checksums, timestamp coverage, units, missing values and population invariants. Successful download is not validated health prediction."),
}


def profile_for(path):
    """Explicit topic routing, with no inference that unrecorded work succeeded."""
    checks = [
        ("chapter-29", "security"), ("chapter-30", "carbon"),
        ("chapter-28", "lora"), ("chapter-13", "prompts"),
        ("chapter-12", "training"), ("chapter-11", "container"),
        ("chapter-05", "stream"), ("chapter-06", "plot"),
        ("chapter-07", "dask"), ("chapter-09", "spark"),
        ("chapter-20", "chemistry"), ("chapter-21", "md"),
        ("chapter-22", "climate"), ("chapter-23", "qe"),
        ("chapter-25", "bio"), ("chapter-24", "raster"),
        ("chapter-26", "raster"), ("chapter-27", "raster"),
        ("chapter-03", "mpi"), ("chapter-08", "mpi"),
        ("chapter-04", "gpu"), ("chapter-10", "gpu"),
        ("02-cpu-array", "pi"), ("03-openmp", "mpi"),
        ("04-science", "diffusion"), ("05-ai-gpu", "gpu"),
        ("02-jupyter", "jupyter"), ("05-output", "plot"),
        ("twinb", "twinb"), ("TWINB_REFERENCE", "twinb"),
        ("weather-health", "weather"), ("enhanced-seir", "agents"),
        ("03-epidemic", "agents"), ("mini-innovation/README", "agents"),
        ("chapter-00", "hello"), ("lanta-foundation", "hello"),
        ("01-first", "hello"),
    ]
    return next((profile for fragment, profile in checks if fragment in path), "orientation")


def booklet_for(profile):
    if profile in {"orientation", "security"}:
        return "5–18", "Part1-FirstDayKnowingHPC.png"
    if profile in {"hello", "container", "jupyter"}:
        return "19–23", "Part2-RunningJobs.png"
    if profile in {"pi", "stream", "dask", "spark", "carbon"}:
        return "24–27", "Part3-A-ProgrammingMatrix.png"
    if profile == "mpi":
        return "27–31", "Part3-MPI.png"
    if profile in {"gpu", "training", "prompts", "lora"}:
        return "37–38", "Part7-AIforScience.png"
    return "33–36", "Part5-ScientificWorkload.png"
