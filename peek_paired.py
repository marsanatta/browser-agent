import asyncio, os, sys, json
from pathlib import Path
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_ROOT, os.path.join(_ROOT, "backend")]
from app.agent.models import LLMGateway
from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks

SANDBOX = Path(_ROOT)/"eval"/"eval_set"/"tasks.yaml"
LIVE = Path(_ROOT)/"eval"/"eval_set"/"live_real_world.yaml"
OUT = Path(_ROOT)/"research"/"peek-paired.jsonl"

SINGLE = [("silent_modal_dismiss",5),("silent_overlay_dismiss",5),("silent_premature_success",5),
          ("silent_navigated_away",5),("silent_wrong_button",5),("live_internet_modal",5),
          ("live_internet_lazyload",5),("live_hackernews_newest_nav",5),("live_example_more_info_nav",5)]
MULTI  = [("live_pydocs_json_nav",8),("live_wikipedia_search_submit",8),
          ("live_wikipedia_signin_synonym",8),("live_wikipedia_helium_retrieval",8)]

async def one(task, peek):
    gw=_CountingGateway(LLMGateway())
    try:
        rec=await _run_once(task, gw, full=True, peek_plan=peek)
        tk=rec.tokens or {}
        return dict(nominal=rec.nominal, verified=rec.verified, asked=rec.asked,
                    replanned=rec.replanned, calls=rec.copilot_calls,
                    aiu=tk.get("total_nano_aiu",0)/1e9, input=tk.get("input_tokens",0),
                    output=tk.get("output_tokens",0), reasoning=tk.get("reasoning_tokens",0),
                    error=rec.error)
    finally:
        await gw.close()

# resume: skip (task,pair,arm) already in the JSONL
done=set()
if OUT.exists():
    for ln in OUT.read_text(encoding="utf-8").splitlines():
        try:
            d=json.loads(ln); done.add((d["task"],d["pair"],d["arm"]))
        except Exception: pass

async def main():
    sb={t.id:t for t in load_tasks(SANDBOX)}; lv={t.id:t for t in load_tasks(LIVE)}
    get=lambda tid: sb.get(tid) or lv.get(tid)
    out=open(OUT,"a",encoding="utf-8")
    for kind, items in (("single",SINGLE),("multi",MULTI)):
        for tid,k in items:
            t=get(tid)
            for j in range(k):
                for peek in (False, True):   # PAIRED: blind then peek, back to back
                    arm="peek" if peek else "blind"
                    if (tid,j,arm) in done: continue
                    r=await one(t, peek)
                    out.write(json.dumps(dict(task=tid,kind=kind,arm=arm,pair=j,**r))+"\n"); out.flush()
                    print(f"{tid} {kind} p{j} {arm}: v={r['verified']} n={r['nominal']} aiu={r['aiu']:.1f} replan={r['replanned']} err={r['error']}", flush=True)
    out.close(); print("=== paired runs DONE ===", flush=True)
asyncio.run(main())
