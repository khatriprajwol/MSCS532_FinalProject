"""
generate_chart.py

Reads results/benchmark_results.csv (written by benchmark.py) and produces
results/benchmark_chart.png: two side-by-side line charts, one for
sequential traversal and one for random-index access, both plotted
against input size.

Run this after benchmark.py any time the CSV changes, so the chart stays
in sync with the latest numbers:

    python3 benchmark.py
    python3 generate_chart.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
CSV_PATH = RESULTS_DIR / "benchmark_results.csv"
CHART_PATH = RESULTS_DIR / "benchmark_chart.png"


def load_rows(csv_path: Path):
    with csv_path.open() as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    rows = load_rows(CSV_PATH)
    sizes = [int(row["n"]) for row in rows]
    ll_traverse_ms = [float(row["linked_list_traverse_s"]) * 1000 for row in rows]
    ca_traverse_ms = [float(row["contiguous_array_traverse_s"]) * 1000 for row in rows]
    ll_access_ms = [float(row["linked_list_random_access_s"]) * 1000 for row in rows]
    ca_access_ms = [float(row["contiguous_array_random_access_s"]) * 1000 for row in rows]

    fig, (traverse_ax, access_ax) = plt.subplots(1, 2, figsize=(11, 4.2))

    traverse_ax.plot(sizes, ll_traverse_ms, marker="o", label="LinkedList (pointer-chasing)")
    traverse_ax.plot(sizes, ca_traverse_ms, marker="s", label="ContiguousArray (packed)")
    traverse_ax.set_xlabel("Number of elements (n)")
    traverse_ax.set_ylabel("Time (ms)")
    traverse_ax.set_title("Sequential traversal")
    traverse_ax.legend()
    traverse_ax.grid(alpha=0.3)

    access_ax.plot(sizes, ll_access_ms, marker="o", label="LinkedList (pointer-chasing)")
    access_ax.plot(sizes, ca_access_ms, marker="s", label="ContiguousArray (packed)")
    access_ax.set_xlabel("Number of elements (n)")
    access_ax.set_ylabel("Time (ms), 2,000 random accesses")
    access_ax.set_title("Random-index access (2,000 lookups)")
    access_ax.set_yscale("log")
    access_ax.legend()
    access_ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(CHART_PATH, dpi=150)
    print(f"Wrote {CHART_PATH}")


if __name__ == "__main__":
    main()
