"""Replan must not silently drop downstream goals (Fix 1).

Repro of the observed silent failure: on a step failure the executor REPLACES the
whole suffix with the replanner's output, so if the replanner omits a later goal
(e.g. "click the 3rd item") the truncated plan "completes" and the agent falsely
claims nominal success. The fix feeds the replanner the ORIGINAL remaining steps
(the failed one + every downstream goal) so it can re-include them. This asserts
the executor actually passes those remaining goal steps to replan().

Network-free: a MockPlanner + a data: URL (no Copilot, no live site).
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider

_HTML = "<body><button onclick=\"o.innerText='x'\">Go</button><p id=o>idle</p></body>"


def _data() -> str:
    return "data:text/html," + urllib.parse.quote(_HTML)


@pytest.mark.anyio
async def test_replan_receives_remaining_goal_steps():
    # navigate -> click "Nope" (absent -> NOT_FOUND -> replan) -> click "GOAL" (downstream).
    planner = MockPlanner(
        [SubTask(action="navigate", url=_data()),
         SubTask(action="click", target="Nope"),
         SubTask(action="click", target="GOAL")],
        replan_subtasks=[SubTask(action="click", target="Go")],
    )
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None)
    async for _ in ex.run("task"):
        pass

    assert planner.replan_calls, "a replan should fire after the NOT_FOUND step"
    remaining = planner.replan_calls[0][3]  # (task, failures, observation, remaining)
    targets = [s.target for s in remaining]
    assert "GOAL" in targets, (
        f"replan must receive the downstream goal step so it cannot be dropped; got {targets}"
    )
