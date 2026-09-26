"""Re=100 cavity, complete five-second integrations and decomposition checks."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

root,out=(Path(str(p).replace('/lustrefs/disk/project/','/project/')) for p in sys.argv[1:])
source=Path('/project/pv915002-hpcign/wdiazcar/openfoam-v2512-mpi-smoke/inside-out-isolated-case')
image='/project/pv915002-hpcign/wdiazcar/containers/openfoam-dev-2512.sif'
rows=[]
def field(path):
    text=path.read_text()
    body=re.search(r'internalField\s+nonuniform\s+List<vector>\s+\d+\s*\((.*?)\n\)',text,re.S)[1]
    values=np.array([[float(x) for x in vector.split()] for vector in re.findall(r'\(([^()]+)\)',body)])
    assert np.isfinite(values).all()
    return values
for n in (20,40,80):
    reference=None
    for ranks in (1,2):
        for repeat in (1,2,3):
            case=out/f'n{n}-p{ranks}-r{repeat}'
            for folder in ('0','constant','system'): shutil.copytree(source/folder,case/folder)
            path=case/'system/blockMeshDict'
            path.write_text(path.read_text().replace('(10 10 1)',f'({n} {n} 1)'))
            path=case/'constant/transportProperties'
            path.write_text(path.read_text().replace('0.01;','0.001;'))
            path=case/'system/controlDict'; text=path.read_text()
            for key,value in {'endTime':'5','deltaT':'0.0005','writeInterval':'1000','writePrecision':'12'}.items():
                text=re.sub(r'\b'+key+r'\s+[^;]+;',key+' '+value+';',text)
            path.write_text(text)
            base=['apptainer','exec','--pwd',str(case),image,'/usr/bin/openfoam2512']
            def run(command,name):
                with (case/name).open('w') as handle:
                    subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,check=True)
            run(base+['blockMesh','-case',str(case)],'mesh.log')
            run(base+['checkMesh','-case',str(case)],'mesh-check.log')
            assert 'Mesh OK' in (case/'mesh-check.log').read_text()
            if ranks==2:
                run(base+['decomposePar','-case',str(case)],'decompose.log')
                solver=base+['-c','mpirun -np 2 --mca plm isolated --mca ras ^slurm --mca pml ob1 --mca btl self,vader,tcp icoFoam -parallel -case "$PWD"']
            else: solver=base+['icoFoam','-case',str(case)]
            start=time.perf_counter()
            run(['/usr/bin/time','-v','-o',str(case/'time.txt')]+solver,'solver.log')
            elapsed=time.perf_counter()-start
            log=(case/'solver.log').read_text()
            assert '\nEnd\n' in log and 'Time = 5\n' in log
            assert not re.search(r'\b(?:nan|inf)\b',log,re.I)
            courant=max(map(float,re.findall(r'Courant Number mean: \S+ max: (\S+)',log)))
            assert courant<1
            if ranks==2: run(base+['reconstructPar','-case',str(case)],'reconstruct.log')
            velocity=field(case/'5/U'); previous=field(case/'4.5/U')
            if reference is None: reference=velocity
            error=float(np.max(np.abs(velocity-reference)))
            assert error<1e-3, 'Decomposition/repeat velocity discrepancy'
            steady=float(np.linalg.norm(velocity-previous)/max(np.linalg.norm(velocity),1e-30))
            rows.append(dict(n=n,cells=n*n,ranks=ranks,repeat=repeat,elapsed_s=elapsed,
                max_courant=courant,max_velocity_difference=error,last_half_second_relative_change=steady,gate='PASS'))
            (out/'performance.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(json.dumps(rows[-1]),flush=True)
    profile=reference.reshape(n,n,3)[:,n//2,0]
    plt.plot(profile,(np.arange(n)+.5)/n,label=f'{n}×{n}')
plt.xlabel('Approximate vertical-centerline u / lid speed'); plt.ylabel('y / L')
plt.legend(); plt.title('Re=100 cavity at t=5 s · actual LANTA output'); plt.savefig(out/'velocity-profiles.png',dpi=140)
