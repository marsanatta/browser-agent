"""Per-task audit trace + deterministic planner attribution + token ledger.

Reads the executor's EXISTING event stream (PLAN_READY, TOOL_CALL_*, LOCATOR_RESOLVED,
RECOVERY, STEP_FINISHED, ASK_USER, RUN_FINISHED) — no LLM, no network — and renders a
human-readable per-task block to eval/AUDIT.md.

Attribution is deterministic: layer 0 = is the plan well-formed; layer 1 = does the
planner's first targeted step ground. Every FAILING task therefore gets a plan-time /
ground-time tag (coverage = 1.0) — answering "was it the planner failing at the start,
or grounding failing mid-run?". No LLM judge of plan quality.

This is auditability EVIDENCE, not a metric to climb: the trace contents are not
optimized, and tokens are reported for cost transparency, never minimized.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.stream.events import Event, EventType

_LEGAL_ACTIONS = {"navigate", "click", "fill", "press"}
_TOKEN_KEYS = ("output_tokens", "input_tokens", "reasoning_tokens", "total_nano_aiu")


def _is_http(url: object) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def _blank_step() -> dict:
    return {"action": None, "target": None, "value": None, "ground": None,
            "verdict": None, "recovery": []}


def reduce_events(events: list[Event]) -> dict:
    """Reduce the raw event stream to {plan, steps, blocked}. Pure, deterministic."""
    plan: list[dict] = []
    order: list[str] = []
    steps: dict[str, dict] = {}
    call_to_step: dict[str, str] = {}
    blocked = False
    for ev in events:
        t, p = ev.type, ev.payload
        if t == EventType.PLAN_READY:
            plan = list(p.get("plan", []))
        elif t == EventType.STEP_STARTED:
            sid = p["step_id"]
            if sid not in steps:
                steps[sid] = _blank_step()
                order.append(sid)
        elif t == EventType.TOOL_CALL_START:
            call_to_step[p["call_id"]] = p["step_id"]
            steps.setdefault(p["step_id"], _blank_step())["action"] = p.get("tool")
        elif t == EventType.TOOL_CALL_ARGS:
            sid = call_to_step.get(p["call_id"])
            if sid and sid in steps:
                args = p.get("args", {})
                steps[sid]["action"] = args.get("action", steps[sid]["action"])
                steps[sid]["target"] = args.get("target")
                steps[sid]["value"] = args.get("value")
        elif t == EventType.LOCATOR_RESOLVED:
            if p["step_id"] in steps:
                steps[p["step_id"]]["ground"] = p.get("ground", "RESOLVED")
        elif t == EventType.RECOVERY:
            if p["step_id"] in steps:
                steps[p["step_id"]]["recovery"].append(p.get("recovery"))
        elif t == EventType.STEP_FINISHED:
            s = steps.get(p["step_id"])
            if s is not None:
                s["verdict"] = p.get("verdict")
                fc = p.get("failure_category")
                if fc == "BLOCKED":
                    blocked = True
                if fc == "NOT_FOUND" and s["ground"] is None:
                    s["ground"] = "NOT_FOUND"
    return {"plan": plan, "steps": [steps[sid] for sid in order], "blocked": blocked}


def plan_wellformed(plan: list[dict]) -> tuple[bool, str]:
    """Layer 0: deterministic plan validity — no LLM, no network."""
    if not plan:
        return False, "empty plan"
    first = plan[0]
    act = first.get("action")
    if act not in _LEGAL_ACTIONS:
        return False, f"first step illegal action {act!r}"
    if act == "navigate" and not _is_http(first.get("url")):
        return False, "first navigate url not http(s)"
    if act in {"click", "fill", "press"} and not first.get("target"):
        return False, "first step missing target"
    for s in plan:
        if s.get("action") == "navigate" and not _is_http(s.get("url")):
            return False, "a navigate url is not http(s)"
    filled: set[str] = set()
    for s in plan:
        a = s.get("action")
        if a == "fill":
            filled.add((s.get("target") or "").strip().lower())
        elif a == "press":
            tgt = (s.get("target") or "").strip().lower()
            if tgt not in filled:
                return False, f"press on an unfilled target {tgt!r}"
    return True, ""


def attribute(plan: list[dict], steps: list[dict], verified: bool) -> str | None:
    """Tag a FAILING task plan-time vs ground-time (None for a passing task).

    plan-time = layer 0 failed, OR a well-formed plan whose first targeted step is
    NOT_FOUND (the planner aimed at something that does not exist). ground-time =
    plan well-formed and the first targeted step grounded, failure came later."""
    if verified:
        return None
    ok, _ = plan_wellformed(plan)
    if not ok:
        return "plan-time"
    first_ground = next((s["ground"] for s in steps if s.get("target") and s.get("ground")), None)
    if first_ground == "NOT_FOUND":
        return "plan-time"
    return "ground-time"


def audit_flag(nominal: bool, verified: bool, asked: bool, blocked: bool) -> str:
    if nominal and verified:
        return "OK"
    if nominal and not verified:
        return "SILENT_FAILURE"
    if blocked:
        return "BLOCKED"
    if verified:  # not nominal, not blocked, but verified -> correct abstention
        return "ABSTAIN"
    if asked:
        return "HONEST_FAIL"
    return "HONEST_FAIL"


@dataclass
class TaskTrace:
    task_id: str
    plan: list[dict]
    steps: list[dict]
    tokens: dict
    calls: int
    nsteps: int
    nominal: bool
    verified: bool
    asked: bool
    flag: str
    attribution: str | None


def build_trace(
    task_id: str,
    *,
    plan: list[dict],
    steps: list[dict],
    tokens: dict,
    calls: int,
    nsteps: int,
    nominal: bool,
    verified: bool,
    asked: bool,
    blocked: bool,
) -> TaskTrace:
    return TaskTrace(
        task_id=task_id,
        plan=plan,
        steps=steps,
        tokens=tokens,
        calls=calls,
        nsteps=nsteps,
        nominal=nominal,
        verified=verified,
        asked=asked,
        flag=audit_flag(nominal, verified, asked, blocked),
        attribution=attribute(plan, steps, verified),
    )


def attribution_coverage(traces: list[TaskTrace]) -> float:
    """Fraction of FAILING tasks that got a plan-time/ground-time tag (deterministic
    -> should be 1.0)."""
    failing = [t for t in traces if not t.verified]
    if not failing:
        return 1.0
    return sum(1 for t in failing if t.attribution is not None) / len(failing)


def _plan_line(i: int, s: dict) -> str:
    if s.get("action") == "navigate":
        return f"{i}. navigate {s.get('url', '')}"
    bits = f'"{s.get("target", "")}"'
    if s.get("value") is not None:
        bits += f' = "{s.get("value")}"'
    return f"{i}. {s.get('action')} {bits}"


def _dash(v: object) -> str:
    return "—" if v in (None, "", []) else str(v)


def render_md(traces: list[TaskTrace], when: str) -> str:
    cov = attribution_coverage(traces)
    flags: dict[str, int] = {}
    for tr in traces:
        flags[tr.flag] = flags.get(tr.flag, 0) + 1
    out = [
        "# Audit Trace — per-task evidence (human-readable, not a metric)",
        "",
        f"Generated **{when}** by `eval.audit` from the executor's event stream "
        "(no LLM, no network in the audit itself).",
        "",
        f"- **attribution_coverage = {cov:.3f}** "
        "(fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)",
        f"- flag tally: " + ", ".join(f"{k}={v}" for k, v in sorted(flags.items())),
        "- Tokens are reported for cost transparency only — never minimized "
        "(abstaining more to lower tokens would game the metric and is not done).",
        "",
        "---",
        "",
    ]
    for tr in traces:
        tok = tr.tokens or {}
        attr = tr.attribution or "n/a (passed)"
        out.append(f"### {tr.task_id} — AUDIT: {tr.flag} — attribution: {attr}")
        out.append(
            f"`nominal={tr.nominal}` `verified={tr.verified}` `asked={tr.asked}` | "
            f"steps={tr.nsteps} calls={tr.calls} | "
            f"tokens(out={tok.get('output_tokens', 0)} in={tok.get('input_tokens', 0)} "
            f"reason={tok.get('reasoning_tokens', 0)} nano_aiu={tok.get('total_nano_aiu', 0)})"
        )
        out.append("")
        out.append("plan:")
        if tr.plan:
            for i, s in enumerate(tr.plan, 1):
                out.append("- " + _plan_line(i, s))
        else:
            out.append("- (empty / planner error)")
        out.append("")
        out.append("| # | action | target | value | ground | verdict | recovery |")
        out.append("|---|---|---|---|---|---|---|")
        for i, s in enumerate(tr.steps, 1):
            rec = ",".join(r for r in s.get("recovery", []) if r) or "—"
            out.append(
                f"| {i} | {_dash(s.get('action'))} | {_dash(s.get('target'))} | "
                f"{_dash(s.get('value'))} | {_dash(s.get('ground'))} | "
                f"{_dash(s.get('verdict'))} | {rec} |"
            )
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out)
