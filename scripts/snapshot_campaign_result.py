"""Save bounded text/image outputs per job without copying credentials."""
import hashlib
import json
import re
import sys
from pathlib import Path

target, workspace = map(Path, sys.argv[1:])
allowed = {'.json', '.csv', '.tsv', '.txt', '.png', '.svg', '.ipynb'}
rows = []
for folder in ('results', 'figures'):
    for path in sorted((workspace/folder).rglob('*')):
        if not path.is_file() or path.is_symlink() or path.suffix not in allowed:
            continue
        size = path.stat().st_size
        if size > 2_000_000:
            rows.append({'path':str(path.relative_to(workspace)), 'bytes':size, 'archived':False})
            continue
        raw = path.read_bytes()
        if path.suffix != '.png':
            raw = re.sub(r'(?i)(token[= :]+)[a-z0-9_-]{16,}', r'\1REDACTED', raw.decode('utf-8', errors='replace')).encode()
        out = target/path.relative_to(workspace)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        rows.append({'path':str(path.relative_to(workspace)), 'bytes':size, 'archived':True, 'sha256':hashlib.sha256(raw).hexdigest()})
(target/'outputs.json').write_text(json.dumps(rows, indent=2)+'\n')
