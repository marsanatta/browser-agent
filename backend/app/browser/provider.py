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
