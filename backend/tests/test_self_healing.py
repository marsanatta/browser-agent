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


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    yield pg
    await provider.close()


@pytest.mark.anyio
async def test_cascade_heals_to_lower_tier_and_recaches(page):
    await page.set_content(_TWO_BUTTONS)
    # Same accessible name on both buttons -> role/role_name/text are ambiguous
    # (count==2, treated as a miss), so only the unique #id resolves first.
    el = IndexedElement(
        0, "button", "Go",
        {"id": "b1", "testid": "", "aria_label": "", "href": "", "cls": "primary-cta"},
    )
    cache = LocatorCache()
    key = page.url.split("?", 1)[0].split("#", 1)[0]

    first = await locate(page, el, cache=cache)
    assert first is not None
    assert (first.tier, first.strategy) == (4, "id")
    assert cache.get(key, el) == (4, "id")  # written back

    # Break the primary tier: strip the id. The cached id-locator no longer
    # resolves, forcing a re-cascade.
    await page.evaluate("() => document.getElementById('b1').removeAttribute('id')")

    healed = await locate(page, el, cache=cache)
    assert healed is not None
    assert (healed.tier, healed.strategy) == (8, "css_exact")  # healed DOWN the cascade
    assert cache.get(key, el) == (8, "css_exact")  # re-cached to the new tier
    # the healed locator still points at the intended element, not its sibling
    assert await healed.locator.get_attribute("class") == "primary-cta"


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
