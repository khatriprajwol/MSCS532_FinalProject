"""
benchmark.py

Timing harness for the LinkedList vs. ContiguousArray comparison used to
demonstrate the "data locality optimization" technique from Azad et al.
(2023). Two operations are measured at a range of input sizes:

  traversal      one full pass over every element, summed into a total
  random access  a fixed batch of get() calls at randomly chosen positions

Both operations run against both structures at every size, so the two
numbers reported at each size are directly comparable. Results are
written to results/benchmark_results.csv for the report's table and
figure; a summary line is also printed to the console as each size
finishes.
"""

from __future__ import annotations

import csv
import gc
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from data_structures import build_contiguous_array, build_linked_list

INPUT_SIZES = (1_000, 5_000, 10_000, 50_000, 100_000, 250_000, 500_000)
ACCESS_SAMPLE_COUNT = 2_000
TRIALS_PER_SIZE = 3
RANDOM_SEED = 42

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@dataclass
class SizeResult:
    n: int
    linked_list_traverse_s: float
    contiguous_array_traverse_s: float
    traverse_speedup_x: float
    linked_list_random_access_s: float
    contiguous_array_random_access_s: float
    random_access_speedup_x: float


def best_of(trials: int, fn) -> float:
    """Run fn() `trials` times and return the fastest wall-clock time.

    Reporting the minimum rather than the mean is standard practice for
    microbenchmarks: it suppresses one-off noise from garbage collection
    pauses and OS scheduling without needing a large trial count.
    """
    fastest = float("inf")
    for _ in range(trials):
        gc.collect()
        started_at = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - started_at
        fastest = min(fastest, elapsed)
    return fastest


def time_full_traversal(build_fn, size: int) -> float:
    structure = build_fn(size)
    return best_of(TRIALS_PER_SIZE, structure.traverse_sum)


def time_random_lookups(build_fn, size: int, positions) -> float:
    structure = build_fn(size)

    def do_all_lookups():
        for position in positions:
            structure.get(position)

    return best_of(TRIALS_PER_SIZE, do_all_lookups)


def measure_one_size(size: int, rng: random.Random) -> SizeResult:
    lookup_positions = [rng.randrange(size) for _ in range(ACCESS_SAMPLE_COUNT)]

    ll_traverse = time_full_traversal(build_linked_list, size)
    ca_traverse = time_full_traversal(build_contiguous_array, size)

    ll_access = time_random_lookups(build_linked_list, size, lookup_positions)
    ca_access = time_random_lookups(build_contiguous_array, size, lookup_positions)

    return SizeResult(
        n=size,
        linked_list_traverse_s=ll_traverse,
        contiguous_array_traverse_s=ca_traverse,
        traverse_speedup_x=ll_traverse / ca_traverse,
        linked_list_random_access_s=ll_access,
        contiguous_array_random_access_s=ca_access,
        random_access_speedup_x=ll_access / ca_access,
    )


def describe(result: SizeResult) -> str:
    return (
        f"n={result.n:>7}  "
        f"traverse: LL={result.linked_list_traverse_s:.5f}s "
        f"CA={result.contiguous_array_traverse_s:.5f}s "
        f"speedup={result.traverse_speedup_x:5.2f}x   |   "
        f"random-access({ACCESS_SAMPLE_COUNT}): "
        f"LL={result.linked_list_random_access_s:.5f}s "
        f"CA={result.contiguous_array_random_access_s:.5f}s "
        f"speedup={result.random_access_speedup_x:6.1f}x"
    )


def write_csv(results, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(results[0]).keys())
    with destination.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    results = []
    for size in INPUT_SIZES:
        result = measure_one_size(size, rng)
        results.append(result)
        print(describe(result))

    csv_path = RESULTS_DIR / "benchmark_results.csv"
    write_csv(results, csv_path)
    print(f"\nWrote {csv_path}")


if __name__ == "__main__":
    main()
