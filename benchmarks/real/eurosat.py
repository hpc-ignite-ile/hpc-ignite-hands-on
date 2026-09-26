"""Full 27,000-chip RGB land-cover benchmark, not a calibrated crop-yield model.

TorchGeo's pinned EuroSAT mirror; dataset attribution/terms retained in report.
The fixed stratified random split does not establish geographic generalization.
"""
import json
from pathlib import Path
import sys
import time
import numpy as np
import torch
from torchvision import datasets, transforms, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt

root,out=map(Path,sys.argv[1:]); torch.set_num_threads(8)
assert torch.cuda.is_available()
dataset=datasets.ImageFolder(root/'inputs/eurosat/2750',transform=transforms.Compose([
    transforms.ToTensor(),transforms.Normalize((.485,.456,.406),(.229,.224,.225))]))
assert len(dataset)==27000 and len(dataset.classes)==10
train,val=train_test_split(np.arange(len(dataset)),test_size=.2,stratify=dataset.targets,random_state=0)
(out/'split.json').write_text(json.dumps({'train':train.tolist(),'validation':val.tolist(),'classes':dataset.classes,'split_warning':'Random chip split; spatial leakage not excluded.'}))
records=[]
for batch in (64,128):
    for repeat in range(3):
        seed=42+repeat; torch.manual_seed(seed); np.random.seed(seed)
        model=models.resnet18(weights=None,num_classes=10).cuda()
        model.conv1=torch.nn.Conv2d(3,64,kernel_size=3,stride=1,padding=1,bias=False).cuda()
        model.maxpool=torch.nn.Identity()
        optimizer=torch.optim.Adam(model.parameters(),lr=1e-3)
        loader=torch.utils.data.DataLoader(torch.utils.data.Subset(dataset,train),batch_size=batch,shuffle=True,num_workers=4,pin_memory=True,persistent_workers=True,generator=torch.Generator().manual_seed(seed))
        validation=torch.utils.data.DataLoader(torch.utils.data.Subset(dataset,val),batch_size=256,num_workers=4,pin_memory=True,persistent_workers=True)
        history=[]; torch.cuda.reset_peak_memory_stats(); start=time.perf_counter()
        for epoch in range(10):
            model.train(); loss_total=0.; count=0; tick=time.perf_counter()
            for x,y in loader:
                x,y=x.cuda(non_blocking=True),y.cuda(non_blocking=True)
                optimizer.zero_grad(set_to_none=True); prediction=model(x)
                loss=torch.nn.functional.cross_entropy(prediction,y)
                assert torch.isfinite(loss)
                loss.backward(); optimizer.step()
                loss_total+=loss.item()*len(y); count+=len(y)
            torch.cuda.synchronize(); train_s=time.perf_counter()-tick
            model.eval(); truth=[]; predicted=[]
            with torch.no_grad():
                for x,y in validation:
                    predicted.extend(model(x.cuda(non_blocking=True)).argmax(1).cpu().tolist()); truth.extend(y.tolist())
            accuracy=float(np.mean(np.array(truth)==predicted))
            history.append(dict(epoch=epoch+1,loss=loss_total/count,accuracy=accuracy,train_s=train_s,images_per_second=count/train_s))
            print(json.dumps({'batch':batch,'repeat':repeat,**history[-1]}),flush=True)
        assert history[-1]['loss']<history[0]['loss'] and accuracy>.6, 'Learning/validation gate failed'
        run=out/f'b{batch}-r{repeat}'; run.mkdir()
        (run/'history.json').write_text(json.dumps(history,indent=2))
        (run/'class-metrics.json').write_text(json.dumps(classification_report(truth,predicted,target_names=dataset.classes,output_dict=True),indent=2))
        matrix=confusion_matrix(truth,predicted); np.savetxt(run/'confusion.csv',matrix,delimiter=',',fmt='%d')
        torch.save(model.state_dict(),run/'model.pt')
        records.append(dict(batch=batch,repeat=repeat,seed=seed,epochs=10,training_images=len(train),validation_images=len(val),accuracy=accuracy,elapsed_s=time.perf_counter()-start,peak_allocated_VRAM_bytes=torch.cuda.max_memory_allocated(),gate='PASS'))
        (out/'performance.json').write_text(json.dumps(records,indent=2)+'\n')
        fig,ax=plt.subplots(figsize=(9,8)); im=ax.imshow(matrix); fig.colorbar(im,ax=ax)
        ax.set_xticks(range(10),dataset.classes,rotation=80); ax.set_yticks(range(10),dataset.classes)
        ax.set(xlabel='Predicted',ylabel='Reference',title=f'EuroSAT RGB · batch {batch}, seed {seed}')
        fig.savefig(run/'confusion.png',dpi=130,bbox_inches='tight'); plt.close(fig)
        del loader,validation,model,optimizer
