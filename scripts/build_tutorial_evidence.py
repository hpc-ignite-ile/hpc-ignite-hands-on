#!/usr/bin/env python3
"""Regenerate marked learning panels and HTML from immutable archived evidence.

No jobs are submitted. No measured values or screenshots are synthesized.
Browser screenshots are captured separately from the generated HTML.
"""
import csv
import hashlib
import html
import json
import os
import re
import tarfile
from pathlib import Path

from tutorial_resource_profiles import PROFILES, profile_for, booklet_for

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'docs/lanta-runs/2026-09-26-pv915002'
OUT = ROOT / 'docs/tutorial-evidence'
START, END = '<!-- resource-learning:start -->', '<!-- resource-learning:end -->'
ROOTS = ('foundation', 'core-hpc', 'ai-applications', 'domain-science', 'lanta-experience', 'mini-innovation')


def slug(path):
    return re.sub(r'[^a-zA-Z0-9]+', '-', str(path).removesuffix('.md')).strip('-').lower()


def allocation_rows(accounting, job):
    return [r for r in accounting if '.' not in r['JobID'] and
            (r['JobID'] == job or r['JobID'].startswith(job + '_'))]


def matching_workflows(path, rows):
    direct = [r for r in rows if r['workflow'].startswith('tutorial:' + path + ':')]
    if direct:
        return direct
    if path.endswith('/README.md'):
        prefix = 'repo:' + path.removesuffix('README.md')
        return [r for r in rows if r['workflow'].startswith(prefix)]
    return []


def excerpts(archive, rows):
    """Only job-ID-associated logs, never guess an unversioned result's job."""
    selected = []
    for row in rows:
        job = row['job_id']
        pattern = re.compile(r'(?<!\d)' + re.escape(job) + r'(?!\d)')
        matches = [m for m in archive.getmembers() if m.isfile() and
                   pattern.search(m.name) and '/logs/' in m.name and
                   (m.name.endswith('.out') or m.name.endswith('.out.excerpt.txt'))]
        # For arrays, show one element, explicitly labelled, rather than duplicate pages.
        for member in sorted(matches, key=lambda m: m.name)[:1]:
            raw = archive.extractfile(member).read()
            text = raw.decode('utf-8', errors='replace')
            text = re.sub(r'(?i)(token[= :]+)[a-z0-9_-]{16,}', r'\1REDACTED', text)
            lines = text.splitlines()
            excerpt = '\n'.join(lines if len(lines) <= 18 else lines[:8] + ['[... excerpt; full log in archive ...]'] + lines[-8:])
            selected.append({'job': job, 'member': member.name,
                             'sha256': hashlib.sha256(raw).hexdigest(), 'text': excerpt})
    return selected


def evidence_table(rows):
    lines = ['| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |',
             '|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        rss = f"{r['max_step_rss_kib']/1024:.2f}" if r['max_step_rss_kib'] else 'not recorded'
        lines.append(f"| {r['job_id']} | {r['states']} | {r['tasks']} | {r['elapsed_task_seconds']} | {r['total_cpu_seconds']:.3f} | {r['allocated_cpu_hours']:.6f} | {rss} |")
    return '\n'.join(lines)


def build_html(path, topic, rows, accounting, samples):
    esc = html.escape
    body = [f'<p class="eyebrow">LANTA · pv915002 · archived runs 2026-09-26</p><h1>{esc(path)}</h1>',
            '<p class="notice">Evidence viewer — captured after the run from archived accounting and logs. '
            'Not a live terminal, not a new rerun, and not an illustration of expected numbers.</p>',
            f'<p>{esc(PROFILES[topic][0])}</p>']
    if not rows:
        body.append('<h2>No page-specific Slurm record</h2><p>This setup/reading page has no matched job in the archived campaign. '
                    'No usage or output is invented. Follow the linked exercise and collect a new record.</p>')
    for row in rows:
        body.append(f'<section><h2>Job {esc(row["job_id"])} · {esc(row["states"])}</h2>')
        body.append(f'<p class="workflow">{esc(row["workflow"])}</p><div class="metrics">')
        metrics = [('Elapsed sum', f'{row["elapsed_task_seconds"]} s'),
                   ('CPU actually used', f'{row["total_cpu_seconds"]:.3f} s'),
                   ('CPU reserved', f'{row["allocated_cpu_hours"]:.6f} h'),
                   ('CPU efficiency', f'{row["cpu_efficiency_percent"]}%'),
                   ('Max step/task RSS', f'{row["max_step_rss_kib"]/1024:.2f} MiB' if row['max_step_rss_kib'] else 'not recorded')]
        body.extend(f'<div><small>{esc(k)}</small><strong>{esc(v)}</strong></div>' for k, v in metrics)
        body.append('</div><table><tr><th>Allocation/array element</th><th>Partition</th><th>CPUs</th><th>ReqMem</th><th>AllocTRES</th></tr>')
        for a in allocation_rows(accounting, row['job_id']):
            body.append('<tr>' + ''.join(f'<td>{esc(a[k])}</td>' for k in ('JobID', 'Partition', 'AllocCPUS', 'ReqMem', 'AllocTRES')) + '</tr>')
        body.append('</table></section>')
    body.append('<p class="footnote">Elapsed sum adds array-element runtimes; it is not array makespan. '
                'CPU-hours are reserved capacity, not billed SHr. MaxRSS is a sampled task/step maximum, not summed node RAM. '
                'GPU utilization/peak VRAM and energy were not systematically recorded in this campaign.</p>')
    for sample in samples:
        body.append(f'<h2>Recorded output excerpt · {esc(sample["job"])}</h2><p class="workflow">'
                    f'{esc(sample["member"])}</p><pre>{esc(sample["text"])}</pre>')
    if rows and not samples:
        body.append('<p>No job-ID-associated stdout excerpt was found; accounting is available, but output is not fabricated.</p>')
    if topic == 'twinb':
        body.append('<p class="notice">Later reference-building runs are documented separately: '
                    '<a href="../TWINB_REFERENCE_BENCHMARKS.md">EnergyPlus + Mesa benchmarks</a>. '
                    'These do not retroactively turn the failed student-geometry jobs above into successes.</p>')
    body.append('<p>Source: <a href="../lanta-runs/2026-09-26-pv915002/accounting.psv">raw accounting</a> · '
                '<a href="../lanta-runs/2026-09-26-pv915002/artifacts.tar.gz">archived logs/results</a> · '
                '<a href="../RESOURCE_ESTIMATION_WORKBOOK.md">interpretation and next-run worksheet</a></p>')
    css = '''body{font:16px/1.5 system-ui,sans-serif;background:#edf2f7;color:#162838;margin:0;padding:32px}
main{max-width:1150px;margin:auto;background:white;padding:32px;border-top:8px solid #147d92;border-radius:12px}
h1{font-size:26px;overflow-wrap:anywhere}h2{font-size:21px;margin-bottom:8px}.eyebrow{color:#12657a;font-weight:700}
.notice{padding:14px;background:#fff4d6;border-left:4px solid #b88715}.metrics{display:flex;flex-wrap:wrap;gap:12px}
.metrics div{background:#e8f3f6;padding:12px;min-width:150px;border-radius:8px}small,strong{display:block}strong{font-size:23px}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:16px}td,th{padding:8px;border-bottom:1px solid #ccd8df;text-align:left;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#142838;color:#e7f8ed;padding:18px;font:13px/1.6 monospace}
.workflow,.footnote{font-size:13px;overflow-wrap:anywhere;color:#425b6a}a{color:#075d91}section{margin:24px 0}'''
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>LANTA archived run evidence</title><style>' + css + '</style><main>' + '\n'.join(body) + '</main></html>\n'


def panel(path, topic, rows, samples):
    here = (ROOT/path).parent
    rel = lambda p: os.path.relpath(ROOT/p, here)
    ident = slug(path)
    pages, illustration = booklet_for(topic)
    scope, estimate, experiment, gate = PROFILES[topic]
    text = [START, '## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab', '',
            f'Booklet flow: pages **{pages}** of the [LANTA handbook]({rel("docs/lanta-hpc-experience-handbook.pdf")}). '
            f'[Full learning sequence and worksheet]({rel("docs/RESOURCE_ESTIMATION_WORKBOOK.md")}).', '',
            f'<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>\n\n'
            f'![Booklet workflow: {topic}]({rel("docs/images/booklet/"+illustration)})\n\n'
            f'Original booklet illustration, not a run screenshot. [Source and limitations]({rel("docs/images/booklet/README.md")}).\n\n</details>', '',
            '### 1. ขอบเขตและการประมาณก่อนรัน', '', scope, '', estimate, '',
            '### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output', '',
            'Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.', '']
    if rows:
        text += [evidence_table(rows), '',
                 'Elapsed is summed across array elements, not array makespan. CPU used is `TotalCPU`; reserved CPU-hours include idle allocation time. '
                 'MaxRSS is the largest sampled task/step value, **not total node RAM**. Missing GPU/energy telemetry must not be interpreted as zero.', '',
                 f'![Screenshot of archived job accounting and stdout]({rel("docs/images/run-evidence/"+ident+".png")})', '',
                 f'Browser screenshot of the [archived evidence viewer]({rel("docs/tutorial-evidence/"+ident+".html")}); not a live terminal capture. '
                 'Open the viewer for exact requested/allocated resources and job-specific log excerpts.']
        first = rows[0]
        if first['elapsed_task_seconds']:
            busy = first['total_cpu_seconds'] / first['elapsed_task_seconds']
            text += ['', f'**Read the numbers:** job `{first["job_id"]}` used {first["total_cpu_seconds"]:.3f} CPU-seconds '
                     f'over {first["elapsed_task_seconds"]} summed elapsed seconds: about **{busy:.2f} busy CPU cores per running element on average**. '
                     'This describes CPU work across the whole allocation, including setup; it does not measure GPU utilization. '
                     'For a seconds-long run, startup and coarse memory sampling can dominate. Do not reduce RAM to the displayed RSS or claim scaling without a longer pilot.']
        if samples:
            text += ['', '<details><summary>ตัวอย่าง output ที่บันทึกจริง / archived stdout excerpt</summary>', '',
                     f'Job `{samples[0]["job"]}` · archive member `{samples[0]["member"]}`', '',
                     '```text', '\n'.join(line.rstrip() for line in samples[0]['text'].splitlines()), '```', '', '</details>']
    else:
        text += ['No page-specific Slurm run is recorded for this setup/reading page. Do not invent usage numbers or a successful-run screenshot. '
                 'Collect evidence from the next executable lesson using the worksheet.']
    text += ['', '### 3. ขยายงานทีละแกนและตรวจความถูกต้อง', '', experiment, '', '**Correctness gate:** ' + gate, '',
             f'[Public applications and research-backed experiments]({rel("docs/REAL_APPLICATION_EXPERIMENTS.md")}#{application_anchor(topic)}) '
             'provide the next workload. Proposed resource budgets there are not measured requirements.', '',
             'Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. '
             'Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. '
             'Use three repeats and report spread; do not claim speedup from one short smoke run.', '']
    if topic == 'twinb':
        text += [f'**Newer real coupled evidence:** [reference-building tutorial]({rel("docs/TWINB_REFERENCE_BENCHMARKS.md")}) '
                 f'and [measured benchmark results]({rel("docs/lanta-runs/2026-09-26-twinb-benchmarks/README.md")}). '
                 'Keep these separate from the original student-model failures and synthetic examples above.', '']
        text += ['The later one-day qualification reserved four CPUs for 117 seconds (job `6339929`) versus one CPU for 113 seconds '
                 '(job `6339935`). Reserved capacity was therefore 0.1300 versus 0.0314 CPU-hours for these observed jobs; '
                 'the [comparison checks](' + rel('docs/lanta-runs/2026-09-26-twinb-benchmarks/resource-comparison.json') + ') '
                 'found equal timestep outputs and seeded trace hashes. This is evidence of avoidable over-allocation, not a reliable 3.5% speedup claim from single job timings.', '',
                 f'![Actual five-zone EnergyPlus and Mesa traces]({rel("docs/lanta-runs/2026-09-26-twinb-benchmarks/6339935-fivezone-actual-traces.png")})', '',
                 'Actual benchmark-output plot, job `6339935`; not a booklet illustration. The school case retains documented warnings, '
                 'and the reference buildings are not calibrated models of the student building.', '']
    return '\n'.join(text + [END, ''])


def application_anchor(topic):
    if topic == 'twinb': return 'energyplus-mesa'
    if topic in {'md', 'chemistry'}: return 'molecular-simulation'
    if topic == 'qe': return 'quantum-espresso'
    if topic in {'gpu', 'training', 'lora', 'prompts'}: return 'nvidia-and-ai'
    if topic in {'raster', 'weather'}: return 'earth-observation'
    if topic == 'bio': return 'bioinformatics'
    if topic in {'stream', 'dask', 'spark'}: return 'data-analytics'
    if topic == 'agents': return 'agent-models'
    return 'miniweather'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads((CAMPAIGN/'workflow-status.json').read_text())
    with (CAMPAIGN/'accounting.psv').open() as f:
        accounting = list(csv.DictReader(f, delimiter='|'))
    paths = sorted(str(p.relative_to(ROOT)) for root in ROOTS for p in (ROOT/root).rglob('*.md'))
    manifest = []
    with tarfile.open(CAMPAIGN/'artifacts.tar.gz') as archive:
        for path in paths:
            topic = profile_for(path)
            matched = matching_workflows(path, rows)
            samples = excerpts(archive, matched)
            ident = slug(path)
            (OUT/(ident+'.html')).write_text(build_html(path, topic, matched, accounting, samples))
            file = ROOT/path
            original = file.read_text()
            block = panel(path, topic, matched, samples)
            if START in original:
                updated = re.sub(re.escape(START)+'.*?'+re.escape(END)+'\n?', lambda _: block, original, flags=re.S)
            else:
                # Put the learning plan before copy/paste instructions so budgeting is not an afterthought.
                heading, separator, rest = original.partition('\n')
                updated = heading + '\n\n' + block + '\n' + rest.lstrip('\n')
            file.write_text(updated)
            manifest.append({'page':path, 'profile':topic, 'jobs':[r['job_id'] for r in matched],
                             'html':ident+'.html', 'screenshot':ident+'.png' if matched else None,
                             'excerpts':[{k:v for k,v in e.items() if k != 'text'} for e in samples]})
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    index = ['# Tutorial evidence index', '', 'Generated from archived 2026-09-26 accounting. No new jobs submitted.', '',
             '| Tutorial | Topic | Job records | Evidence |', '|---|---|---:|---|']
    index += [f'| [{m["page"]}](../../{m["page"]}) | {m["profile"]} | {len(m["jobs"])} | [viewer]({m["html"]}) |' for m in manifest]
    (OUT/'README.md').write_text('\n'.join(index)+'\n')
    print(f'Enhanced {len(paths)} pages; {sum(bool(m["jobs"]) for m in manifest)} have matched archived jobs.')


if __name__ == '__main__':
    main()
