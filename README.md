# Memory-Aware Rotation-Key Selection for CKKS

Reproducible experiments for the COMP6704 Advanced Topics in Optimization Individual Assignment, PolyU Fall 2026.

The project studies workload-aware optimization of CKKS rotation-key selection under a memory budget. It is an optimization study and does not claim a new cryptographic construction.

## Overview

CKKS rotation keys can consume substantial memory. Selecting fewer keys reduces memory, while rotations without direct keys can be evaluated as bounded compositions of available rotations. This project optimizes the resulting latency-memory trade-off for deterministic uniform, Zipf/hotspot, convolution, and BSGS-like workloads.

The evaluated methods are:

- `DIRECT_IN_POOL`: direct keys for targets present in the main candidate pool, with compositions otherwise;
- `ALL_REQUIRED`: unconstrained reference with one direct key for every workload target;
- `POWER_OF_TWO`: signed powers of two from the candidate pool;
- `EXACT`: exhaustive search on the small candidate pool;
- original `GREEDY` and `GREEDY_SWAP`;
- `COVERAGE_GREEDY` and `COVERAGE_GREEDY_SWAP`, which use a coverage-first feasibility phase.

## Main results

All figures below are verified V2 results under OpenFHE v1.4.2, commit `aa391988d354d4360f390f223a90e0d1b98839d7`.

- 731 unique composed paths measured end-to-end;
- 731/731 composed-path correctness checks passed;
- maximum composed decryption error: `9.459e-12`;
- measured/predicted latency ratio: median `0.9985`, mean `1.0090`;
- 95th-percentile absolute relative error: `12.60%`;
- 20 EXACT-feasible small workload/budget cases;
- original GREEDY feasible in 4/20 cases;
- COVERAGE_GREEDY feasible in 19/20 cases;
- COVERAGE_GREEDY_SWAP feasible in 20/20 cases;
- COVERAGE_GREEDY_SWAP observed a 0% optimality gap on all 20 tested exact-feasible small instances;
- mean Jaccard similarity in the deterministic stability experiment: `0.973`.

The observed 0% gap is limited to these tested small exact-search instances. It is not a claim of general global optimality for COVERAGE_GREEDY_SWAP.

## Environment

- Apple M2 Pro, 32 GiB RAM;
- macOS 26.5.1;
- Apple Clang 15.0.0;
- Release build;
- single-threaded main benchmarks;
- no GPU.

CKKS configuration:

- `HEStd_128_classic` security;
- ring dimension `N = 16384`;
- 8192 slots;
- multiplicative depth 3;
- 50-bit scaling modulus;
- HYBRID key switching;
- `numLargeDigits = 3`.

See [environment.txt](environment.txt) for the complete recorded environment.

## Quick reproduction

The inexpensive path uses the committed raw benchmark CSV files and regenerates V2 optimization results, summaries, and plots without running OpenFHE:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./run_all.sh
```

## Full benchmark reproduction

Install the pinned OpenFHE release outside this repository:

```bash
git clone --branch v1.4.2 https://github.com/openfheorg/openfhe-development.git openfhe-development
test "$(git -C openfhe-development rev-parse HEAD)" = "aa391988d354d4360f390f223a90e0d1b98839d7"
cmake -S openfhe-development -B openfhe-development/build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DWITH_OPENMP=OFF -DBUILD_UNITTESTS=OFF \
  -DBUILD_EXAMPLES=OFF -DBUILD_BENCHMARKS=OFF \
  -DCMAKE_INSTALL_PREFIX="$PWD/openfhe-install"
cmake --build openfhe-development/build --parallel
cmake --install openfhe-development/build
```

Then, from this repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
OPENFHE_PREFIX="$PWD/../openfhe-install" ./run_benchmark.sh
./run_analysis.sh
```

`run_benchmark.sh` is expensive: it collects primitive rotations, constructs the optimization plans, measures complete composed paths, and measures direct rotations required by `ALL_REQUIRED`. `run_analysis.sh` performs only deterministic processing of existing raw measurements.

## Repository structure

- `src/`: OpenFHE C++ primitive, composed-path, correctness, and serialization benchmark;
- `python/`: shortest-path optimization, exact search, greedy methods, analysis, and plotting;
- `data/`: raw primitive/composed measurements, workloads, optimizer outputs, correctness, stability, and exact-search audits;
- `plots_v2/`: publication-quality V2 figures in PDF and PNG;
- `result_summary_v2.md` and `report_notes_v2.md`: verified results and methodological notes.

## Important experimental notes

1. Under this fixed CKKS configuration, every measured singleton rotation key has the same serialized proxy size: `5,507,945` bytes. Therefore the memory-budget problem in this experiment is equivalent to a key-count/cardinality constraint. The general formulation still supports heterogeneous key sizes.
2. Summing individually serialized singleton-key sizes repeats serialization/container metadata. The byte count is a consistent experimental proxy, not the exact serialized size of one combined evaluation-key map.
3. Measured workload latency is a workload model formed from measured complete rotation paths, not a full application end-to-end runtime.
4. Missing measurements remain `NA`; no missing value is fabricated.

