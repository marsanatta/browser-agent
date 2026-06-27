"""peek-plan (the root fix for a-priori blindness) — deterministic plumbing anchor.

Proves, offline (no network, no Copilot): the BLIND plan targets an element that is
absent on the live page (a-priori guess) and fails; the PEEK plan first navigates +
perceives the start page, the real observation reaches `planner.plan(observation=...)`,
and the grounded plan hits the element that is actually there and succeeds. This is the
plumbing proof; the live paired runs measure the effect.
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

# The real element is "Submit Order"; clicking it reveals DONE (independently checkable).
_HTML = (
    "<body><button onclick=\"document.body.insertAdjacentHTML('beforeend',"
    "'<h1 id=d>DONE</h1>')\">Submit Order</button></body>"
)
_URL = "data:text/html," + urllib.parse.quote(_HTML)


def _planner():
    # Blind plan targets the ABSENT "Place Order"; given an observation, peek plans the
    # REAL "Submit Order". replan_subtasks=[] so a blind failure abstains (no loop).
    return MockPlanner(
        [SubTask(action="navigate", url=_URL), SubTask(action="click", target="Place Order")],
        replan_subtasks=[],
        peek_subtasks=[SubTask(action="click", target="Submit Order")],
    )


async def _run(planner, peek):
    async def vhook(page):
        loc = page.locator("#d").first
        return await loc.count() > 0 and (await loc.inner_text()).strip() == "DONE"

    ex = Executor(
        PlaywrightProvider(headless=True), planner, gateway=None,
        verify_hook=vhook, peek_plan=peek, start_url=_URL,
    )
    fin = next(
        e for e in [e async for e in ex.run("place the order")]
        if e.type == EventType.RUN_FINISHED
    )
    return fin.payload["nominal_completion"], fin.payload["verified_completion"]


@pytest.mark.anyio
async def test_blind_plan_misses_absent_element_and_sees_no_observation():
    p = _planner()
    _nominal, verified = await _run(p, peek=False)
    assert verified is False  # a-priori guess targets an absent element -> fails
    assert all(obs is None for (_t, _s, obs) in p.plan_calls)  # blind never peeked


@pytest.mark.anyio
async def test_peek_plan_navigates_perceives_and_grounds_the_plan():
    p = _planner()
    nominal, verified = await _run(p, peek=True)
    assert nominal is True and verified is True  # grounded plan hits the real element
    peeked = [obs for (_t, _s, obs) in p.plan_calls if obs is not None]
    assert peeked and "Submit Order" in peeked[0]  # the real observation reached plan()
