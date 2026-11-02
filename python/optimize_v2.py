#!/usr/bin/env python3
import csv,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';sys.path.insert(0,str(ROOT/'python'))
import optimize_keyset as old

def metrics(K,w,cost):
 old.score(K,w,cost);best=old.PATH_CACHE.get(tuple(sorted(K)),{})
 ps={r:best.get(r%old.S) for r in w};cov=sum(w[r] for r,p in ps.items() if p);res=len(best)
 hop=sum(w[r]*p[1] for r,p in ps.items() if p)/cov if cov else math.inf
 val=sum(w[r]*p[0] for r,p in ps.items()) if cov>1-1e-12 else math.inf
 return cov,res,hop,val,ps
def coverage_greedy(pool,budget,w,cost,mem):
 K=[]
 while True:
  cov,res,hop,val,_=metrics(K,w,cost);opts=[]
  for k in pool:
   if k in K or sum(mem[x] for x in K)+mem[k]>budget:continue
   nc,nr,nh,nv,_=metrics(K+[k],w,cost)
   if cov<1-1e-12:rank=(-(nc-cov)/mem[k],-(nr-res)/mem[k],nh,abs(k),k,nv)
   else:rank=(-((val-nv)/mem[k]),0,nh,abs(k),k,nv)
   opts.append((rank,k,nc,nv))
  if not opts:break
  opts.sort(key=lambda x:x[0]);rank,k,nc,nv=opts[0]
  if cov<1-1e-12:
   if nc<=cov+1e-15 and rank[1]>=0:break
  elif not nv<val-1e-12:break
  K.append(k)
 return sorted(K,key=lambda x:(abs(x),x))
def coverage_swap(K,pool,budget,w,cost,mem):
 while K:
  cov,_,_,val,_=metrics(K,w,cost);base=(-cov,val if cov>=1-1e-12 else math.inf)
  opts=[]
  for a in K:
   for b in pool:
    if b in K:continue
    J=[x for x in K if x!=a]+[b]
    if sum(mem[x] for x in J)>budget:continue
    nc,_,_,nv,_=metrics(J,w,cost);obj=(-nc,nv if nc>=1-1e-12 else math.inf)
    if obj<base:opts.append((obj,abs(b),b,abs(a),a,J))
  if not opts:break
  K=sorted(opts,key=lambda x:x[:-1])[0][-1]
 return sorted(K,key=lambda x:(abs(x),x))
def row(wn,mn,frac,K,w,cost,mem,allmem,runtime):
 cov,res,hop,val,ps=metrics(K,w,cost);ok=cov>=1-1e-12
 return {'workload':wn,'method':mn,'budget_fraction':frac,'status':'OK' if ok else 'INFEASIBLE','selected_keys':json.dumps(K),'key_count':len(K),'total_bytes':sum(mem[k] for k in K),'normalized_memory':sum(mem[k] for k in K)/allmem,'predicted_latency_us':val if ok else 'inf','measured_latency_us':'NA','average_hops':hop if cov else 'NA','maximum_hops':max((p[1] for p in ps.values() if p),default='NA'),'max_error':'NA','optimizer_runtime_s':runtime,'exact_optimum_us':'NA','optimality_gap':'NA','paths':json.dumps({r:(ps[r][2] if ps[r] else None) for r in w})}
def main():
 prim=list(csv.DictReader(open(DATA/'primitive_rotation_bench.csv')));cost={int(r['rotation']):float(r['median_us']) for r in prim};mem={int(r['rotation']):int(r['serialized_bytes']) for r in prim};allmem=sum(mem.values());ws=old.workloads();budgets=[.15,.25,.4,.6,.8,1.0]
 base=list(csv.DictReader(open(DATA/'optimization_results.csv')));new=[]
 for wn,w in ws.items():
  for frac in budgets:
   b=frac*allmem;t=time.perf_counter();K=coverage_greedy(old.MAIN,b,w,cost,mem);rt=time.perf_counter()-t;new.append(row(wn,'COVERAGE_GREEDY',frac,K,w,cost,mem,allmem,rt))
   t=time.perf_counter();J=coverage_swap(K,old.MAIN,b,w,cost,mem);new.append(row(wn,'COVERAGE_GREEDY_SWAP',frac,J,w,cost,mem,allmem,rt+time.perf_counter()-t))
 fields=list(base[0]);
 with open(DATA/'coverage_results.csv','w',newline='') as f:wri=csv.DictWriter(f,fieldnames=fields);wri.writeheader();wri.writerows(new)
 # Exact audit: identical small-pool budgets, with infeasible heuristic gaps recorded as infinity.
 audit=[];sm=sum(mem[k] for k in old.SMALL)
 for wn,w in ws.items():
  for frac in budgets:
   b=frac*sm;E=old.exact(old.SMALL,b,w,cost,mem);ev=old.score(E or [],w,cost)[0]
   methods={'OLD_GREEDY':old.greedy(old.SMALL,b,w,cost,mem)};methods['OLD_GREEDY_SWAP']=old.swap(methods['OLD_GREEDY'],old.SMALL,b,w,cost,mem)
   C=coverage_greedy(old.SMALL,b,w,cost,mem);methods['COVERAGE_GREEDY']=C;methods['COVERAGE_GREEDY_SWAP']=coverage_swap(C,old.SMALL,b,w,cost,mem)
   for mn,K in methods.items():
    v=old.score(K or [],w,cost)[0]
    if not math.isfinite(ev):status='EXACT_INFEASIBLE';gap='NA'
    elif not math.isfinite(v):status='HEURISTIC_INFEASIBLE_BUT_EXACT_FEASIBLE';gap='inf'
    else:status='FEASIBLE';gap=v/ev-1
    audit.append([wn,frac,mn,status,json.dumps(K),v,json.dumps(E),ev,gap])
 with open(DATA/'exact_audit_v2.csv','w',newline='') as f:csv.writer(f).writerows([['workload','budget_fraction','method','status','selected_keys','cost_us','exact_keys','exact_cost_us','optimality_gap']]+audit)
 # Include paths from old feasible configurations and new coverage configurations for one complete composed benchmark.
 paths=set()
 for r in base+new:
  if r['status']=='OK':
   for p in json.loads(r['paths']).values():
    if p:paths.add(tuple(p))
 paths=sorted(paths,key=lambda p:(len(p),p))
 with open(DATA/'composition_paths_input.csv','w',newline='') as f:wri=csv.writer(f);wri.writerow(['path_id','path']);wri.writerows((i,';'.join(map(str,p))) for i,p in enumerate(paths,1))
 targets={r for w in ws.values() for r in w};(DATA/'all_required_missing.txt').write_text('\n'.join(map(str,sorted(targets-set(cost))))+'\n')
 print('coverage rows',len(new),'unique combined paths',len(paths))
if __name__=='__main__':main()
