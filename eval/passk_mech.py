"""Reference-mechanism pass^k runner (round-3 experiments).

Loads eval/eval_set/mechanisms.yaml and runs each probe through the SAME harness._run_once
k times, then aggregates per-FAMILY pass^k + false-success(CuP) + abstain-correctness and —
crucially — COST (Copilot calls, input tokens ~= perception size, total nano_aiu). The central
question for the index-all / stable-ID / change-signal mechanisms is the cost tradeoff, so the
cost columns are first-class. harness.py is ONE LINE UNCHANGED (external k-loop only).

  AGENT_MODE=agentic GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.passk_mech --k 3
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Any

from eval.harness import _CountingGateway, _run_once, make_gateway
from eval.loader import EvalTask, load_tasks

MECH_PATH = Path(__file__).resolve().parent / "eval_set" / "mechanisms.yaml"
REPORT_PATH = Path(__file__).resolve().parent / "PASSK_MECH.md"


def _family(task_id: str) -> str:
    # mech_A1_dup_same_dest -> "A"
    parts = task_id.split("_")
    return parts[1][0] if len(parts) > 1 and parts[1] else "?"


async def _run(tasks: list[EvalTask], k: int) -> tuple[dict[str, Any], _CountingGateway]:
    gw = make_gateway()
    per_task: dict[str, dict[str, Any]] = {}
    try:
        for t in tasks:
            runs = []
            for _ in range(k):
                runs.append(await _run_once(t, gw, full=True))
            false_success = any(r.nominal and not r.verified for r in runs)
            per_task[t.id] = {
                "family": _family(t.id),
                "purpose": t.purpose,
                "abstain": t.expect_abstain,
                "passk": all(r.verified for r in runs),
                "false_success": false_success,
                "calls": sum(r.copilot_calls for r in runs) / k,
                "steps": sum(r.steps for r in runs) / k,
                "in_tok": sum(r.tokens.get("input_tokens", 0) for r in runs) / k,
                "naiu": sum(r.tokens.get("total_nano_aiu", 0) for r in runs) / k,
            }
    finally:
        await gw.close()
    return per_task, gw


def _aggregate(per_task: dict[str, Any]) -> str:
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for v in per_task.values():
        by_fam[v["family"]].append(v)
    lines = ["| family | n | pass^k | false-succ | avg calls | avg steps | avg in_tok | avg nano_aiu |",
             "|---|---|---|---|---|---|---|---|"]
    for fam in sorted(by_fam):
        rows = by_fam[fam]
        n = len(rows)
        passk = sum(r["passk"] for r in rows)
        fs = sum(r["false_success"] for r in rows)
        calls = sum(r["calls"] for r in rows) / n
        steps = sum(r["steps"] for r in rows) / n
        intok = sum(r["in_tok"] for r in rows) / n
        naiu = sum(r["naiu"] for r in rows) / n
        lines.append(f"| {fam} | {n} | {passk}/{n} | {fs}/{n} | {calls:.1f} | {steps:.1f} "
                     f"| {intok:.0f} | {naiu/1e9:.2f}e9 |")
    return "\n".join(lines)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="runs per probe for pass^k (default 3)")
    ap.add_argument("--tag", default="baseline", help="label for this run (e.g. baseline, index_all)")
    args = ap.parse_args()

    tasks = [t for t in load_tasks(MECH_PATH) if t.split != "sealed"]
    per_task, gw = await _run(tasks, args.k)

    n = len(per_task)
    passk = sum(1 for v in per_task.values() if v["passk"])
    n_fs = sum(v["false_success"] for v in per_task.values())
    usd = gw.tokens.get("total_nano_aiu", 0) / 1e11

    body = (
        f"# Reference-mechanism pass^k report — {args.tag} (k={args.k})\n\n"
        f"- probes: {n} | overall pass^k: {passk}/{n} | false-success: {n_fs}\n"
        f"- TOTAL Copilot calls: {gw.calls} | ${usd:.2f}\n\n"
        f"## Per family (cost is first-class: calls / in_tok / nano_aiu)\n\n{_aggregate(per_task)}\n\n"
        f"## Per probe\n\n"
        + "\n".join(
            f"- {tid}: pass^k={'Y' if v['passk'] else 'N'} "
            f"false_succ={'Y' if v['false_success'] else 'N'} "
            f"calls={v['calls']:.0f} steps={v['steps']:.0f} in_tok={v['in_tok']:.0f} "
            f"[{v['family']}/{v['purpose']}]"
            for tid, v in per_task.items()
        )
        + "\n"
    )
    REPORT_PATH.write_text(body, encoding="utf-8")
    print(f"MECH[{args.tag}] pass^k={passk}/{n} false_success={n_fs} "
          f"calls={gw.calls} usd={usd:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
