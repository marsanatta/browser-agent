"""Capture the agent's event trajectory for ONE case (debug a false abstention).
    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python research/finance-cases/capture_traj.py --only <id>
"""
import argparse, asyncio, json, os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)                       # repo root -> `eval` package
sys.path.insert(0, os.path.join(_ROOT, "backend"))  # `app` package
from app.agent.agentic_executor import AgenticExecutor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType
from eval.loader import load_tasks
from eval.harness import _StartUrlPlanner
from eval.run_live_tier import LIVE_PATH


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    ap.add_argument("--file", default=str(LIVE_PATH))
    args = ap.parse_args()
    task = next(t for t in load_tasks(args.file) if t.id == args.only)

    gw = LLMGateway()
    planner = _StartUrlPlanner(LLMPlanner(gw), task.start_url)
    ex = AgenticExecutor(
        PlaywrightProvider(headless=True), planner, gateway=gw,
        start_url=task.start_url, max_attempts=4, peek_plan=True,
    )
    asks, tools, texts, final_url = [], [], [], None
    async for ev in ex.run(task.instruction):
        t = ev.type
        if t == EventType.ASK_USER:
            asks.append(ev.payload)
        elif t == EventType.TOOL_CALL_END:
            tools.append(str(ev.payload)[:140])
        elif t == EventType.TEXT_MESSAGE:
            for v in ev.payload.values():
                if isinstance(v, str) and v.strip():
                    texts.append(v.strip())
    print("INSTRUCTION:", task.instruction)
    print("\nLAST 16 TOOL RESULTS:")
    for x in tools[-16:]:
        print("  ", x)
    print("\nASK_USER payloads:", json.dumps(asks, ensure_ascii=False))
    print("\nAGENT TEXT (last 800):", " ".join(texts)[-800:])
    await gw.close()


asyncio.run(main())
