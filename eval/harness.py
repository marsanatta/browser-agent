"""M3 eval harness: run each task through the REAL agent, score against
independent ground truth, and emit REPORT.md.

What is REAL here:
  - Tasks run through the actual Executor (perceive/locate/act/verify loop).
  - The LLM planner routes through the Copilot gateway (the hard constraint).
  - Success is re-derived from the LIVE page via eval.verify (never self-report).
  - A budget-matched vanilla baseline (max_attempts=1, no L2 heal) runs alongside
    the full agent, satisfying the non-negotiable ablation rule (architecture/03 §4).
  - pass^k (k=3) is measured for side-effecting tasks by re-running them.

Run (from the repo root, with COPILOT auth available for the planner):
    PYTHONPATH=backend python -m eval.harness [--limit N] [--k 3]
or use scripts/run-eval.ps1. `eval` is a top-level package that imports `app.*`,
so the backend dir must be on PYTHONPATH and the cwd must be the repo root.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass
from typing import Any

from app.agent.executor import Executor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

from eval import report as report_mod
from eval import scoring
from eval.loader import EvalTask, load_tasks
from eval.scoring import TaskResult
from eval.verify import key_node_check, state_check

K_SIDE_EFFECT = 3  # pass^k for side-effecting tasks (eval/02 §F2)


class _CountingGateway:
    """Wraps the real LLMGateway to count Copilot calls (the binding cost metric —
    DESIGN §11: requests-per-task, not $/token). Delegates everything else."""

    def __init__(self, inner: LLMGateway) -> None:
        self._inner = inner
        self.calls = 0

    async def complete(self, prompt: str, model: str | None = None) -> Any:
        self.calls += 1
        if model is None:
            return await self._inner.complete(prompt)
        return await self._inner.complete(prompt, model=model)

    async def judge(self, prompt: str) -> Any:
        self.calls += 1
        return await self._inner.judge(prompt)

    async def close(self) -> None:
        await self._inner.close()


class _StartUrlPlanner:
    """Seed a navigate sub-task for the task's start URL (same shape as main.py)."""

    def __init__(self, inner: Any, start_url: str) -> None:
        self._inner = inner
        self._start_url = start_url

    async def plan(self, task: str) -> list[SubTask]:
        subtasks = await self._inner.plan(task)
        if subtasks and subtasks[0].action == "navigate":
            return subtasks
        return [SubTask(action="navigate", url=self._start_url, description="open start URL"), *subtasks]


@dataclass
class RunRecord:
    nominal: bool
    verified: bool
    key_nodes_hit: int
    key_nodes_total: int
    error: str | None
    steps: int
    copilot_calls: int


async def _run_once(task: EvalTask, gateway: _CountingGateway, *, full: bool) -> RunRecord:
    """One execution of one task. `full` = agent with the recovery ladder + L2 heal;
    not full = budget-matched vanilla baseline (1 attempt, no heal)."""
    hit_nodes: list[bool] = [False] * len(task.key_nodes)

    async def step_hook(page: Any) -> bool:
        for idx, node in enumerate(task.key_nodes):
            if not hit_nodes[idx] and await key_node_check(page, node):
                hit_nodes[idx] = True
        return True

    verified_box: dict[str, bool] = {"v": False}

    async def verify_hook(page: Any) -> bool:
        # check key nodes once more on the final page too (covers end-state nodes)
        await step_hook(page)
        ok = await state_check(page, task.assertion)
        verified_box["v"] = ok
        return ok

    calls_before = gateway.calls
    planner = _StartUrlPlanner(LLMPlanner(gateway), task.start_url)
    executor = Executor(
        PlaywrightProvider(headless=True),
        planner,
        gateway=gateway if full else None,   # L2 LLM heal only in the full agent
        verify_hook=verify_hook,
        step_hook=step_hook,
        max_attempts=4 if full else 1,        # budget-matched: baseline gets 1 attempt
    )

    nominal = False
    steps = 0
    error: str | None = None
    try:
        async for ev in executor.run(task.instruction):
            if ev.type == EventType.STEP_STARTED:
                steps += 1
            elif ev.type == EventType.RUN_FINISHED:
                nominal = bool(ev.payload.get("nominal_completion"))
            elif ev.type == EventType.RUN_ERROR:
                error = str(ev.payload.get("error"))
    except Exception as exc:  # harness must survive a single task crashing
        error = f"{type(exc).__name__}: {exc}"

    return RunRecord(
        nominal=nominal,
        verified=verified_box["v"],
        key_nodes_hit=sum(hit_nodes),
        key_nodes_total=len(task.key_nodes),
        error=error,
        steps=steps,
        copilot_calls=gateway.calls - calls_before,
    )


def _to_result(task: EvalTask, rec: RunRecord) -> TaskResult:
    return TaskResult(
        task_id=task.id,
        nominal=rec.nominal,
        verified=rec.verified,
        key_nodes_hit=rec.key_nodes_hit,
        key_nodes_total=rec.key_nodes_total,
        task_type=task.task_type,
        held_out=task.held_out,
        error=rec.error,
        extra={"steps": rec.steps, "copilot_calls": rec.copilot_calls},
    )


async def run_eval(tasks: list[EvalTask], k: int = K_SIDE_EFFECT) -> dict[str, Any]:
    gateway = _CountingGateway(LLMGateway())
    agent_results: list[TaskResult] = []
    baseline_results: list[TaskResult] = []
    passk_runs: dict[str, list[TaskResult]] = {}

    try:
        for task in tasks:
            rec = await _run_once(task, gateway, full=True)
            agent_results.append(_to_result(task, rec))

            base = await _run_once(task, gateway, full=False)
            baseline_results.append(_to_result(task, base))

            if task.task_type == "side_effect":
                runs = [agent_results[-1]]
                for _ in range(k - 1):
                    extra = await _run_once(task, gateway, full=True)
                    runs.append(_to_result(task, extra))
                passk_runs[task.id] = runs
    finally:
        await gateway.close()

    return {
        "agent": agent_results,
        "baseline": baseline_results,
        "passk_runs": passk_runs,
        "k": k,
        "copilot_calls": gateway.calls,
    }


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    agent = data["agent"]
    baseline = data["baseline"]
    tsr_mean, tsr_se = scoring.mean_se(agent)
    base_tsr_mean, base_tsr_se = scoring.mean_se(baseline)
    held = [r for r in agent if r.held_out]
    return {
        "agent_tcr": scoring.tcr(agent),
        "agent_tsr": tsr_mean,
        "agent_tsr_se": tsr_se,
        "agent_cup": scoring.silent_failure_gap(agent),
        "baseline_tcr": scoring.tcr(baseline),
        "baseline_tsr": base_tsr_mean,
        "baseline_tsr_se": base_tsr_se,
        "baseline_cup": scoring.silent_failure_gap(baseline),
        "passk": scoring.pass_hat_k(data["passk_runs"]),
        "held_out_tsr": scoring.tsr(held) if held else None,
        "n": len(agent),
        "n_held_out": len(held),
        "copilot_calls": data["copilot_calls"],
    }


async def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="run only first N tasks")
    ap.add_argument("--k", type=int, default=K_SIDE_EFFECT)
    args = ap.parse_args()

    tasks = load_tasks()
    if args.limit:
        tasks = tasks[: args.limit]

    t0 = time.time()
    data = await run_eval(tasks, k=args.k)
    elapsed = time.time() - t0
    summary = summarize(data)

    out_path = report_mod.write_report(tasks, data, summary, elapsed)
    print(f"REPORT written: {out_path}")
    print(
        f"agent TSR={summary['agent_tsr']:.3f}  TCR={summary['agent_tcr']:.3f}  "
        f"CuP-gap={summary['agent_cup']:.3f}  pass^{args.k}={summary['passk']:.3f}  "
        f"Copilot calls={summary['copilot_calls']}  ({elapsed:.0f}s)"
    )


if __name__ == "__main__":
    asyncio.run(_main())
