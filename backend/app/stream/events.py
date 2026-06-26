"""AG-UI-style event vocabulary for SSE step streaming.

AG-UI defines a standard event set (RUN_*, STEP_*, TOOL_CALL_*, TEXT_MESSAGE_*)
that CopilotKit-style frontends consume. AG-UI has no screenshot event, so we
add a custom `SCREENSHOT_ANNOTATED` event carrying an element highlight box plus
a screenshot reference (never inline image bytes on the hot SSE path).

Every payload passes through `redact()` before serialization so no secret/PII
reaches the SSE `data:` field.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.obs.tracing import redact


class EventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TEXT_MESSAGE = "TEXT_MESSAGE"
    SCREENSHOT_ANNOTATED = "SCREENSHOT_ANNOTATED"
    LOCATOR_RESOLVED = "LOCATOR_RESOLVED"
    ASK_USER = "ASK_USER"
    RECOVERY = "RECOVERY"
    PLAN_READY = "PLAN_READY"
    PHASE = "PHASE"


@dataclass(frozen=True)
class HighlightBox:
    """Element highlight in CSS pixels relative to the screenshot's top-left."""

    x: float
    y: float
    width: float
    height: float
    label: str | None = None


@dataclass(frozen=True)
class ScreenshotAnnotated:
    """Custom AG-UI extension: a captured page screenshot plus the element the
    agent acted on. `screenshot_ref` is an opaque id/URL into the trace store —
    image bytes are served out-of-band, never inlined on the SSE stream."""

    step_id: str
    screenshot_ref: str
    highlight: HighlightBox
    caption: str | None = None


@dataclass
class Event:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_sse(self) -> dict[str, str]:
        safe = redact(self.payload)
        data = json.dumps({"type": self.type.value, "ts": self.ts, "payload": safe})
        return {"event": self.type.value, "data": data}


def run_started(task: str, run_id: str) -> Event:
    return Event(EventType.RUN_STARTED, {"run_id": run_id, "task": task})


def step_started(step_id: str, description: str) -> Event:
    return Event(EventType.STEP_STARTED, {"step_id": step_id, "description": description})


def step_finished(
    step_id: str, status: str, failure_category: str | None = None, verdict: str | None = None
) -> Event:
    payload: dict[str, Any] = {"step_id": step_id, "status": status}
    if failure_category:
        payload["failure_category"] = failure_category
    if verdict:
        payload["verdict"] = verdict  # per-step verify-after-act verdict: CHANGED | NO_CHANGE
    return Event(EventType.STEP_FINISHED, payload)


def locator_resolved(step_id: str, tier: int, strategy: str, ground: str = "RESOLVED") -> Event:
    """Surface the grounding outcome + chosen locator (DESIGN §8: chosen locator +
    cascade level is part of the inspectable per-step diagnostics). `ground` is the
    observe-only grounding outcome: RESOLVED (deterministic cascade) or AMBIGUOUS_L2
    (resolved by the L2 LLM re-rank). A NOT_FOUND step emits no LOCATOR_RESOLVED."""
    return Event(
        EventType.LOCATOR_RESOLVED,
        {"step_id": step_id, "tier": tier, "strategy": strategy, "ground": ground},
    )


def phase(run_id: str, name: str) -> Event:
    """Observe-only lifecycle marker emitted by the executor to fill the dead air
    of blocking awaits (planner LLM call, browser launch) that yield no other
    event. `name` is a stable machine token the frontend translates — never human
    text — so it carries no secret/PII."""
    return Event(EventType.PHASE, {"run_id": run_id, "phase": name})


def plan_ready(run_id: str, plan: list[dict[str, Any]]) -> Event:
    """The planner's initial decomposition, emitted by the executor (NOT the
    planner) right after planning, so the audit/attribution can read it from the
    event stream without touching planner.py."""
    return Event(EventType.PLAN_READY, {"run_id": run_id, "plan": plan})


def tool_call_start(step_id: str, tool: str, call_id: str) -> Event:
    return Event(
        EventType.TOOL_CALL_START, {"step_id": step_id, "tool": tool, "call_id": call_id}
    )


def tool_call_args(call_id: str, args: dict[str, Any]) -> Event:
    return Event(EventType.TOOL_CALL_ARGS, {"call_id": call_id, "args": args})


def tool_call_end(call_id: str, result: str) -> Event:
    return Event(EventType.TOOL_CALL_END, {"call_id": call_id, "result": result})


def text_message(role: str, content: str) -> Event:
    return Event(EventType.TEXT_MESSAGE, {"role": role, "content": content})


def screenshot_annotated(shot: ScreenshotAnnotated) -> Event:
    return Event(EventType.SCREENSHOT_ANNOTATED, asdict(shot))


def ask_user(step_id: str, question: str) -> Event:
    return Event(EventType.ASK_USER, {"step_id": step_id, "question": question})


def recovery(
    step_id: str,
    failure_class: str,
    action: str,
    attempt: int,
    tried: str | None = None,
    tier: int | None = None,
    strategy: str | None = None,
    detail: str | None = None,
) -> Event:
    """`action` is the recovery taken; the optional fields are observe-only context
    for the per-attempt log: `tried` (what the agent attempted this attempt — the
    sub-task action + target), `tier`/`strategy` (the locator resolved this attempt,
    when one was), and `detail` (a short result/why for the failure)."""
    payload: dict[str, Any] = {
        "step_id": step_id,
        "failure_class": failure_class,
        "recovery": action,
        "attempt": attempt,
    }
    if tried is not None:
        payload["tried"] = tried
    if tier is not None:
        payload["tier"] = tier
    if strategy is not None:
        payload["strategy"] = strategy
    if detail is not None:
        payload["detail"] = detail
    return Event(EventType.RECOVERY, payload)


def run_finished(
    run_id: str, nominal: bool, verified: bool, tokens: dict[str, int] | None = None
) -> Event:
    return Event(
        EventType.RUN_FINISHED,
        {
            "run_id": run_id,
            "nominal_completion": nominal,
            "verified_completion": verified,
            "tokens": tokens or {},
        },
    )
