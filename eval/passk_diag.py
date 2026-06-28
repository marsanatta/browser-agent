"""Diagnostic pass^k runner (#5, LLM_LOOP_IMPROVEMENT_PLAN §5/§7).

Loads the controlled diagnostic set (eval/eval_set/diagnostic.yaml) and runs each task
through the SAME harness._run_once k times, then aggregates per-task pass^k + per-purpose
verified / false-success(CuP) / abstain-correctness / cost, with a mean±bootstrap CI over
tasks. harness.py and its scoring are ONE LINE UNCHANGED — this is purely an external
k-loop + aggregation (respects the "eval untouched" guardrail).

  dev split drives before/after;  --sealed runs ONLY the sealed split, once, at the end.

Run (worktree root, agentic engine):
    AGENT_MODE=agentic GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.passk_diag --k 5
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.agent.models import LLMGateway
from eval.harness import _CountingGateway, _run_once
from eval.loader import EvalTask, load_tasks

DIAG_PATH = Path(__file__).resolve().parent / "eval_set" / "diagnostic.yaml"
REPORT_PATH = Path(__file__).resolve().parent / "PASSK_DIAG.md"


def _bootstrap_ci(values: list[float], iters: int = 1000, seed: int = 12345) -> tuple[float, float]:
    """95% CI of the mean via bootstrap resampling (benchmark generate_plots.py:163-174).
    Deterministic (fixed seed) so the verifier is reproducible."""
    if not values:
        return (0.0, 0.0)
    n = len(values)
    # LCG (no Math.random / numpy needed; deterministic across runs)
    state = seed
    means = []
    for _ in range(iters):
        s = 0.0
        for _ in range(n):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            s += values[state % n]
        means.append(s / n)
    means.sort()
    return (means[int(0.025 * iters)], means[int(0.975 * iters)])


async def _run(tasks: list[EvalTask], k: int) -> tuple[dict[str, Any], _CountingGateway]:
    gw = _CountingGateway(LLMGateway())
    per_task: dict[str, dict[str, Any]] = {}
    try:
        for t in tasks:
            runs = []
            for _ in range(k):
                runs.append(await _run_once(t, gw, full=True))
            verified_all = all(r.verified for r in runs)          # pass^k
            verified_any = any(r.verified for r in runs)
            # false success = the agent claimed done (nominal) but it was not verified, on ANY run
            false_success = any(r.nominal and not r.verified for r in runs)
            per_task[t.id] = {
                "purpose": t.purpose, "split": t.split, "abstain": t.expect_abstain,
                "passk": verified_all, "any": verified_any, "false_success": false_success,
                "calls": sum(r.copilot_calls for r in runs) / k,
                "steps": sum(r.steps for r in runs) / k,
            }
    finally:
        await gw.close()
    return per_task, gw


def _aggregate(per_task: dict[str, Any]) -> str:
    by_purpose: dict[str, list[dict]] = defaultdict(list)
    for v in per_task.values():
        by_purpose[v["purpose"]].append(v)
    lines = ["| purpose | n | pass^k | false-success | avg calls | avg steps |",
             "|---|---|---|---|---|---|"]
    for purpose in sorted(by_purpose):
        rows = by_purpose[purpose]
        n = len(rows)
        passk = sum(r["passk"] for r in rows)
        fs = sum(r["false_success"] for r in rows)
        calls = sum(r["calls"] for r in rows) / n
        steps = sum(r["steps"] for r in rows) / n
        lines.append(f"| {purpose} | {n} | {passk}/{n} | {fs}/{n} | {calls:.1f} | {steps:.1f} |")
    return "\n".join(lines)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5, help="runs per task for pass^k (diag default 5)")
    ap.add_argument("--sealed", action="store_true", help="run ONLY the sealed split, once")
    args = ap.parse_args()

    all_tasks = load_tasks(DIAG_PATH)
    if args.sealed:
        tasks = [t for t in all_tasks if t.split == "sealed"]
        k = 1
    else:
        tasks = [t for t in all_tasks if t.split != "sealed"]
        k = args.k

    per_task, gw = await _run(tasks, k)

    passk_vals = [1.0 if v["passk"] else 0.0 for v in per_task.values()]
    overall_passk = sum(passk_vals) / len(passk_vals) if passk_vals else 0.0
    lo, hi = _bootstrap_ci(passk_vals)
    n_fs = sum(v["false_success"] for v in per_task.values())
    total_calls = gw.calls
    usd = gw.tokens.get("total_nano_aiu", 0) / 1e11

    body = (
        f"# Diagnostic pass^k report (k={k}{', SEALED' if args.sealed else ''})\n\n"
        f"- tasks: {len(per_task)} | overall pass^k: {overall_passk:.3f} "
        f"(95% CI {lo:.3f}–{hi:.3f})\n"
        f"- false-success (nominal&!verified) tasks: {n_fs}\n"
        f"- Copilot calls: {total_calls} | ${usd:.2f}\n\n"
        f"## Per purpose\n\n{_aggregate(per_task)}\n\n"
        f"## Per task\n\n"
        + "\n".join(
            f"- {tid}: pass^k={'Y' if v['passk'] else 'N'} "
            f"false_success={'Y' if v['false_success'] else 'N'} "
            f"calls={v['calls']:.0f} steps={v['steps']:.0f} [{v['purpose']}]"
            for tid, v in per_task.items()
        )
        + "\n"
    )
    REPORT_PATH.write_text(body, encoding="utf-8")
    # headline line for the autoresearch verifier to extract
    print(f"DIAG pass^k={overall_passk:.3f} ci=[{lo:.3f},{hi:.3f}] "
          f"false_success={n_fs} calls={total_calls} usd={usd:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
