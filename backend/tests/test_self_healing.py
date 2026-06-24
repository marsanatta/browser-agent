"""Self-maintenance proof: when a cached locator's primary tier stops resolving
(selector/DOM changed), the deterministic cascade must HEAL to a lower tier and
RE-CACHE the new tier. docs/architecture/02 §2.5.

Two layers of evidence:
- offline (deterministic, no network): full control over which tier breaks.
- live: the same heal on a real seed page (the-internet.herokuapp.com).
"""

import pytest

from app.agent import act
from app.agent.locate import LocatorCache, locate
from app.agent.perceive import IndexedElement, perceive
from app.browser.provider import PlaywrightProvider

BASE = "https://the-internet.herokuapp.com"

_TWO_BUTTONS = """
<html><body>
<button id="b1" class="primary-cta">Go</button>
<button id="b2" class="ghost">Go</button>
</body></html>
"""

_HEAL_PAGE = """
<html><body>
<button id="b1" class="primary-cta">Go</button>
</body></html>
"""


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    yield pg
    await provider.close()


@pytest.mark.anyio
async def test_cascade_heals_down_tiers_and_recaches(page):
    """Healing mechanism: when the cached tier stops resolving, re-cascade to a
    lower tier and re-cache. Uses a UNIQUE accessible name so role+name is
    unambiguous; breakage is simulated by mutating the live name / stripping
    attributes. (On-page duplicate names now route to L2 instead of resolving via
    a carried attribute — see the ambiguity test below.)"""
    await page.set_content(_HEAL_PAGE)
    el = IndexedElement(
        0, "button", "Go",
        {"id": "b1", "testid": "", "aria_label": "", "href": "", "cls": "primary-cta"},
    )
    cache = LocatorCache()
    key = page.url.split("?", 1)[0].split("#", 1)[0]

    first = await locate(page, el, cache=cache)
    assert first is not None
    assert (first.tier, first.strategy) == (1, "role_name")
    assert cache.get(key, el) == (1, "role_name")

    # Break role+name: mutate the live accessible name. The cached role_name
    # locator no longer resolves -> re-cascade heals to the unique #id.
    await page.evaluate("() => { document.getElementById('b1').textContent = 'Proceed'; }")
    healed = await locate(page, el, cache=cache)
    assert healed is not None
    assert (healed.tier, healed.strategy) == (4, "id")
    assert cache.get(key, el) == (4, "id")  # re-cached to the new tier

    # Break the id too -> heal further DOWN to the class selector.
    await page.evaluate("() => { document.querySelector('.primary-cta').removeAttribute('id'); }")
    healed2 = await locate(page, el, cache=cache)
    assert healed2 is not None
    assert (healed2.tier, healed2.strategy) == (8, "css_exact")
    assert cache.get(key, el) == (8, "css_exact")
    assert await healed2.locator.get_attribute("class") == "primary-cta"


@pytest.mark.anyio
async def test_same_name_ambiguity_does_not_silently_resolve(page):
    """Grounding fix: when role+name matches multiple visible in-viewport elements,
    locate must NOT silently resolve via a carried attribute — the perceive-merged
    element holds only the FIRST node's id/href, so resolving it would silently
    pick the wrong one. With no L2 wired, it abstains (None)."""
    await page.set_content(_TWO_BUTTONS)
    el = IndexedElement(
        0, "button", "Go",
        {"id": "b1", "testid": "", "aria_label": "", "href": "", "cls": "primary-cta"},
    )
    assert await locate(page, el, cache=LocatorCache()) is None


@pytest.mark.live
@pytest.mark.anyio
async def test_live_heals_role_name_to_href(page):
    await act.navigate(page, BASE)
    perception = await perceive(page)
    el = next(
        e for e in perception.elements
        if e.role == "link" and e.name.strip() == "Form Authentication"
    )
    cache = LocatorCache()

    first = await locate(page, el, cache=cache)
    assert first is not None
    assert (first.tier, first.strategy) == (1, "role_name")

    # Mutate the link's accessible name so role+name no longer matches; the
    # href (/login) is unchanged, so the cascade should heal to the href tier.
    await page.evaluate(
        """() => {
            const a = [...document.querySelectorAll('a')]
                .find(x => x.textContent.trim() === 'Form Authentication');
            a.textContent = 'FA';
        }"""
    )

    healed = await locate(page, el, cache=cache)
    assert healed is not None
    assert (healed.tier, healed.strategy) == (7, "href")
    assert await healed.locator.get_attribute("href") == "/login"
