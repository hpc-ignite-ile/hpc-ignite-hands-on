"""Build an honest point-in-time benchmark ledger from recorded evidence."""
import csv
import json
from pathlib import Path
import re
import statistics
import sys

root=Path(sys.argv[1]); receipts=[json.loads(x) for x in (root/'submissions.jsonl').read_text().splitlines()]
rows=list(csv.DictReader((root/'accounting.psv').read_text().splitlines(),delimiter='|'))
jobs={r['JobID']:r for r in rows if '.' not in r['JobID']}
snapshot=json.loads((root/'summary.json').read_text())['snapshot_utc']
lines=['# Real-science LANTA campaign — 26 September 2026','',f'Accounting snapshot: **{snapshot}**. Account `pv915002`. This is a live campaign, not a claim that every proposed catalog experiment is complete.','',
'## Executed protocols','',
'| Application | Scientific workload | Repeats/comparisons |','|---|---|---|',
'| GROMACS 2026.3 | Public benchMEM, 50,000 steps (100 ps) | CPU versus A100; three repeats each |',
'| miniWeather | Thermal and density current, 1,000 model seconds | 200×100 and 400×200; 1/2/4 ranks; three repeats |',
'| OpenFOAM v2512 | Re=100 cavity, 10,000 steps to 5 s | 20²/40²/80²; 1/2 ranks; three repeats |',
'| Quantum ESPRESSO | Four upstream pwscf benchmark inputs, converged SCF | 1/2/4 ranks; three repeats per case |',
'| Athena++ | Sod shock to t=0.25 | 128/256/512 cells; 1/2/4 ranks; three repeats |',
'| MITgcm | 62×62×15 baroclinic gyre, 30 model days | 1/4 ranks; three repeats |',
'| Scanpy | Full PBMC3k QC→normalization→PCA→UMAP→Leiden→markers | Three seeded repeats |',
'| climlab | EBM equilibrium, control/+4 W m⁻² | 90/180 latitude cells, tolerance-based stop |',
'| REBOUND | Specified three-body system, 100 inner orbits | Three timesteps × three repeats, IAS15 reference |',
'| Astropy / SunPy | Real Horsehead FITS / AIA171 solar image | Three repeats, WCS round-trip and data checks |',
'| EuroSAT | All 27,000 RGB chips; ResNet18 trained from scratch | Batch 64/128 × three seeds × ten epochs |',
'| NVIDIA PhysicsNeMo | 256² Darcy FNO, 2,048 fresh PDE samples/epoch | Three 256-epoch jobs; 256 held-out samples |','',
'“Full” means the stated protocol is completed, not a reproduction of every paper, production simulation, or upstream default. MITgcm is a 30-day transient, not an equilibrated ocean; REBOUND is a small accuracy experiment; miniWeather is a mini-application. WRF, CMIP6, Oceananigans, LAMMPS and other catalog alternatives are not executed by this campaign. Existing EnergyPlus/Mesa full-year evidence is archived separately.','',
'## Resource ledger','',
'Elapsed time includes setup/build where present. Reserved CPU-hours = allocated CPUs × elapsed seconds / 3,600; GPU-hours = allocated GPUs × elapsed seconds / 3,600. Neither is billed SHr. Running jobs show elapsed usage only. GNU time and Slurm step records provide CPU time and sampled RSS; MaxRSS is not node-wide summed memory. GPU CSVs record utilization, VRAM and power at one-second intervals.','',
'| Job | Workflow | Slurm state | Elapsed | Reserved CPU-h | GPU-h |','|---|---|---|---:|---:|---:|']
cpu=gpu=0.
for receipt in receipts:
    jid=receipt.get('job_id'); r=jobs.get(jid)
    if not r: continue
    ch=int(r['AllocCPUS'])*int(r['ElapsedRaw'])/3600
    match=re.search(r'(?:^|,)gres/gpu=(\d+)',r['AllocTRES']); gh=(int(match[1]) if match else 0)*int(r['ElapsedRaw'])/3600
    cpu+=ch; gpu+=gh
    lines.append(f"| {jid} | {receipt['workflow']} | {r['State']} | {r['Elapsed']} | {ch:.4f} | {gh:.4f} |")
lines+=['',f'All attempts, including failed qualifications and running elapsed usage: **{cpu:.4f} reserved CPU-hours; {gpu:.4f} GPU-hours**.','',
'## Scientific checks and measured examples','']
validation=json.loads((root/'validation.json').read_text()) if (root/'validation.json').exists() else {}
for name,result in validation.items():
    lines.append(f"- `{name}`: {result['gate']}, {len(result['runs'])} numerical comparisons. See [validation.json](validation.json).")
for jid,label in [('6340325','CPU'),('6340336','GPU')]:
    values=[]; temperatures=[]
    for p in (root/'results'/f'gromacs-{jid}').glob('repeat-*/md.log'):
        match=re.search(r'Performance:\s+([\d.]+)',p.read_text());
        if match: values.append(float(match[1]))
    if values: lines.append(f'- GROMACS {label}: {len(values)} repeats, median **{statistics.median(values):.3f} ns/day** (values {values}). Energy output contains only the endpoint at 100 ps, not an equilibrium distribution.')
for name in ('cfd','scanpy','rebound','climlab','astropy','sunpy','eurosat','darcy','qe'):
    for p in sorted((root/'results').glob(f'{name}-*/performance.json')):
        data=json.loads(p.read_text()); lines.append(f'- [{p.parent.name}: recorded performance and checks]({p.relative_to(root)}), {len(data)} records. A partially written file does not establish completion; check its job state above.')
lines+=['','## Actual output figures','']
for pattern in ('athena-*/sod-reference.png','miniweather-*/*theta.png','mitgcm-*/gyre-ssh.png','scanpy-*/*.png','rebound-*/*.png','climlab-*/*.png','eurosat-*/b64-r0/confusion.png','darcy-*/repeat-0/prediction.png'):
    for p in sorted((root/'results').glob(pattern)):
        lines += [f'![Measured output: {p.parent.name}]({p.relative_to(root)})','']
lines+=['## Caveats and failed attempts','',
'- Job 6340324 exited zero but Athena++ printed a fatal meshblock error. It is scientifically INVALID, despite Slurm COMPLETED. Corrected job 6340337 passed global analytic-solution checks; upstream per-block shock-errors.dat is not treated as global error.',
'- GROMACS short GPU qualification 6340318 failed when reset overlapped PME tuning. Corrected short and longer jobs succeeded.',
'- QE 7.3.1 crashes with the legacy case-1 nitrogen RRKJ pseudopotential (6340323/6340338). Case 1 uses qualified QE 7.2; cases 2–4 use 7.3.1. This is not a cross-version performance comparison.',
'- Missing pooch, an MPI preprocessing include, and a downloaded Git LFS pointer caused 6340329, 6340335 and 6340344 to fail. Their corrected runs are retained separately, not overwritten.',
'- Scanpy first-run JIT/cache cost must be separated from warm repeats. Identical seeds measure repeatability, not biological robustness.',
'- EuroSAT uses a stratified random chip split: geographic leakage is not excluded. Accuracy is not evidence of crop-yield prediction or spatial generalization.',
'- PhysicsNeMo is a pinned development checkout (2.3.0a0), not a stable-release claim. The four-epoch job is a timing pilot only. Three full jobs repeat seed 42 to measure performance repeatability; they do not estimate seed uncertainty.',
'- Proposed accuracy thresholds are tutorial checks, not proof of physical validity. Plots here are actual computed outputs, not generated expected-result images.','',
'## Reproduce and inspect','',
'[Source commits and input SHA-256](provenance.json), [submission receipts](submissions.jsonl), [raw accounting including job steps](accounting.psv), and [retained-file inventory](inventory.json). Large grids, trajectories and model checkpoints remain under `/project/pv915002-hpcign/wdiazcar/real-benchmarks-20260926/results/` on LANTA. Run scripts are in [benchmarks/real](../../../benchmarks/real/).','',
'Stage sources/data through the transfer host, inspect the pinned versions, qualify dependencies in Slurm, then submit reviewed scripts from the campaign root. Do not execute solver/training scripts on a login node. The scripts rely on staged inputs and qualified environments; they are not a one-command portable installer.','',
'Refresh the remote bounded evidence with `python scripts/collect.py "$PWD"`, then build this report with `python scripts/report.py evidence`. Transfer the evidence folder back using rsync.','',
'## Primary sources and attribution','',
'- [GROMACS benchMEM](https://www.mpinat.mpg.de/grubmueller/bench): CC BY 4.0, Department of Theoretical and Computational Biophysics, Max Planck Institute, Göttingen.',
'- [miniWeather](https://github.com/mrnorman/miniWeather), [QE benchmarks](https://github.com/QEF/benchmarks), [Athena++](https://github.com/PrincetonUniversity/athena), [MITgcm](https://github.com/MITgcm/MITgcm). Upstream license/notices apply; QE benchmark script retains its GPL notice.',
'- [PBMC3k workflow](https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering-2017.html), [Astropy FITS tutorial](https://learn.astropy.org/tutorials/FITS-images.html), [SunPy sample data](https://github.com/sunpy/data).',
'- [PhysicsNeMo Darcy FNO](https://github.com/NVIDIA/physicsnemo/tree/main/examples/cfd/darcy_fno), [EuroSAT](https://github.com/phelber/EuroSAT), [pinned dataset mirror used by torchvision](https://github.com/pytorch/vision/blob/main/torchvision/datasets/eurosat.py). Original authors/data terms apply; this archive does not redistribute the datasets.','']
(root/'README.md').write_text('\n'.join(lines))
