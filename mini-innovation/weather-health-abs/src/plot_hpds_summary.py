from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd
from matplotlib import pyplot as plt


def main() -> None:
    results = Path("results/hpds_weather_abs_summary.csv")
    figures = Path("figures")
    figures.mkdir(exist_ok=True)
    df = pd.read_csv(results)
    grouped = (
        df.groupby("policy", as_index=False)
        .agg(
            max_heat_index_c=("max_heat_index_c", "mean"),
            exposure_agent_hours=("exposure_agent_hours", "mean"),
            cooling_kwh=("cooling_kwh", "mean"),
            infection_risk_proxy=("infection_risk_proxy", "mean"),
        )
        .sort_values("policy")
    )
    grouped.to_csv("results/hpds_policy_summary.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    panels = [
        ("max_heat_index_c", "Mean max heat index (C)", "#2563eb"),
        ("exposure_agent_hours", "Exposure agent-hours", "#dc2626"),
        ("cooling_kwh", "Cooling proxy (kWh)", "#0f766e"),
        ("infection_risk_proxy", "Risk proxy", "#7c3aed"),
    ]
    for ax, (column, title, color) in zip(axes.ravel(), panels):
        ax.bar(grouped["policy"], grouped[column], color=color)
        ax.set_title(title)
        ax.tick_params(axis="x", labelrotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Weather-Health ABS HPDS Summary")
    out = figures / "hpds_weather_abs_summary.png"
    fig.savefig(out, dpi=160)
    print(f"wrote={out}")
    print("wrote=results/hpds_policy_summary.csv")


if __name__ == "__main__":
    main()
