"""Refresh the STANDARD population metrics (verified rate + silent-failure) over the full live
eval set, on the current DEFAULT engine (agentic, EXECUTION_MODEL=claude-opus-4.8 / medium).

PROCESS-ISOLATED: each task runs in its own `eval.run_one` subprocess (running many agentic
sessions in one process intermittently drops the Copilot session). RESUMABLE: every result is
appended to research/full_metrics_results.jsonl, so an interrupted run re-uses what's done.
Scoring is the harness standard (scoring.tsr / silent_failure_gap; abstain tasks via
harness.score_abstain), so the numbers are directly comparable to the README/ANALYSIS tables.

    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python research/run_full_metrics.py
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from collections import defaultdict

# Make the repo-root `eval` package importable when run as a plain script (PYTHONPATH=backend
# only provides `app`; `-m eval.x` would add cwd, but a script's sys.path[0] is its own dir).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.harness import score_abstain
from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH

OUT = os.path.join("research", "full_metrics_results.jsonl")


def _reap() -> None:
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "copilot.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "copilot/bin/copilot"], capture_output=True)
    except Exception:
        pass


async def _run_one_sub(case_id: str) -> dict:
    _reap()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "eval.run_one", "--only", case_id,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("RESULT "):
            try:
                return json.loads(line[len("RESULT "):])
            except Exception:
                pass
    return {"id": case_id, "error": "no RESULT line", "nominal": None,
            "verified": False, "asked": False, "blocked": False}


def _std_verified(task, r: dict) -> bool:
    """The standard per-task verdict: abstain tasks score by score_abstain, others by the
    independent state-check (`verified`)."""
    if getattr(task, "expect_abstain", False):
        return score_abstain(getattr(task, "abstain_reason", None),
                             asked=bool(r.get("asked")), nominal=bool(r.get("nominal")),
                             blocked=bool(r.get("blocked")))
    return bool(r.get("verified"))


async def main() -> None:
    tasks = load_tasks(str(LIVE_PATH))
    done: dict[str, dict] = {}
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                d = json.loads(line)
                done[d["id"]] = d
            except Exception:
                pass
    print(f"total live tasks: {len(tasks)} | already done: {len(done)} | model=default(opus-4.8)", flush=True)

    f = open(OUT, "a", encoding="utf-8")
    rows = []
    for i, t in enumerate(tasks):
        r = done.get(t.id)
        if r is None:
            r = await _run_one_sub(t.id)
            f.write(json.dumps(r) + "\n")
            f.flush()
        sv = _std_verified(t, r)
        sf = bool(r.get("nominal")) and not sv
        rows.append((t, r, sv))
        print(f"[{i+1}/{len(tasks)}] {t.id} split={t.split} verified={sv} silent_fail={sf} "
              f"err={r.get('error')}", flush=True)
    f.close()

    by = defaultdict(list)
    for t, r, sv in rows:
        by[t.split].append((t, r, sv))
    print("\n=== per-split (standard scoring · default engine = agentic / opus-4.8 / medium) ===", flush=True)
    print("| Split | Tasks | Verified | Silent failures |")
    print("|---|---|---|---|")
    tot_v = tot = tot_sf = 0
    for split in ("dev", "holdout", "sealed"):
        rs = by.get(split, [])
        if not rs:
            continue
        n = len(rs)
        v = sum(1 for _, _, sv in rs if sv)
        sf = sum(1 for _, r, sv in rs if bool(r.get("nominal")) and not sv)
        tot_v += v; tot += n; tot_sf += sf
        print(f"| {split} | {n} | {v/n:.3f} ({v}/{n}) | {sf} |")
    if tot:
        print(f"| **Total** | **{tot}** | **{tot_v/tot:.3f} ({tot_v}/{tot})** | **{tot_sf}** |")
    print(f"\nMETRICS-DONE verified={tot_v}/{tot} silent_failures={tot_sf}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
