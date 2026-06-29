"""Bot-wall / interstitial detection (route, don't evade).

The agent must NOT claim success on a block (CAPTCHA / challenge / "unusual
traffic" interstitial); it abstains and routes blocked-unsupported. Deterministic
and network-free: benign srcs/text that still match the high-confidence markers.
"""

import urllib.parse

import pytest

from app.agent import verify
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


@pytest.fixture
async def page():
    p = PlaywrightProvider(headless=True)
    await p.launch()
    pg = await p.new_page()
    yield pg
    await p.close()


@pytest.mark.anyio
async def test_detect_block_flags_recaptcha_widget(page):
    await page.set_content('<h1>Verify</h1><iframe src="about:blank#recaptcha"></iframe>')
    assert await verify.detect_block(page) is not None


@pytest.mark.anyio
async def test_detect_block_ignores_invisible_recaptcha_helper(page):
    # Legit pages (e.g. stockanalysis.com) load an invisible reCAPTCHA v3 helper
    # frame (recaptcha/api2/aframe, 0x0 display:none) for form scoring. It is NOT
    # a challenge and the page is fully usable, so detect_block must not flag it.
    await page.set_content(
        '<h1>NVIDIA</h1><p>Market Cap 4.66T</p>'
        '<iframe src="https://www.google.com/recaptcha/api2/aframe"'
        ' style="display:none;width:0;height:0"></iframe>'
    )
    assert await verify.detect_block(page) is None


@pytest.mark.anyio
async def test_detect_block_flags_unusual_traffic_text(page):
    await page.set_content(
        "<p>Our systems have detected unusual traffic from your computer network.</p>"
    )
    assert await verify.detect_block(page) is not None


@pytest.mark.anyio
async def test_detect_block_passes_clean_page(page):
    await page.set_content("<button>Continue</button><p>welcome to the docs</p>")
    assert await verify.detect_block(page) is None


@pytest.mark.anyio
async def test_detect_block_flags_datadome_challenge(page):
    # DataDome 403 interstitial (real g2.com behaviour): empty visible body, the whole
    # page is a challenge loaded from geo.captcha-delivery.com in a script. URL/selector/
    # text markers all miss it (nothing visible), so without the HTML-host check the
    # agent silently "succeeds" on a blocked page.
    await page.set_content("<script>var dd={'host':'geo.captcha-delivery.com'};</script>")
    assert await verify.detect_block(page) is not None


@pytest.mark.anyio
async def test_detect_block_ignores_datadome_host_on_full_page(page):
    # A usable page that merely embeds anti-bot scoring must NOT be flagged just because
    # the HTML mentions the delivery host — only an empty-body challenge page is a block.
    # (Mirrors the invisible-helper caution: do not route usable pages to unsupported.)
    await page.set_content(
        "<h1>Marketing Software</h1><p>" + ("Compare top marketing tools. " * 20)
        + "</p><script>var ref='captcha-delivery.com';</script>"
    )
    assert await verify.detect_block(page) is None


@pytest.mark.anyio
async def test_blocked_action_abstains_not_silent_success():
    # A clean page whose button injects a CAPTCHA on click (mirrors google's press ->
    # /sorry/): the click changes the DOM, but detect_block overrides success -> the
    # agent abstains (blocked-unsupported), never claims nominal success.
    html = (
        '<button id="go">Continue</button><div id="out">none</div>'
        "<script>document.getElementById('go').onclick=function(){"
        "var f=document.createElement('iframe');f.src='about:blank#recaptcha';"
        "document.body.appendChild(f);"
        "document.getElementById('out').textContent='CLICKED';};</script>"
    )
    data_url = "data:text/html," + urllib.parse.quote(html)
    planner = MockPlanner(
        [SubTask(action="navigate", url=data_url), SubTask(action="click", target="Continue")]
    )
    ex = Executor(PlaywrightProvider(headless=True), planner)

    nominal = asked = None
    blocked_seen = False
    async for ev in ex.run("continue past the wall"):
        if ev.type == EventType.ASK_USER:
            asked = True
        elif ev.type == EventType.STEP_FINISHED and ev.payload.get("failure_category") == "BLOCKED":
            blocked_seen = True
        elif ev.type == EventType.RUN_FINISHED:
            nominal = ev.payload.get("nominal_completion")

    assert blocked_seen is True   # surfaced as the distinct BLOCKED class
    assert asked is True          # routed to abstain
    assert nominal is False       # never claimed success on the bot-wall
