#!/usr/bin/env python3
import ast,csv
from pathlib import Path
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; D=R/'data'; P=R/'plots';P.mkdir(exist_ok=True)
rows=list(csv.DictReader(open(D/'optimization_results.csv'))); ok=[r for r in rows if r['status']=='OK']
methods=sorted({r['method'] for r in ok}); marks=['o','s','^','D','x']
def save(name):
 plt.tight_layout();plt.savefig(P/(name+'.png'),dpi=180);plt.savefig(P/(name+'.pdf'));plt.close()
for wn in sorted({r['workload'] for r in ok}):
 a=[r for r in ok if r['workload']==wn]
 for m,mk in zip(methods,marks):
  x=[float(r['normalized_memory']) for r in a if r['method']==m];y=[float(r['predicted_latency_us']) for r in a if r['method']==m]
  if x:plt.plot(x,y,mk+'-',label=m)
 plt.xlabel('Normalized serialized key memory');plt.ylabel('Predicted workload latency (us)');plt.title(wn);plt.legend(fontsize=7);save('pareto_'+wn.lower())
for field,xlab,name in [('key_count','Key count','key_count_latency'),('budget_fraction','Budget / all-key memory','budget_hops')]:
 for m,mk in zip(methods,marks):
  a=[r for r in ok if r['method']==m];x=[float(r[field]) for r in a];y=[float(r['predicted_latency_us'] if field=='key_count' else r['average_hops']) for r in a]
  if x:plt.scatter(x,y,label=m,marker=mk,alpha=.7)
 plt.xlabel(xlab);plt.ylabel('Predicted latency (us)' if field=='key_count' else 'Average hops');plt.legend(fontsize=7);save(name)
g=list(csv.DictReader(open(D/'exact_gaps.csv'))); gg=[r for r in g if r['optimality_gap']!='NA']
for m,mk in [('GREEDY','o'),('GREEDY_SWAP','s')]:
 a=[r for r in gg if r['method']==m];plt.scatter([float(r['budget_fraction']) for r in a],[100*float(r['optimality_gap']) for r in a],label=m,marker=mk)
plt.xlabel('Budget fraction (small pool)');plt.ylabel('Optimality gap (%)');plt.legend();save('optimality_gap')
for m,mk in [('GREEDY','o'),('GREEDY_SWAP','s')]:
 a=[r for r in ok if r['method']==m];plt.scatter([float(r['budget_fraction']) for r in a],[float(r['optimizer_runtime_s']) for r in a],label=m,marker=mk)
plt.xlabel('Budget fraction');plt.ylabel('Optimizer runtime (s)');plt.yscale('log');plt.legend();save('optimizer_runtime')
c=list(csv.DictReader(open(D/'correctness.csv')));plt.scatter([int(r['hops']) for r in c],[float(r['max_abs_error']) for r in c]);plt.yscale('log');plt.xlabel('Hop count');plt.ylabel('Max absolute error');save('correctness_error')
# No fabricated end-to-end values: an annotated empty plot makes the missing measurement explicit.
plt.axline((0,0),slope=1,color='k',ls='--');plt.text(.5,.5,'NA: composed end-to-end benchmark not collected',ha='center',transform=plt.gca().transAxes);plt.xlabel('Predicted latency (us)');plt.ylabel('Measured latency (us)');save('predicted_vs_measured')
