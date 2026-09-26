"""Prepare a one-day integration smoke in a disposable Twin-B snapshot, not the source repo.

Requires eppy/PyYAML and ENERGYPLUS_HOME. This does not validate synchronization
of the existing asynchronous feedback loop; it only bounds the integration run.
"""
import argparse
import csv
import os
from pathlib import Path
import yaml
from eppy.modeleditor import IDF

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('snapshot', type=Path)
args = parser.parse_args()
root = args.snapshot.resolve()
manifest = root/'innovation/generated/heatlab_sweep/manifest.tsv'
with manifest.open() as handle:
    row = next(csv.DictReader(handle, delimiter='\t'))
out = root/'innovation/generated/day-smoke'
out.mkdir(exist_ok=True)
IDF.setiddname(str(Path(os.environ['ENERGYPLUS_HOME'])/'Energy+.idd'))
idf = IDF(row['idf'])
assert len(idf.idfobjects['RUNPERIOD']) == 1, 'Review multiple run periods manually'
period = idf.idfobjects['RUNPERIOD'][0]
period.End_Month = period.Begin_Month
period.End_Day_of_Month = period.Begin_Day_of_Month
period.End_Year = period.Begin_Year
idf.saveas(str(out/'day.idf'))
config = yaml.safe_load(Path(row['config']).read_text())
config['mesa']['steps'] = 24 * int(idf.idfobjects['TIMESTEP'][0].Number_of_Timesteps_per_Hour)
(out/'config.yaml').write_text(yaml.safe_dump(config))
row.update(config=str(out/'config.yaml'), idf=str(out/'day.idf'), output_dir=str(out/'energyplus'))
with (out/'manifest.tsv').open('w') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(row), delimiter='\t')
    writer.writeheader()
    writer.writerow(row)
main = root/'main.py'
text = main.read_text().replace('ep_args = ["-d",', 'ep_args = ["-x", "-d",')
marker = '        def ep_agent_callback(state):\n'
guard = '            if ep_model.exchange.warmup_flag(state):\n                return\n'
assert marker in text, 'Unexpected Twin-B callback layout'
if marker + guard not in text:
    text = text.replace(marker, marker + guard, 1)
text = text.replace('zone_temps = callback_queue.get()', 'zone_temps = callback_queue.get(timeout=60)')
main.write_text(text)
print(out/'manifest.tsv')
print('scope=one-day integration only; asynchronous coupling requires separate scientific validation')
