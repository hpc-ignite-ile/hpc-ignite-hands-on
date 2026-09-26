# Full Twin-B repair: baseline gate blocked

Executed the first correctness gate on LANTA under `pv915002`, using EnergyPlus
25.1.0 and the previously prepared one-day Boonchoo/Lampang inputs. This is **not
a successful full EnergyPlus/Mesa integration**. Original Twin-B files and
historical run outputs were not modified.

## Implemented and tested

- `scripts/twinb_baseline_gate.py`: isolated output directory, input SHA-256,
  bounded process runtime, `/usr/bin/time -v`, and rejection of severe/fatal
  errors even when EnergyPlus returns zero.
- `scripts/twinb_audit_geometry.py`: read-only surface/construction audit,
  matching both zone and space names.
- `slurm/qualification/twinb-baseline.sbatch`: four CPUs, 7 GB, ten-minute
  allocation; compute-node preprocessing and simulation, no GPU.
- Local suite: `python3 -m unittest discover -s tests` — 31 tests passed.

## Actual results

| Job | Slurm elapsed | Simulator wall seconds | EnergyPlus exit | Gate exit | Severe |
|---|---:|---:|---:|---:|---:|
| 6339887 | 18 s | 3.34 | 0 | 1 | 3 |
| 6339889 | 5 s | 2.21 | 0 | 1 | 3 |

Both simulations also reported 43 warnings, zero fatal errors. Job 6339889 reran
with corrected audit matching: the affected identifiers name **spaces**, not
zones. Do not use job 6339887's empty geometry lists as evidence of absent surfaces.

Job 6339889 process peak RSS was **303,668 KiB** according to
[`time.txt`](6339889/baseline/time.txt). Slurm sampling recorded only 12.85 MB
for its short batch step; this underestimates the process peak. Raw
[`accounting.psv`](accounting.psv) preserves both jobs and all steps. These are
baseline diagnostics, not a coupled-model speedup comparison. No billed-SHr
estimate is asserted.

Example real gate output:

```json
{"returncode": 0, "errors": {"Warning": 43, "Severe": 3, "Fatal": 0}, "passed": false}
```

Full [gate output and input hashes](6339889/baseline/gate.json),
[simulator log](6339889/baseline/console.log),
[error file](6339889/baseline/eplusout.err),
[geometry audit](6339889/geometry.json), runtime, packages and script hashes
are retained. Large simulator products remain in the isolated remote directory
`/project/pv915002-hpcign/wdiazcar/twinb-fix-20260926/results/<job-id>/baseline/`.

## Why progression stopped

EnergyPlus reports that solar gains cannot be absorbed by floors in
`F2-3_LOBBY`, `F4_LOBBY`, and `F5_LOBBY`. The corrected audit finds:

| Space | Walls | Roofs | Floors |
|---|---:|---:|---:|
| F2-3_Lobby | 8 | 1 | 0 |
| F4_Lobby | 1 | 0 | 0 |
| F5_Lobby | 1 | 1 | 0 |

All three belong to `Zone_Central-hall_F2-3`. The source also assigns zero
volume to `F4_Lobby`. These findings require review of the intended atrium/open
space geometry and boundaries; changing material absorptance alone does not
create missing floor surfaces. Adding guessed floors or changing solar
distribution would change the physical model and is not an approved repair.

```text
Pinned one-day input → standalone EnergyPlus → severe/fatal gate
                                                   │
                                                   └─ FAILED: geometry decision required
Corrected, reviewed building → rerun gate → read-only adapter equality
 → fixed setpoint/reset tests → small Mesa → 1,875 agents × 96 timesteps
 → three reproducible repeats → longer runs → performance optimization
```

The synchronous adapter, runtime actuator discovery and coupled qualification
stages remain pending. Choose either owner-reviewed corrected Boonchoo geometry
or authorize a clearly labelled EnergyPlus reference-building fixture for
independent adapter development; reference-fixture success would not qualify
the original building. GPU/DDP and annual runs remain deferred.

## Reproduce

See the [Bash command reference](../../BASH_COMMAND_REFERENCE_TH.md) for command explanations.

Transfer the two Python scripts and the batch script into a fresh working
directory. The checked-in batch script uses the pinned campaign paths above;
edit those paths for another installation. From that directory on LANTA:

```bash
sbatch slurm/qualification/twinb-baseline.sbatch
sacct -j <job-id> --units=M --parsable2 \
  --format=JobID,State,ExitCode,Elapsed,AllocCPUS,TotalCPU,MaxRSS
```

Expect `FAILED 1:0` for the current input: that is the deliberate correctness
gate, not an infrastructure crash. Do not remove it to make the job green.
