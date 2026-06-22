"""Deterministic integration test against live books.toscrape.com.

No LLM: perceive the catalog, locate a book by its accessible name via the
cascade, navigate, assert the product title. Ground truth (probed): the first
catalog book is 'A Light in the Attic'.
"""

import pytest

from app.agent import act, verify
from app.agent.locate import LocatorCache, locate
from app.agent.perceive import perceive
from app.browser.provider import PlaywrightProvider

BASE = "https://books.toscrape.com"
BOOK = "A Light in the Attic"


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    yield pg
    await provider.close()


@pytest.mark.live
@pytest.mark.anyio
async def test_perceive_catalog_has_books(page):
    await act.navigate(page, BASE)
    perception = await perceive(page)
    names = {e.name.strip() for e in perception.elements if e.role == "link"}
    assert BOOK in names
    assert "Travel" in names  # category nav


@pytest.mark.live
@pytest.mark.anyio
async def test_locate_book_navigate_and_assert_title(page):
    await act.navigate(page, BASE)
    perception = await perceive(page)
    target = next(
        e for e in perception.elements if e.role == "link" and e.name.strip() == BOOK
    )

    located = await locate(page, target, cache=LocatorCache())
    assert located is not None

    before = await verify.snapshot(page)
    await act.click(located.locator)
    result = await verify.verify_after_act(
        page, before, verify.Expectation(url_changes=True)
    )
    assert result is verify.VerifyResult.CHANGED

    title = await page.locator("h1").first.inner_text()
    assert title.strip() == BOOK
