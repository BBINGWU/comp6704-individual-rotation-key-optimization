#!/usr/bin/env python3
import csv,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'data';P=R/'plots_v2';P.mkdir(exist_ok=True)
def read(n):return list(csv.DictReader(open(D/n)))
old=read('optimization_results.csv');coverage=read('coverage_results.csv');work=read('workloads.csv');comp=read('composed_rotation_bench.csv')
lookup={tuple(map(int,r['path'].split(';'))):r for r in comp};weights=defaultdict(dict)
for r in work:weights[r['workload']][int(r['target_rotation'])]=float(r['weight'])
rows=[]
for r in old+coverage:
 x=dict(r);x['raw_method']=r['method'];x['display_method']='DIRECT_IN_POOL' if r['method']=='DIRECT_ALL' else r['method'];x['measured_model_latency_us']='NA'
 if r['status']=='OK':
  paths=json.loads(r['paths']);total=0;valid=True
  for target,w in weights[r['workload']].items():
   p=paths.get(str(target));m=lookup.get(tuple(p)) if p else None
   if not m:valid=False;break
   total+=w*float(m['measured_median_us'])
  if valid:x['measured_model_latency_us']=total
 rows.append(x)
fields=list(rows[0]);
with open(D/'optimization_results_v2.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
# True ALL_REQUIRED baseline from direct measurements.
prim=read('primitive_rotation_bench.csv')+read('primitive_rotation_bench_extra.csv');pm={int(r['rotation']):r for r in prim};refs=[]
for wn,ww in weights.items():
 targets=sorted(ww);refs.append({'workload':wn,'required_key_count':len(targets),'total_serialized_bytes':sum(int(pm[t]['serialized_bytes']) for t in targets),'measured_weighted_direct_latency_us':sum(ww[t]*float(pm[t]['median_us']) for t in targets),'max_abs_error':max(float(r['max_abs_error']) for r in read('correctness.csv')+read('correctness_extra.csv') if int(r['rotation']) in targets)})
with open(D/'all_required_baseline.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=refs[0]);w.writeheader();w.writerows(refs)
def save(name):plt.tight_layout();plt.savefig(P/(name+'.png'),dpi=220);plt.savefig(P/(name+'.pdf'));plt.close()
style={'DIRECT_IN_POOL':'o','POWER_OF_TWO':'s','GREEDY':'^','GREEDY_SWAP':'D','COVERAGE_GREEDY':'P','COVERAGE_GREEDY_SWAP':'X'}
valid=[r for r in rows if r['status']=='OK' and r['measured_model_latency_us']!='NA']
for wn in sorted(weights):
 for m,mk in style.items():
  a=sorted([r for r in valid if r['workload']==wn and r['display_method']==m],key=lambda z:float(z['normalized_memory']))
  if a:plt.plot([float(r['normalized_memory']) for r in a],[float(r['measured_model_latency_us']) for r in a],mk+'-',label=m,ms=5)
 ref=next(r for r in refs if r['workload']==wn);allmem=sum(int(x['serialized_bytes']) for x in read('primitive_rotation_bench.csv'))
 plt.scatter([ref['total_serialized_bytes']/allmem],[ref['measured_weighted_direct_latency_us']],marker='*',s=120,label='ALL_REQUIRED',c='black')
 plt.xlabel('Serialized-key memory / main all-key proxy');plt.ylabel('Measured-model workload latency (us)');plt.title(wn);plt.legend(fontsize=6,ncol=2);save('memory_measured_'+wn.lower())
x=np.array([float(r['predicted_us']) for r in comp]);y=np.array([float(r['measured_median_us']) for r in comp]);lo=min(x.min(),y.min());hi=max(x.max(),y.max());plt.scatter(x,y,s=9,alpha=.55);plt.plot([lo,hi],[lo,hi],'k--',label='y=x');plt.xlabel('Predicted path latency (us)');plt.ylabel('Measured path median (us)');plt.legend();save('predicted_vs_measured_paths')
err=defaultdict(list)
for r in comp:err[int(r['hop_count'])].append(float(r['max_abs_error']))
for h,v in sorted(err.items()):plt.scatter([h]*len(v),v,s=10,alpha=.5);plt.plot(h,statistics.median(v),'r_')
plt.yscale('log');plt.xlabel('Composition hop count');plt.ylabel('Max absolute decryption error');save('composed_error_by_hop')
audit=read('exact_audit_v2.csv');methods=['OLD_GREEDY','OLD_GREEDY_SWAP','COVERAGE_GREEDY','COVERAGE_GREEDY_SWAP'];statuses=['FEASIBLE','HEURISTIC_INFEASIBLE_BUT_EXACT_FEASIBLE','EXACT_INFEASIBLE'];bottom=np.zeros(len(methods))
for st,col in zip(statuses,['#4daf4a','#e41a1c','#999999']):
 vals=[sum(r['method']==m and r['status']==st for r in audit) for m in methods];plt.bar(methods,vals,bottom=bottom,label=st,color=col);bottom+=vals
plt.ylabel('Small-pool workload/budget cases');plt.xticks(rotation=18,ha='right');plt.legend(fontsize=7);save('exact_audit_feasibility')
rates=[]
for m in ['OLD_GREEDY','COVERAGE_GREEDY']:
 eligible=[r for r in audit if r['method']==m and r['status']!='EXACT_INFEASIBLE'];rates.append(sum(r['status']=='FEASIBLE' for r in eligible)/len(eligible))
plt.bar(['Original GREEDY','COVERAGE_GREEDY'],rates,color=['#e41a1c','#4daf4a']);plt.ylim(0,1);plt.ylabel('Feasibility rate when EXACT is feasible');save('greedy_feasibility_rate')
for m,mk in style.items():
 a=[r for r in valid if r['display_method']==m];
 if a:plt.scatter([int(r['key_count']) for r in a],[float(r['measured_model_latency_us']) for r in a],marker=mk,label=m,alpha=.65)
plt.xlabel('Selected key count');plt.ylabel('Measured-model workload latency (us)');plt.legend(fontsize=6,ncol=2);save('key_count_measured_latency')
ratios=[float(r['ratio']) for r in comp];rel=[abs(float(r['measured_median_us'])/float(r['predicted_us'])-1) for r in comp]
hoplines=[]
for h,v in sorted(err.items()):hoplines.append(f"|{h}|{len(v)}|{max(v):.3e}|{statistics.median(v):.3e}|")
oldfail=sum(r['method']=='OLD_GREEDY' and r['status']=='HEURISTIC_INFEASIBLE_BUT_EXACT_FEASIBLE' for r in audit);covfail=sum(r['method']=='COVERAGE_GREEDY' and r['status']=='HEURISTIC_INFEASIBLE_BUT_EXACT_FEASIBLE' for r in audit);covswapfail=sum(r['method']=='COVERAGE_GREEDY_SWAP' and r['status']=='HEURISTIC_INFEASIBLE_BUT_EXACT_FEASIBLE' for r in audit)
summary=f'''# Result summary V2

## Status

All {len(comp)} unique paths were measured end-to-end from the same original ciphertext per repetition; all passed the `1e-6` correctness tolerance. These measurements form a workload-weighted **measured path model**, not a full application runtime.

- Median measured/predicted path ratio: **{statistics.median(ratios):.4f}**
- Mean measured/predicted path ratio: **{statistics.mean(ratios):.4f}**
- 95th percentile absolute relative error: **{np.percentile(rel,95):.2%}**
- Original GREEDY exact-feasible failures: **{oldfail}**
- COVERAGE_GREEDY exact-feasible failures: **{covfail}**
- COVERAGE_GREEDY_SWAP exact-feasible failures: **{covswapfail}**
- Maximum composed-path error: **{max(max(v) for v in err.values()):.3e}**

The correct audit interpretation is: among the 13 old cases where both the heuristic and exact search returned finite solutions, the observed gap was 0%; however, the original heuristic failed to find a feasible solution in many tight-budget cases where exact search was feasible.

## Correctness by hop count

|Hops|Paths|Maximum error|Median error|
|---:|---:|---:|---:|
{chr(10).join(hoplines)}

## ALL_REQUIRED reference

|Workload|Keys|Serialized-byte proxy|Measured weighted direct latency (us)|
|---|---:|---:|---:|
{chr(10).join(f"|{r['workload']}|{r['required_key_count']}|{r['total_serialized_bytes']:,}|{r['measured_weighted_direct_latency_us']:.2f}|" for r in refs)}
'''
(R/'result_summary_v2.md').write_text(summary)
notes='''# Report notes V2

This is a workload-aware optimization study and makes no claim of cryptographic novelty.

Under the fixed CKKS parameter set, every measured singleton rotation key has the same serialized size (5,507,945 bytes). Therefore the memory constraint in this experiment is equivalent to a cardinality/key-count constraint. The general formulation still allows heterogeneous key sizes.

Individual singleton-key serialization repeats some container metadata, so summed bytes are a consistent experimental proxy rather than the exact serialized size of one combined key map.

`DIRECT_ALL` is preserved in the old raw CSV for compatibility and is called `DIRECT_IN_POOL` in V2 report-facing outputs. `ALL_REQUIRED` directly provisions every workload target and is an unconstrained reference, not a candidate-pool budget point.

Composed measurements restart from the same original ciphertext for every timed repetition. `measured_model_latency_us` is the workload-weighted sum of complete-path median measurements; it is not full application end-to-end runtime. See `report_notes.md` for the complexity analysis, which remains unchanged.
'''
(R/'report_notes_v2.md').write_text(notes)
print('wrote',len(rows),'V2 configurations and',len(refs),'ALL_REQUIRED references')
if __name__=='__main__':pass
