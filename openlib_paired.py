import asyncio, os, sys, json
from pathlib import Path
_ROOT=os.path.dirname(os.path.abspath(__file__))
sys.path[:0]=[_ROOT, os.path.join(_ROOT,'backend')]
from app.agent.models import LLMGateway
from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks
LIVE=Path(_ROOT)/'eval'/'eval_set'/'live_real_world.yaml'
OUT=Path(_ROOT)/'research'/'openlib-paired.jsonl'
TID='live_openlibrary_login_nav'; K=8
async def one(t,peek):
    gw=_CountingGateway(LLMGateway())
    try:
        r=await _run_once(t,gw,full=True,peek_plan=peek)
        return r.verified, r.nominal, (r.tokens or {}).get('total_nano_aiu',0)/1e9, r.error
    finally: await gw.close()
async def main():
    t={x.id:x for x in load_tasks(LIVE)}[TID]
    out=open(OUT,'a',encoding='utf-8')
    for j in range(K):
        for peek in (False,True):
            v,n,a,e=await one(t,peek)
            out.write(json.dumps(dict(task=TID,arm='peek' if peek else 'blind',pair=j,verified=v,nominal=n,aiu=a,error=e))+'\n'); out.flush()
            print(f"pair{j} {'peek' if peek else 'blind'}: v={v} n={n} aiu={a:.1f} err={e}",flush=True)
    rows=[json.loads(l) for l in OUT.read_text(encoding='utf-8').splitlines() if l.strip()]
    from collections import defaultdict
    byk=defaultdict(dict)
    for r in rows: byk[r['pair']][r['arm']]=r['verified']
    pairs=[(d['blind'],d['peek']) for d in byk.values() if 'blind' in d and 'peek' in d]
    bo=sum(1 for x,y in pairs if x and not y); po=sum(1 for x,y in pairs if y and not x)
    bv=sum(1 for x,y in pairs if x); pv=sum(1 for x,y in pairs if y)
    print(f"=== openlib paired n={len(pairs)}: blind verified={bv}/{len(pairs)}  peek verified={pv}/{len(pairs)}  peek-only-win={po} blind-only-win={bo} ===",flush=True)
    print("VERDICT:", "peek REAL regression" if bo>=3 and bo>po else ("single-flip was NOISE / peek not worse" if pv>=bv else "inconclusive"),flush=True)
asyncio.run(main())
