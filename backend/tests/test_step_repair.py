"""Localized step-repair: a failed step is repaired in place; not-yet-reached
FUTURE steps are preserved by the executor (the LLM cannot drop them).

Repro of the observed silent failure: today the executor REPLACES the whole
suffix on a replan (`subtasks[:i] + new_subtasks`), so when the replanner returns
only a fix for the failed step the later goal steps are dropped and a truncated
plan "completes" falsely. The redesign splices `subtasks[:i] + repair +
subtasks[i+1:]` so the future steps run after the repair.

Network-free: MockPlanner + a data: URL. Whether a step ran is read from the LIVE
page (#l, written only by an actual click) via a verify_hook — not from event
descriptions (the navigate step's description is the data: URL, which contains
the button labels and would pollute a text match).
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

_HTML = (
    "<body>"
    "<button onclick=\"l.innerText+=' Rdone'\">Repair</button>"
    "<button onclick=\"l.innerText+=' F1done'\">Future1</button>"
    "<button onclick=\"l.innerText+=' F2done'\">Future2</button>"
    "<p id=l></p></body>"
)


def _data() -> str:
    return "data:text/html," + urllib.parse.quote(_HTML)


async def _run(planner):
    box, fin = {"log": ""}, None

    async def vh(page):
        try:
            box["log"] = await page.inner_text("#l")
        except Exception:
            box["log"] = ""
        return True

    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, verify_hook=vh)
    async for ev in ex.run("t"):
        if ev.type == EventType.RUN_FINISHED:
            fin = ev.payload
    return box["log"], fin


@pytest.mark.anyio
async def test_step_repair_preserves_future_steps():
    # navigate -> click "Nope" (absent -> NOT_FOUND -> repair) -> click Future1 -> Future2.
    # The repair fixes ONLY the failed step ("Repair"); Future1/Future2 are future steps
    # the executor must preserve (today they are dropped by the suffix-replace).
    planner = MockPlanner(
        [SubTask(action="navigate", url=_data()),
         SubTask(action="click", target="Nope"),
         SubTask(action="click", target="Future1"),
         SubTask(action="click", target="Future2")],
        replan_subtasks=[SubTask(action="click", target="Repair")],
    )
    log, fin = await _run(planner)
    assert "F1done" in log and "F2done" in log, (
        f"future steps must survive a step-repair (not be dropped); page #l = {log!r}"
    )
    assert fin and fin["nominal_completion"] is True


class _CascadePlanner:
    """Returns a step-specific repair so a PRESERVED future step that later fails
    can get its OWN repair (cascade), proving problems isolate per step."""

    def __init__(self, url: str) -> None:
        self._url = url

    async def plan(self, task, start_url=None, observation=None):
        from app.agent.planner import PlanResult
        return PlanResult([
            SubTask(action="navigate", url=self._url),
            SubTask(action="click", target="Nope1"),
            SubTask(action="click", target="Nope2"),
            SubTask(action="click", target="Goal"),
        ], "")

    async def replan(self, task, failure_log, observation, remaining=None):
        from app.agent.planner import PlanResult
        last = failure_log[-1]["step"] if failure_log else ""
        if "Nope1" in last:
            return PlanResult([SubTask(action="click", target="Fix1")], "")
        if "Nope2" in last:
            return PlanResult([SubTask(action="click", target="Fix2")], "")
        return PlanResult([], "")


_CASCADE_HTML = (
    "<body>"
    "<button onclick=\"l.innerText+=' Fix1done'\">Fix1</button>"
    "<button onclick=\"l.innerText+=' Fix2done'\">Fix2</button>"
    "<button onclick=\"l.innerText+=' Goaldone'\">Goal</button>"
    "<p id=l></p></body>"
)


@pytest.mark.anyio
async def test_step_repair_cascades_to_later_failures():
    # Nope1 fails -> repair Fix1; the PRESERVED Nope2 then fails -> its OWN repair Fix2;
    # the PRESERVED Goal then runs. All three must execute (cascade + final goal kept).
    url = "data:text/html," + urllib.parse.quote(_CASCADE_HTML)
    log, fin = await _run(_CascadePlanner(url))
    assert "Fix1done" in log and "Fix2done" in log and "Goaldone" in log, (
        f"cascade must repair each failure and still reach the final goal; #l = {log!r}"
    )
    assert fin and fin["nominal_completion"] is True


async def _run_with_events(planner):
    box, fin, asked = {"log": ""}, None, []

    async def vh(page):
        try:
            box["log"] = await page.inner_text("#l")
        except Exception:
            box["log"] = ""
        return True

    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, verify_hook=vh, max_replans=3)
    async for ev in ex.run("t"):
        if ev.type == EventType.RUN_FINISHED:
            fin = ev.payload
        elif ev.type == EventType.ASK_USER:
            asked.append(ev.payload.get("question", ""))
    return box["log"], fin, asked


@pytest.mark.anyio
async def test_unrepairable_step_abstains_not_silent_success():
    # The failed step can never be repaired (repair target is also absent). The agent
    # must ABSTAIN (ask_user, nominal=False) — NOT silently "complete" by skipping the
    # goal. The preserved Goal must NOT have run (the agent never got past the bad step).
    planner = MockPlanner(
        [SubTask(action="navigate", url="data:text/html," + urllib.parse.quote(_CASCADE_HTML)),
         SubTask(action="click", target="NeverWorks"),
         SubTask(action="click", target="Goal")],
        replan_subtasks=[SubTask(action="click", target="AlsoAbsent")],
    )
    log, fin, asked = await _run_with_events(planner)
    assert fin and fin["nominal_completion"] is False, "an unrepairable step must NOT claim success"
    assert asked, "an unrepairable step must abstain via ask_user"
    assert "Goaldone" not in log, f"the goal must not run when the prior step never succeeded; #l = {log!r}"
