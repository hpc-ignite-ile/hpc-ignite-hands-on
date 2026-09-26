"""Retain the 62x62x15 tutorial grid while changing decomposition or duration."""
from pathlib import Path
import re
import sys
p=Path(sys.argv[1]); text=p.read_text()
if sys.argv[2]=='4':
    for key,value in {'nSx':1,'nSy':1,'nPx':2,'nPy':2}.items():
        text=re.sub(r'(\b'+key+r'\s*=)\s*\d+',r'\g<1> '+str(value),text)
elif sys.argv[2]=='run':
    text=re.sub(r'(?m)^ endTime=.*', ' endTime=2592000.,',text)
    text=re.sub(r'(?m)^ dumpFreq=.*',' dumpFreq=2592000.,',text)
    text=re.sub(r'(?m)^ monitorFreq=.*',' monitorFreq=86400.,',text)
    pkg=p.parent/'data.pkg'
    pkg.write_text(re.sub(r'(?i)(useMNC\s*=)\s*\.TRUE\.',r'\1.FALSE.',pkg.read_text()))
p.write_text(text)
