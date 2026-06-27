"""Plan reasoning + replan history wiring.

The live-run UI must (1) show the planner LLM's verbatim output, not just parsed
step blocks, and (2) preserve every plan -> replan version with the failure input
that drove each replan. Both are carried on the PLAN_READY event:

  - `reasoning`  the planner's verbatim output (MockPlanner synthesizes the same
                 JSON-array shape a real planner emits).
  - `version` / `kind`  mark the initial plan vs the Nth replan (history, not overwrite).
  - `failures`  the accumulated failure log fed to the planner on a replan (the "why").

Network-free: a MockPlanner + a data: URL trap page force a deterministic replan
(no Copilot, no live site), so this runs in the offline gate.
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, PlanResult, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

# Click "Go" mutates the DOM -> CHANGED (a real success the replan can reach); the
# initial plan targets a non-existent element -> NOT_FOUND -> local exhaustion -> replan.
_HTML = "<body><button onclick=\"o.innerText='done'\">Go</button><p id=o>idle</p></body>"


def _data(html: str) -> str:
    return "data:text/html," + urllib.parse.quote(html)


async def _plan_ready_events(planner) -> list[dict]:
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None)
    return [
        ev.payload async for ev in ex.run("task") if ev.type == EventType.PLAN_READY
    ]


@pytest.mark.anyio
async def test_plan_ready_carries_raw_reasoning_and_version():
    planner = MockPlanner([SubTask(action="navigate", url=_data(_HTML)),
                           SubTask(action="click", target="Go")])
    plans = await _plan_ready_events(planner)
    assert len(plans) == 1
    p = plans[0]
    assert p["version"] == 1 and p["kind"] == "plan"
    assert "Go" in p["reasoning"]  # the planner's verbatim output, surfaced to the UI
    assert [s["action"] for s in p["steps"]] == ["navigate", "click"]


@pytest.mark.anyio
async def test_replan_emits_second_version_with_failures():
    # Initial plan targets a missing element -> NOT_FOUND -> replan; the replan's plan
    # clicks the real "Go" button and succeeds.
    planner = MockPlanner(
        [SubTask(action="navigate", url=_data(_HTML)),
         SubTask(action="click", target="DoesNotExist")],
        replan_subtasks=[SubTask(action="click", target="Go")],
    )
    plans = await _plan_ready_events(planner)

    assert len(plans) == 2, "history must keep BOTH the initial plan and the replan"
    assert plans[0]["version"] == 1 and plans[0]["kind"] == "plan"

    replan = plans[1]
    assert replan["version"] == 2 and replan["kind"] == "replan"
    # The exact failure log fed to the planner (the "why we replanned").
    assert replan["failures"], "replan version must carry the failure log shown to the LLM"
    assert all("step" in f and "class" in f for f in replan["failures"])
    assert any("DoesNotExist" in f["step"] for f in replan["failures"])
    # This version's OWN output (the suffix), distinct from the full reconciled plan.
    assert [s["action"] for s in replan["steps"]] == ["click"]
    assert "Go" in replan["reasoning"]


@pytest.mark.anyio
async def test_planresult_subtasks_unchanged_behaviour():
    # The contract change (plan() -> PlanResult) must not alter the executed plan: the
    # run still completes nominally off the MockPlanner's subtasks.
    planner = MockPlanner([SubTask(action="navigate", url=_data(_HTML)),
                           SubTask(action="click", target="Go")])
    finished = [
        ev.payload async for ev in
        Executor(PlaywrightProvider(headless=True), planner, gateway=None).run("t")
        if ev.type == EventType.RUN_FINISHED
    ]
    assert finished and finished[0]["nominal_completion"] is True


@pytest.mark.anyio
async def test_mock_planner_returns_planresult():
    planner = MockPlanner([SubTask(action="click", target="X")])
    res = await planner.plan("t")
    assert isinstance(res, PlanResult)
    assert [s.target for s in res.subtasks] == ["X"]
    assert "X" in res.raw
