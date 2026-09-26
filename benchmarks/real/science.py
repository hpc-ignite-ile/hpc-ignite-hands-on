"""Complete bounded public-data/scientific workflows, with explicit gates."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

experiment, root, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
records = []


def save(record):
    records.append(record)
    (out/'performance.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(record),flush=True)


if experiment == 'astropy':
    from astropy.io import fits
    from astropy.wcs import WCS
    filename = root/'inputs/HorseHead.fits'
    digest = hashlib.sha256(filename.read_bytes()).hexdigest()
    for repeat in range(3):
        start = time.perf_counter()
        with fits.open(filename,memmap=True) as hdus:
            raw = hdus[0].data.astype(np.float64)
            header = hdus[0].header.copy()
        io_s = time.perf_counter()-start
        start = time.perf_counter()
        values = raw[np.isfinite(raw)]
        full = [len(values),float(values.sum()),float((values*values).sum())]
        full_s = time.perf_counter()-start
        start = time.perf_counter()
        parts = []
        for tile in np.array_split(raw,16,axis=0):
            v=tile[np.isfinite(tile)]
            parts.append([len(v),v.sum(),(v*v).sum()])
        tiled=np.sum(parts,axis=0)
        tile_s=time.perf_counter()-start
        assert np.allclose(full,tiled,rtol=1e-12)
        wcs=WCS(header)
        pixels=np.array([[100.,100.],[400.,400.],[700.,700.]])
        error=float(np.max(np.abs(wcs.all_world2pix(wcs.all_pix2world(pixels,0),0)-pixels)))
        assert error < 1e-3
        save(dict(repeat=repeat,input_sha256=digest,shape=list(raw.shape),pixels=len(values),mean=float(values.mean()),std=float(values.std()),io_s=io_s,full_s=full_s,tiled_s=tile_s,wcs_roundtrip_px=error,gate='PASS'))
    fig=plt.figure(figsize=(9,6)); ax=fig.add_subplot(projection=wcs)
    ax.imshow(raw,origin='lower',cmap='gray',vmin=np.percentile(values,5),vmax=np.percentile(values,99))
    ax.set(xlabel='Right ascension',ylabel='Declination',title='Horsehead Nebula · actual FITS data')
    fig.savefig(out/'horsehead.png',dpi=140)
    header.totextfile(out/'original-header.txt',overwrite=True)

elif experiment == 'sunpy':
    import sunpy.map
    import astropy.units as u
    filename=root/'inputs/AIA171-real.fits'
    for repeat in range(3):
        start=time.perf_counter()
        solar=sunpy.map.Map(filename)
        x=np.array([200,512,800])*u.pixel; y=np.array([200,512,800])*u.pixel
        world=solar.pixel_to_world(x,y); back=solar.world_to_pixel(world)
        error=float(max(np.max(np.abs(back.x.to_value(u.pixel)-x.value)),np.max(np.abs(back.y.to_value(u.pixel)-y.value))))
        assert error<1e-3
        assert int(solar.meta.get('quality',0))==0
        exposure=solar.exposure_time.to_value(u.s); assert exposure>0
        array=np.asarray(solar.data,dtype=float)/exposure
        region=array[400:624,400:624]; values=region[np.isfinite(region)]
        assert len(values)==224*224
        save(dict(repeat=repeat,date=str(solar.date),wavelength=str(solar.wavelength),exposure_s=exposure,
                  region_pixel_bounds=[400,624,400,624],region_mean_DN_per_s=float(values.mean()),
                  wcs_roundtrip_px=error,elapsed_s=time.perf_counter()-start,gate='PASS'))
    fig=plt.figure(figsize=(8,7)); ax=fig.add_subplot(projection=solar)
    solar.plot(axes=ax); solar.draw_grid(axes=ax)
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((400,400),224,224,fill=False,edgecolor='cyan'))
    fig.savefig(out/'solar-observation.png',dpi=140)

elif experiment == 'rebound':
    import rebound
    def make(integrator):
        sim=rebound.Simulation(); sim.units=('yr','AU','Msun')
        sim.add(m=1); sim.add(m=1e-3,a=1,e=0.05); sim.add(m=3e-4,a=2.5,e=0.03)
        sim.move_to_com(); sim.integrator=integrator
        return sim
    reference=make('ias15'); period=reference.particles[1].P
    reference.integrate(100*period)
    ref=np.array([[p.x,p.y,p.z] for p in reference.particles])
    for denominator in (20,40,80):
        for repeat in range(3):
            sim=make('whfast'); sim.dt=period/denominator
            energy=sim.energy(); angular=np.array(sim.angular_momentum())
            history=[]; start=time.perf_counter()
            for t in np.linspace(0,100*period,501):
                sim.integrate(t,exact_finish_time=0)
                history.append([sim.t,float(abs((sim.energy()-energy)/energy)),sim.particles[1].x,sim.particles[1].y])
            elapsed=time.perf_counter()-start
            # Compare at exactly the achieved WHFast time, not a mismatched endpoint.
            target=make('ias15'); target.integrate(sim.t)
            err=float(np.max(np.abs(np.array([[p.x,p.y,p.z] for p in sim.particles])-np.array([[p.x,p.y,p.z] for p in target.particles]))))
            max_energy=max(r[1] for r in history)
            angular_error=float(np.linalg.norm(np.array(sim.angular_momentum())-angular)/np.linalg.norm(angular))
            assert max_energy < 1e-4 and angular_error < 1e-10 and err < .02
            save(dict(steps_per_inner_orbit=denominator,repeat=repeat,orbits=100,elapsed_s=elapsed,max_relative_energy_error=max_energy,relative_angular_momentum_error=angular_error,max_position_error_AU=err,gate='PASS'))
            np.savetxt(out/f'orbit-d{denominator}-r{repeat}.csv',history,delimiter=',',header='time_yr,relative_energy_error,x_AU,y_AU')
            if repeat==0: plt.semilogy(np.array(history)[:,0],np.maximum(np.array(history)[:,1],1e-18),label=f'P/{denominator}')
    plt.legend(); plt.xlabel('Time (yr)'); plt.ylabel('Relative energy error'); plt.savefig(out/'orbit-error.png',dpi=140)
    (out/'initial-conditions.json').write_text(json.dumps({'units':['yr','AU','Msun'],'bodies':[{'m':1},{'m':1e-3,'a':1,'e':.05},{'m':3e-4,'a':2.5,'e':.03}],'note':'Explicit benchmark system, not an observed exoplanet system.'},indent=2))

elif experiment == 'climlab':
    import climlab
    for latitudes in (90,180):
        temperatures={}
        for forcing in (0,4):
            model=climlab.EBM(num_lat=latitudes)
            model.subprocess['LW'].A -= forcing
            start=time.perf_counter(); history=[]
            previous=float(model.global_mean_temperature())
            for year in range(1,301):
                model.integrate_years(1,verbose=False)
                mean=float(model.global_mean_temperature())
                imbalance=float(climlab.global_mean(model.ASR-model.OLR))
                history.append([year,mean,imbalance])
                if abs(imbalance)<.01 and abs(mean-previous)<.001: break
                previous=mean
            assert abs(imbalance)<.01 and np.isfinite(model.Ts).all(), 'Climate equilibrium not reached'
            temperatures[forcing]=mean
            save(dict(latitudes=latitudes,forcing_W_m2=forcing,years=year,elapsed_s=time.perf_counter()-start,global_temperature_C=mean,toa_imbalance_W_m2=imbalance,gate='PASS'))
            np.savetxt(out/f'ebm-lat{latitudes}-forcing{forcing}.csv',history,delimiter=',',header='year,temperature_C,imbalance_W_m2')
            plt.plot(model.lat,np.asarray(model.Ts).squeeze(),label=f'{latitudes} lat, +{forcing} W/m²')
        assert temperatures[4] > temperatures[0]
    plt.legend(); plt.xlabel('Latitude'); plt.ylabel('Equilibrium temperature (°C)'); plt.savefig(out/'climate-equilibrium.png',dpi=140)

elif experiment == 'scanpy':
    import scanpy as sc
    from sklearn.metrics import adjusted_rand_score
    labels=[]
    for repeat in range(3):
        start=time.perf_counter(); stages={}
        def stage(name):
            stages[name]=time.perf_counter()-start
        ad=sc.read_10x_mtx(root/'inputs/filtered_gene_bc_matrices/hg19',var_names='gene_symbols',cache=False)
        ad.var_names_make_unique(); assert ad.shape==(2700,32738)
        stage('read_cumulative_s')
        sc.pp.filter_cells(ad,min_genes=200); sc.pp.filter_genes(ad,min_cells=3)
        ad.var['mt']=ad.var_names.str.startswith('MT-')
        sc.pp.calculate_qc_metrics(ad,qc_vars=['mt'],percent_top=None,log1p=False,inplace=True)
        ad=ad[(ad.obs.n_genes_by_counts<2500)&(ad.obs.pct_counts_mt<5),:].copy()
        assert ad.n_obs==2638
        sc.pp.normalize_total(ad,target_sum=1e4); sc.pp.log1p(ad); ad.raw=ad
        sc.pp.highly_variable_genes(ad,min_mean=.0125,max_mean=3,min_disp=.5,flavor='seurat')
        ad=ad[:,ad.var.highly_variable].copy()
        sc.pp.regress_out(ad,['total_counts','pct_counts_mt'],n_jobs=1)
        sc.pp.scale(ad,max_value=10); sc.tl.pca(ad,svd_solver='arpack',random_state=0)
        stage('preprocess_pca_cumulative_s')
        sc.pp.neighbors(ad,n_neighbors=10,n_pcs=40,random_state=0)
        sc.tl.umap(ad,random_state=0)
        sc.tl.leiden(ad,flavor='igraph',n_iterations=2,random_state=0)
        sc.tl.rank_genes_groups(ad,'leiden',method='wilcoxon')
        assert np.isfinite(ad.obsm['X_pca']).all() and np.isfinite(ad.obsm['X_umap']).all()
        labels.append(ad.obs.leiden.to_numpy())
        ari=adjusted_rand_score(labels[0],labels[-1]); assert ari==1
        stage('complete_cumulative_s')
        save(dict(repeat=repeat,cells=ad.n_obs,highly_variable_genes=ad.n_vars,clusters=len(ad.obs.leiden.cat.categories),seeded_repeat_ARI=ari,stages=stages,gate='PASS'))
        ad.write_h5ad(out/f'pbmc3k-repeat{repeat}.h5ad')
        if repeat==0:
            sc.pl.umap(ad,color=['leiden','MS4A1','LYZ'],show=False)
            plt.savefig(out/'pbmc3k-umap-markers.png',dpi=140,bbox_inches='tight')
else:
    raise ValueError(experiment)
