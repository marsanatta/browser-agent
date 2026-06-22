"""Full loop test with a MockPlanner (no Copilot auth).

Asserts the executor drives perceive->locate->act->verify end to end and emits
the real AG-UI event sequence over the same Event objects the SSE endpoint uses.
Runs against live the-internet.herokuapp.com (deterministic, no bot wall).
"""

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

BASE = "https://the-internet.herokuapp.com"


@pytest.mark.live
@pytest.mark.anyio
async def test_executor_runs_navigate_then_click():
    planner = MockPlanner([
        SubTask(action="navigate", url=BASE, description="open site"),
        SubTask(action="click", target="Form Authentication", role="link"),
    ])
    executor = Executor(PlaywrightProvider(headless=True), planner)

    types = []
    payloads = []
    async for ev in executor.run("log in via form authentication"):
        types.append(ev.type)
        payloads.append(ev.payload)

    assert types[0] == EventType.RUN_STARTED
    assert EventType.STEP_STARTED in types
    assert EventType.TOOL_CALL_START in types
    assert EventType.TOOL_CALL_END in types
    assert types[-1] == EventType.RUN_FINISHED

    finished = payloads[-1]
    assert finished["nominal_completion"] is True
    assert finished["verified_completion"] is True


@pytest.mark.live
@pytest.mark.anyio
async def test_executor_surfaces_missing_element():
    planner = MockPlanner([
        SubTask(action="navigate", url=BASE),
        SubTask(action="click", target="This Link Does Not Exist", role="link"),
    ])
    executor = Executor(PlaywrightProvider(headless=True), planner)

    types = [ev.type async for ev in executor.run("click a missing link")]

    assert types[-1] == EventType.RUN_FINISHED
    # missing element -> step did not complete ok -> run not verified


@pytest.mark.anyio
async def test_executor_planner_error_emits_run_error():
    class BrokenPlanner:
        async def plan(self, task):
            raise RuntimeError("llm down")

    executor = Executor(PlaywrightProvider(headless=True), BrokenPlanner())
    events = [ev async for ev in executor.run("anything")]

    assert events[0].type == EventType.RUN_STARTED
    assert events[-1].type == EventType.RUN_ERROR
    assert "llm down" in events[-1].payload["error"]
