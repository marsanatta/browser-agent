"""Capture the agent's FULL action log for ONE case (tool + args + result per call),
to prove HOW it handled an obstacle (e.g. did it actually click a popup-close?).
    GH_TOKEN=$(gh auth token) python research/finance-cases/capture_traj.py --only <id>
"""
import argparse, asyncio, json, os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "backend"))
from app.agent.agentic_executor import AgenticExecutor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType
from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    ap.add_argument("--file", default=str(LIVE_PATH))
    args = ap.parse_args()
    task = next(t for t in load_tasks(args.file) if t.id == args.only)

    gw = LLMGateway()
    planner = _make_planner(gw, task.start_url)
    ex = AgenticExecutor(PlaywrightProvider(headless=True), planner, gateway=gw,
                         start_url=task.start_url, max_attempts=4, peek_plan=True)

    calls = {}   # call_id -> {tool, args, result}
    order = []
    asks = []
    async for ev in ex.run(task.instruction):
        p = ev.payload
        if ev.type == EventType.TOOL_CALL_START:
            cid = p.get("call_id"); calls[cid] = {"tool": p.get("tool"), "args": None, "result": None}; order.append(cid)
        elif ev.type == EventType.TOOL_CALL_ARGS:
            cid = p.get("call_id")
            if cid in calls: calls[cid]["args"] = p.get("args")
        elif ev.type == EventType.TOOL_CALL_END:
            cid = p.get("call_id")
            if cid in calls: calls[cid]["result"] = p.get("result")
        elif ev.type == EventType.ASK_USER:
            asks.append(p)

    print(f"INSTRUCTION: {task.instruction}\nSTART_URL: {task.start_url}\n--- ACTION LOG ({len(order)} calls) ---")
    for i, cid in enumerate(order, 1):
        c = calls[cid]
        a = json.dumps(c["args"], ensure_ascii=False) if c["args"] else ""
        print(f"{i:2}. {c['tool']}({a[:90]}) -> {str(c['result'])[:90]}")
    print("ASKS:", json.dumps(asks, ensure_ascii=False))
    await gw.close()


def _make_planner(gw, start_url):
    try:
        from eval.harness import _StartUrlPlanner
        return _StartUrlPlanner(LLMPlanner(gw), start_url)
    except Exception:
        return LLMPlanner(gw)


asyncio.run(main())
