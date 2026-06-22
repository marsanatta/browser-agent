"""RECOVER: deterministic per-class recovery actions (no LLM).

docs/architecture/02 §1.2 maps each failure class to a fix:
    not-interactable -> wait / scroll-into-view / dismiss overlay
    stale / timing   -> state-based wait (attached + stable), then retry same

These produce a NEW observation that justifies the next retry (§1.3: "never
retry blindly — every retry must be justified by a NEW observation"). Each
returns True when it changed something worth retrying on, False otherwise, so
the executor can stop escalating when a recovery is a no-op.
"""

from __future__ import annotations

import asyncio
from typing import Any


async def wait_scroll_dismiss(page: Any, locator: Any) -> bool:
    """not-interactable: the element exists but is occluded/disabled/off-screen.
    Try, in order: dismiss a blocking overlay, scroll the target into view, and
    poll briefly for it to become visible+enabled (e.g. a disabled input that a
    sibling control enables). Ground truth is is_visible()/is_enabled().

    Returns True only when it produced a NEW observation worth retrying on:
    either an overlay was dismissed or the element actually became interactable.
    A bare scroll that leaves the element still disabled is NOT progress, so the
    bounded ladder stops escalating instead of spinning (docs/architecture/02
    §1.3: every retry must be justified by a new observation)."""
    dismissed = await _dismiss_overlay(page)

    try:
        await locator.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass

    for _ in range(8):  # ~2s bounded poll
        try:
            if await locator.is_visible() and await locator.is_enabled():
                return True
        except Exception:
            break
        await asyncio.sleep(0.25)
    return dismissed


async def state_wait(page: Any, locator: Any) -> bool:
    """stale / timing: race with async render. Wait for the network to settle
    and for the element to be attached again, producing a fresh handle."""
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    try:
        await locator.first.wait_for(state="attached", timeout=5000)
        return True
    except Exception:
        return False


_OVERLAY_SELECTORS = (
    "[role=dialog] button[aria-label*=close i]",
    "button[aria-label*=close i]",
    ".modal.show button.close",
    "#onetrust-accept-btn-handler",
    "button:has-text('Accept')",
)


async def _dismiss_overlay(page: Any) -> bool:
    for sel in _OVERLAY_SELECTORS:
        try:
            loc = page.locator(sel).first
            if await loc.count() and await loc.is_visible():
                await loc.click(timeout=1000)
                return True
        except Exception:
            continue
    return False
