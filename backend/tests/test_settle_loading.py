"""Iteration 1 (Probe A): the lazy-load ground-time fix — deterministic + offline.

Reproduces the `live_internet_lazyload` SILENT_FAILURE class (click -> spinner ->
async result) on a `data:`-content fixture with NO network, and asserts the settle
fix makes it pass. This deterministic green is the PRIMARY keep signal; the noisy
live row is corroboration only (plan §5). settle touches verify TIMING, never the
state-check assertion (plan G3 sub-clause).
"""

import urllib.parse

import pytest

from app.agent import recover
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

# Click "Load" -> a #loading spinner shows, then after 800ms hides and #finish
# renders "Done". Without a settle the check races the spinner (target absent ->
# verified=False while the DOM changed -> nominal=True = a silent failure).
_SPINNER = (
    '<button id="go">Load</button>'
    '<div id="loading" style="display:none">loading…</div>'
    '<div id="finish"></div>'
    "<script>document.getElementById('go').onclick=function(){"
    "var l=document.getElementById('loading'); l.style.display='block';"
    "setTimeout(function(){ l.style.display='none';"
    "document.getElementById('finish').textContent='Done'; }, 800);};</script>"
)


@pytest.fixture
async def page():
    p = PlaywrightProvider(headless=True)
    await p.launch()
    pg = await p.new_page()
    yield pg
    await p.close()


@pytest.mark.anyio
async def test_settle_loading_waits_out_spinner(page):
    await page.set_content(_SPINNER)
    await page.get_by_role("button", name="Load").click()  # spinner now visible, #finish empty
    assert (await page.locator("#finish").inner_text()).strip() == ""
    settled = await recover.settle_loading(page)
    assert settled is True
    assert (await page.locator("#finish").inner_text()).strip() == "Done"  # observed, not raced


@pytest.mark.anyio
async def test_settle_loading_noop_when_no_spinner(page):
    await page.set_content("<button>x</button><p>ready</p>")
    assert await recover.settle_loading(page) is False  # nothing to settle -> fast no-op


@pytest.mark.anyio
async def test_lazyload_run_verifies_with_settle_not_silent():
    # End-to-end regression guard: with the settle wired, the spinner-race row
    # VERIFIES (nominal AND verified) instead of silently failing. Reverting the
    # settle turns this red.
    data_url = "data:text/html," + urllib.parse.quote(_SPINNER)
    planner = MockPlanner([SubTask(action="navigate", url=data_url),
                           SubTask(action="click", target="Load")])

    async def verify_hook(pg):
        return (await pg.locator("#finish").inner_text()).strip() == "Done"

    ex = Executor(PlaywrightProvider(headless=True), planner, verify_hook=verify_hook)
    nominal = verified = None
    async for ev in ex.run("load the deferred result"):
        if ev.type == EventType.RUN_FINISHED:
            nominal = ev.payload.get("nominal_completion")
            verified = ev.payload.get("verified_completion")
    assert nominal is True
    assert verified is True  # NOT a silent failure: the async result was observed
