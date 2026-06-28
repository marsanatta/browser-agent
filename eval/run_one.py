"""Run a SINGLE live case by id through the official harness path (_run_once,
independent state checks). Used by the autoresearch finance-cases loop to
validate one freshly-designed case at a time.

    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.run_one --only <task_id>
"""

from __future__ import annotations

import argparse
import asyncio
import json

from app.agent.models import LLMGateway

from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True, help="task id to run")
    ap.add_argument("--file", default=str(LIVE_PATH), help="eval-set yaml path")
    args = ap.parse_args()

    tasks = load_tasks(args.file)
    task = next((t for t in tasks if t.id == args.only), None)
    if task is None:
        print("RESULT " + json.dumps({"error": f"task '{args.only}' not found"}))
        return

    gw = _CountingGateway(LLMGateway())
    err = None
    rec = None
    try:
        rec = await _run_once(task, gw, full=True)
    except Exception as exc:  # a flaky live site must not crash the loop
        err = f"{type(exc).__name__}: {exc}"
    finally:
        await gw.close()

    out = {
        "id": task.id,
        "purpose": getattr(task, "purpose", None),
        "error": err,
        "nominal": getattr(rec, "nominal", None),
        "verified": getattr(rec, "verified", None),
        "asked": getattr(rec, "asked", None),
        "blocked": getattr(rec, "blocked", None),
        "steps": getattr(rec, "steps", None),
        "calls": getattr(rec, "copilot_calls", None),
    }
    print("RESULT " + json.dumps(out))


if __name__ == "__main__":
    asyncio.run(main())
