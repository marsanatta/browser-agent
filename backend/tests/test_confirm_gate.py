"""Confirm-before-submit gates the SIDE-EFFECTING actions (press, submit-click),
NOT the benign fill (docs/architecture/02 §1.3: confirm before write/submit).

A `confirm_submit` returning False must block a `press` and a submit `click` from
executing their action, while a `fill` proceeds unconfirmed. Deterministic, network
-free: a data: URL whose elements record whether their action fired.
"""

import urllib.parse

import pytest

from app.agent import act
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


def test_write_actions_are_submit_class_not_fill():
    assert "fill" not in act._WRITE_ACTIONS
    assert "press" in act._WRITE_ACTIONS
    assert "click" in act._WRITE_ACTIONS
    assert "submit" not in act._WRITE_ACTIONS  # dead kind dropped


async def _run(plan, instruction, verify_hook, confirm_submit):
    ex = Executor(
        PlaywrightProvider(headless=True),
        MockPlanner(plan),
        confirm_submit=confirm_submit,
        verify_hook=verify_hook,
    )
    async for ev in ex.run(instruction):
        if ev.type == EventType.RUN_FINISHED:
            return ev.payload.get("verified_completion")
    return None


_PRESS_FORM = """
<form id="f"><input aria-label="Query" /></form>
<div id="out">none</div>
<script>document.getElementById('f').onsubmit=function(){document.getElementById('out').textContent='SENT';return false;};</script>
"""


@pytest.mark.anyio
async def test_press_blocked_when_confirm_false():
    data_url = "data:text/html," + urllib.parse.quote(_PRESS_FORM)
    plan = [
        SubTask(action="navigate", url=data_url),
        SubTask(action="fill", target="Query", value="steam"),
        SubTask(action="press", target="Query", value="Enter"),
    ]

    async def verify_hook(page):
        return (await page.locator("#out").inner_text()) == "SENT"

    async def deny():
        return False

    verified = await _run(plan, "search", verify_hook, deny)
    assert verified is False  # press was gated -> form never submitted


_CLICK_BTN = """
<button id="go">Submit Order</button>
<div id="out">none</div>
<script>document.getElementById('go').onclick=function(){document.getElementById('out').textContent='ORDERED';};</script>
"""


@pytest.mark.anyio
async def test_submit_click_blocked_when_confirm_false():
    data_url = "data:text/html," + urllib.parse.quote(_CLICK_BTN)
    plan = [
        SubTask(action="navigate", url=data_url),
        SubTask(action="click", target="Submit Order"),
    ]

    async def verify_hook(page):
        return (await page.locator("#out").inner_text()) == "ORDERED"

    async def deny():
        return False

    verified = await _run(plan, "order", verify_hook, deny)
    assert verified is False  # click gated -> order never placed


@pytest.mark.anyio
async def test_fill_proceeds_unconfirmed():
    data_url = "data:text/html," + urllib.parse.quote(_PRESS_FORM)
    plan = [
        SubTask(action="navigate", url=data_url),
        SubTask(action="fill", target="Query", value="steam"),
    ]

    async def verify_hook(page):
        return (await page.locator("input[aria-label='Query']").input_value()) == "steam"

    async def deny():
        return False

    verified = await _run(plan, "type", verify_hook, deny)
    assert verified is True  # fill is not a write/submit gate -> proceeds
