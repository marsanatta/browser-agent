"""CDP real-browser escalation provider + its selection wiring (network-free).

`_make_provider()` picks the CDP real-browser runtime when `BROWSER_CDP_URL` is set,
else the default headless Playwright. CDPProvider construction is lazy (no connect)
and close() is safe before launch — so these run with no browser/network.
"""

import pytest

from app.browser.provider import CDPProvider, PlaywrightProvider
from app.main import _make_provider


def test_make_provider_defaults_to_headless_playwright(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    assert isinstance(_make_provider(), PlaywrightProvider)


def test_make_provider_uses_cdp_when_env_set(monkeypatch):
    monkeypatch.setenv("BROWSER_CDP_URL", "http://127.0.0.1:18800")
    p = _make_provider()
    assert isinstance(p, CDPProvider)
    assert p._cdp_url == "http://127.0.0.1:18800"


def test_cdp_provider_construction_is_lazy():
    # No connect at construction — nothing reaches the network until launch().
    p = CDPProvider("http://127.0.0.1:9999")
    assert p._browser is None and p._page is None


@pytest.mark.anyio
async def test_cdp_provider_close_without_launch_is_safe():
    # close() before launch() must be a no-op, not a crash.
    await CDPProvider("http://127.0.0.1:9999").close()
