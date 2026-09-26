"""Render fresh campaign evidence without replacing historical measurements."""
import csv
import html
import json
import os
from pathlib import Path
import re
import tarfile

from build_tutorial_evidence import excerpts, matching_workflows, slug, evidence_table

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'docs/lanta-runs/2026-09-26-performance'
START, END = '<!-- performance-rerun:start -->', '<!-- performance-rerun:end -->'
STYLE = '''<style>body{font:17px system-ui;background:#f0f4f8;color:#172e40;margin:36px auto;max-width:1180px;padding:24px}h1{font-size:32px}h2{margin-top:30px}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td,th{padding:10px;border:1px solid #c4d1dc;text-align:left}pre{white-space:pre-wrap;background:#122d42;color:#edf5fa;padding:20px;font-size:13px;overflow-wrap:anywhere}.note{padding:18px;background:#fff3ce}.flow{padding:18px;background:#d8ece6}a{color:#065cad}</style>'''


def table(rows):
    headings = ['Job', 'State', 'Elements', 'Elapsed sum (s)', 'CPU used (s)', 'Reserved CPU-h', 'CPU efficiency %', 'Max sampled task RSS (MiB)']
    body = '<table><tr>'+''.join('<th>'+x+'</th>' for x in headings)+'</tr>'
    for r in rows:
        values = [r['job_id'], r['states'], r['tasks'], r['elapsed_task_seconds'], r['total_cpu_seconds'], r['allocated_cpu_hours'], r['cpu_efficiency_percent'], round(r['max_step_rss_kib']/1024, 2) or 'not sampled']
        body += '<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in values)+'</tr>'
    return body+'</table>'


def main():
    rows = json.loads((DEST/'workflow-status.json').read_text())
    accounting = list(csv.DictReader((DEST/'accounting.psv').open(), delimiter='|'))
    allocations = [r for r in accounting if '.' not in r['JobID']]
    cpu_h = sum(int(r['AllocCPUS'])*int(r['ElapsedRaw'])/3600 for r in allocations)
    gpu_h = 0
    for r in allocations:
        found = re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)', r['AllocTRES'])
        if found:
            gpu_h += int(found[1])*int(r['ElapsedRaw'])/3600
    summary = {'workflow_count':len(rows), 'latest_states':{s:sum(r['states']==s for r in rows) for s in sorted({r['states'] for r in rows})},
               'all_attempt_allocation_records':len(allocations), 'all_attempt_reserved_cpu_hours':cpu_h,
               'all_attempt_reserved_gpu_hours':gpu_h,
               'note':'Includes failed attempts. Resource-hours are not billed SHr. One tutorial campaign repetition, not statistical scaling of every tutorial.'}
    (DEST/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    pages = []
    with tarfile.open(DEST/'artifacts.tar.gz') as archive:
        for section in ('foundation','core-hpc','ai-applications','domain-science','lanta-experience','mini-innovation'):
            for path in sorted((ROOT/section).rglob('*.md')):
                relative = str(path.relative_to(ROOT))
                selected = matching_workflows(relative, rows)
                if not selected:
                    continue
                name = slug(relative)
                body = f'<h1>{html.escape(relative)}</h1><p>Fresh LANTA rerun · pv915002 · 26 September 2026</p>'
                body += '<p class="flow">Estimate → allocate → run → measure → validate → resize and repeat</p>'
                body += table(selected)
                body += '<p class="note">Elapsed sum adds array elements, not array makespan. CPU used is process time; reserved CPU-hours use actual AllocCPUS. MaxRSS is a sampled task/step maximum, not total node RAM. Completion alone is not scientific validation. Short runs include startup/import overhead.</p>'
                for sample in excerpts(archive, selected):
                    display = '\n'.join(line.rstrip() for line in sample['text'].splitlines())
                    body += '<h2>Recorded output · job '+html.escape(sample['job'])+'</h2><pre>'+html.escape(display)+'</pre>'
                body += '<p>Full accounting, bounded outputs, GNU time files and available 1-second GPU telemetry are retained in the campaign archive. Missing GPU samples are not zero utilization. No node energy measurement is inferred.</p>'
                (DEST/(name+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>LANTA run evidence</title>'+STYLE+body)
                pages.append({'page':relative, 'html':name+'.html', 'screenshot':name+'.png'})
                link = os.path.relpath(DEST/'README.md', path.parent)
                screenshot = os.path.relpath(DEST/(name+'.png'), path.parent)
                panel = '\n'.join([START, '## Fresh measured rerun — 26 September 2026', '',
                    evidence_table(selected), '',
                    'These are new measured jobs, not estimates. One campaign pass does not establish scaling or runtime variance. Allocated CPU-hours are not billed SHr; sampled RSS is not total node memory.', '',
                    f'[Accounting, output archive and measurement limitations]({link})', '',
                    f'![Browser capture of fresh measured accounting and recorded output]({screenshot})', END])
                text = path.read_text()
                if START in text:
                    text = re.sub(re.escape(START)+r'.*?'+re.escape(END), lambda _:panel, text, flags=re.S)
                else:
                    text += '\n'+panel+'\n'
                path.write_text(text)
    (DEST/'pages.json').write_text(json.dumps(pages,indent=2)+'\n')
    overview = '<h1>LANTA tutorial performance campaign</h1><p>pv915002 · 26 September 2026 · measured results</p>'
    overview += '<p class="flow">Estimate resources → bounded Slurm jobs → timing + accounting + GPU samples → correctness checks → preserve outputs → optimize</p>'
    overview += '<pre>'+html.escape(json.dumps(summary,indent=2))+'</pre>'
    overview += '<p class="note">Existing runnable tutorials were rerun. New application catalogs remain proposals unless explicitly listed as executed. Preflight jobs do not constitute full scientific experiments.</p>'
    overview += '<h2>Per-tutorial evidence</h2><ul>'+''.join(f'<li><a href="{p["html"]}">{html.escape(p["page"])}</a></li>' for p in pages)+'</ul>'
    (DEST/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>LANTA performance campaign</title>'+STYLE+overview)
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
