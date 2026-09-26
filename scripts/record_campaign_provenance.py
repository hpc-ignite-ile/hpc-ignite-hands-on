"""Record source and host provenance without storing credentials or full environments."""
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination', type=Path)
parser.add_argument('--source', type=Path)
args = parser.parse_args()
args.destination.mkdir(parents=True, exist_ok=True)
record = {'host': platform.node(), 'python': platform.python_version()}
if args.source:
    def git(*command):
        return subprocess.check_output(['git','-C',str(args.source),*command])
    record.update({'source':str(args.source),'commit':git('rev-parse','HEAD').decode().strip(),
                   'status':git('status','--short').decode(),
                   'tracked_diff_sha256':hashlib.sha256(git('diff','--binary')).hexdigest(),
                   'source_hashes':{str(p.relative_to(args.source)):hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in args.source.rglob('*.py') if '.git' not in p.parts and '__pycache__' not in p.parts}})
else:
    for label, command in {'balance':['bash','-lc','sbalance | awk \'NR < 4 || $1 == "pv915002"\''],
                           'queue':['squeue','-A','pv915002'], 'filesystem':['df','-Th',str(args.destination)]}.items():
        result = subprocess.run(command,capture_output=True,text=True)
        record[label] = {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
(args.destination/('source-provenance.json' if args.source else 'host-provenance.json')).write_text(json.dumps(record,indent=2)+'\n')
