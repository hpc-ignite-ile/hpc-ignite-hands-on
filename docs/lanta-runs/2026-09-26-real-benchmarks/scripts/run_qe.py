"""Run literal upstream small-benchmark SCF input; do not execute its shell driver."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

root, out = map(Path, sys.argv[1:])
source = root/'sources/qe-benchmarks/small-benchmarks'
text = (source/'pwscf_bench.sh').read_text()
case = int(os.environ.get('QE_CASE','1'))
template = re.search(r'cat > test_'+str(case)+r'\.in << EOF\n(.*?)\nEOF', text, re.S)[1]
rows = []
for ranks in map(int, os.environ.get('RANKS','1 2 4').split()):
    for repeat in range(1,int(os.environ.get('REPEATS','3'))+1):
        run = out/f'case{case}-p{ranks}-r{repeat}'
        run.mkdir(parents=True)
        scratch = run/'scratch'
        scratch.mkdir()
        (run/'input.in').write_text(template.replace('$SCRATCH_DIR',str(scratch)).replace('$PSEUDO_DIR',str(source/'pseudopotentials.d')))
        start = time.perf_counter()
        with (run/'solver.log').open('w') as log:
            subprocess.run(['/usr/bin/time','-v','-o',str(run/'time.txt'),'srun','--exact','-n',str(ranks),'-c','1','pw.x','-inp',str(run/'input.in')],stdout=log,stderr=subprocess.STDOUT,check=True)
        log = (run/'solver.log').read_text()
        energies = re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',log)
        assert 'JOB DONE.' in log and 'convergence has been achieved' in log and energies
        energy = float(energies[-1])
        if rows:
            assert abs(energy-rows[0]['energy_Ry']) < 1e-6, 'Rank/repeat energy mismatch'
        rows.append(dict(case=case,ranks=ranks,repeat=repeat,elapsed_s=time.perf_counter()-start,energy_Ry=energy,gate='PASS'))
        (out/'performance.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(json.dumps(rows[-1]),flush=True)
