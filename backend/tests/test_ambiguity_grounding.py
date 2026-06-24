"""Grounding fix: element ambiguity routes to L2 / abstain, never a silent pick.

Covers two of the three ambiguity classes from the RCA deterministically:
  A. substring / distinct names  -> _match must not return candidates[0]; the
     executor abstains (ask_user) instead of silently clicking the wrong link.
  C. same name, one off-viewport -> locate narrows by interactability to the one
     visible in-viewport element.
(B — two same-name links merged by perceive — can only honestly abstain and is
proved end-to-end through the real eval harness, not here.)
"""

import urllib.parse

import pytest

from app.agent.executor import Executor, _match
from app.agent.locate import LocatorCache, locate
from app.agent.models import MockGateway
from app.agent.perceive import IndexedElement
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


async def _run(planner, gateway, instruction, verify_hook):
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=gateway, verify_hook=verify_hook)
    nominal = verified = None
    async for ev in ex.run(instruction):
        if ev.type == EventType.RUN_FINISHED:
            nominal = ev.payload.get("nominal_completion")
            verified = ev.payload.get("verified_completion")
    return nominal, verified


def _el(i, role, name, attrs=None):
    return IndexedElement(i, role, name, attrs or {})


# --- A: _match never silently picks among distinct candidates -------------------


def test_match_substring_tie_is_ambiguous_not_first():
    els = [_el(0, "link", "Login Page"), _el(1, "link", "Login"), _el(2, "link", "Blog login")]
    target, ambiguous = _match(els, SubTask(action="click", target="log"))
    assert target is None
    assert {e.name for e in ambiguous} == {"Login Page", "Login", "Blog login"}


def test_match_exact_unique_returns_target():
    els = [_el(0, "button", "Search"), _el(1, "link", "Home")]
    target, ambiguous = _match(els, SubTask(action="click", target="Search", role="button"))
    assert ambiguous == []
    assert target is not None and target.name == "Search"


def test_match_role_breaks_tie():
    els = [_el(0, "link", "Search"), _el(1, "button", "Search")]
    target, ambiguous = _match(els, SubTask(action="click", target="Search", role="button"))
    assert ambiguous == []
    assert target is not None and target.role == "button"


# --- Playwright fixtures --------------------------------------------------------


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    yield pg
    await provider.close()


# --- C: locate narrows two same-name buttons to the in-viewport one -------------

_TWO_SEARCH = """
<html><body>
<button class="real">Search</button>
<button class="ghost" style="position:absolute; top:-9999px; left:-9999px;">Search</button>
</body></html>
"""


@pytest.mark.anyio
async def test_locate_narrows_to_in_viewport_button(page):
    await page.set_content(_TWO_SEARCH)
    el = _el(0, "button", "Search")
    located = await locate(page, el, cache=LocatorCache())
    assert located is not None
    assert (located.tier, located.strategy) == (1, "role_name")
    assert await located.locator.get_attribute("class") == "real"


# --- A end-to-end: ambiguous click abstains, never silently navigates -----------

_THREE_LINKS = """
<html><body>
<a href="#login-page">Login Page</a>
<a href="#login">Login</a>
<a href="#blog-login">Blog login</a>
</body></html>
"""


@pytest.mark.anyio
async def test_ambiguous_click_abstains_without_silent_navigation():
    data_url = "data:text/html," + urllib.parse.quote(_THREE_LINKS)
    planner = MockPlanner(
        [
            SubTask(action="navigate", url=data_url, description="open page"),
            SubTask(action="click", target="log", description="click log"),
        ]
    )
    # gateway=None -> no L2 -> must abstain (ask_user), never silently click 'Login Page'.
    executor = Executor(PlaywrightProvider(headless=True), planner)

    nominal = None
    asked = False
    changed_clicks = 0
    async for ev in executor.run("click the log link"):
        if ev.type == EventType.ASK_USER:
            asked = True
        elif ev.type == EventType.RUN_FINISHED:
            nominal = bool(ev.payload.get("nominal_completion"))
        elif ev.type == EventType.TOOL_CALL_END and "CHANGED" in str(ev.payload.get("result", "")):
            changed_clicks += 1

    assert asked is True
    assert nominal is False
    assert changed_clicks == 0  # never silently resolved + clicked a wrong link


# --- Fix: zero-candidate _match (synonym/label mismatch) routes to L2 ------------

_SYNONYM = """
<button id="b">Log in</button>
<div id="out">none</div>
<script>document.getElementById('b').onclick=function(){document.getElementById('out').textContent='SUBMITTED'};</script>
"""


@pytest.mark.anyio
async def test_zero_candidate_synonym_routes_to_l2():
    # Instruction targets "Sign In" but the only element is named "Log in" -> _match
    # returns ZERO candidates. With a gateway, L2 ranks the full perceived list and
    # picks "Log in"; the click then fires.
    data_url = "data:text/html," + urllib.parse.quote(_SYNONYM)
    planner = MockPlanner(
        [SubTask(action="navigate", url=data_url), SubTask(action="click", target="Sign In")]
    )
    gateway = MockGateway(lambda _p: "0")  # L2 picks shortlist[0]

    async def verify_hook(page):
        return (await page.locator("#out").inner_text()) == "SUBMITTED"

    nominal, verified = await _run(planner, gateway, "sign in", verify_hook)
    assert nominal is True
    assert verified is True  # the L2-picked 'Log in' button was actually clicked


@pytest.mark.anyio
async def test_zero_candidate_synonym_abstains_without_gateway():
    # Same page, NO gateway -> no L2 -> must abstain honestly, never silent-click.
    data_url = "data:text/html," + urllib.parse.quote(_SYNONYM)
    planner = MockPlanner(
        [SubTask(action="navigate", url=data_url), SubTask(action="click", target="Sign In")]
    )

    async def verify_hook(page):
        return (await page.locator("#out").inner_text()) == "SUBMITTED"

    nominal, verified = await _run(planner, None, "sign in", verify_hook)
    assert nominal is False
    assert verified is False  # abstained; the wrong element was NOT clicked


# --- Fix: press action submits a form Enter can't be done by a click -------------

_PRESS_FORM = """
<form id="f"><input aria-label="Query" /></form>
<div id="out">none</div>
<script>document.getElementById('f').onsubmit=function(){document.getElementById('out').textContent='SENT';return false;};</script>
"""


@pytest.mark.anyio
async def test_press_action_submits_form():
    data_url = "data:text/html," + urllib.parse.quote(_PRESS_FORM)
    planner = MockPlanner(
        [
            SubTask(action="navigate", url=data_url),
            SubTask(action="fill", target="Query", value="steam"),
            SubTask(action="press", target="Query", value="Enter"),
        ]
    )

    async def verify_hook(page):
        return (await page.locator("#out").inner_text()) == "SENT"

    nominal, verified = await _run(planner, None, "search steam", verify_hook)
    assert nominal is True
    assert verified is True  # Enter submitted the form (a click could not)
