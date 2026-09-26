import json
import sys
from pathlib import Path
import torch
import warp as wp
out=Path(sys.argv[2])
assert torch.cuda.is_available()
x=torch.arange(1024,device='cuda',dtype=torch.float32)
assert float((x*x).sum())>0
wp.init()
from physicsnemo.models.fno import FNO
from physicsnemo.datapipes.benchmarks.darcy import Darcy2D
pipe=Darcy2D(resolution=32,batch_size=2,device='cuda')
batch=next(iter(pipe))
net=FNO(in_channels=1,out_channels=1,dimension=2,latent_channels=16,num_fno_layers=2,num_fno_modes=8).cuda()
prediction=net(batch['permeability'])
loss=((prediction-batch['darcy'])**2).mean()
loss.backward(); torch.cuda.synchronize()
result={'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'gpu':torch.cuda.get_device_name(),'loss':float(loss.detach()),'gate':'PASS'}
assert torch.isfinite(loss)
(out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
