"""Scientific gates for complete atmosphere, ocean and shock benchmarks."""
import json
from pathlib import Path
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

root=Path(sys.argv[1]); results={}

def sod(x,t=.25,g=1.4):
    dl,pl,ul,dr,pr,ur=1.,1.,0.,.125,.1,0.
    al=np.sqrt(g*pl/dl); ar=np.sqrt(g*pr/dr)
    def f(p,d,pk,a):
        return (p-pk)*np.sqrt(2/((g+1)*d)/(p+(g-1)/(g+1)*pk)) if p>pk else 2*a/(g-1)*((p/pk)**((g-1)/(2*g))-1)
    p=brentq(lambda p:f(p,dl,pl,al)+f(p,dr,pr,ar),.1,1)
    u=.5*(f(p,dr,pr,ar)-f(p,dl,pl,al))
    sl=-al; st=u-al*(p/pl)**((g-1)/(2*g)); sr=ar*np.sqrt((g+1)/(2*g)*p/pr+(g-1)/(2*g))
    xi=x/t; density=np.full_like(x,dr)
    density[xi<sl]=dl
    fan=(xi>=sl)&(xi<st); a=2/(g+1)*(al-(g-1)/2*xi[fan])
    density[fan]=dl*(a/al)**(2/(g-1))
    density[(xi>=st)&(xi<u)]=dl*(p/pl)**(1/g)
    density[(xi>=u)&(xi<sr)]=dr*((p/pr+(g-1)/(g+1))/((g-1)/(g+1)*p/pr+1))
    return density

for folder in sorted((root/'results').glob('athena-*')):
    runs=list(folder.glob('sod-*/Sod.block*.out1.00025.tab'))
    if len(runs)<10: continue
    records=[]; errors=[]
    for n in (128,256,512):
        baseline=None
        for p in (1,2,4):
            for r in (1,2,3):
                path=folder/f'sod-n{n}-p{p}-r{r}'
                parts=[np.loadtxt(f) for f in path.glob('Sod.block*.out1.00025.tab')]
                if not parts: raise ValueError(f'Missing numerical output: {path}')
                data=np.concatenate(parts); data=data[np.argsort(data[:,1])]
                assert len(data)==n and np.isfinite(data).all() and (data[:,2:4]>0).all()
                if baseline is None: baseline=data
                assert np.allclose(data,baseline,rtol=1e-10,atol=1e-12)
                error=float(np.mean(np.abs(data[:,2]-sod(data[:,1]))))
                assert error<.02
                records.append(dict(n=n,ranks=p,repeat=r,density_L1=error,rank_repeat_equal=True))
        errors.append(error)
        plt.plot(data[:,1],data[:,2],label=str(n))
    assert errors[2]<errors[1]<errors[0]
    x=np.linspace(-.5,.5,2000); plt.plot(x,sod(x),'k--',label='Exact Sod solution'); plt.legend()
    plt.xlabel('x'); plt.ylabel('Density'); plt.savefig(folder/'sod-reference.png',dpi=140); plt.close()
    results[folder.name]={'gate':'PASS','runs':records,'note':'Global assembled fields; upstream per-block shock-errors.dat is not used as global accuracy evidence.'}

from netCDF4 import Dataset
for folder in sorted((root/'results').glob('miniweather-*')):
    if len(list(folder.glob('*/output.nc')))!=36: continue
    records=[]
    for spec in ('THERMAL','DENSITY_CURRENT'):
        for n in (200,400):
            reference=None
            for p in (1,2,4):
                for r in (1,2,3):
                    run=folder/f'{spec}-n{n}-p{p}-r{r}'
                    with Dataset(run/'output.nc') as ds:
                        fields={k:np.asarray(v[-1]) for k,v in ds.variables.items() if v.ndim==3}
                    assert fields and all(np.isfinite(v).all() for v in fields.values())
                    if reference is None: reference=fields
                    assert all(np.allclose(v,reference[k],rtol=1e-9,atol=1e-10) for k,v in fields.items())
                    log=(run/'solver.log').read_text()
                    mass=float(re.findall(r'd_mass:\s+(\S+)',log)[-1]); energy=float(re.findall(r'd_te:\s+(\S+)',log)[-1])
                    assert abs(mass)<1e-10 and abs(energy)<1e-2
                    records.append(dict(case=spec,nx=n,ranks=p,repeat=r,mass_relative_change=mass,energy_relative_change=energy,fields_equal=True))
            key=next(k for k in reference if 'theta' in k)
            plt.imshow(reference[key],origin='lower',aspect='auto'); plt.colorbar(); plt.title(f'{spec} {n}×{n//2}, t=1000 s')
            plt.savefig(folder/f'{spec}-{n}-theta.png',dpi=140); plt.close()
    results[folder.name]={'gate':'PASS','runs':records}

from MITgcmutils import rdmds
for folder in sorted((root/'results').glob('mitgcm-*')):
    if not (folder/'gyre-p4-r3').exists(): continue
    records=[]; reference=None
    for p in (1,4):
        for r in (1,2,3):
            run=folder/f'gyre-p{p}-r{r}'
            fields={k:rdmds(str(run/k),2160) for k in ('T','U','V','Eta')}
            assert all(v.size and np.isfinite(v).all() for v in fields.values())
            if reference is None: reference=fields
            errors={k:float(np.max(np.abs(v-reference[k]))) for k,v in fields.items()}
            assert all(np.allclose(v,reference[k],rtol=1e-6,atol=1e-7) for k,v in fields.items()),errors
            records.append(dict(ranks=p,repeat=r,max_absolute_difference=errors,model_days=30))
    plt.imshow(reference['Eta'],origin='lower'); plt.colorbar(label='Sea-surface height (m)')
    plt.title('MITgcm baroclinic gyre, day 30 (not equilibrated)'); plt.savefig(folder/'gyre-ssh.png',dpi=140); plt.close()
    results[folder.name]={'gate':'PASS','runs':records,'note':'Finite fields and decomposition/repeat agreement; no equilibrium or closed tracer-budget claim.'}
(root/'validation.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:v['gate'] for k,v in results.items()}))
