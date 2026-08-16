# MSCS-532 Final Project: Data Locality Optimization in HPC

Implementation companion to the final project report "Optimization in
High-Performance Computing: Data Locality and Cache-Efficient Data
Structures," based on Azad et al. (2023), *An Empirical Study of High
Performance Computing (HPC) Performance Bugs*.

## What this demonstrates

Two from-scratch data structures with the same interface:

- `LinkedList` — singly linked list, node-per-element, scattered heap allocation
- `ContiguousArray` — manually resized, packed contiguous block (ctypes-backed)

`src/benchmark.py` times sequential traversal and random-index access for
both structures across input sizes from 1,000 to 500,000 elements and
writes `results/benchmark_results.csv` and `results/benchmark_chart.png`.

## Run it

```
cd src
python3 benchmark.py
```

## Files

- `src/data_structures.py` — LinkedList and ContiguousArray implementations
- `src/benchmark.py` — benchmark harness
- `results/benchmark_results.csv` — raw timing results
- `results/benchmark_chart.png` — traversal and random-access charts

## Report

Full analysis, literature review, and lessons learned are in the project
report submitted alongside this repository.
