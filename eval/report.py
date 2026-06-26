"""Render REPORT.md from a real harness run. Numbers are passed in from an actual
run — this module only formats them, never fabricates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval.loader import EvalTask
from eval.scoring import TaskResult, task_tcr

REPORT_PATH = Path(__file__).resolve().parent / "REPORT.md"


def _pf(b: bool) -> str:
    return "PASS" if b else "FAIL"


def _per_task_rows(tasks: list[EvalTask], agent: list[TaskResult], baseline: list[TaskResult]) -> str:
    by_id_base = {r.task_id: r for r in baseline}
    lines = [
        "| task | type | held-out | key-nodes | agent verified | baseline verified | nominal | silent? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t, r in zip(tasks, agent):
        b = by_id_base.get(t.id)
        silent = "YES" if (r.nominal and not r.verified) else ""
        kn = f"{r.key_nodes_hit}/{r.key_nodes_total} ({task_tcr(r):.0%})"
        tid = f"{t.id} (anchor)" if t.regression_anchor else t.id
        lines.append(
            f"| {tid} | {t.task_type} | {'yes' if t.held_out else ''} | {kn} | "
            f"{_pf(r.verified)} | {_pf(b.verified) if b else '-'} | "
            f"{_pf(r.nominal)} | {silent} |"
        )
    return "\n".join(lines)


def write_report(
    tasks: list[EvalTask],
    data: dict[str, Any],
    summary: dict[str, Any],
    elapsed_s: float,
) -> Path:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    s = summary
    held_tsr = "n/a" if s["held_out_tsr"] is None else f"{s['held_out_tsr']:.3f}"
    n_anchor = s.get("n_regression_anchors", 0)
    anchor_note = (
        f" + {n_anchor} regression-anchor(s) [green-on-day-one, excluded from the "
        f"headline rate; {s.get('regression_anchors_verified', 0)}/{n_anchor} passing]"
        if n_anchor else ""
    )

    metric_table = "\n".join([
        "| metric | agent | budget-matched baseline |",
        "|---|---|---|",
        f"| TCR (key-node completion) | {s['agent_tcr']:.3f} | {s['baseline_tcr']:.3f} |",
        f"| TSR (task success) | {s['agent_tsr']:.3f} +/- {s['agent_tsr_se']:.3f} | "
        f"{s['baseline_tsr']:.3f} +/- {s['baseline_tsr_se']:.3f} |",
        f"| silent-failure gap (CuP) | {s['agent_cup']:.3f} | {s['baseline_cup']:.3f} |",
        f"| pass^{data['k']} (side-effect tasks) | {s['passk']:.3f} | n/a |",
    ])

    body = f"""# M3 Eval Report

Generated from a REAL run on {now}. Metrics are computed by independent
programmatic assertions on the live page (eval/01 §4) — never the agent's
self-report. Per the ablation rule (architecture/03 §4) a budget-matched vanilla
baseline (max_attempts=1, no L2 heal) runs alongside the full agent.

- Tasks: {s['n']} headline ({s['n_held_out']} held-out on quotes.toscrape.com, a site
  never used in dev — generalization test, eval/01 §5.3){anchor_note}
- Approx Copilot calls (this run): **{s['copilot_calls']}**
- Wall time: {elapsed_s:.0f}s
- Held-out TSR: {held_tsr}

## Headline metrics

{metric_table}

Definitions: TCR = mean key-nodes hit per task with key nodes (partial credit;
zero-key-node tasks such as abstain rows are excluded so they cannot contribute a
free 1.0); TSR = fraction of tasks whose independent assertion passed; silent-
failure gap (CuP) = fraction
where the agent claimed success but verification failed; pass^k = fraction of
side-effecting tasks that verified on ALL {data['k']} runs (reliability, eval/02 §C1).
SE is Bernoulli sqrt(p(1-p)/n) — independent-item; clustered SE would be larger
because tasks share sites (eval/02 §C2).

## Per-task results

{_per_task_rows(tasks, data['agent'], data['baseline'])}

## What is REAL vs SEAM

REAL (run in this report):
- Full agent loop (perceive/locate/act/verify) via the Copilot-backed LLM planner.
- Independent programmatic state assertion on the live final page (`eval/verify/state.py`).
- Nominal-vs-verified silent-failure gap (CuP).
- Consistency check (`eval/verify/consistency.py`) — unit-tested; a Semantic-
  Entropy-style sampling signal (run extraction n times, flag disagreement).
- Budget-matched vanilla baseline column.
- pass^{data['k']} for side-effecting tasks.

SEAM (designed-for, not built — `eval/verify/seams.py`, raise NotImplementedError):
- SVDD trajectory-anomaly trip-wire (needs a normal-trace corpus; eval/01 §4.2).
- Inspect AI sandbox adapter (eval/02 §D1).
- Full REAL deterministic-replica state-diff via agisdk (architecture/03 §3.2).
- Hidden-state Semantic Entropy Probe (Copilot gateway exposes no logits; we ship
  the sampling approximation instead — eval/02 §B3).

## Honest caveats

- n={s['n']} is far below the ~1,000 items needed to detect a 3% delta at 80%
  power (eval/02 §C2). These numbers are directional, not statistically powered —
  the SE columns make the uncertainty explicit.
- Live seed sites can change or rate-limit; a task FAIL may be a site change, not
  an agent regression. Re-run to distinguish.
- The judge/LLM is used only for PLANNING here; success is graded programmatically,
  so judge bias does not enter the headline metrics.
- Key-node TCR counts a checkpoint hit if it was observable at a step's post-state
  (the step_hook fires after each sub-task), an approximation of WebCanvas
  trajectory semantics — not a continuous within-step observation. Tasks with no
  key nodes are excluded from the TCR aggregate.
"""
    REPORT_PATH.write_text(body, encoding="utf-8")
    return REPORT_PATH
