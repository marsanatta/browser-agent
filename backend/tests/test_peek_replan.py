"""Peek-the-page close-the-loop replan (docs/architecture/02 §1.3).

Deterministic offline anchor (no network, no Copilot): the first plan targets an
element that is ABSENT under the planned name, so the sub-task exhausts local
recovery. The executor then PEEKS the live page and calls planner.replan() with the
real elements; a page-grounded replan picks the element that is actually present and
the run completes. The old context-free replan (re-issuing plan()) would re-target
the absent element and fail identically -> nominal stays True ONLY because replan's
page-grounded output was used.
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

# Only "Submit Order" exists; clicking it mutates the DOM so verify-after-act sees CHANGED.
_PAGE = """<html><body>
<button onclick="this.insertAdjacentHTML('afterend','<h1 id=done>Order Placed</h1>')">Submit Order</button>
</body></html>"""
_URL = "data:text/html," + urllib.parse.quote(_PAGE)


async def _run(planner):
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None)
    events = [e async for e in ex.run("place the order")]
    fin = next(e for e in events if e.type == EventType.RUN_FINISHED)
    asked = any(e.type == EventType.ASK_USER for e in events)
    return fin, asked


@pytest.mark.anyio
async def test_peek_replan_resolves_via_page_grounded_suffix():
    planner = MockPlanner(
        [SubTask(action="navigate", url=_URL),
         SubTask(action="click", target="Place Order")],   # absent -> exhausts
        replan_subtasks=[SubTask(action="click", target="Submit Order")],  # present
    )
    fin, asked = await _run(planner)

    assert fin.payload["nominal_completion"] is True   # only possible via replan's suffix
    assert not asked
    assert len(planner.replan_calls) == 1
    task, failure_log, observation = planner.replan_calls[0]
    assert any("Place Order" in f["step"] for f in failure_log)  # the failed step was passed
    assert "Submit Order" in observation               # the page was peeked + passed


@pytest.mark.anyio
async def test_context_free_replan_would_not_recover():
    # Control: without a page-grounded replan (replan re-issues the same absent
    # target), the run cannot complete and abstains -- proving the suffix in the
    # test above is what closes the loop, not some other recovery.
    planner = MockPlanner(
        [SubTask(action="navigate", url=_URL),
         SubTask(action="click", target="Place Order")],
        replan_subtasks=[SubTask(action="click", target="Place Order")],  # still absent
    )
    fin, asked = await _run(planner)

    assert fin.payload["nominal_completion"] is False
    assert asked


@pytest.mark.anyio
async def test_replan_is_bounded_and_accumulates_failures():
    # NOT one-shot: the agent re-plans up to max_replans, each replan shown the GROWING
    # failure log, then abstains (instead of giving up after a single replan).
    planner = MockPlanner(
        [SubTask(action="navigate", url=_URL),
         SubTask(action="click", target="Place Order")],
        replan_subtasks=[SubTask(action="click", target="Place Order")],  # keeps failing
    )
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, max_replans=3)
    events = [e async for e in ex.run("do it")]
    fin = next(e for e in events if e.type == EventType.RUN_FINISHED)
    asked = any(e.type == EventType.ASK_USER for e in events)

    assert len(planner.replan_calls) == 3                 # bounded by max_replans, not one-shot
    assert asked and fin.payload["nominal_completion"] is False
    # the failure log GROWS across replans (accumulation), 1 -> 2 -> 3
    assert [len(fl) for (_t, fl, _o) in planner.replan_calls] == [1, 2, 3]
