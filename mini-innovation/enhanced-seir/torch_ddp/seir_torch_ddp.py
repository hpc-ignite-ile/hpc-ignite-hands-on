#!/usr/bin/env python3
"""GPU-ready age/spatial SEIR-H-D scenario engine using PyTorch distributed execution."""

from __future__ import annotations

import argparse
import csv
import os
import socket
import time
from pathlib import Path
from typing import Iterable

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP


AGE_COLUMNS = ["pop_0_19", "pop_20_39", "pop_40_64", "pop_65_plus"]
AGE_COUNT = 4


def read_patches(path: Path):
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    population = []
    initial_e = []
    initial_i = []
    for row in rows:
        population.append([float(row[col]) for col in AGE_COLUMNS])
        initial_e.append(float(row["initial_exposed"]))
        initial_i.append(float(row["initial_infectious"]))
    return population, initial_e, initial_i


def read_contact(path: Path):
    rows = list(csv.reader(path.open(encoding="utf-8")))
    return [[float(value) for value in row[1:]] for row in rows[1:]]


def read_mobility(path: Path, patch_count: int):
    matrix = [[0.0 for _ in range(patch_count)] for _ in range(patch_count)]
    for row in csv.DictReader(path.open(encoding="utf-8")):
        src = int(row["from_patch"])
        dst = int(row["to_patch"])
        matrix[src][dst] = float(row["weight"])
    for src, row in enumerate(matrix):
        total = sum(row)
        if total <= 0.0:
            matrix[src][src] = 1.0
        else:
            matrix[src] = [value / total for value in row]
    return matrix


def read_scenarios(path: Path):
    scenarios = []
    for row in csv.DictReader(path.open(encoding="utf-8")):
        scenarios.append(
            {
                "scenario_id": int(row["scenario_id"]),
                "policy": row["policy"],
                "beta_scale": float(row["beta_scale"]),
                "mobility_scale": float(row["mobility_scale"]),
                "vaccination_rate": float(row["vaccination_rate"]),
                "contact_reduction": float(row["contact_reduction"]),
                "days": int(row["days"]),
            }
        )
    return scenarios


class SEIRKernel(nn.Module):
    def __init__(self, population, initial_e, initial_i, contact, mobility):
        super().__init__()
        pop = torch.tensor(population, dtype=torch.float32)
        patch_total = pop.sum(dim=1, keepdim=True).clamp_min(1.0)
        init_e = torch.tensor(initial_e, dtype=torch.float32).unsqueeze(1) * pop / patch_total
        init_i = torch.tensor(initial_i, dtype=torch.float32).unsqueeze(1) * pop / patch_total
        self.register_buffer("population", pop)
        self.register_buffer("initial_e", init_e)
        self.register_buffer("initial_i", init_i)
        self.register_buffer("contact", torch.tensor(contact, dtype=torch.float32))
        self.register_buffer("mobility", torch.tensor(mobility, dtype=torch.float32))
        self.register_buffer("susceptibility", torch.tensor([0.75, 1.00, 1.08, 0.90], dtype=torch.float32))
        self.register_buffer("asymptomatic_prob", torch.tensor([0.42, 0.34, 0.26, 0.20], dtype=torch.float32))
        self.register_buffer("hospital_prob", torch.tensor([0.006, 0.014, 0.045, 0.135], dtype=torch.float32))
        self.register_buffer("fatality_prob", torch.tensor([0.0003, 0.0010, 0.0080, 0.0450], dtype=torch.float32))
        self.log_beta_adjust = nn.Parameter(torch.zeros(()))

    def forward(self, scenario_tensor: torch.Tensor, max_days: int):
        batch = scenario_tensor.shape[0]
        pop = self.population.unsqueeze(0).repeat(batch, 1, 1)
        s = (self.population - self.initial_e - self.initial_i).clamp_min(0.0).unsqueeze(0).repeat(batch, 1, 1)
        v = torch.zeros_like(s)
        e = self.initial_e.unsqueeze(0).repeat(batch, 1, 1)
        ip = torch.zeros_like(s)
        ia = torch.zeros_like(s)
        isym = self.initial_i.unsqueeze(0).repeat(batch, 1, 1)
        h = torch.zeros_like(s)
        r = torch.zeros_like(s)
        d = torch.zeros_like(s)

        beta_scale = scenario_tensor[:, 0].view(batch, 1, 1)
        mobility_scale = scenario_tensor[:, 1].view(batch, 1, 1)
        vaccination_rate = scenario_tensor[:, 2].view(batch, 1, 1)
        contact_reduction = scenario_tensor[:, 3].view(batch, 1, 1)
        days = scenario_tensor[:, 4].view(batch, 1, 1)

        peak_infectious = torch.zeros(batch, device=scenario_tensor.device)
        peak_hospital = torch.zeros(batch, device=scenario_tensor.device)
        cumulative_infections = torch.zeros(batch, device=scenario_tensor.device)
        total_pop = pop.sum(dim=(1, 2)).clamp_min(1.0)

        for day in range(max_days):
            active = (days > day).to(s.dtype)
            infectious = 0.65 * ip + 0.45 * ia + isym + 0.08 * h
            prevalence = infectious / pop.clamp_min(1.0)
            imported = torch.einsum("pq,bqa->bpa", self.mobility, prevalence)
            mixed = (1.0 - mobility_scale) * prevalence + mobility_scale * imported
            contact_force = torch.einsum("aj,bpj->bpa", self.contact, mixed)
            seasonality = 1.0 + 0.10 * torch.cos(torch.tensor(2.0 * 3.141592653589793 * (day - 15) / 365.0, device=s.device))
            lam = (0.055 * self.log_beta_adjust.exp() * beta_scale * contact_reduction * seasonality * contact_force * self.susceptibility).clamp(0.0, 0.85)
            new_e_s = (lam * s).minimum(s)
            new_e_v = (lam * 0.38 * v).minimum(v)
            new_e = active * (new_e_s + new_e_v)
            new_v = active * ((vaccination_rate * s).minimum((s - new_e_s).clamp_min(0.0)))

            new_ip = active * (e * (1.0 / 3.0)).minimum(e)
            leaving_ip = active * (ip * (1.0 / 2.0)).minimum(ip)
            new_ia = leaving_ip * self.asymptomatic_prob
            new_is = leaving_ip - new_ia
            new_ra = active * (ia * (1.0 / 5.5)).minimum(ia)

            new_h = active * (isym * self.hospital_prob * (1.0 / 5.0)).minimum(isym)
            new_rs = active * (isym * (1.0 - self.hospital_prob) * (1.0 / 6.5)).minimum(isym)
            overflow = (new_h + new_rs).clamp_min(1.0)
            scale = torch.minimum(torch.ones_like(overflow), isym / overflow)
            new_h = new_h * scale
            new_rs = new_rs * scale

            new_d = active * (h * self.fatality_prob * (1.0 / 12.0)).minimum(h)
            new_rh = active * (h * (1.0 - self.fatality_prob) * (1.0 / 9.0)).minimum(h)
            overflow_h = (new_d + new_rh).clamp_min(1.0)
            scale_h = torch.minimum(torch.ones_like(overflow_h), h / overflow_h)
            new_d = new_d * scale_h
            new_rh = new_rh * scale_h

            s = (s - new_e - new_v).clamp_min(0.0)
            v = (v + new_v).clamp_min(0.0)
            e = (e + new_e - new_ip).clamp_min(0.0)
            ip = (ip + new_ip - leaving_ip).clamp_min(0.0)
            ia = (ia + new_ia - new_ra).clamp_min(0.0)
            isym = (isym + new_is - new_h - new_rs).clamp_min(0.0)
            h = (h + new_h - new_d - new_rh).clamp_min(0.0)
            r = r + new_ra + new_rs + new_rh
            d = d + new_d
            pop = (s + v + e + ip + ia + isym + h + r).clamp_min(1.0)

            cumulative_infections = cumulative_infections + new_e.sum(dim=(1, 2))
            peak_infectious = torch.maximum(peak_infectious, (ip + ia + isym).sum(dim=(1, 2)))
            peak_hospital = torch.maximum(peak_hospital, h.sum(dim=(1, 2)))

        return torch.stack(
            [
                total_pop,
                peak_infectious,
                peak_hospital,
                cumulative_infections / total_pop,
                d.sum(dim=(1, 2)),
                r.sum(dim=(1, 2)),
            ],
            dim=1,
        )


def setup_distributed(enable: bool):
    world_size = int(os.environ.get("WORLD_SIZE", os.environ.get("SLURM_NTASKS", "1")))
    rank = int(os.environ.get("RANK", os.environ.get("SLURM_PROCID", "0")))
    local_rank = int(os.environ.get("LOCAL_RANK", os.environ.get("SLURM_LOCALID", "0")))
    if enable and world_size > 1:
        backend = "nccl" if torch.cuda.is_available() else "gloo"
        if backend == "nccl":
            torch.cuda.set_device(local_rank)
        dist.init_process_group(backend=backend, init_method="env://", rank=rank, world_size=world_size)
        return True, rank, world_size, local_rank, backend
    return False, 0, 1, 0, "single"


def scenario_tensor(rows: list[dict], device):
    values = [[r["beta_scale"], r["mobility_scale"], r["vaccination_rate"], r["contact_reduction"], float(r["days"])] for r in rows]
    if not values:
        return torch.empty((0, 5), dtype=torch.float32, device=device)
    return torch.tensor(values, dtype=torch.float32, device=device)


def write_summary(path: Path, rows: Iterable[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields = [
        "scenario_id",
        "policy",
        "rank",
        "world_size",
        "device",
        "backend",
        "elapsed_sec",
        "total_population",
        "peak_infectious",
        "peak_hospitalized",
        "attack_rate",
        "final_deaths",
        "final_recovered",
        "host",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patches", default="data/patches.csv")
    parser.add_argument("--mobility", default="data/mobility.csv")
    parser.add_argument("--contact", default="data/age_contact_4x4.csv")
    parser.add_argument("--scenario-file", default="data/scenarios.csv")
    parser.add_argument("--out", default="results/seir_torch_summary.csv")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--ddp", action="store_true")
    args = parser.parse_args()

    distributed, rank, world_size, local_rank, backend = setup_distributed(args.ddp)
    if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()):
        device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device("cpu")

    population, initial_e, initial_i = read_patches(Path(args.patches))
    contact = read_contact(Path(args.contact))
    mobility = read_mobility(Path(args.mobility), len(population))
    scenarios = read_scenarios(Path(args.scenario_file))
    local_scenarios = scenarios[rank::world_size]

    kernel = SEIRKernel(population, initial_e, initial_i, contact, mobility).to(device)
    if distributed:
        model = DDP(kernel, device_ids=[local_rank] if device.type == "cuda" else None)
    else:
        model = kernel

    start = time.perf_counter()
    with torch.no_grad():
        tensor = scenario_tensor(local_scenarios, device)
        max_days = max([row["days"] for row in local_scenarios], default=0)
        if tensor.shape[0] > 0:
            result = model(tensor, max_days).detach().cpu()
        else:
            result = torch.empty((0, 6), dtype=torch.float32)
    elapsed = time.perf_counter() - start

    local_rows = []
    for row, summary in zip(local_scenarios, result.tolist()):
        local_rows.append(
            {
                "scenario_id": row["scenario_id"],
                "policy": row["policy"],
                "rank": rank,
                "world_size": world_size,
                "device": str(device),
                "backend": backend,
                "elapsed_sec": f"{elapsed:.6f}",
                "total_population": f"{summary[0]:.3f}",
                "peak_infectious": f"{summary[1]:.6f}",
                "peak_hospitalized": f"{summary[2]:.6f}",
                "attack_rate": f"{summary[3]:.8f}",
                "final_deaths": f"{summary[4]:.6f}",
                "final_recovered": f"{summary[5]:.6f}",
                "host": socket.gethostname(),
            }
        )

    if distributed:
        gathered = [None for _ in range(world_size)]
        dist.all_gather_object(gathered, local_rows)
        all_rows = [item for rows in gathered for item in rows]
        dist.destroy_process_group()
    else:
        all_rows = local_rows

    if rank == 0:
        all_rows.sort(key=lambda item: int(item["scenario_id"]))
        write_summary(Path(args.out), all_rows)
        print(f"wrote {args.out} with {len(all_rows)} scenario summaries")


if __name__ == "__main__":
    main()
