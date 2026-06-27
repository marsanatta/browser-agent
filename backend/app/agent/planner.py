"""PLANNER: NL task -> ordered sub-tasks.

The only LLM-dependent perception/planning seam in M1. `LLMPlanner` routes
through the Copilot `LLMGateway` (hard constraint); `MockPlanner` returns a
canned list so the whole loop is testable without Copilot auth.

A SubTask is a structured target, not free text, so the deterministic executor
can run it. The planner decides WHAT to do; perceive/locate/act/verify decide HOW
(grounding is the dominant bottleneck — docs/architecture/02 §1.1 — so we keep it
deterministic and out of the LLM's hands).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol

from app.agent.models import PLANNER_EFFORT, PLANNER_MODEL, LLMGateway


@dataclass(frozen=True)
class SubTask:
    action: str  # navigate | click | fill | press
    target: str | None = None  # accessible name of the element (click/fill/press)
    role: str | None = None  # optional role hint for disambiguation
    url: str | None = None  # for navigate
    value: str | None = None  # fill value, or the key to press (e.g. "Enter")
    description: str = ""
    # predict-then-verify: an optional goal-grounded post-state the planner declares
    # for a click/press (e.g. {"text_visible": "Results"}). The executor verifies it
    # after acting, so a "page moved but goal not reached" action (dismissing a modal,
    # clicking the wrong button) fails instead of silently counting as success.
    # hash=False: a dict field would make this frozen dataclass's auto __hash__ throw
    # if ever hashed (set/dict-key/dedup); excluded so SubTask stays hashable.
    expect: dict | None = field(default=None, hash=False)


class Planner(Protocol):
    async def plan(
        self, task: str, start_url: str | None = None, observation: str | None = None
    ) -> list[SubTask]: ...

    async def replan(
        self, task: str, failed: str, failure_class: str, observation: str
    ) -> list[SubTask]: ...


class MockPlanner:
    """Test double: returns a fixed plan, no LLM/auth required. `replan_subtasks`
    lets a test return a DIFFERENT plan on replan (the peek-the-page path); it
    records each replan call so a test can assert the page observation was passed."""

    def __init__(
        self,
        subtasks: list[SubTask],
        replan_subtasks: list[SubTask] | None = None,
        peek_subtasks: list[SubTask] | None = None,
    ) -> None:
        self._subtasks = subtasks
        self._replan_subtasks = replan_subtasks
        # peek_subtasks: returned when plan() is called WITH an observation (peek-plan),
        # so a test can prove "seeing the page -> a different/correct plan".
        self._peek_subtasks = peek_subtasks
        self.replan_calls: list[tuple[str, str, str, str]] = []
        self.plan_calls: list[tuple[str, str | None, str | None]] = []  # (task, start_url, observation)

    async def plan(
        self, task: str, start_url: str | None = None, observation: str | None = None
    ) -> list[SubTask]:
        self.plan_calls.append((task, start_url, observation))
        if observation is not None and self._peek_subtasks is not None:
            return list(self._peek_subtasks)
        return list(self._subtasks)

    async def replan(
        self, task: str, failed: str, failure_class: str, observation: str
    ) -> list[SubTask]:
        self.replan_calls.append((task, failed, failure_class, observation))
        src = self._replan_subtasks if self._replan_subtasks is not None else self._subtasks
        return list(src)


_PLAN_PROMPT = """You are the planner for a browser-automation agent.
Decompose the user task into an ordered list of atomic sub-tasks.
Each sub-task is one of: navigate (needs "url": an ABSOLUTE https:// URL, never a
relative path), click (needs "target": the visible label/accessible name), fill
(needs "target" and "value"), press (needs "target" and "value": a key such as
"Enter" — use it AFTER fill to submit a search box or form when there is no obvious
submit button).
Optionally add "expect" to a click or press: an object declaring the OBSERVABLE result
that proves the step worked — one of {"text_visible":"..."} (text that should appear),
{"selector_visible":"css"}, or {"url_contains":"..."}. Add it ONLY when success means
something specific must appear (e.g. a result or a title) AND you can name that exact
observable; a wrong or guessed goal causes false failures, so omit "expect" when you are
unsure or when any change is fine.
Respond with ONLY a JSON array, no prose. Example:
[{"action":"navigate","url":"https://www.google.com"},
 {"action":"fill","target":"Search","value":"steam"},
 {"action":"press","target":"Search","value":"Enter","expect":{"text_visible":"results"}}]

User task: __TASK__
"""


# Start-context (planner-sees-start-url): the planner only gets the task, so it would
# otherwise invent a navigate to a site's generic portal (e.g. www.wikipedia.org)
# instead of acting on the page the agent actually starts on. Telling it the start URL
# keeps it on the right page.
_START_CONTEXT = (
    "The browser is ALREADY loaded on this page: {url}\n"
    "Plan your steps FROM that page. Do NOT navigate to a different site — in "
    "particular do NOT navigate to a site's generic home/portal — unless the task "
    "clearly requires leaving the current page.\n\n"
)


# Peek-plan (the root fix for a-priori blindness): the agent navigates to the start page
# and PERCEIVES it BEFORE the initial plan, so the planner sees the real elements and can
# ground both the plan and any `expect` in what is actually there (vs guessing blind).
_PEEK_PLAN_PROMPT = (
    "The browser is ALREADY loaded on the start page and you can SEE its real interactive\n"
    "elements (listed at the end). Plan FROM this page using the ACTUAL visible labels, not\n"
    'guesses, and ground any "expect" in what you can see.\n\n'
    + _PLAN_PROMPT
    + "\nElements currently on the page:\n__OBSERVATION__\n"
)


# Peek-the-page replan (docs/architecture/02 §1.3, the close-the-loop fix): on local
# recovery exhaustion the agent spends tokens to SHOW the planner the current page's
# real elements and asks for a revised plan from here — closing the open loop where
# the original plan's words matched no element on the live page.
_REPLAN_PROMPT = """You are the planner for a browser-automation agent, RE-PLANNING
after a step failed. The agent has already run the earlier steps and is CURRENTLY on a
page. It tried the failed step below but could not complete it. Produce a NEW plan to
finish the task FROM THE CURRENT PAGE, using ONLY the elements actually present (listed
below). Prefer the visible element whose label best matches the intent even if the
wording differs (e.g. click "Log in" when the goal said "Sign In"). If a listed link's
target path already satisfies the goal, navigate to it directly.

Each sub-task is one of: navigate (needs "url"), click (needs "target": the visible
label), fill (needs "target" and "value"), press (needs "target" and "value": a key
such as "Enter"). A click/press may carry "expect" — {"text_visible":"..."} /
{"selector_visible":"css"} / {"url_contains":"..."} — the observable result that proves
it worked, so a wrong-but-page-changing action is not mistaken for success. Respond with
ONLY a JSON array of the REMAINING steps from here, no prose.

User task: __TASK__
Failed step: __FAILED__ (failure class: __CLASS__)

Elements currently on the page:
__OBSERVATION__
"""


class LLMPlanner:
    def __init__(
        self,
        gateway: LLMGateway,
        model: str = PLANNER_MODEL,
        reasoning_effort: str = PLANNER_EFFORT,
    ) -> None:
        self._gateway = gateway
        self._model = model
        self._effort = reasoning_effort

    async def plan(
        self, task: str, start_url: str | None = None, observation: str | None = None
    ) -> list[SubTask]:
        if observation is not None:
            # peek-plan: the agent already saw the start page; plan grounded in it.
            prompt = _PEEK_PLAN_PROMPT.replace("__TASK__", task).replace("__OBSERVATION__", observation)
        elif start_url:
            prompt = _START_CONTEXT.format(url=start_url) + _PLAN_PROMPT.replace("__TASK__", task)
        else:
            prompt = _PLAN_PROMPT.replace("__TASK__", task)
        resp = await self._gateway.complete(prompt, model=self._model, reasoning_effort=self._effort)
        return _parse_plan(resp.content)

    async def replan(
        self, task: str, failed: str, failure_class: str, observation: str
    ) -> list[SubTask]:
        prompt = (
            _REPLAN_PROMPT.replace("__TASK__", task)
            .replace("__FAILED__", failed)
            .replace("__CLASS__", failure_class)
            .replace("__OBSERVATION__", observation)
        )
        # The deep replan is the gated escalation tier: use the gateway's replanner
        # model/effort (a stronger model thinking harder), falling back to this
        # planner's own model when the gateway doesn't route a separate tier.
        model = getattr(self._gateway, "replanner_model", None) or self._model
        effort = getattr(self._gateway, "replanner_effort", None) or self._effort
        resp = await self._gateway.complete(prompt, model=model, reasoning_effort=effort)
        return _parse_plan(resp.content)


def _parse_plan(content: str) -> list[SubTask]:
    raw = _extract_json_array(content)
    items = json.loads(raw)
    out: list[SubTask] = []
    for it in items:
        expect = it.get("expect")
        out.append(
            SubTask(
                action=str(it["action"]),
                target=it.get("target"),
                role=it.get("role"),
                url=it.get("url"),
                value=it.get("value"),
                description=it.get("description", ""),
                # drop an empty/malformed expect so it never forces a guaranteed fail
                expect=expect if isinstance(expect, dict) and expect else None,
            )
        )
    return out


def _extract_json_array(content: str) -> str:
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("planner response contained no JSON array")
    return content[start : end + 1]
