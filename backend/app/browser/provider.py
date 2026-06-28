"""Swappable browser-runtime interface + async Playwright skeleton.

Async (not sync) Playwright: the backend is FastAPI + sse-starlette (asyncio),
and the agent loop is I/O-bound (navigation, network waits, element waits). The
async API runs natively in the event loop and lets ephemeral browsers per task
scale without thread offloading. Sync Playwright cannot run inside a running
asyncio loop.

M0 is the interface + lifecycle skeleton only — no agent logic, no perception,
no locator cascade (those are M1+).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BrowserProvider(ABC):
    """Runtime-agnostic seam. Self-hosted Playwright is the default; Steel.dev /
    Browserbase are escalation targets behind this same interface."""

    @abstractmethod
    async def launch(self) -> None: ...

    @abstractmethod
    async def new_page(self) -> Any: ...

    @abstractmethod
    async def close(self) -> None: ...


class PlaywrightProvider(BrowserProvider):
    """Self-hosted Chromium via Playwright async API. One ephemeral context per
    task; recycled on close to bound memory creep."""

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None

    async def launch(self) -> None:
        if self._browser is not None:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context()

    async def new_page(self) -> Any:
        if self._context is None:
            raise RuntimeError("launch() must be called before new_page()")
        return await self._context.new_page()

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None


class CDPProvider(BrowserProvider):
    """Drive an externally-managed REAL browser over CDP — the Steel.dev / Browserbase
    escalation tier behind the same seam. A real (non-headless, real
    profile/fingerprint) Chrome bypasses the headless anti-bot walls that fail the
    default `PlaywrightProvider` on sites like Amazon. The
    browser is NOT owned by us: `close()` detaches our tab and disconnects the local
    driver, and NEVER closes the external browser or its other tabs."""

    def __init__(self, cdp_url: str) -> None:
        self._cdp_url = cdp_url
        self._playwright: Any = None
        self._browser: Any = None
        self._page: Any = None

    async def launch(self) -> None:
        if self._browser is not None:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
        except Exception:
            # Connecting to an external endpoint fails far more often than a local
            # launch (browser down / wrong port) — don't leak the local driver process.
            await self._playwright.stop()
            self._playwright = None
            raise

    async def new_page(self) -> Any:
        if self._browser is None:
            raise RuntimeError("launch() must be called before new_page()")
        # Use the external browser's existing context (its real profile/cookies) — the
        # real-profile fingerprint is the whole point, so never spawn an isolated one.
        if not self._browser.contexts:
            raise RuntimeError("connected browser exposes no context over CDP")
        self._page = await self._browser.contexts[0].new_page()
        return self._page

    async def close(self) -> None:
        if self._page is not None:
            try:
                await self._page.close()  # close only OUR tab
            except Exception:
                pass
            self._page = None
        # Deliberately NOT browser.close(): that disconnects/clears the EXTERNAL browser.
        # Dropping the ref + stopping the local driver detaches without killing it.
        self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
