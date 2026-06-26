"""Scoring math for the M3 eval harness. Pure functions, no browser, no Copilot —
so every metric is unit-testable offline against hand-computed ground truth.

Metrics (grounded):
  TCR  key-node Task Completion Rate: mean over tasks of (key-nodes hit / total).
       Partial credit (WebCanvas, architecture/03 §3.1).
  TSR  Task Success Rate: fraction of tasks whose INDEPENDENT assertion passed.
       Binary per task (architecture/03 §3.1).
  pass^k  P(all k trials succeed); reliability metric for side-effecting tasks,
       k=3 (eval/02 §C1/F2). Estimated as (#tasks where all k runs verified)/(#tasks).
  silent_failure_gap (CuP)  fraction of tasks where the agent reported success
       (nominal) but the independent assertion failed (verified=False)
       (eval/01 §4, DESIGN §6). This is the headline silent-failure metric.
  mean_se  Bernoulli standard error sqrt(p(1-p)/n) (eval/02 §C2/F3).

A task is "verified" iff its independent assertion passed — never the agent's
self-report. `nominal` is the agent's own success claim, recorded ONLY so the gap
can be measured; it never contributes to TSR/TCR.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class TaskResult:
    """One run of one task. `key_nodes_*` and `verified` come from independent
    programmatic checks on the live page; `nominal` is the agent's self-report."""

    task_id: str
    nominal: bool                 # agent claimed success (RUN_FINISHED.nominal_completion)
    verified: bool                # independent assertion passed on the live final page
    key_nodes_hit: int
    key_nodes_total: int
    task_type: str = "action"
    held_out: bool = False
    error: str | None = None
    extra: dict = field(default_factory=dict)


def task_tcr(r: TaskResult) -> float:
    if r.key_nodes_total == 0:
        return 1.0 if r.verified else 0.0
    return r.key_nodes_hit / r.key_nodes_total


def tcr(results: list[TaskResult]) -> float:
    """Mean key-node completion over tasks that HAVE key nodes (partial credit).

    Zero-key-node tasks (e.g. abstain rows) carry no key-node signal, so a verified
    one would otherwise contribute a free 1.0 that inflates the aggregate. They are
    excluded here; their correctness is reported separately (TSR / abstain). Returns
    0.0 when no task has key nodes."""
    keyed = [r for r in results if r.key_nodes_total > 0]
    if not keyed:
        return 0.0
    return sum(task_tcr(r) for r in keyed) / len(keyed)


def tsr(results: list[TaskResult]) -> float:
    """Fraction of tasks fully verified (independent assertion passed)."""
    if not results:
        return 0.0
    return sum(1 for r in results if r.verified) / len(results)


def silent_failure_gap(results: list[TaskResult]) -> float:
    """CuP: fraction of tasks where nominal success but verification failed.

    This is the silent-failure rate — the agent said "done" but the world says
    otherwise. Bounded in [0, 1]; lower is better."""
    if not results:
        return 0.0
    silent = sum(1 for r in results if r.nominal and not r.verified)
    return silent / len(results)


def pass_hat_k(runs_by_task: dict[str, list[TaskResult]]) -> float:
    """pass^k estimate over tasks that were each run k times.

    A task contributes 1 iff ALL its runs verified; else 0. Mean over tasks.
    (eval/02 §C1: pass^k = P(all k trials succeed).) Only meaningful when every
    task has the same k>=2 runs; single-run tasks are excluded."""
    multi = {t: rs for t, rs in runs_by_task.items() if len(rs) >= 2}
    if not multi:
        return 0.0
    all_pass = sum(1 for rs in multi.values() if all(r.verified for r in rs))
    return all_pass / len(multi)


def mean_se(results: list[TaskResult], key=lambda r: r.verified) -> tuple[float, float]:
    """(mean, Bernoulli SE) of a binary per-task signal.

    SE = sqrt(p(1-p)/n) (eval/02 §C2). Independent-item assumption; clustered SE
    is a documented refinement when tasks share a site (noted in the report)."""
    n = len(results)
    if n == 0:
        return 0.0, 0.0
    p = sum(1 for r in results if key(r)) / n
    se = math.sqrt(p * (1 - p) / n)
    return p, se
