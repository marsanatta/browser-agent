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
async def test_l2_fallback_returns_none_when_llm_declines(page):
    perception = await perceive(page)
    ghost = IndexedElement(99, "button", "Nonexistent control", {})
    gateway = MockGateway(lambda _p: "-1")  # LLM says none match
    l2 = make_l2_fallback(gateway, perception.elements)

    located = await locate(page, ghost, cache=LocatorCache(), l2_fallback=l2)
    assert located is None
