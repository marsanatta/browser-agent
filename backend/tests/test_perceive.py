"""PERCEIVE must not run a dead per-step table/list DOM pass: its `markdown`
output was read NOWHERE (grep `.markdown` over backend/app = 0). Removing it
drops one full page.evaluate() per perceive call and the unused field.

Network-free: a data: URL with a table; we count page.evaluate() calls.
"""

import urllib.parse

import pytest

from app.agent.perceive import Perception, perceive
from app.browser.provider import PlaywrightProvider

_TABLE_PAGE = "data:text/html," + urllib.parse.quote(
    "<table><tr><th>A</th></tr><tr><td>1</td></tr></table><button>Go</button>"
)


@pytest.fixture
async def page():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    await pg.goto(_TABLE_PAGE)
    yield pg
    await provider.close()


def test_perception_has_no_markdown_field():
    assert "markdown" not in Perception.__dataclass_fields__


@pytest.mark.anyio
async def test_perceive_does_not_run_table_pass(page):
    calls = {"n": 0}
    real_eval = page.evaluate

    async def counting(script, *a, **kw):
        calls["n"] += 1
        return await real_eval(script, *a, **kw)

    page.evaluate = counting
    p = await perceive(page)

    assert not hasattr(p, "markdown")
    assert any(e.name == "Go" for e in p.elements)
    # exactly one evaluate: the interactive scan. The removed table/list pass was a
    # second evaluate() per perceive call.
    assert calls["n"] == 1
