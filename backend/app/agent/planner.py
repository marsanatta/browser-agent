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
from dataclasses import dataclass
from typing import Protocol

from app.agent.models import ACTOR_WORKHORSE, LLMGateway


@dataclass(frozen=True)
class SubTask:
    action: str  # navigate | click | fill | press
    target: str | None = None  # accessible name of the element (click/fill/press)
    role: str | None = None  # optional role hint for disambiguation
    url: str | None = None  # for navigate
    value: str | None = None  # fill value, or the key to press (e.g. "Enter")
    description: str = ""


class Planner(Protocol):
    async def plan(self, task: str) -> list[SubTask]: ...


class MockPlanner:
    """Test double: returns a fixed plan, no LLM/auth required."""

    def __init__(self, subtasks: list[SubTask]) -> None:
        self._subtasks = subtasks

    async def plan(self, task: str) -> list[SubTask]:
        return list(self._subtasks)


_PLAN_PROMPT = """You are the planner for a browser-automation agent.
Decompose the user task into an ordered list of atomic sub-tasks.
Each sub-task is one of: navigate (needs "url"), click (needs "target": the
visible label/accessible name), fill (needs "target" and "value"), press (needs
"target" and "value": a key such as "Enter" — use it AFTER fill to submit a
search box or form when there is no obvious submit button).
Respond with ONLY a JSON array, no prose. Example:
[{"action":"navigate","url":"https://www.google.com"},
 {"action":"fill","target":"Search","value":"steam"},
 {"action":"press","target":"Search","value":"Enter"}]

User task: __TASK__
"""


class LLMPlanner:
    def __init__(self, gateway: LLMGateway, model: str = ACTOR_WORKHORSE) -> None:
        self._gateway = gateway
        self._model = model

    async def plan(self, task: str) -> list[SubTask]:
        prompt = _PLAN_PROMPT.replace("__TASK__", task)
        resp = await self._gateway.complete(prompt, model=self._model)
        return _parse_plan(resp.content)


def _parse_plan(content: str) -> list[SubTask]:
    raw = _extract_json_array(content)
    items = json.loads(raw)
    out: list[SubTask] = []
    for it in items:
        out.append(
            SubTask(
                action=str(it["action"]),
                target=it.get("target"),
                role=it.get("role"),
                url=it.get("url"),
                value=it.get("value"),
                description=it.get("description", ""),
            )
        )
    return out


def _extract_json_array(content: str) -> str:
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("planner response contained no JSON array")
    return content[start : end + 1]
