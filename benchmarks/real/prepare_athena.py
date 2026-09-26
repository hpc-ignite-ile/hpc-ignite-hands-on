from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
dest.write_text(source.read_text()+'\n<meshblock>\nnx1 = 32\nnx2 = 1\nnx3 = 1\n')
