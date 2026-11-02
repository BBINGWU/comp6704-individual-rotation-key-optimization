#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OPENFHE_PREFIX="${OPENFHE_PREFIX:-$ROOT/../.openfhe-v1.4.2/install}"
cmake -S "$ROOT" -B "$ROOT/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DOpenFHE_DIR="$OPENFHE_PREFIX/lib/OpenFHE"
cmake --build "$ROOT/build" --parallel 1
OMP_NUM_THREADS=1 "$ROOT/build/benchmark_rotations" "$ROOT/data"
PYTHON="${PYTHON:-python3}"
test ! -x "$ROOT/.venv/bin/python" || PYTHON="$ROOT/.venv/bin/python"
"$PYTHON" "$ROOT/python/optimize_v2.py"
OMP_NUM_THREADS=1 "$ROOT/build/benchmark_rotations" "$ROOT/data" composed
OMP_NUM_THREADS=1 "$ROOT/build/benchmark_rotations" "$ROOT/data" direct-extra
