"""Bounded OpenFOAM v2512 cavity mesh/rank/repeat experiment on one node.

Uses the previously qualified container/MPI launch, never srun with its
PMI-incompatible Open MPI. Timing includes container startup, not meshing.
This is a transient performance experiment, not a steady-state validation.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

image = '/project/pv915002-hpcign/wdiazcar/containers/openfoam-dev-2512.sif'
source = Path('/project/pv915002-hpcign/wdiazcar/openfoam-v2512-mpi-smoke/inside-out-isolated-case')
# Python resolves LANTA's physical mount; the container binds its /project alias.
root = Path(str(Path.cwd()).replace('/lustrefs/disk/project/', '/project/'))/'results'/os.environ['SLURM_JOB_ID']
root.mkdir(parents=True, exist_ok=True)
rows = []
for cells in (20, 40, 80):
    for ranks in (1, 2):
        for repeat in (1, 2, 3):
            case = root/f'n{cells}-p{ranks}-r{repeat}'
            for folder in ('0', 'constant', 'system'):
                shutil.copytree(source/folder, case/folder)
            mesh = case/'system/blockMeshDict'
            mesh.write_text(mesh.read_text().replace('(10 10 1)', f'({cells} {cells} 1)'))
            control = case/'system/controlDict'
            text = re.sub(r'endTime\s+[^;]+;', 'endTime 0.1;', control.read_text())
            text = re.sub(r'deltaT\s+[^;]+;', 'deltaT 0.001;', text)
            text = re.sub(r'writeInterval\s+[^;]+;', 'writeInterval 100;', text)
            control.write_text(text)
            base = ['apptainer', 'exec', '--pwd', str(case), image, '/usr/bin/openfoam2512']
            def run(command, name):
                with (case/name).open('w') as log:
                    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
            run(base+['blockMesh', '-case', str(case)], 'mesh.log')
            run(base+['checkMesh', '-case', str(case)], 'checkmesh.log')
            if ranks == 2:
                run(base+['decomposePar', '-case', str(case)], 'decompose.log')
                solver = base+['-c', 'mpirun -np 2 --mca plm isolated --mca ras ^slurm --mca pml ob1 --mca btl self,vader,tcp icoFoam -parallel -case "$PWD"']
            else:
                solver = base+['icoFoam', '-case', str(case)]
            start = time.perf_counter()
            run(['/usr/bin/time', '-v', '-o', str(case/'time.txt')]+solver, 'solver.log')
            elapsed = time.perf_counter()-start
            log = (case/'solver.log').read_text()
            courant = [float(v) for v in re.findall(r'Courant Number mean: \S+ max: (\S+)', log)]
            residuals = [float(v) for v in re.findall(r'Final residual = ([\d.eE+-]+)', log)]
            assert '\nEnd\n' in log and 'Time = 0.1\n' in log
            assert 'Mesh OK' in (case/'checkmesh.log').read_text()
            assert courant and max(courant) < 1
            assert residuals and all(0 <= v < 1 for v in residuals)
            rows.append(dict(cells=cells*cells, ranks=ranks, repeat=repeat,
                             elapsed_s=elapsed, max_courant=max(courant),
                             max_final_residual=max(residuals), gate='PASS'))
            print(json.dumps(rows[-1]), flush=True)
            with (root/'performance.csv').open('w') as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
print('CFD_TRANSIENT_GATES=PASS (not steady-state or mesh-convergence proof)')
