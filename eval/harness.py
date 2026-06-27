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
from dataclasses import dataclass, field
from typing import Any

from app.agent.executor import Executor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

from eval import audit
from eval import report as report_mod
from eval import scoring
from eval.loader import EvalTask, load_tasks
from eval.scoring import TaskResult
from eval.verify import key_node_check, state_check

K_SIDE_EFFECT = 3  # pass^k for side-effecting tasks (eval/02 §F2)


def score_abstain(abstain_reason: str | None, *, asked: bool, nominal: bool, blocked: bool) -> bool:
    """Score an expect_abstain task by OUTCOME, not page state. A correct refusal is
    asking the user without falsely claiming success. When `abstain_reason == "blocked"`
    the refusal must be caused by a real bot-wall (rec.blocked) — a generic
    local-exhaustion ask_user does NOT count as a correct blocked-abstain. Default /
    "impossible" keep the original outcome-only rule (asked AND not nominal)."""
    correct_refusal = asked and not nominal
    if abstain_reason == "blocked":
        return correct_refusal and blocked
    return correct_refusal


class _CountingGateway:
    """Wraps the real LLMGateway to count Copilot calls (the binding cost metric —
    DESIGN §11: requests-per-task, not $/token). Delegates everything else."""

    def __init__(self, inner: LLMGateway) -> None:
        self._inner = inner
        self.calls = 0
        self.tokens = {"output_tokens": 0, "input_tokens": 0, "reasoning_tokens": 0,
                       "total_nano_aiu": 0}

    def __getattr__(self, name: str) -> Any:
        # Transparent proxy for inner-gateway attributes the executor/planner read
        # (e.g. replanner_model, replanner_effort, workhorse_model). __getattr__ only
        # fires for attributes absent on the wrapper, so .calls/.tokens stay local.
        if name == "_inner":
            raise AttributeError(name)
        return getattr(self._inner, name)

    def _accrue(self, resp: Any) -> None:
        # Prefer the full assistant.usage ledger; fall back to the output_tokens read.
        usage = getattr(resp, "usage", None)
        if usage:
            for k in self.tokens:
                if usage.get(k):
                    self.tokens[k] += usage[k]
        else:
            ot = getattr(resp, "output_tokens", None)
            if ot:
                self.tokens["output_tokens"] += ot

    async def complete(
        self, prompt: str, model: str | None = None, reasoning_effort: str | None = None
    ) -> Any:
        self.calls += 1
        resp = await self._inner.complete(prompt, model=model, reasoning_effort=reasoning_effort)
        self._accrue(resp)
        return resp

    async def close(self) -> None:
        await self._inner.close()


class _StartUrlPlanner:
    """Seed a navigate sub-task for the task's start URL (same shape as main.py)."""

    def __init__(self, inner: Any, start_url: str) -> None:
        self._inner = inner
        self._start_url = start_url

    async def plan(
        self, task: str, start_url: str | None = None, observation: str | None = None
    ) -> list[SubTask]:
        if observation is not None:
            # peek-plan: the executor already navigated to the start page, so do NOT
            # prepend a navigate; plan grounded in the observation.
            return await self._inner.plan(task, observation=observation)
        subtasks = await self._inner.plan(task, start_url=self._start_url)
        if subtasks and subtasks[0].action == "navigate":
            return subtasks
        return [SubTask(action="navigate", url=self._start_url, description="open start URL"), *subtasks]

    async def replan(self, task: str, failure_log: list[dict], observation: str) -> list[SubTask]:
        return await self._inner.replan(task, failure_log, observation)


@dataclass
class RunRecord:
    nominal: bool
    verified: bool
    key_nodes_hit: int
    key_nodes_total: int
    error: str | None
    steps: int
    copilot_calls: int
    step_verdicts: list[str] = field(default_factory=list)
    asked: bool = False
    # Audit instrumentation (observe-only): the planner's plan, the reduced per-step
    # trace, the real per-task token ledger, and whether a bot-wall was hit.
    tokens: dict = field(default_factory=dict)
    blocked: bool = False
    plan: list = field(default_factory=list)
    audit_steps: list = field(default_factory=list)
    replanned: bool = False  # did a global replan fire (peek-plan experiment cost cut)


async def _run_once(
    task: EvalTask, gateway: _CountingGateway, *, full: bool, peek_plan: bool = True
) -> RunRecord:
    """One execution of one task. `full` = agent with the recovery ladder + L2 heal;
    not full = budget-matched vanilla baseline (1 attempt, no heal). `peek_plan` = see
    the start page before the initial plan; DEFAULT True (autoresearch KEEP — more
    verified, net cheaper, M3->0). Pass peek_plan=False to measure the blind baseline."""
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
    tokens_before = dict(gateway.tokens)
    planner = _StartUrlPlanner(LLMPlanner(gateway), task.start_url)
    executor = Executor(
        PlaywrightProvider(headless=True),
        planner,
        gateway=gateway if full else None,   # L2 LLM heal only in the full agent
        verify_hook=verify_hook,
        step_hook=step_hook,
        max_attempts=4 if full else 1,        # budget-matched: baseline gets 1 attempt
        peek_plan=peek_plan,
        start_url=task.start_url,
    )

    nominal = False
    steps = 0
    asked = False
    step_verdicts: list[str] = []
    error: str | None = None
    events_seen: list = []
    try:
        async for ev in executor.run(task.instruction):
            events_seen.append(ev)
            if ev.type == EventType.STEP_STARTED:
                steps += 1
            elif ev.type == EventType.STEP_FINISHED:
                v = ev.payload.get("verdict")
                if v:
                    step_verdicts.append(v)
            elif ev.type == EventType.ASK_USER:
                asked = True
            elif ev.type == EventType.RUN_FINISHED:
                nominal = bool(ev.payload.get("nominal_completion"))
            elif ev.type == EventType.RUN_ERROR:
                error = str(ev.payload.get("error"))
    except Exception as exc:  # harness must survive a single task crashing
        error = f"{type(exc).__name__}: {exc}"

    reduced = audit.reduce_events(events_seen)
    task_tokens = {k: gateway.tokens[k] - tokens_before.get(k, 0) for k in gateway.tokens}

    # Abstain tasks are scored by OUTCOME, not page state (see score_abstain): a
    # `blocked` task must have actually hit a bot-wall, not just exhausted locally.
    if task.expect_abstain:
        verified = score_abstain(
            task.abstain_reason, asked=asked, nominal=nominal, blocked=reduced["blocked"]
        )
    else:
        verified = verified_box["v"]

    return RunRecord(
        nominal=nominal,
        verified=verified,
        key_nodes_hit=sum(hit_nodes),
        key_nodes_total=len(task.key_nodes),
        error=error,
        steps=steps,
        copilot_calls=gateway.calls - calls_before,
        step_verdicts=step_verdicts,
        asked=asked,
        tokens=task_tokens,
        blocked=reduced["blocked"],
        plan=reduced["plan"],
        audit_steps=reduced["steps"],
        replanned=any("REPLAN" in (s.get("recovery") or []) for s in reduced["steps"]),
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
        extra={
            "steps": rec.steps,
            "copilot_calls": rec.copilot_calls,
            "step_verdicts": rec.step_verdicts,
            "asked": rec.asked,
        },
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


def summarize(data: dict[str, Any], tasks: list[EvalTask]) -> dict[str, Any]:
    # Regression-anchors (green-on-day-one) are kept OUT of the headline rate so
    # they cannot inflate it; they still run and are reported as a separate count.
    anchor_ids = {t.id for t in tasks if t.regression_anchor}
    agent = [r for r in data["agent"] if r.task_id not in anchor_ids]
    baseline = [r for r in data["baseline"] if r.task_id not in anchor_ids]
    anchors = [r for r in data["agent"] if r.task_id in anchor_ids]
    passk_runs = {t: rs for t, rs in data["passk_runs"].items() if t not in anchor_ids}
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
        "passk": scoring.pass_hat_k(passk_runs),
        "held_out_tsr": scoring.tsr(held) if held else None,
        "n": len(agent),
        "n_held_out": len(held),
        "n_regression_anchors": len(anchors),
        "regression_anchors_verified": sum(1 for r in anchors if r.verified),
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
    summary = summarize(data, tasks)

    out_path = report_mod.write_report(tasks, data, summary, elapsed)
    print(f"REPORT written: {out_path}")
    print(
        f"agent TSR={summary['agent_tsr']:.3f}  TCR={summary['agent_tcr']:.3f}  "
        f"CuP-gap={summary['agent_cup']:.3f}  pass^{args.k}={summary['passk']:.3f}  "
        f"Copilot calls={summary['copilot_calls']}  ({elapsed:.0f}s)"
    )


if __name__ == "__main__":
    asyncio.run(_main())
