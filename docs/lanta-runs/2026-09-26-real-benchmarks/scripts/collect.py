"""Collect bounded evidence and accounting without copying large scientific data."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(sys.argv[1]).resolve()
dest=root/'evidence'; dest.mkdir(exist_ok=True)
receipts=[json.loads(s) for s in (root/'submissions.jsonl').read_text().splitlines()]
ids=[r['job_id'] for r in receipts if r.get('job_id')]
fields='JobID,JobName%60,Account,Partition,State,ExitCode,Elapsed,ElapsedRaw,TotalCPU,AllocCPUS,ReqMem,AllocTRES%160,MaxRSS,MaxVMSize,NodeList,Submit,Start,End'
accounting=subprocess.run(['sacct','-j',','.join(ids),'-P','-o',fields],text=True,capture_output=True,check=True).stdout
(dest/'accounting.psv').write_text(accounting)
shutil.copy2(root/'submissions.jsonl',dest)
if (root/'validation.json').exists(): shutil.copy2(root/'validation.json',dest)
commits={p.name:subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (root/'sources').iterdir() if (p/'.git').exists()}
inputs={}
for p in (root/'inputs').iterdir():
    if p.is_file():
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
        inputs[p.name]={'bytes':p.stat().st_size,'sha256':h.hexdigest()}
(dest/'provenance.json').write_text(json.dumps({'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(root),'source_commits':commits,'inputs':inputs},indent=2)+'\n')
inventory=[]
for directory in ('results','logs','provenance','scripts','slurm'):
    for p in sorted((root/directory).rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root); size=p.stat().st_size
        # Native grids, models, source/build trees and core dumps remain on LANTA.
        allowed=p.suffix in ('.json','.jsonl','.csv','.txt','.out','.err','.log','.png','.xvg','.sbatch','.py')
        copy=allowed and size<4_000_000 and 'build' not in rel.parts and p.name!='input-dump.txt'
        inventory.append({'path':str(rel),'bytes':size,'copied':copy})
        if copy:
            target=dest/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
(dest/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
rows=list(csv.DictReader(accounting.splitlines(),delimiter='|'))
jobs=[r for r in rows if '.' not in r['JobID']]
cpu_hours=sum(int(r['AllocCPUS'])*int(r['ElapsedRaw'])/3600 for r in jobs)
summary={'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':len(jobs),'states':{s:sum(r['State']==s for r in jobs) for s in sorted({r['State'] for r in jobs})},'reserved_cpu_hours_including_running_elapsed':cpu_hours,'note':'Allocated CPU-hours are not ThaiSC billed SHr. MaxRSS is a sampled per-task high-water mark; see step records, not just allocation rows.'}
(dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
