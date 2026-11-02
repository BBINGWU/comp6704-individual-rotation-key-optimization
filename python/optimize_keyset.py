#!/usr/bin/env python3
import csv,heapq,itertools,json,math,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; H=8; S=8192
MAIN=sorted({s*x for x in [1,2,3,4,5,7,8,9,15,16,17,31,32,33,63,64] for s in (-1,1)},key=lambda x:(abs(x),x))
SMALL=sorted({s*x for x in [1,2,3,4,7,8] for s in (-1,1)},key=lambda x:(abs(x),x))
PATH_CACHE={}
def workloads():
 d={}; d['UNIFORM']={r:1/64 for r in range(1,65)}
 z=sum(r**-1.2 for r in range(1,65)); d['ZIPF']={r:r**-1.2/z for r in range(1,65)}
 x=[-33,-32,-31,-1,1,31,32,33]; d['CONV3']={r:1/8 for r in x}
 x=sorted({dy*32+dx for dy in range(-3,4) for dx in range(-3,4) if dy or dx}); d['CONV7']={r:1/len(x) for r in x}
 trace=[]
 for giant in range(0,64,8):
  if giant: trace.append(giant)
  trace += list(range(1,8))
 from collections import Counter
 c=Counter(trace); d['BSGS64']={r:n/len(trace) for r,n in sorted(c.items())}
 return d
def path(target,K,cost):
 # hop-expanded Dijkstra; state is (residue,hops), retains H_max exactly.
 q=[(0,0,0,())]; seen={}; best=None
 while q:
  c,h,r,p=heapq.heappop(q)
  if seen.get((h,r),1e300)<=c: continue
  seen[h,r]=c
  if r==target%S and h: best=(c,h,p); break
  if h<H:
   for k in K: heapq.heappush(q,(c+cost[k],h+1,(r+k)%S,p+(k,)))
 return best
def score(K,w,cost):
 key=tuple(sorted(K))
 if key in PATH_CACHE:
  best=PATH_CACHE[key];ps={r:best.get(r%S) for r in w}
  return (math.inf,ps) if any(v is None for v in ps.values()) else (sum(w[r]*ps[r][0] for r in w),ps)
 # One hop-bounded dynamic program computes all target residues together.
 cur={0:(0,())}; best={}
 for h in range(1,H+1):
  nxt={}
  for r,(v,p) in cur.items():
   for k in K:
    nr=(r+k)%S; nv=v+cost[k]
    if nr not in nxt or (nv,p+(k,))<nxt[nr]:nxt[nr]=(nv,p+(k,))
  for r,(v,p) in nxt.items():
   if r not in best or (v,h,p)<best[r]:best[r]=(v,h,p)
  cur=nxt
 PATH_CACHE[key]=best
 ps={r:best.get(r%S) for r in w}
 return (math.inf,ps) if any(v is None for v in ps.values()) else (sum(w[r]*ps[r][0] for r in w),ps)
def greedy(pool,budget,w,cost,mem):
 K=[-1,1] if -1 in pool and 1 in pool else []
 if sum(mem[k] for k in K)>budget:return None
 while True:
  old,_=score(K,w,cost); choices=[]
  for k in pool:
   if k in K or sum(mem[x] for x in K)+mem[k]>budget:continue
   new,_=score(K+[k],w,cost); gain=(old-new)/mem[k]
   choices.append((-gain,abs(k),k,new))
  if not choices:break
  choices.sort(); _,_,k,new=choices[0]
  if math.isfinite(old) and new>=old-1e-12:break
  K.append(k)
 return sorted(K,key=lambda x:(abs(x),x))
def swap(K,pool,budget,w,cost,mem):
 if K is None:return None
 while True:
  old,_=score(K,w,cost); opts=[]
  for a in K:
   for b in pool:
    if b in K:continue
    J=[x for x in K if x!=a]+[b]
    if sum(mem[x] for x in J)<=budget:
     v,_=score(J,w,cost)
     if v<old-1e-12:opts.append((v,abs(b),b,abs(a),a,J))
  if not opts:return sorted(K,key=lambda x:(abs(x),x))
  K=sorted(opts)[0][-1]
def exact(pool,budget,w,cost,mem):
 best=(math.inf,None)
 for mask in range(1,1<<len(pool)):
  K=[pool[i] for i in range(len(pool)) if mask>>i&1]
  if sum(mem[k] for k in K)>budget:continue
  v,_=score(K,w,cost)
  if (v,[ (abs(x),x) for x in K]) < (best[0],[ (abs(x),x) for x in best[1]] if best[1] else [(999,999)]):best=(v,K)
 return best[1]
def main():
 rows=list(csv.DictReader(open(DATA/'primitive_rotation_bench.csv'))); cost={int(r['rotation']):float(r['median_us']) for r in rows}; mem={int(r['rotation']):int(r['serialized_bytes']) for r in rows}
 ws=workloads();
 with open(DATA/'workloads.csv','w',newline='') as f:
  z=csv.writer(f);z.writerow(['workload','target_rotation','weight']);[z.writerow([n,r,w]) for n,d in ws.items() for r,w in d.items()]
 allmem=sum(mem.values()); budgets=[.15,.25,.4,.6,.8,1.0]
 out=[]
 for wn,w in ws.items():
  for frac in budgets:
   budget=frac*allmem
   methods={'DIRECT_ALL':[k for k in MAIN if k in w],'POWER_OF_TWO':[k for k in MAIN if abs(k)&(abs(k)-1)==0]}
   t=time.perf_counter();methods['GREEDY']=greedy(MAIN,budget,w,cost,mem); gt=time.perf_counter()-t
   t=time.perf_counter();methods['GREEDY_SWAP']=swap(methods['GREEDY'],MAIN,budget,w,cost,mem); st=time.perf_counter()-t+gt
   for mn,K in methods.items():
    t=time.perf_counter()
    if K and sum(mem[k] for k in K)>budget: K=None
    v,ps=score(K or [],w,cost); rt=(gt if mn=='GREEDY' else st if mn=='GREEDY_SWAP' else time.perf_counter()-t)
    hops=[ps[r][1] for r in w] if math.isfinite(v) else []
    out.append([wn,mn,frac,'INFEASIBLE' if not math.isfinite(v) else 'OK',json.dumps(K),len(K or []),sum(mem[k] for k in K or []),sum(mem[k] for k in K or []) / allmem,v,'NA',sum(w[r]*ps[r][1] for r in w) if hops else 'NA',max(hops) if hops else 'NA','NA',rt,'NA','NA',json.dumps({r:(ps[r][2] if ps[r] else None) for r in w})])
  # exact small pool at budgets relative to small baseline; gap rows kept separately
 cols=['workload','method','budget_fraction','status','selected_keys','key_count','total_bytes','normalized_memory','predicted_latency_us','measured_latency_us','average_hops','maximum_hops','max_error','optimizer_runtime_s','exact_optimum_us','optimality_gap','paths']
 with open(DATA/'optimization_results.csv','w',newline='') as f: csv.writer(f).writerows([cols]+out)
 # exact/gap study on small candidate pool, with greedy variants under the same small-pool budgets
 gaps=[]; sm=sum(mem[k] for k in SMALL)
 for wn,w in ws.items():
  for frac in budgets:
   b=frac*sm;t=time.perf_counter();E=exact(SMALL,b,w,cost,mem); et=time.perf_counter()-t; ev,_=score(E or [],w,cost)
   for mn,fun in [('GREEDY',lambda:greedy(SMALL,b,w,cost,mem)),('GREEDY_SWAP',lambda:swap(greedy(SMALL,b,w,cost,mem),SMALL,b,w,cost,mem))]:
    t=time.perf_counter();K=fun();rt=time.perf_counter()-t;v,_=score(K or [],w,cost);gap=(v/ev-1) if math.isfinite(v) and math.isfinite(ev) else 'NA'
    gaps.append([wn,frac,mn,json.dumps(K),v,json.dumps(E),ev,gap,rt,et])
 with open(DATA/'exact_gaps.csv','w',newline='') as f:csv.writer(f).writerows([['workload','budget_fraction','method','selected_keys','cost_us','exact_keys','exact_cost_us','optimality_gap','runtime_s','exact_runtime_s']]+gaps)
 # deterministic stability at 60% main budget
 stab=[]
 for wn,w in ws.items():
  base=swap(greedy(MAIN,.6*allmem,w,cost,mem),MAIN,.6*allmem,w,cost,mem)
  for seed in range(1,11):
   rng=random.Random(seed); p={r:max(0,w[r]*(1+rng.uniform(-.1,.1))) for r in w};z=sum(p.values());p={r:v/z for r,v in p.items()};K=swap(greedy(MAIN,.6*allmem,p,cost,mem),MAIN,.6*allmem,p,cost,mem);j=len(set(base)&set(K))/len(set(base)|set(K))
   stab.append([wn,seed,json.dumps(base),json.dumps(K),j,K!=base])
 with open(DATA/'stability.csv','w',newline='') as f:csv.writer(f).writerows([['workload','seed','baseline_keys','perturbed_keys','jaccard','changed']]+stab)
if __name__=='__main__':main()
