from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape


WIDTH = 900
HEIGHT = 560
PAD_L = 76
PAD_R = 28
PAD_T = 42
PAD_B = 68


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def latest(pattern: str) -> Path | None:
    files = sorted(Path("results").glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def sx(x: float, xmin: float, xmax: float) -> float:
    if xmax == xmin:
        return PAD_L
    return PAD_L + (x - xmin) * (WIDTH - PAD_L - PAD_R) / (xmax - xmin)


def sy(y: float, ymin: float, ymax: float) -> float:
    if ymax == ymin:
        return HEIGHT - PAD_B
    return HEIGHT - PAD_B - (y - ymin) * (HEIGHT - PAD_T - PAD_B) / (ymax - ymin)


def svg_line_chart(
    path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    xs: list[float],
    series: list[tuple[str, list[float], str]],
) -> None:
    xmin, xmax = min(xs), max(xs)
    ymax = max(max(values) for _, values, _ in series) * 1.12
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{WIDTH/2}" y="26" text-anchor="middle" font-size="22" font-family="sans-serif">{escape(title)}</text>',
        f'<line x1="{PAD_L}" y1="{HEIGHT-PAD_B}" x2="{WIDTH-PAD_R}" y2="{HEIGHT-PAD_B}" stroke="#222"/>',
        f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{HEIGHT-PAD_B}" stroke="#222"/>',
    ]
    for tick in range(6):
        yv = ymax * tick / 5.0
        yp = sy(yv, 0, ymax)
        lines.append(f'<line x1="{PAD_L-5}" y1="{yp:.1f}" x2="{WIDTH-PAD_R}" y2="{yp:.1f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{PAD_L-10}" y="{yp+4:.1f}" text-anchor="end" font-size="12" font-family="monospace">{yv:.2f}</text>')
    for x in xs:
        xp = sx(x, xmin, xmax)
        lines.append(f'<line x1="{xp:.1f}" y1="{HEIGHT-PAD_B}" x2="{xp:.1f}" y2="{HEIGHT-PAD_B+5}" stroke="#222"/>')
        lines.append(f'<text x="{xp:.1f}" y="{HEIGHT-PAD_B+24}" text-anchor="middle" font-size="12" font-family="monospace">{x:g}</text>')
    for name, values, color in series:
        points = " ".join(f"{sx(x, xmin, xmax):.1f},{sy(y, 0, ymax):.1f}" for x, y in zip(xs, values))
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{points}"/>')
        for x, y in zip(xs, values):
            lines.append(f'<circle cx="{sx(x, xmin, xmax):.1f}" cy="{sy(y, 0, ymax):.1f}" r="4" fill="{color}"/>')
        lx = WIDTH - PAD_R - 220
        ly = PAD_T + 22 * series.index((name, values, color))
        lines.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+36}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text x="{lx+44}" y="{ly+4}" font-size="13" font-family="sans-serif">{escape(name)}</text>')
    lines.append(f'<text x="{WIDTH/2}" y="{HEIGHT-18}" text-anchor="middle" font-size="14" font-family="sans-serif">{escape(xlabel)}</text>')
    lines.append(f'<text x="20" y="{HEIGHT/2}" transform="rotate(-90 20 {HEIGHT/2})" text-anchor="middle" font-size="14" font-family="sans-serif">{escape(ylabel)}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def svg_bar_chart(path: Path, title: str, ylabel: str, labels: list[str], values: list[float]) -> None:
    ymax = max(values + [1e-9]) * 1.18
    bar_gap = 12
    area_w = WIDTH - PAD_L - PAD_R
    bar_w = max(18, (area_w - bar_gap * (len(labels) + 1)) / max(1, len(labels)))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{WIDTH/2}" y="26" text-anchor="middle" font-size="22" font-family="sans-serif">{escape(title)}</text>',
        f'<line x1="{PAD_L}" y1="{HEIGHT-PAD_B}" x2="{WIDTH-PAD_R}" y2="{HEIGHT-PAD_B}" stroke="#222"/>',
        f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{HEIGHT-PAD_B}" stroke="#222"/>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        x = PAD_L + bar_gap + i * (bar_w + bar_gap)
        y = sy(value, 0, ymax)
        h = HEIGHT - PAD_B - y
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="#0f766e"/>')
        lines.append(f'<text x="{x+bar_w/2:.1f}" y="{y-7:.1f}" text-anchor="middle" font-size="12" font-family="monospace">{value:.3f}</text>')
        lines.append(f'<text x="{x+bar_w/2:.1f}" y="{HEIGHT-PAD_B+23}" text-anchor="middle" font-size="11" font-family="sans-serif">{escape(label)}</text>')
    lines.append(f'<text x="20" y="{HEIGHT/2}" transform="rotate(-90 20 {HEIGHT/2})" text-anchor="middle" font-size="14" font-family="sans-serif">{escape(ylabel)}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    Path("figures").mkdir(exist_ok=True)
    summary_path = Path("results/perf_workshop_summary.csv")
    if not summary_path.exists():
        raise SystemExit("run performance/perf_workshop_report.py first")
    summary = read_csv(summary_path)
    ranks = [float(row["ranks"]) for row in summary]
    speedup = [float(row["speedup"]) for row in summary]
    ideal = ranks
    efficiency = [float(row["efficiency"]) for row in summary]
    overhead = [max(0.0, float(row["overhead_sec"])) for row in summary]
    svg_line_chart(Path("figures/perf_summary_speedup.svg"), "MPI Solver Speedup", "MPI ranks", "speedup", ranks, [("observed", speedup, "#2563eb"), ("ideal", ideal, "#94a3b8")])
    svg_line_chart(Path("figures/perf_summary_efficiency.svg"), "Parallel Efficiency", "MPI ranks", "efficiency", ranks, [("efficiency", efficiency, "#7c3aed")])
    svg_bar_chart(Path("figures/perf_summary_overhead.svg"), "Estimated Overhead", "seconds", [row["ranks"] for row in summary], overhead)

    python_path = Path("results/python_stack_overhead.csv")
    python_note = "Python stack CSV is pending."
    if python_path.exists():
        py_rows = read_csv(python_path)
        svg_bar_chart(
            Path("figures/perf_summary_python_stack.svg"),
            "Python Stack Cost",
            "seconds",
            [row["case"].replace("_", " ")[:15] for row in py_rows],
            [float(row["elapsed_sec"]) for row in py_rows],
        )
        python_note = "figures/perf_summary_python_stack.svg"

    md = Path("results/perf_summary_display.md")
    md.write_text(
        "\n".join(
            [
                "# Performance Summary Display",
                "",
                "## Figures",
                "",
                "- figures/perf_summary_speedup.svg",
                "- figures/perf_summary_efficiency.svg",
                "- figures/perf_summary_overhead.svg",
                f"- {python_note}",
                "",
                "## Reading Order",
                "",
                "1. Compare observed speedup with the ideal line.",
                "2. Read efficiency drop as a signal for synchronization or communication overhead.",
                "3. Use overhead bars to choose the next rank count or problem size.",
                "4. Compare Python stack cost with total model runtime before moving logic into Python loops.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("wrote figures/perf_summary_speedup.svg")
    print("wrote figures/perf_summary_efficiency.svg")
    print("wrote figures/perf_summary_overhead.svg")
    print("wrote", md)


if __name__ == "__main__":
    main()
