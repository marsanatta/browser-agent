"""Per-class recovery + bounded escalation (docs/architecture/02 §1.2/§1.3).

Failure class is decided from OBSERVABLE browser state (is_visible/is_enabled,
exception text), never the LLM. Each class maps to a fixed recovery; retries are
bounded and only continue on a NEW observation; on local exhaustion the ladder
escalates replan -> ask_user.

These run on real Playwright with local HTML (no network) for determinism, plus
one live stale/timing case on a real seed page.
"""

import pytest

from app.agent import act, recover
from app.agent.classify import (
    FailureClass,
    Recovery,
    classify_exception,
    recovery_for,
)
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import BrowserProvider, PlaywrightProvider
from app.stream.events import EventType

BASE = "https://the-internet.herokuapp.com"


class _LocalProvider(BrowserProvider):
    """Real Chromium serving fixed HTML — exercises the full executor offline."""

    def __init__(self, html: str) -> None:
        self._html = html
        self._pw = self._browser = self._ctx = None

    async def launch(self) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._ctx = await self._browser.new_context()

    async def new_page(self):
        pg = await self._ctx.new_page()
        await pg.set_content(self._html)
        return pg

    async def close(self) -> None:
        if self._ctx:
            await self._ctx.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()


async def _drive(provider, plan, task):
    ex = Executor(provider, MockPlanner(plan))
    recoveries, asks, finished = [], [], None
    async for ev in ex.run(task):
        if ev.type == EventType.RECOVERY:
            recoveries.append(ev.payload)
        elif ev.type == EventType.ASK_USER:
            asks.append(ev.payload)
        elif ev.type == EventType.RUN_FINISHED:
            finished = ev.payload
    return recoveries, asks, finished


# ---- unit: exception -> class mapping (Playwright ground-truth text) ----

@pytest.mark.parametrize("msg,expected", [
    ("element is not enabled", FailureClass.NOT_INTERACTABLE),
    ("Element is outside of the viewport", FailureClass.NOT_INTERACTABLE),
    ("Element is not visible", FailureClass.NOT_INTERACTABLE),
    ("locator.click: Timeout 5000ms exceeded", FailureClass.STALE_TIMING),
    ("element is not attached to the DOM", FailureClass.STALE_TIMING),
])
def test_classify_exception(msg, expected):
    assert classify_exception(Exception(msg)) is expected


def test_recovery_mapping():
    assert recovery_for(FailureClass.NOT_FOUND) is Recovery.REGROUND
    assert recovery_for(FailureClass.NOT_INTERACTABLE) is Recovery.WAIT_SCROLL_DISMISS
    assert recovery_for(FailureClass.WRONG_PAGE) is Recovery.REPLAN
    assert recovery_for(FailureClass.STALE_TIMING) is Recovery.STATE_WAIT


# ---- not-interactable: permanently disabled -> bounded escalation -> ask_user ----

_DISABLED = """
<html><body>
<button aria-label="Place Order" disabled>Place Order</button>
</body></html>
"""


@pytest.mark.anyio
async def test_not_interactable_bounded_escalation_to_ask_user():
    plan = [SubTask(action="click", target="Place Order", role="button")]
    recoveries, asks, finished = await _drive(_LocalProvider(_DISABLED), plan, "click disabled")

    classes = {r["failure_class"] for r in recoveries}
    assert classes == {FailureClass.NOT_INTERACTABLE.value}
    assert any(r["recovery"] == Recovery.WAIT_SCROLL_DISMISS.value for r in recoveries)
    assert any(r["recovery"] == Recovery.REPLAN.value for r in recoveries)  # escalated
    assert asks, "bounded ladder must terminate at ask_user"
    assert finished["nominal_completion"] is False
    # bound: even with one replan the ladder is finite (no infinite loop)
    assert len(recoveries) < 12


# ---- not-interactable that resolves: recovery succeeds, action retried ----

_TRANSIENT = """
<html><body>
<button id="cta" aria-label="Submit" disabled
        onclick="document.body.innerHTML += '<p>done</p>'">Submit</button>
<script>setTimeout(() => document.getElementById('cta').removeAttribute('disabled'), 800)</script>
</body></html>
"""


@pytest.mark.anyio
async def test_not_interactable_recovers_then_succeeds():
    plan = [SubTask(action="click", target="Submit", role="button")]
    recoveries, asks, finished = await _drive(_LocalProvider(_TRANSIENT), plan, "click once enabled")

    assert recoveries, "the first attempt must observe NOT_INTERACTABLE"
    assert recoveries[0]["failure_class"] == FailureClass.NOT_INTERACTABLE.value
    assert recoveries[0]["recovery"] == Recovery.WAIT_SCROLL_DISMISS.value
    assert not asks
    assert finished["nominal_completion"] is True  # wait recovery -> retry succeeds


# ---- stale / timing: state_wait re-attaches a re-rendered node (live) ----

@pytest.mark.live
@pytest.mark.anyio
async def test_state_wait_reattaches_rerendered_node():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    try:
        await act.navigate(pg, BASE + "/add_remove_elements/")
        await pg.get_by_role("button", name="Add Element").click()
        delete = pg.get_by_role("button", name="Delete")
        assert await delete.count() == 1
        assert await recover.state_wait(pg, delete) is True
    finally:
        await provider.close()
