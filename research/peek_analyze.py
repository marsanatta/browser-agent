import json, math, os
from pathlib import Path
from collections import defaultdict
_ROOT = os.path.dirname(os.path.abspath(__file__))
J = Path(_ROOT)/"research"/"peek-paired.jsonl"

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0)
    p=k/n; den=1+z*z/n
    c=(p+z*z/(2*n))/den
    h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/den
    return (max(0,c-h), min(1,c+h))

rows=[json.loads(l) for l in J.read_text(encoding="utf-8").splitlines() if l.strip()]
def vr(rs):
    n=len(rs); k=sum(1 for r in rs if r["verified"]); lo,hi=wilson(k,n)
    return f"{k}/{n}={k/n:.2f} [{lo:.2f},{hi:.2f}]" if n else "n/a", (lo,hi)

print(f"=== rows: {len(rows)} ===")
for sub in ("ALL","single","multi"):
    rs=[r for r in rows if sub=="ALL" or r["kind"]==sub]
    b=[r for r in rs if r["arm"]=="blind"]; p=[r for r in rs if r["arm"]=="peek"]
    bs,(blo,bhi)=vr(b); ps,(plo,phi)=vr(p)
    sep = "SEPARATE" if (plo>bhi or blo>phi) else "OVERLAP"
    print(f"\n[{sub}] verified-rate  blind={bs}  peek={ps}  CIs {sep}")
    # paired McNemar over (task,pair)
    byk=defaultdict(dict)
    for r in rs: byk[(r['task'],r['pair'])][r['arm']]=r['verified']
    pairs=[(d['blind'],d['peek']) for d in byk.values() if 'blind' in d and 'peek' in d]
    b_only=sum(1 for x,y in pairs if x and not y); p_only=sum(1 for x,y in pairs if y and not x)
    diff=sum(y-x for x,y in pairs)/len(pairs) if pairs else 0
    print(f"        paired n={len(pairs)}  peek-only-win={p_only} blind-only-win={b_only}  paired Δverified={diff:+.2f}")
    # cost
    def aiu(rs): 
        a=[r['aiu'] for r in rs]; return sum(a)/len(a) if a else 0
    print(f"        cost AIU/task  blind={aiu(b):.1f}  peek={aiu(p):.1f}  Δ={aiu(p)-aiu(b):+.1f}")
    print(f"        calls/task     blind={sum(r['calls'] for r in b)/max(len(b),1):.2f}  peek={sum(r['calls'] for r in p)/max(len(p),1):.2f}")
    print(f"        replan-rate    blind={sum(r['replanned'] for r in b)/max(len(b),1):.2f}  peek={sum(r['replanned'] for r in p)/max(len(p),1):.2f}")

print("\n=== 2x2 cost AIU/task: {blind-replanned?} x {single/multi} ===")
for kind in ("single","multi"):
    for rp in (False,True):
        b=[r for r in rows if r['arm']=='blind' and r['kind']==kind and r['replanned']==rp]
        # peek cost for the SAME (task,pair) cells where blind had replanned==rp
        keys={(r['task'],r['pair']) for r in b}
        p=[r for r in rows if r['arm']=='peek' and (r['task'],r['pair']) in keys]
        ba=sum(r['aiu'] for r in b)/len(b) if b else 0
        pa=sum(r['aiu'] for r in p)/len(p) if p else 0
        print(f"  {kind:6} blind-replanned={str(rp):5}: n={len(b):3}  blind AIU={ba:5.1f}  peek AIU={pa:5.1f}  Δ={pa-ba:+5.1f}")

print("\n=== modal probe (live_internet_modal silent-failure rate) ===")
for arm in ("blind","peek"):
    rs=[r for r in rows if r['task']=='live_internet_modal' and r['arm']==arm]
    sil=sum(1 for r in rs if r['nominal'] and not r['verified'])
    print(f"  {arm}: silent(nominal&!verified)={sil}/{len(rs)}  verified={sum(r['verified'] for r in rs)}/{len(rs)}")

print("\n=== M3 (silent_failure_gap) over PAIRED tasks per arm ===")
for arm in ("blind","peek"):
    rs=[r for r in rows if r['arm']==arm]
    sil=sum(1 for r in rs if r['nominal'] and not r['verified'])
    print(f"  {arm}: M3={sil}/{len(rs)}={sil/max(len(rs),1):.3f}  (note: full-tier M3 measured separately)")
