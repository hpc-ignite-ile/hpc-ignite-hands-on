"""Package bounded, token-redacted campaign evidence and accounting summaries."""
import argparse
import csv
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path


def seconds(value):
    days, _, value = value.rpartition('-') if '-' in value else ('0', '', value)
    parts = [float(p) for p in value.split(':')]
    return int(days) * 86400 + sum(p * 60**i for i, p in enumerate(reversed(parts)))


def rss_kib(value):
    match = re.fullmatch(r'([\d.]+)([KMGT]?)', value or '0')
    return float(match[1]) * {'': 1/1024, 'K': 1, 'M': 1024, 'G': 1024**2, 'T': 1024**3}[match[2]] if match else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    root, dest = args.root.resolve(), args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    receipts = [json.loads(s) for s in (root/'submissions.jsonl').read_text().splitlines()]
    accounting = list(csv.DictReader((root/'accounting.psv').open(), delimiter='|'))
    latest = {row['workflow']: row for row in receipts}
    summary = []
    for workflow, receipt in sorted(latest.items()):
        job = receipt['job_id']
        rows = [r for r in accounting if job and (r['JobID'] == job or r['JobID'].startswith(job+'_')) and '.' not in r['JobID']]
        steps = [r for r in accounting if job and (r['JobID'].startswith(job+'.') or r['JobID'].startswith(job+'_')) and '.' in r['JobID']]
        elapsed = sum(int(r['ElapsedRaw']) for r in rows)
        capacity = sum(int(r['ElapsedRaw'])*int(r['AllocCPUS']) for r in rows)
        cpu = sum(seconds(r['TotalCPU']) for r in rows)
        summary.append({'workflow':workflow, 'job_id':job, 'states':','.join(sorted({r['State'] for r in rows})) or 'NO_ACCOUNTING',
            'exit_codes':','.join(sorted({r['ExitCode'] for r in rows})), 'tasks':len(rows),
            'elapsed_task_seconds':elapsed, 'total_cpu_seconds':round(cpu,3),
            'cpu_efficiency_percent':round(100*cpu/capacity,2) if capacity else None,
            'max_step_rss_kib':round(max((rss_kib(r['MaxRSS']) for r in steps),default=0),2),
            'allocated_cpu_hours':round(capacity/3600,6)})
    (dest/'workflow-status.json').write_text(json.dumps(summary,indent=2)+'\n')
    table = ['# Latest workflow accounting', '', 'Slurm completion is not scientific validation. See README.md for scope and exceptions.', '',
             '| Workflow | Job | State | Task-seconds | Total CPU s | Sampled max RSS KiB |', '|---|---:|---|---:|---:|---:|']
    table += [f"| {r['workflow']} | {r['job_id']} | {r['states']} | {r['elapsed_task_seconds']} | {r['total_cpu_seconds']} | {r['max_step_rss_kib']} |" for r in summary]
    (dest/'WORKFLOWS.md').write_text('\n'.join(table)+'\n')
    (dest/'accounting.psv').write_bytes((root/'accounting.psv').read_bytes())
    (dest/'submissions.jsonl').write_bytes((root/'submissions.jsonl').read_bytes())
    roots = [root/'notes',root/'tutorials',root/'repo/logs',root/'repo/results',root/'repo/foundation/chapter-00',
             root/'repo/mini-innovation/enhanced-seir',root/'repo/mini-innovation/weather-health-abs',
             root/'twinb/logs',root/'twinb/results',root/'twinb/notes',root/'twinb/mesa_out_result',root/'twinb/innovation/generated',root/'cadc',
             root/'repo/notes',root/'benchmarks',root/'cfd']
    suffixes = {'.out','.err','.txt','.log','.csv','.tsv','.json','.png','.svg','.md','.ipynb','.sha256'}
    candidates = set()
    for folder in roots:
        for path in folder.rglob('*'):
            if path.is_file() and not path.is_symlink() and path.suffix in suffixes and '__pycache__' not in path.parts:
                rel = path.relative_to(root)
                if any(p in rel.parts for p in ('logs','results','notes','figures','notebooks','mesa_out_result','manifest','energyplus','data')):
                    candidates.add(path)
    inventory = []
    with tarfile.open(dest/'artifacts.tar.gz','w:gz') as archive:
        for path in sorted(candidates):
            rel = str(path.relative_to(root))
            size = path.stat().st_size
            if size > 2_000_000:
                digest = hashlib.sha256()
                with path.open('rb') as handle:
                    for block in iter(lambda: handle.read(1024*1024), b''):
                        digest.update(block)
                inventory.append({'path':rel,'bytes':size,'sha256':digest.hexdigest(),'archived':False,'reason':'larger than 2 MB; retained on LANTA'})
                if path.suffix in {'.out','.err','.log'}:
                    with path.open('rb') as handle:
                        head = handle.read(32768)
                        handle.seek(-32768,2)
                        tail = handle.read()
                    text = (head+b'\n[...middle omitted; full-file SHA256 in inventory...]\n'+tail).decode('utf-8',errors='replace')
                    data = re.sub(r'(?i)(token[= :]+)[a-z0-9]{16,}',r'\1REDACTED',text).encode()
                    info = tarfile.TarInfo(rel+'.excerpt.txt')
                    info.size = len(data)
                    info.mode = 0o644
                    archive.addfile(info,io.BytesIO(data))
                continue
            data = path.read_bytes()
            if path.suffix != '.png':
                text = data.decode('utf-8',errors='replace')
                text = re.sub(r'(?i)(token[= :]+)[a-z0-9]{16,}',r'\1REDACTED',text)
                data = text.encode()
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info,io.BytesIO(data))
            inventory.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'archived':True})
    (dest/'artifact-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps({'workflows':len(summary),'states':{state:sum(r['states']==state for r in summary) for state in sorted({r['states'] for r in summary})},'artifacts':len(inventory)},indent=2))


if __name__ == '__main__':
    main()
