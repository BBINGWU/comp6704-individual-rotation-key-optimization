#!/usr/bin/env python3
import csv,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data'
p=list(csv.DictReader(open(D/'primitive_rotation_bench.csv')));o=list(csv.DictReader(open(D/'optimization_results.csv')));g=list(csv.DictReader(open(D/'exact_gaps.csv')));s=list(csv.DictReader(open(D/'stability.csv')))
lines=['# Generated result summary','',f"All-key serialized memory (sum of individually serialized keys): **{sum(int(x['serialized_bytes']) for x in p):,} bytes**.",'',f"Primitive correctness: **{sum(x['passed']=='true' for x in csv.DictReader(open(D/'correctness.csv')))}/{len(p)} passed**.",'','## Best predicted configurations at each workload/budget','', '|Workload|Budget|Method|Memory|Latency us|Avg hops|','|---|---:|---|---:|---:|---:|']
for w in sorted({x['workload'] for x in o}):
 for b in sorted({x['budget_fraction'] for x in o},key=float):
  a=[x for x in o if x['workload']==w and x['budget_fraction']==b and x['status']=='OK'];
  if a:
   x=min(a,key=lambda z:float(z['predicted_latency_us']));lines.append(f"|{w}|{float(b):.2f}|{x['method']}|{int(x['total_bytes']):,}|{float(x['predicted_latency_us']):.2f}|{float(x['average_hops']):.2f}|")
vals=[float(x['jaccard']) for x in s];lines += ['',f"Stability mean Jaccard across deterministic perturbations: **{statistics.mean(vals):.3f}**."]
(R/'result_summary.md').write_text('\n'.join(lines)+'\n')
