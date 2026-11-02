#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
test ! -x "$ROOT/.venv/bin/python" || PYTHON="$ROOT/.venv/bin/python"
for f in primitive_rotation_bench.csv composed_rotation_bench.csv primitive_rotation_bench_extra.csv correctness.csv correctness_extra.csv workloads.csv optimization_results.csv stability.csv; do
  test -s "$ROOT/data/$f" || { echo "Missing raw evidence: data/$f" >&2; exit 1; }
done
"$PYTHON" "$ROOT/python/optimize_v2.py"
"$PYTHON" "$ROOT/python/finalize_v2.py"
