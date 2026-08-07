# Training Sheet: Enhanced SEIR Performance Clinic บน LANTA

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

หน้านี้เป็นแผ่นงานสำหรับผู้เรียนในห้องอบรม ผู้ใช้แปะคำสั่งทีละ block บน LANTA แล้วสร้าง data, source code, Slurm script, log และ result ได้ครบใน `$HOME/lanta-enhanced-seir` โดยสร้างทุกไฟล์จาก heredoc บน LANTA จากหน้าเดียว

เป้าหมายคือเปรียบเทียบ workflow เดียวกันสองทาง: C++/MPI บน CPU และ PyTorch GPU/DDP จากนั้นอ่านหลักฐานแบบ booklet หน้า 15-17 ได้แก่ คำถามวิทยาศาสตร์, resource ที่ขอ, runtime, memory, GPU evidence, output CSV และข้อสรุปของ run ถัดไป

## Copy-Paste จากเครื่อง Local

### ขั้นที่ 1: Login เข้า LANTA

block นี้เปิด shell บน LANTA login node

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

## Copy-Paste บน LANTA

### ขั้นที่ 1: เตรียม workspace และตัวแปร

block นี้สร้าง folder ของ practical และตั้งค่า account/partition สำหรับ job สั้น

```bash
mkdir -p "$HOME/lanta-enhanced-seir"
cd "$HOME/lanta-enhanced-seir"
mkdir -p cpp_mpi torch_ddp data jobs logs notes results src figures

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
pwd
```

### ขั้นที่ 2: สร้าง input data

block นี้สร้าง patch, contact matrix, mobility และ scenario table ที่ทั้ง MPI และ GPU ใช้ร่วมกัน

```bash
cat > data/patches.csv <<'CSV'
patch_id,name,pop_0_19,pop_20_39,pop_40_64,pop_65_plus,initial_exposed,initial_infectious
0,Campus,26000,42000,31000,9000,14,8
1,City,54000,78000,72000,28000,8,4
2,Rural,18000,23000,26000,17000,2,1
CSV

cat > data/age_contact_4x4.csv <<'CSV'
age_group,0_19,20_39,40_64,65_plus
0_19,8.2,2.6,1.4,0.6
20_39,2.1,7.4,3.2,1.0
40_64,1.0,3.0,6.1,1.9
65_plus,0.4,0.9,1.8,3.2
CSV

cat > data/mobility.csv <<'CSV'
from_patch,to_patch,weight
0,0,0.82
0,1,0.16
0,2,0.02
1,0,0.08
1,1,0.86
1,2,0.06
2,0,0.03
2,1,0.17
2,2,0.80
CSV

cat > data/scenarios.csv <<'CSV'
scenario_id,policy,beta_scale,mobility_scale,vaccination_rate,contact_reduction,days
101,baseline,1.00,0.35,0.0000,1.00,80
102,contact_reduction,1.00,0.35,0.0000,0.72,80
103,vaccination,1.00,0.35,0.0012,0.92,80
104,mobility_reduction,1.00,0.12,0.0000,0.95,80
105,combined,1.00,0.12,0.0012,0.68,80
106,high_transmission,1.18,0.35,0.0000,1.00,80
CSV

cat > data/notes.txt <<'TXT'
patches=Campus,City,Rural
age_groups=0_19,20_39,40_64,65_plus
model=SEIR-H-D with vaccination, mobility, age contact, hospitalization, deaths
TXT

ls -lh data/*.csv
sed -n '1,5p' data/patches.csv
```

### ขั้นที่ 3: สร้าง C++/MPI source ส่วนที่ 1

block นี้สร้าง header, data structure และ CSV parser ของ `cpp_mpi/seir_mpi_train.cpp`

```bash
cat > cpp_mpi/seir_mpi_train.cpp <<'CPP'
#include <mpi.h>
#include <array>
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>
struct Scenario{int id,days;std::string policy;double beta,mob,vacc,contact;};
struct Summary{int id,rank,days;char policy[32];double sec,pop,peakI,peakH,attack,deaths,recovered;};
std::vector<std::string> split(const std::string& line){
    std::vector<std::string> out;std::stringstream ss(line);std::string x;
    while(std::getline(ss,x,',')) out.push_back(x);return out;
}
std::vector<Scenario> read_scenarios(const std::string& path){
    std::ifstream in(path);std::string line;std::getline(in,line);std::vector<Scenario> rows;
    while(std::getline(in,line)){if(line.empty()) continue;auto r=split(line);
        rows.push_back({std::stoi(r[0]),std::stoi(r[6]),r[1],std::stod(r[2]),std::stod(r[3]),std::stod(r[4]),std::stod(r[5])});
    }return rows;
}
int ix(int patch,int age){return patch*4+age;}
CPP
```

### ขั้นที่ 4: เติม C++/MPI source ส่วนที่ 2

block นี้เติม kernel จำลอง SEIR-H-D ที่มี age contact, mobility, vaccination และ hospitalization

```bash
cat >> cpp_mpi/seir_mpi_train.cpp <<'CPP'
Summary run_one(const Scenario& sc,int rank){
    double t0=MPI_Wtime();const int P=3,A=4,C=12;
    double pop[P][A]={{26000,42000,31000,9000},{54000,78000,72000,28000},{18000,23000,26000,17000}};
    double contact[A][A]={{8.2,2.6,1.4,0.6},{2.1,7.4,3.2,1.0},{1.0,3.0,6.1,1.9},{0.4,0.9,1.8,3.2}};
    double mob[P][P]={{0.82,0.16,0.02},{0.08,0.86,0.06},{0.03,0.17,0.80}};
    double sus[A]={0.75,1.00,1.08,0.90},hosp[A]={0.006,0.014,0.045,0.135},fatal[A]={0.0003,0.001,0.008,0.045};
    std::vector<double>S(C),V(C),E(C),I(C),H(C),R(C),D(C),N(C);
    double e0[P]={14,8,2},i0[P]={8,4,1},total=0,peakI=0,peakH=0,cum=0;
    for(int p=0;p<P;p++){double ps=0;for(int a=0;a<A;a++)ps+=pop[p][a];
        for(int a=0;a<A;a++){int c=ix(p,a);double f=pop[p][a]/ps;E[c]=e0[p]*f;I[c]=i0[p]*f;S[c]=pop[p][a]-E[c]-I[c];N[c]=pop[p][a];total+=N[c];}}
    for(int day=0;day<sc.days;day++){
        std::vector<double>prev(C),nE(C),nV(C),nI(C),nH(C),nR(C),nD(C);
        for(int c=0;c<C;c++)prev[c]=(I[c]+0.2*H[c])/std::max(1.0,N[c]);
        for(int p=0;p<P;p++)for(int a=0;a<A;a++){double force=0;
            for(int b=0;b<A;b++){double mix=(1-sc.mob)*prev[ix(p,b)];
                for(int q=0;q<P;q++)mix+=sc.mob*mob[p][q]*prev[ix(q,b)];
                force+=contact[a][b]*mix;}
            int c=ix(p,a);double lambda=std::min(0.85,0.055*sc.beta*sc.contact*sus[a]*force);
            nE[c]=std::min(S[c],lambda*S[c])+std::min(V[c],0.38*lambda*V[c]);nV[c]=std::min(S[c]-std::min(S[c],lambda*S[c]),sc.vacc*S[c]);
        }
CPP
```

### ขั้นที่ 5: เติม C++/MPI source ส่วนที่ 3

block นี้เติม transition, MPI gather และการเขียน summary CSV

```bash
cat >> cpp_mpi/seir_mpi_train.cpp <<'CPP'
        for(int c=0;c<C;c++){int a=c%4;nI[c]=std::min(E[c],E[c]/3.0);nH[c]=std::min(I[c],hosp[a]*I[c]/5.0);
            nR[c]=std::min(I[c]-nH[c],0.14*I[c])+std::min(H[c],0.09*H[c]);nD[c]=std::min(H[c],fatal[a]*H[c]/12.0);}
        double nowI=0,nowH=0;for(int c=0;c<C;c++){S[c]=std::max(0.0,S[c]-nE[c]-nV[c]);V[c]+=nV[c];E[c]=std::max(0.0,E[c]+nE[c]-nI[c]);
            I[c]=std::max(0.0,I[c]+nI[c]-nH[c]-nR[c]);H[c]=std::max(0.0,H[c]+nH[c]-nD[c]-0.09*H[c]);R[c]+=nR[c];D[c]+=nD[c];
            N[c]=std::max(1.0,S[c]+V[c]+E[c]+I[c]+H[c]+R[c]);cum+=nE[c];nowI+=I[c];nowH+=H[c];}
        peakI=std::max(peakI,nowI);peakH=std::max(peakH,nowH);
    }
    Summary s{};s.id=sc.id;s.rank=rank;s.days=sc.days;std::strncpy(s.policy,sc.policy.c_str(),31);s.sec=MPI_Wtime()-t0;s.pop=total;s.peakI=peakI;s.peakH=peakH;
    s.attack=cum/total;s.deaths=std::accumulate(D.begin(),D.end(),0.0);s.recovered=std::accumulate(R.begin(),R.end(),0.0);return s;
}
int main(int argc,char**argv){MPI_Init(&argc,&argv);int rank,size;MPI_Comm_rank(MPI_COMM_WORLD,&rank);MPI_Comm_size(MPI_COMM_WORLD,&size);
    auto scenarios=read_scenarios("data/scenarios.csv");std::vector<Summary> local;for(int i=rank;i<(int)scenarios.size();i+=size)local.push_back(run_one(scenarios[i],rank));
    int bytes=local.size()*sizeof(Summary);std::vector<int>counts(size),disp(size);MPI_Gather(&bytes,1,MPI_INT,counts.data(),1,MPI_INT,0,MPI_COMM_WORLD);
    int total=0;if(rank==0){for(int i=0;i<size;i++){disp[i]=total;total+=counts[i];}}
    std::vector<Summary> all(total/sizeof(Summary));MPI_Gatherv(local.data(),bytes,MPI_BYTE,all.data(),counts.data(),disp.data(),MPI_BYTE,0,MPI_COMM_WORLD);
    if(rank==0){std::sort(all.begin(),all.end(),[](auto&a,auto&b){return a.id<b.id;});std::ofstream out("results/seir_mpi_summary.csv");
        out<<"scenario_id,policy,rank,days,elapsed_sec,total_population,peak_infectious,peak_hospitalized,attack_rate,final_deaths,final_recovered\n"<<std::fixed<<std::setprecision(6);
        for(auto&s:all)out<<s.id<<","<<s.policy<<","<<s.rank<<","<<s.days<<","<<s.sec<<","<<s.pop<<","<<s.peakI<<","<<s.peakH<<","<<s.attack<<","<<s.deaths<<","<<s.recovered<<"\n";
        std::cout<<"wrote results/seir_mpi_summary.csv rows="<<all.size()<<"\n";}
    MPI_Finalize();return 0;}
CPP
```

### ขั้นที่ 6: สร้าง Slurm script สำหรับ C++/MPI

block นี้สร้าง job ที่ compile ด้วย Cray C++ wrapper และรันด้วย `srun`

```bash
cat > jobs/seir_mpi_train.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=seir-mpi-train
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p notes results
module purge
module load cpeCray/25.03 2>/dev/null || true
module list 2> "notes/modules_${SLURM_JOB_ID}.txt"
CC -O3 -std=c++17 cpp_mpi/seir_mpi_train.cpp -o "results/seir_mpi_train_${SLURM_JOB_ID}"
/usr/bin/time -v srun -n "$SLURM_NTASKS" "results/seir_mpi_train_${SLURM_JOB_ID}"
cp results/seir_mpi_summary.csv "results/seir_mpi_summary_${SLURM_JOB_ID}.csv"
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode > "notes/sacct_${SLURM_JOB_ID}.txt"
SLURM
```

### ขั้นที่ 7: ส่ง C++/MPI job

block นี้ส่งงานและเก็บ job id ไว้ใช้เปรียบเทียบ

```bash
mpi_job=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/seir_mpi_train.sbatch)
echo "$mpi_job	seir_mpi_train	$(date -Is)" >> notes/job-history.tsv
echo "MPI job: $mpi_job"
squeue -j "$mpi_job"
```

### ขั้นที่ 8: อ่านผล C++/MPI job

block นี้อ่าน log, accounting และ summary CSV หลัง job จบ

```bash
squeue -j "$mpi_job"
sacct -j "$mpi_job" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
tail -80 "logs/seir-mpi-train_${mpi_job}.out"
sed -n '1,12p' "results/seir_mpi_summary_${mpi_job}.csv"
```

### ขั้นที่ 9: สร้าง PyTorch/DDP source ส่วนที่ 1

block นี้สร้าง import, scenario reader และ module buffers สำหรับ tensor SEIR-H-D

```bash
cat > torch_ddp/seir_torch_train.py <<'PY'
import argparse,csv,os,socket,time
from pathlib import Path
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP

def read_scenarios(path):
    rows=[]
    for r in csv.DictReader(open(path,encoding="utf-8")):
        rows.append({"id":int(r["scenario_id"]),"policy":r["policy"],"beta":float(r["beta_scale"]),"mob":float(r["mobility_scale"]),"vacc":float(r["vaccination_rate"]),"contact":float(r["contact_reduction"]),"days":int(r["days"])})
    return rows

class Kernel(nn.Module):
    def __init__(self):
        super().__init__()
        self.log_beta=nn.Parameter(torch.zeros(()))
        pop=torch.tensor([[26000,42000,31000,9000],[54000,78000,72000,28000],[18000,23000,26000,17000]],dtype=torch.float32)
        self.register_buffer("pop",pop)
        self.register_buffer("contact",torch.tensor([[8.2,2.6,1.4,0.6],[2.1,7.4,3.2,1.0],[1.0,3.0,6.1,1.9],[0.4,0.9,1.8,3.2]],dtype=torch.float32))
        self.register_buffer("mobility",torch.tensor([[0.82,0.16,0.02],[0.08,0.86,0.06],[0.03,0.17,0.80]],dtype=torch.float32))
        self.register_buffer("sus",torch.tensor([0.75,1.00,1.08,0.90]))
        self.register_buffer("hosp",torch.tensor([0.006,0.014,0.045,0.135]))
        self.register_buffer("fatal",torch.tensor([0.0003,0.001,0.008,0.045]))
PY
```

### ขั้นที่ 10: เติม PyTorch/DDP source ส่วนที่ 2

block นี้เติม forward pass แบบ batch scenario บน tensor device

```bash
cat >> torch_ddp/seir_torch_train.py <<'PY'
    def forward(self,x,max_days):
        b=x.shape[0];pop=self.pop.unsqueeze(0).repeat(b,1,1)
        s=pop.clone();v=torch.zeros_like(s);e=torch.zeros_like(s);i=torch.zeros_like(s);h=torch.zeros_like(s);r=torch.zeros_like(s);d=torch.zeros_like(s)
        frac=pop/pop.sum(2,keepdim=True)
        e=e+torch.tensor([14,8,2],device=x.device).view(1,3,1)*frac
        i=i+torch.tensor([8,4,1],device=x.device).view(1,3,1)*frac
        s=(s-e-i).clamp_min(0)
        beta=x[:,0].view(b,1,1);mob=x[:,1].view(b,1,1);vacc=x[:,2].view(b,1,1);contact_scale=x[:,3].view(b,1,1);days=x[:,4].view(b,1,1)
        peak_i=torch.zeros(b,device=x.device);peak_h=torch.zeros(b,device=x.device);cum=torch.zeros(b,device=x.device);total=pop.sum((1,2))
        for day in range(max_days):
            active=(days>day).float();prev=(i+0.2*h)/pop.clamp_min(1)
            imported=torch.einsum("pq,bqa->bpa",self.mobility,prev)
            mixed=(1-mob)*prev+mob*imported
            force=torch.einsum("ag,bpg->bpa",self.contact,mixed)
            lam=(0.055*self.log_beta.exp()*beta*contact_scale*force*self.sus).clamp(0,0.85)
            inf_s=(lam*s).minimum(s);inf_v=(0.38*lam*v).minimum(v);new_e=active*(inf_s+inf_v);new_v=active*(vacc*s).minimum((s-inf_s).clamp_min(0))
            new_i=active*(e/3).minimum(e);new_h=active*(self.hosp*i/5).minimum(i);new_r=active*((0.14*i).minimum((i-new_h).clamp_min(0))+(0.09*h).minimum(h))
            new_d=active*(self.fatal*h/12).minimum(h)
            s=(s-new_e-new_v).clamp_min(0);v=v+new_v;e=(e+new_e-new_i).clamp_min(0);i=(i+new_i-new_h-new_r).clamp_min(0)
            h=(h+new_h-new_d-0.09*h).clamp_min(0);r=r+new_r;d=d+new_d;pop=(s+v+e+i+h+r).clamp_min(1)
            cum=cum+new_e.sum((1,2));peak_i=torch.maximum(peak_i,i.sum((1,2)));peak_h=torch.maximum(peak_h,h.sum((1,2)))
        return torch.stack([total,peak_i,peak_h,cum/total,d.sum((1,2)),r.sum((1,2))],1)
PY
```

### ขั้นที่ 11: เติม PyTorch/DDP source ส่วนที่ 3

block นี้เติม distributed setup, scenario sharding และ CSV writer

```bash
cat >> torch_ddp/seir_torch_train.py <<'PY'
def setup(ddp):
    world=int(os.environ.get("WORLD_SIZE","1"));rank=int(os.environ.get("RANK","0"));local=int(os.environ.get("LOCAL_RANK","0"))
    if ddp and world>1:
        backend="nccl" if torch.cuda.is_available() else "gloo"
        if backend=="nccl": torch.cuda.set_device(local)
        dist.init_process_group(backend=backend,init_method="env://",rank=rank,world_size=world)
        return True,rank,world,local,backend
    return False,0,1,0,"single"
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--scenario-file",default="data/scenarios.csv");ap.add_argument("--out",default="results/seir_torch_summary.csv");ap.add_argument("--device",default="auto");ap.add_argument("--ddp",action="store_true");args=ap.parse_args()
    distributed,rank,world,local,backend=setup(args.ddp)
    device=torch.device(f"cuda:{local}" if (args.device=="cuda" or (args.device=="auto" and torch.cuda.is_available())) and torch.cuda.is_available() else "cpu")
    rows=read_scenarios(args.scenario_file);mine=rows[rank::world];model=Kernel().to(device)
    model=DDP(model,device_ids=[local] if distributed and device.type=="cuda" else None) if distributed else model
    x=torch.tensor([[r["beta"],r["mob"],r["vacc"],r["contact"],r["days"]] for r in mine],dtype=torch.float32,device=device)
    start=time.perf_counter()
    with torch.no_grad(): y=model(x,max([r["days"] for r in mine],default=0)).cpu()
    elapsed=time.perf_counter()-start;out=[]
    for r,v in zip(mine,y.tolist()):
        out.append({"scenario_id":r["id"],"policy":r["policy"],"rank":rank,"world_size":world,"device":str(device),"backend":backend,"elapsed_sec":f"{elapsed:.6f}","total_population":f"{v[0]:.3f}","peak_infectious":f"{v[1]:.6f}","peak_hospitalized":f"{v[2]:.6f}","attack_rate":f"{v[3]:.8f}","final_deaths":f"{v[4]:.6f}","final_recovered":f"{v[5]:.6f}","host":socket.gethostname()})
    if distributed:
        bag=[None]*world;dist.all_gather_object(bag,out);out=[x for part in bag for x in part];dist.destroy_process_group()
    if rank==0:
        out=sorted(out,key=lambda r:int(r["scenario_id"]));Path(args.out).parent.mkdir(exist_ok=True)
        with open(args.out,"w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
        print(f"wrote {args.out} rows={len(out)}")
if __name__=="__main__": main()
PY
```

### ขั้นที่ 12: สร้าง Slurm script สำหรับ PyTorch GPU/DDP

block นี้สร้าง job ที่ใช้ `torchrun` และ PyTorch environment ของ LANTA

```bash
cat > jobs/seir_torch_gpu.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=seir-gpu-train
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-node=1
#SBATCH --mem=12G
#SBATCH --time=00:12:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p notes results
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true
if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
    fi
fi
conda activate pytorch-2.2.2 2>/dev/null || true
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
module list 2> "notes/modules_${SLURM_JOB_ID}.txt"
nvidia-smi > "notes/nvidia-smi_${SLURM_JOB_ID}.txt"
/usr/bin/time -v torchrun --standalone --nproc_per_node=1 torch_ddp/seir_torch_train.py --ddp --device cuda --scenario-file data/scenarios.csv --out "results/seir_torch_summary_${SLURM_JOB_ID}.csv"
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode > "notes/sacct_${SLURM_JOB_ID}.txt"
SLURM
```

### ขั้นที่ 13: ส่ง PyTorch GPU job

block นี้ส่งงาน GPU และเก็บ job id ไว้ใช้เปรียบเทียบ

```bash
gpu_job=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_GPU_PARTITION" --parsable jobs/seir_torch_gpu.sbatch)
echo "$gpu_job	seir_torch_gpu	$(date -Is)" >> notes/job-history.tsv
echo "GPU job: $gpu_job"
squeue -j "$gpu_job"
```

### ขั้นที่ 14: อ่านผล PyTorch GPU job

block นี้อ่าน log, accounting, GPU evidence และ summary CSV หลัง job จบ

```bash
squeue -j "$gpu_job"
sacct -j "$gpu_job" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
tail -80 "logs/seir-gpu-train_${gpu_job}.out"
sed -n '1,20p' "notes/nvidia-smi_${gpu_job}.txt"
sed -n '1,12p' "results/seir_torch_summary_${gpu_job}.csv"
```

### ขั้นที่ 15: สร้าง script สรุป performance

block นี้สร้าง script ที่รวม summary ของ MPI และ GPU เป็นตารางเดียว

```bash
cat > src/compare_perf.py <<'PY'
import csv
from pathlib import Path

def read(path, engine):
    rows=[]
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["engine"]=engine
            rows.append(row)
    return rows

root=Path("results")
mpi=sorted(root.glob("seir_mpi_summary_*.csv"))[-1]
gpu=sorted(root.glob("seir_torch_summary_*.csv"))[-1]
rows=read(mpi,"C++/MPI")+read(gpu,"PyTorch/GPU")
out=root/"seir_perf_compare.csv"
fields=["engine","scenario_id","policy","rank","elapsed_sec","peak_infectious","peak_hospitalized","attack_rate","final_deaths"]
with out.open("w", newline="", encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k,"") for k in fields})
print(out)
print("engine,scenario,policy,elapsed_sec,peak_infectious,attack_rate")
for row in rows:
    print(f"{row['engine']},{row['scenario_id']},{row['policy']},{row['elapsed_sec']},{row['peak_infectious']},{row['attack_rate']}")
PY
```

### ขั้นที่ 16: ดูผลเปรียบเทียบ

block นี้สร้างตารางเปรียบเทียบและเปิดดูหลักฐานทั้งหมดที่ควรส่งท้าย lab

```bash
module purge
module load cray-python/3.10.10 2>/dev/null || module load cray-python 2>/dev/null || true
PYTHON_BIN="$(command -v python || command -v python3)"
"$PYTHON_BIN" src/compare_perf.py
sed -n '1,20p' results/seir_perf_compare.csv
cat notes/job-history.tsv
ls -lh logs notes results | sed -n '1,80p'
```

## วิธีอ่านผล

ผลที่ใช้สอนได้ควรตอบได้ห้าข้อ

1. job ทั้งสองจบ `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `attack_rate` อยู่ในช่วง `0` ถึง `1`
3. policy `combined` ลด `peak_infectious` เมื่อเทียบกับ `baseline`
4. C++/MPI ใช้ CPU หลาย rank เพื่อแบ่ง scenario ensemble
5. PyTorch/GPU มีค่า startup overhead จาก `torchrun` และ GPU allocation ที่มองเห็นจาก `nvidia-smi`

## คำถามสะท้อนผล

- ถ้าเพิ่ม scenario จาก 6 เป็น 600 งาน CPU/MPI หรือ GPU/DDP ควรเปลี่ยนอย่างไร
- ควรเปลี่ยน resource ทีละปัจจัยใดก่อน เช่น `--ntasks`, `--gpus-per-node`, จำนวนวัน หรือจำนวน scenario
- หลักฐานใดบอกว่าคอขวดอยู่ที่ scheduler startup, CPU compute, GPU launch, memory หรือ I/O
