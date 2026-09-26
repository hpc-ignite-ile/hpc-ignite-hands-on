# Public applications: from smoke tests to repeatable scientific experiments

**Fresh execution evidence:** the [real-science campaign ledger](lanta-runs/2026-09-26-real-benchmarks/README.md) now records extended GROMACS, miniWeather, CFD, materials, ocean, single-cell, climate and astronomy workflows, plus full EuroSAT and PhysicsNeMo training jobs. Consult its timestamp and job states: ongoing jobs are not completed results. The earlier [tutorial performance campaign](lanta-runs/2026-09-26-performance/README.md) remains a separate archive.

Research checked **2026-09-26**. This is a selection and experiment-design catalog,
not a claim that these new applications have run on LANTA. The existing
[EnergyPlus + Mesa benchmark](TWINB_REFERENCE_BENCHMARKS.md) already has archived
LANTA evidence. The entries below preserve the original **pilot designs**; the new campaign ledger specifies which protocols were actually executed and their limits.
Use the [resource worksheet](RESOURCE_ESTIMATION_WORKBOOK.md) and
[Bash reference](BASH_COMMAND_REFERENCE_TH.md) alongside these plans.

## Recommended first wave

**Additional domain tracks:** [CFD, weather/climate and ocean science](CFD_CLIMATE_OCEAN_EXPERIMENTS.md)
cover OpenFOAM, WRF, climlab, CMIP6, MITgcm and Oceananigans.
[Space and astronomical science](SPACE_ASTRONOMY_EXPERIMENTS.md) covers REBOUND,
Athena++, Astropy and SunPy. Each has input sources, a pilot ceiling, scaling
questions, scientific validation and a post-run image checklist. These are
experiment designs; completion status and actual output are in the new campaign ledger, not inferred from these plans.

| Priority | Application | What replaces a toy result | Initial ceiling per pilot, not measured need |
|---|---|---|---|
| 1 | GROMACS benchMEM | Version check → actual biomolecular trajectory | 1 node, 8 CPU, 16 GiB, 1 GPU, 15 min |
| 2 | miniWeather | MPI hello → conservative fluid solver | 1 node, 4 MPI ranks, 8 GiB, no GPU, 15 min |
| 3 | NVIDIA PhysicsNeMo Darcy FNO | CUDA check → training with a PDE validation target | 1 node, 4 CPU, 16 GiB host RAM, 1 GPU, 20 min |
| 4 | EnergyPlus + Mesa | Repeat/extend the already qualified reference-building experiment | Use the measured one-CPU baseline and its existing script |
| 5 | Scanpy PBMC3k | Package import → complete public-data analysis | 1 node, 4 CPU, 8 GiB, no GPU, 15 min |

These are conservative **caps chosen for pilot design**, not guarantees that setup
or the complete scientific study fits. Start with one pilot per application, no
unbounded arrays. Excluding the existing EnergyPlus workflow, running all four
new pilots to their caps would reserve 5.3333 CPU-hours and 0.5833 GPU-hours; these are
resource-unit totals, **not billed SHr**. Three repeats of every variant multiply
the budget. Review measurements before expanding the matrix.

### Live LANTA compatibility check

A read-only login/module check on 2026-09-26 found `compute-devel` and `gpu-devel`
with two-hour limits, and these candidates:

- `GROMACS/2026.3-cpeGNU-25.03-CUDA-12.6` (also 2025.3 and older versions).
- `QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu` and `QuantumESPRESSO/7.3.1-libxc-6.2.2-NV24.11-CUDA12.6`.
- CUDA 12.6 and `CrayNVHPC/23.03` appeared in the visible module search.
- No LAMMPS module appeared in that search; do not assume a binary is installed.

Module visibility is **not runtime qualification**. miniWeather still needs a
compatible MPI/Parallel-NetCDF build. NVIDIA packages need Python/PyTorch/CUDA
and GPU-driver compatibility checks inside an allocation. Current upstream
PyTorch MNIST code uses `torch.accelerator`, so do not blindly run its latest
branch in the older `pytorch-2.2.2` environment. Pin a compatible commit/environment
or qualify an isolated newer environment; do not replace the shared working env.

Before each pilot, record repository commit, application version, input checksum,
license and environment lock/container digest. Fetch data/dependencies through
the transfer host. Build/run compute work through Slurm using account `pv915002`.
No latest-branch snapshot should silently change between repeats.

## miniWeather

**Primary source:** [ORNL/NVIDIA miniWeather](https://github.com/mrnorman/miniWeather),
including its [license](https://github.com/mrnorman/miniWeather/blob/main/LICENSE).
It provides weather-like fluid dynamics with MPI, OpenMP and accelerator variants.
It is a scientific mini-application, not a complete operational weather model.

**Fits:** parallel, MPI, OpenMP, climate, diffusion, environment, containers and
visualization tutorials. The input is generated analytically, avoiding large
external weather datasets. The license has BSD-style source/binary notice terms;
retain the file rather than relying on GitHub's unclassified license badge.

**Protocol we propose:** use the rising-thermal case with `NX=200`, `NZ=100` and
`SIM_TIME=100`, then 400×200. Build configuration fixes these parameters; preserve
both configurations. First compare serial and MPI fields, then hold the grid
fixed for 1/2/4 ranks, three repeats each. Do not use the repository's old
machine-specific launch commands unchanged on LANTA; adapt to Cray MPI and `srun`.

**Estimate/measure:** live fluid arrays scale with cells and halos; refining the
mesh also changes timestep count for a fixed physical duration. Measure cell
updates/second, step count, MPI scaling, RSS, output bytes and separate NetCDF I/O.
Require finite fields and acceptable mass/energy conservation diagnostics; compare
field norms with a declared tolerance. Save a potential-temperature/velocity plot
and the conservation/timing log as the post-run evidence.

## Molecular simulation

**First choice:** [Max Planck GROMACS benchmark set](https://www.mpinat.mpg.de/grubmueller/bench).
`benchMEM` contains approximately 82k atoms in a membrane-protein/water system.
Its input files are CC-BY-4.0; retain the listed departmental attribution. The same
page links Kutzner et al.'s GPU-performance publications, so this can repeat a
published **benchmark system**, not reproduce their hardware-specific timings.

**Proposed protocol:** fetch/checksum the `.tpr`, inspect compatibility with the
selected GROMACS module, then run a bounded 2000-step pilot. Compare CPU-only
and one-GPU modes at identical input and step count; use measured runtime to choose
a longer timing interval. Keep warmup, output cadence and tuning policy consistent.
Do not assume every GPU offload flag is compatible with every constraint setup.
Record `md.log`, ns/day, step count, energy diagnostics, warning/error logs, CPU
allocation, VRAM and GPU utilization. A 15-minute allocation is a cap, not a claim
that a given trajectory duration will finish. Short-run trajectory differences
need physical/statistical interpretation, not an exact coordinate hash test.

**Alternative without external molecular data:** [LAMMPS standard benchmarks](https://doc.lammps.org/stable/Speed_bench.html)
and [LAMMPS source](https://github.com/lammps/lammps). The provided `bench/in.lj`
is a Lennard-Jones fluid benchmark; default benchmark cases are 32k atoms and
100 steps. Extend measured runtime only after that pilot. Compare fixed-atom
1/2/4-rank performance, then size scaling separately; capture atom-steps/second,
temperature/energy evolution and neighbor statistics. LAMMPS source is GPL-2.0;
check notices for any additional potential files. Installation/container
qualification is required because no LAMMPS module was found in our search.

## Quantum ESPRESSO

**Source:** [QEF benchmark inputs](https://github.com/QEF/benchmarks), MIT licensed,
including `small-benchmarks`; pseudopotential provenance must also be retained.
Prefer those small cases over the large surface benchmarks for the first pilot.

**Proposed extension:** inspect the benchmark driver before adapting it; replace
site-specific launch assumptions with the LANTA job pattern. Use a 4-rank,
8-GiB, 15-minute CPU ceiling for one selected small case. Freeze pseudopotential,
cell, cutoff, k-grid and convergence thresholds, then compare 1/2/4 ranks.
Record total energy, SCF iterations, force/stress when relevant, memory estimates
and elapsed time. Convergence studies change the scientific problem and must
be reported separately from parallel speedup. Save the SCF convergence plot
and `JOB DONE`/energy excerpt; failed convergence is not a valid fast result.

## NVIDIA and AI

### PhysicsNeMo Darcy-flow Fourier Neural Operator

**Source:** [NVIDIA PhysicsNeMo](https://github.com/NVIDIA/physicsnemo), Apache-2.0,
and its [single-GPU Darcy example](https://github.com/NVIDIA/physicsnemo/blob/main/examples/cfd/darcy_fno/README.md).
The example generates training data on the fly. Its research reference is
[Li et al., Fourier Neural Operator for Parametric Partial Differential Equations](https://arxiv.org/abs/2010.08895).
Use the current PhysicsNeMo project rather than assuming old Modulus instructions
still match the current code.

**Proposed bounded pilot:** inspect the pinned `config.yaml`; the inspected branch
uses `training.resolution`, `training.batch_size`, `training.max_pseudo_epochs`
and `training.pseudo_epoch_sample_size`. Create a recorded pilot configuration
at resolution 64, batch 8, two pseudo-epochs, 128 samples/pseudo-epoch, with
validation at every pseudo-epoch. The upstream default is much larger; do not
launch it accidentally. Configuration changes must pass a startup check before
timing. Then test batch 8/16/32 at fixed resolution and sample count, three repeats.

**Evidence:** separate data generation and training time, samples/second, peak
VRAM, loss and held-out relative L2 error. Fix validation samples and RNG seeds.
Save reference/predicted solution and error-field images. This is a smaller
**similar experiment**, not a reproduction of the paper's full datasets, accuracy
or speedup claims. Main-branch package requirements need qualification on LANTA.

### NVIDIA Warp: numerical GPU simulation

[NVIDIA Warp](https://github.com/NVIDIA/warp) is Apache-2.0 and provides CPU/CUDA
simulation examples, including linked Ising and Navier–Stokes tutorials. Select
one fixed-grid solver from the [NVIDIA Accelerated Computing Hub](https://github.com/NVIDIA/accelerated-computing-hub)
after reviewing that notebook's code/content licenses and dependencies.
For a first CPU/GPU comparison, propose a 128² grid and 100 steps under a
one-GPU, 4-CPU, 8-GiB, 10-minute ceiling. Exclude first JIT compilation from
steady-state timing, but report it separately. Preserve solver/timestep settings;
measure updates/second and conservation/residual error. Save an actual field plot,
not a performance number inferred from NVIDIA's demonstrations.

### Real labelled-data training bridge

[PyTorch MNIST](https://github.com/pytorch/examples/blob/main/mnist/main.py)
(BSD-3-Clause code) is a modest labelled-data benchmark between five random-data
updates and a scientific model. Cache the dataset before entering the compute
job; record its source/terms separately from the code license. Start with one
epoch, fixed seed, batch 64; compare batches 64/128 and CPU/GPU while retaining
the same test set. Report test accuracy, examples/second, VRAM and time to a
fixed accuracy threshold. This is not an LLM/LoRA benchmark; those lessons must
select a model and dataset with explicit redistribution/use terms before training.

## Data analytics

Use [NVIDIA cuDF](https://github.com/NVIDIA/cudf), Apache-2.0, for real GPU
DataFrame operations and its Dask integration. Compare pandas and cuDF on an
identical fixed Parquet dataset and aggregation, initially 1M rows. A proposed
ceiling is 4 CPU, 16 GiB host RAM, one GPU and 10 minutes. Time loading, transfer,
compute and writing separately; compare sorted outputs and null semantics before
scaling to 10M rows. Data must fit the measured live-memory budget, not just its
compressed file size. Preserve CUDA/package compatibility and record any fallback.

For the Spark chapter, implement a genuine SparkSession using the
[Apache Spark Python examples](https://github.com/apache/spark/tree/master/examples/src/main/python)
rather than renaming Python `Counter` output. Start in single-node local mode,
then qualify a distributed launcher separately. Measure partitions, shuffle/spill,
executor memory and the same aggregation's correctness. Screenshot Spark's job
metrics only after an actual Spark run; the present archived exercise has none.

## Earth observation

[TorchGeo](https://github.com/torchgeo/torchgeo) (MIT code) supplies geospatial
datasets and models. A first real land-cover task is EuroSAT; consult the
[dataset metadata and license](https://docs.torchgeo.org/en/stable/api/datasets.html)
and [Helber et al.'s EuroSAT paper](https://arxiv.org/abs/1709.00029).
Code license does not automatically cover imagery. Record bands, preprocessing,
sample manifest and split; avoid geographic leakage.

Propose a stratified 1000-chip pilot and a held-out fixed validation set on one
GPU, 4 CPU, 16 GiB, capped at 20 minutes. Save confusion matrix, class metrics,
chips/second, data-loader time and VRAM. Then scale sample count or batch size,
one variable at a time. Land-cover classification is an adjacent application for
forest/agriculture tutorials, **not** a validated fire, flood or health predictor.
Operational hazard studies need appropriate event labels, validation and domain
review; do not relabel EuroSAT classification as disaster prediction.

## Bioinformatics

[Scanpy](https://github.com/scverse/scanpy) (BSD-3-Clause code) and the
[official PBMC3k workflow](https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering-2017.html)
provide a public-data path through filtering, normalization, PCA, neighbors,
clustering and visualization. This is an adjacent complete biological analysis,
not a replacement for BLAST's different scientific question. Pin the legacy
workflow/environment when comparing it; do not mix it silently with newer defaults.

Propose the complete PBMC3k input under 4 CPU, 8 GiB, 15 minutes. Record dataset
terms/attribution, sparse versus dense memory, stage timings, retained cell/gene
counts and fixed stochastic seeds. Save QC distributions, marker-gene checks and
UMAP. A visually similar UMAP alone is not a correctness criterion; compare the
underlying counts, PCA/neighborhood results and clustering stability.

## Agent models

[Mesa examples](https://github.com/mesa/mesa-examples) and its
[Apache-2.0 license](https://github.com/mesa/mesa-examples/blob/main/LICENSE)
provide inspectable agent-model implementations. Select a model explicitly
compatible with the pinned Mesa version; inspect batch-run API changes before
adapting the existing epidemic lessons.

Use a fixed 100/1000-agent, 100-step pilot with a documented interaction model,
one CPU and a 10-minute ceiling. Repeat seeds, then parallelize independent runs
rather than duplicating one model across MPI ranks without a decomposition.
Capture state invariants, distributions across seeds, agents×steps/second,
history-storage cost and a trajectory plot. Model examples demonstrate mechanisms,
not calibrated predictions about real communities.

## EnergyPlus Mesa

Use the already implemented [reference-building benchmark](TWINB_REFERENCE_BENCHMARKS.md)
and [actual LANTA report](lanta-runs/2026-09-26-twinb-benchmarks/README.md):
five-zone and secondary-school inputs, one/three-day experiments, read-only/reset
equivalence, interventions and repeated seeded Mesa traces. Source model/runtime
versions, weather and input provenance are recorded there. This remains the
best ready-to-repeat real integration example in this repository.

Next experiments should hold physics/input fixed while comparing allocation or
adapter overhead. A different thermostat policy is a scientific/control change,
not a performance-only optimization. Do not claim the reference buildings repair
or calibrate the student's geometry.

## What counts as a completed repeat?

For each new application, publish a pinned manifest, adapted job script,
submission receipt, raw accounting, stdout/stderr, quality checks, metric table
and actual output screenshot. Include failures and warnings. Mark it **pilot
qualified** only after those exist; mark **paper reproduced** only when the
paper's actual method, inputs and evaluation protocol have been matched.
Until then the entries above remain researched experiment plans.
