import asyncio, os, sys, json
from pathlib import Path
_ROOT=os.path.dirname(os.path.abspath(__file__))
sys.path[:0]=[_ROOT, os.path.join(_ROOT,'backend')]
from app.agent.models import LLMGateway
from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks
LIVE=Path(_ROOT)/'eval'/'eval_set'/'live_real_world.yaml'
OUT=Path(_ROOT)/'research'/'peek-fulltier.jsonl'
done=set()
if OUT.exists():
    for l in OUT.read_text(encoding='utf-8').splitlines():
        try: d=json.loads(l); done.add((d['task'],d['arm']))
        except: pass
async def main():
    tasks=load_tasks(LIVE)
    out=open(OUT,'a',encoding='utf-8')
    for peek in (False, True):
        arm='peek' if peek else 'blind'
        for t in tasks:
            if (t.id,arm) in done: continue
            gw=_CountingGateway(LLMGateway())
            try:
                rec=await _run_once(t, gw, full=True, peek_plan=peek)
                silent=bool(rec.nominal and not rec.verified)
                d=dict(task=t.id, arm=arm, nominal=rec.nominal, verified=rec.verified, silent=silent,
                       aiu=(rec.tokens or {}).get('total_nano_aiu',0)/1e9, error=rec.error)
                out.write(json.dumps(d)+'\n'); out.flush()
                print(f"{arm} {t.id}: v={rec.verified} n={rec.nominal} {'SILENT' if silent else ''}", flush=True)
            except Exception as e:
                print(f"{arm} {t.id}: EXC {e}", flush=True)
            finally: await gw.close()
    # summary
    rows=[json.loads(l) for l in OUT.read_text(encoding='utf-8').splitlines() if l.strip()]
    for arm in ('blind','peek'):
        rs=[r for r in rows if r['arm']==arm]
        sil=sum(1 for r in rs if r['silent']); ver=sum(1 for r in rs if r['verified'])
        print(f"=== {arm} full-tier: M3(silent)={sil}/{len(rs)}={sil/max(len(rs),1):.3f}  verified={ver}/{len(rs)} ===", flush=True)
asyncio.run(main())
