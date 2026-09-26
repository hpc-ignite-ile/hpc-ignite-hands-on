"""Full-size PhysicsNeMo Darcy FNO benchmark with fixed held-out validation.

Architecture and training defaults follow NVIDIA's Apache-2.0 darcy_fno example:
256², batch 64, 256 pseudo-epochs, 2048 fresh PDE samples per pseudo-epoch.
This adapter adds explicit seeds, stage timing and physical relative-L2 checks.
"""
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch
from physicsnemo.models.fno import FNO
from physicsnemo.datapipes.benchmarks.darcy import Darcy2D
import matplotlib.pyplot as plt

root,out=map(Path,sys.argv[1:]); torch.set_num_threads(8)
assert torch.cuda.is_available()
resolution=256; batch_size=64; epochs=int(os.environ.get('EPOCHS','256'))
repeats=int(os.environ.get('REPEATS','3'))
norm={'permeability':(1.25,.75),'darcy':(.0452,.0279)}
np.random.seed(2026); torch.manual_seed(2026)
start=time.perf_counter(); pipe=Darcy2D(resolution=resolution,batch_size=batch_size,normaliser=norm)
validation=[]
for _,batch in zip(range(4),pipe):
    validation.append({k:v.clone() for k,v in batch.items()})
torch.cuda.synchronize(); setup=time.perf_counter()-start
(out/'protocol.json').write_text(json.dumps({'resolution':resolution,'batch_size':batch_size,'epochs':epochs,'samples_per_epoch':2048,'repeats':repeats,'validation_samples':256,'validation_seed':2026,'training_seed':42,'normalisation':norm,'validation_generation_s':setup},indent=2))
completed=[]
for repeat in range(repeats):
    run=out/f'repeat-{repeat}'; run.mkdir()
    np.random.seed(42); torch.manual_seed(42)
    model=FNO(in_channels=1,out_channels=1,decoder_layers=1,decoder_layer_size=32,
              dimension=2,latent_channels=32,num_fno_layers=4,num_fno_modes=12,padding=9).cuda()
    optimizer=torch.optim.Adam(model.parameters(),lr=1e-3)
    scheduler=torch.optim.lr_scheduler.ExponentialLR(optimizer,gamma=.85)
    training=iter(Darcy2D(resolution=resolution,batch_size=batch_size,normaliser=norm))
    history=[]; started=time.perf_counter(); torch.cuda.reset_peak_memory_stats()
    for epoch in range(1,epochs+1):
        model.train(); loss_sum=0.; data_s=0.; train_s=0.
        for step in range(32):
            tick=time.perf_counter(); batch=next(training); torch.cuda.synchronize(); data_s+=time.perf_counter()-tick
            tick=time.perf_counter(); optimizer.zero_grad(set_to_none=True)
            prediction=model(batch['permeability']); loss=torch.nn.functional.mse_loss(prediction,batch['darcy'])
            assert torch.isfinite(loss); loss.backward(); optimizer.step(); torch.cuda.synchronize()
            train_s+=time.perf_counter()-tick; loss_sum+=float(loss.detach())
        record={'epoch':epoch,'training_mse':loss_sum/32,'data_generation_s':data_s,'training_s':train_s,'samples_per_s':2048/(data_s+train_s)}
        if epoch%4==0 or epoch==epochs:
            model.eval(); errors=[]
            with torch.no_grad():
                for val in validation:
                    pred=model(val['permeability'])*.0279+.0452; target=val['darcy']*.0279+.0452
                    errors.extend((torch.linalg.vector_norm((pred-target).flatten(1),dim=1)/torch.linalg.vector_norm(target.flatten(1),dim=1)).cpu().tolist())
            record['validation_relative_L2']=float(np.mean(errors))
        history.append(record); (run/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        print(json.dumps({'repeat':repeat,**record}),flush=True)
        if epoch%8==0: scheduler.step()
        if epoch%32==0: torch.save({'epoch':epoch,'model':model.state_dict(),'optimizer':optimizer.state_dict()},run/'checkpoint.pt')
    final_error=history[-1]['validation_relative_L2']
    if epochs>=256:
        assert final_error<.25 and history[-1]['training_mse']<history[0]['training_mse'], 'Full training accuracy gate failed'
    completed.append({'repeat':repeat,'epochs':epochs,'samples':epochs*2048,'elapsed_s':time.perf_counter()-started,'validation_relative_L2':final_error,'peak_VRAM_bytes':torch.cuda.max_memory_allocated(),'gate':'PASS' if epochs>=256 else 'TIMING PILOT ONLY'})
    (out/'performance.json').write_text(json.dumps(completed,indent=2)+'\n')
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,field,title in zip(axes,[target[0,0],pred[0,0],(pred-target)[0,0]],['Held-out PDE solution','FNO prediction','Prediction error']):
        im=ax.imshow(field.detach().cpu(),origin='lower'); ax.set_title(title); fig.colorbar(im,ax=ax)
    fig.tight_layout(); fig.savefig(run/'prediction.png',dpi=140); plt.close(fig)
    del model,optimizer,training
