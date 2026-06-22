"""Deterministic integration test against live the-internet.herokuapp.com.

No LLM: exercises perceive -> 10-tier cascade -> click -> verify-after-act.
Ground truth (probed): the home page has a 'Form Authentication' link that
navigates to /login.
"""

import pytest

from app.agent import act, verify
from app.agent.locate import LocatorCache, locate
from app.agent.perceive import perceive
from app.browser.provider import PlaywrightProvider

BASE = "https://the-internet.herokuapp.com"


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    yield pg
    await provider.close()


@pytest.mark.live
@pytest.mark.anyio
async def test_cascade_resolves_and_click_changes_url(page):
    await act.navigate(page, BASE)
    perception = await perceive(page)

    target = next(
        e for e in perception.elements
        if e.role == "link" and e.name.strip() == "Form Authentication"
    )

    located = await locate(page, target, cache=LocatorCache())
    assert located is not None
    assert located.tier == 1  # ARIA role + accessible name resolves first
    assert located.strategy == "role_name"

    before = await verify.snapshot(page)
    await act.click(located.locator)
    result = await verify.verify_after_act(
        page, before, verify.Expectation(url_contains="/login")
    )

    assert result is verify.VerifyResult.CHANGED
    assert page.url.endswith("/login")


@pytest.mark.live
@pytest.mark.anyio
async def test_cascade_cache_hit_second_call(page):
    await act.navigate(page, BASE)
    perception = await perceive(page)
    target = next(
        e for e in perception.elements
        if e.role == "link" and e.name.strip() == "Checkboxes"
    )
    cache = LocatorCache()

    first = await locate(page, target, cache=cache)
    assert first is not None
    assert cache.get(BASE + "/", target) is not None  # written back

    second = await locate(page, target, cache=cache)
    assert second is not None
    assert second.tier == first.tier
