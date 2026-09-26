# Space and astronomical science: reproducible experiment track

Sources checked **2026-09-26**. These are proposed pilots, **not completed runs**.
They extend booklet pages 33–38 from scientific simulation and data workflows
to gravitational dynamics, astrophysical fluids and real telescope observations.
Use the [resource worksheet](RESOURCE_ESTIMATION_WORKBOOK.md) for accounting and
the [application catalog](REAL_APPLICATION_EXPERIMENTS.md) for the common gates.

## Choose the scientific question

| Experiment | Data type | First question | Proposed ceiling per pilot |
|---|---|---|---|
| S1 REBOUND planetary dynamics | Specified initial conditions; optionally cached ephemerides | Does an orbit integration meet the error budget? | 1 CPU, 2 GiB, 10 min |
| S2 Athena++ shock/blast dynamics | Generated numerical test problem | Is shock evolution convergent and conservative? | 4 MPI ranks, 8 GiB, 15 min |
| S3 Astropy FITS analysis | Public telescope image | Can we reproduce image statistics and coordinates? | 1 CPU, 2 GiB, 10 min |
| S4 SunPy solar imaging | Public SDO/AIA observations | Can we align and compare solar regions consistently? | 2 CPUs, 4 GiB, 10 min |

These caps are planning choices, not measured requirements. None needs a GPU by
default. A small image or planetary system can be too small to benefit from HPC;
the useful scaling workload is a scientifically justified ensemble or image batch,
not allocation of more processors to unchanged serial code.

## S1. REBOUND: planetary dynamics and accuracy versus cost

Sources: [REBOUND repository](https://github.com/hannorein/rebound),
[WHFast tutorial](https://rebound.hanno-rein.de/ipython_examples/WHFast/), and
[Rein & Tamayo's WHFast paper](https://arxiv.org/abs/1506.01084).
REBOUND provides gravitational integrators; MPI support is specific to selected
problems, not automatic distribution of arbitrary Python simulations.

**Inputs and pilot:** begin with the tutorial's explicitly specified planetary
initial conditions and fixed units; save them as a manifest. Integrate a bounded
100 inner-orbit periods, comparing timesteps P/20, P/40 and P/80. These are proposed
resolution trials, not guaranteed accuracy settings. For Solar-System runs using
JPL Horizons, cache the exact epoch, reference frame, body IDs and returned state;
do not query a changing live service independently in every repeat.

**Resource estimate:** particle state is O(N), but gravitational cost depends on
active/test-particle configuration and solver. Direct all-pairs self-gravity can
grow as O(N²) per force evaluation; do not apply that law blindly to a small
planetary splitting integrator. Measure wall seconds/orbit and stored snapshots.
For independent systems, arrays of 10 then 100 seeds/initial conditions are the
scaling path; cap concurrency and preserve each run's state and seed.

**Validation and optimization:** compare relative energy error, angular momentum,
orbital elements and a shorter high-accuracy reference integration. Use a suitable
integrator for close encounters; faster WHFast settings are not automatically
valid there. Fix error targets when comparing cost. LANTA's recorded EPYC 7713
CPU is not an AVX-512 target: do not choose WHFast512 from a benchmark headline.

**Capture after running:** orbit plot, energy-error versus time, timestep/error/cost
table and per-array accounting. A repeat of the method on a bounded system is not
a reproduction of all performance claims in the paper.

## S2. Athena++: shocks and blast waves, with an MHD extension

Sources: [Athena++](https://github.com/PrincetonUniversity/athena), its
[running guide](https://github.com/PrincetonUniversity/athena/wiki/Running-the-Code),
and [Stone et al.'s method paper](https://arxiv.org/abs/2005.06651).
This is an astrophysical fluid/MHD application; do not mix Athena++ configuration
with old Athena C-version tutorials.

**Progression:** use the pinned release's supplied hydrodynamic shock-tube problem
first (128/256/512 cells), then its two-dimensional blast-wave case (64²/128²/256²).
Preserve equations of state, reconstruction, Riemann solver, boundary conditions
and final physical time. The selected problem generator must match the build.
Start on CPU and uniform mesh; add AMR or magnetic fields only after that baseline.

**Estimate:** bytes scale with local cells, ghost zones, conserved/primitive fields
and work arrays. CFL-limited refinement also increases steps. Record cell-updates/s,
rank count, solver time, RSS and output bytes. A 1-D tiny case establishes accuracy;
the larger fixed 2-D case is more suitable for 1/2/4-rank scaling.

**Validate:** shock tube against its analytic Riemann solution; blast evolution
against a compatible similarity/reference solution with matching geometry and
energy conventions. Track positivity, mass/energy budgets and boundary fluxes.
AMR comparisons require both accuracy and active-cell histories, not only elapsed
time. A later MHD benchmark must also monitor the divergence constraint.

**Capture:** density/pressure/velocity profiles, reference-error curves, blast
density maps and conservation histories. These are numerical verification cases,
not observations of a particular supernova or a complete star-formation study.

## S3. Astropy: public astronomical images, not synthetic arrays

Use the official [FITS-image tutorial](https://learn.astropy.org/tutorials/FITS-images.html)
and [Astropy source](https://github.com/astropy/astropy). The tutorial supplies a
Horsehead Nebula FITS image. Download it once, retain checksum, original header,
provenance and image-specific credit/terms; the library's license does not replace
the observing archive's data policy.

**Pilot:** reproduce FITS inspection, finite/masked pixel statistics and a
coordinate-labelled image. Then compare full-array and tiled statistics at
identical masking/scaling. For a real throughput extension, select a documented
fixed list of public images; duplicating one file measures implementation load,
not a larger independent observational sample.

**Estimate/validate:** raw bytes ≈ pixels × decoded bytes/pixel; FITS scaling,
byte-order conversion, masks and plotting introduce copies. Measure I/O and
compute separately, pixels/s, peak RSS and output volume. Require agreement of
counts/statistics within stated tolerance, preserve units and FITS scaling, and
test pixel↔world-coordinate round trips where WCS is present. Do not silently
repair or overwrite the original FITS file.

**Capture:** image with labelled axes, histogram/mask and tile-versus-full
comparison. This validates an analysis workflow, not a new astrophysical finding.

## S4. SunPy: solar observations and a space-weather precursor workflow

Use [SunPy](https://github.com/sunpy/sunpy) and its official
[AIA map example](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.AIAMap.html),
starting with `AIA_171_IMAGE`. This is measured solar imagery, unlike S1/S2's
simulation-generated states.

**Pilot:** plot the sample map with correct time, wavelength, observer and solar
coordinates; extract a documented region. A second stage uses a bounded set of
10 then 100 explicitly timestamped frames, with archive access and data attribution
recorded. Stage downloads separately. Normalize by exposure where appropriate,
inspect quality flags and account for alignment/solar rotation before interpreting
temporal intensity changes.

**Resource/validation plan:** streaming a sequence bounds RAM; stacking all
float32 images requires at least 4×frames×height×width bytes plus masks and
reprojection temporaries. Compare serial and 2/4-worker independent frame analysis
at fixed inputs, avoiding nested thread oversubscription. Check coordinate
round trips, off-disk masks, units and invariance of regional statistics under
the chosen processing method. Reprojection need not conserve flux unless the
algorithm is designed for it; explicitly test the quantity you intend to preserve.

**Capture:** registered solar image, selected-region overlay, quality-checked
intensity curve and stage timing. This is a space-weather data-processing
precursor, **not a validated flare forecast**; forecast claims require event
labels, a leakage-safe time split and independent validation.

## Execution and evidence gates

1. Pin each repository/package and retain its license; separately check all
   observational-data terms. Archive configuration, seeds, units and input hashes.
2. Qualify dependencies in an isolated environment. These applications were not
   runtime-tested on LANTA in this documentation update. Do not replace shared
   environments or assume a public repository is already installed.
3. Stage dependencies/data via the transfer host, then use a bounded Slurm job
   under `pv915002`; never put numerical integration on the login node.
4. Require scientific checks before three-repeat timing/scaling studies. Preserve
   failed runs, warnings and actual allocation, not just successful plots.
5. Save raw output, accounting, environment provenance and screenshots after
   execution. Until then, result/usage fields remain **not measured**.

For a related continuum-solver path, see [CFD, climate and ocean](CFD_CLIMATE_OCEAN_EXPERIMENTS.md).
