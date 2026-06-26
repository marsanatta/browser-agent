"""L2 LLM locator fallback (docs/architecture/02 §2.5, Healwright pattern).

On a FULL deterministic-cascade miss, the executor hands the LLM a compact
<=5-candidate shortlist and lets it pick one; the chosen candidate is then
resolved through the same deterministic tiers and cached. A MockGateway stands in
for Copilot so this runs offline with no auth.
"""

import pytest

from app.agent.locate import LocatorCache, locate, make_l2_fallback
from app.agent.models import MockGateway
from app.agent.perceive import IndexedElement, perceive
from app.browser.provider import PlaywrightProvider

_PAGE = """
<html><body>
<button id="x1" class="btn-primary">Submit Order</button>
<a href="/help">Help Center</a>
<button class="btn-ghost">Cancel</button>
</body></html>
"""


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    await pg.set_content(_PAGE)
    yield pg
    await provider.close()


@pytest.mark.anyio
async def test_l2_fallback_resolves_on_full_miss(page):
    perception = await perceive(page)
    # A target whose name matches NO element directly -> the 10-tier deterministic
    # cascade misses entirely.
    ghost = IndexedElement(99, "button", "Place the order now", {})
    key = page.url.split("?", 1)[0].split("#", 1)[0]

    assert await locate(page, ghost, cache=LocatorCache()) is None  # deterministic miss

    captured = {}

    def responder(prompt: str) -> str:
        captured["prompt"] = prompt
        return "0"  # pick the first shortlisted candidate (Submit Order)

    gateway = MockGateway(responder)
    cache = LocatorCache()
    l2 = make_l2_fallback(gateway, perception.elements)

    located = await locate(page, ghost, cache=cache, l2_fallback=l2)

    assert located is not None
    assert await located.locator.inner_text() == "Submit Order"
    assert cache.get(key, ghost) is not None  # L2 result cached for reuse
    assert len(gateway.calls) == 1
    # shortlist is role-filtered: the link must not be offered to the LLM
    assert "Help Center" not in captured["prompt"]
    assert "Submit Order" in captured["prompt"]


@pytest.mark.anyio
async def test_l2_hit_is_cached_second_locate_makes_zero_gateway_calls(page):
    # The L2 fix: a 2nd locate of the SAME pseudo-target must resolve from cache
    # with ZERO gateway calls (the cached entry rebuilds from the chosen element,
    # not the pseudo-target's unresolvable name).
    perception = await perceive(page)
    ghost = IndexedElement(-1, "button", "Place the order now", {})  # pseudo-target
    gateway = MockGateway(lambda _p: "0")  # picks shortlist[0] = "Submit Order"
    cache = LocatorCache()
    l2 = make_l2_fallback(gateway, perception.elements)

    first = await locate(page, ghost, cache=cache, l2_fallback=l2)
    assert first is not None
    assert await first.locator.inner_text() == "Submit Order"
    assert len(gateway.calls) == 1

    second = await locate(page, ghost, cache=cache, l2_fallback=l2)
    assert second is not None
    assert await second.locator.inner_text() == "Submit Order"
    assert len(gateway.calls) == 1  # cache hit -> NO second gateway call


_SIGNIN_SUBSTR = """
<html><body>
<button id="m">Member Sign In Now</button>
</body></html>
"""


@pytest.fixture
async def signin_page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    await pg.set_content(_SIGNIN_SUBSTR)
    yield pg
    await provider.close()


@pytest.mark.anyio
async def test_pseudo_target_abstains_instead_of_substring_pick(signin_page):
    # A pseudo-target (index == -1) must NOT be resolved by the fuzzy tier-2 role
    # substring match ("Sign In" inside "Member Sign In Now"). With no L2 it abstains
    # (returns None) instead of silently clicking the wrong button.
    pseudo = IndexedElement(-1, "button", "Sign In", {})
    located = await locate(signin_page, pseudo, cache=LocatorCache())
    assert located is None


@pytest.mark.anyio
async def test_pseudo_target_routes_to_l2(signin_page):
    perception = await perceive(signin_page)
    pseudo = IndexedElement(-1, "button", "Sign In", {})
    gateway = MockGateway(lambda _p: "0")  # L2 picks the one candidate
    l2 = make_l2_fallback(gateway, perception.elements)
    located = await locate(signin_page, pseudo, cache=LocatorCache(), l2_fallback=l2)
    assert located is not None
    assert await located.locator.inner_text() == "Member Sign In Now"
    assert len(gateway.calls) == 1


@pytest.mark.anyio
async def test_real_target_still_uses_substring_tier(signin_page):
    # A REAL indexed element (index >= 0) keeps the full fuzzy cascade: the tier-2
    # role substring resolves "Sign In" -> "Member Sign In Now" with no L2 needed.
    real = IndexedElement(0, "button", "Sign In", {})
    located = await locate(signin_page, real, cache=LocatorCache())
    assert located is not None
    assert await located.locator.inner_text() == "Member Sign In Now"


@pytest.mark.anyio
async def test_l2_fallback_returns_none_when_llm_declines(page):
    perception = await perceive(page)
    ghost = IndexedElement(99, "button", "Nonexistent control", {})
    gateway = MockGateway(lambda _p: "-1")  # LLM says none match
    l2 = make_l2_fallback(gateway, perception.elements)

    located = await locate(page, ghost, cache=LocatorCache(), l2_fallback=l2)
    assert located is None
