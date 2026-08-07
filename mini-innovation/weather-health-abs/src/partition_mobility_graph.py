from __future__ import annotations

import csv
from pathlib import Path


EDGES = [
    ("campus", "market", 80),
    ("campus", "clinic", 30),
    ("campus", "transit", 120),
    ("market", "transit", 90),
    ("market", "residential", 70),
    ("clinic", "residential", 45),
    ("transit", "industrial", 110),
    ("industrial", "residential", 60),
]

NODES = {
    "campus": 4200,
    "market": 2600,
    "clinic": 1100,
    "transit": 3600,
    "residential": 5200,
    "industrial": 3100,
}


def score(parts: dict[str, int]) -> dict[str, float]:
    loads = [0.0, 0.0]
    cuts = 0.0
    for node, weight in NODES.items():
        loads[parts[node]] += weight
    for left, right, weight in EDGES:
        if parts[left] != parts[right]:
            cuts += weight
    return {
        "load_part_0": loads[0],
        "load_part_1": loads[1],
        "imbalance": max(loads) / max(1.0, min(loads)),
        "edge_cut_weight": cuts,
    }


def main() -> None:
    naive = {node: idx % 2 for idx, node in enumerate(NODES)}
    locality = {
        "campus": 0,
        "market": 0,
        "clinic": 0,
        "transit": 1,
        "residential": 1,
        "industrial": 1,
    }
    rows = []
    for name, parts in [("naive_round_robin", naive), ("locality_partition", locality)]:
        metric = score(parts)
        metric["partitioner"] = name
        rows.append(metric)
    Path("results").mkdir(exist_ok=True)
    with Path("results/mobility_partition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["partitioner", "load_part_0", "load_part_1", "imbalance", "edge_cut_weight"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote=results/mobility_partition_summary.csv")


if __name__ == "__main__":
    main()
