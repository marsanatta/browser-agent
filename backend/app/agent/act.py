"""ACT: execute a browser action via a Playwright page.

docs/architecture/02 §1.3: distinguish read actions (safe to auto-run) from
write/submit actions (require confirmation). `requires_confirmation` is the
confirm-before-submit seam; M1 has no human-in-the-loop yet, so an autopilot
default approves it, but the classification is real for M2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ActionKind = Literal["navigate", "click", "fill", "press"]
# Submit-class actions: a press (Enter submits a form) and a click (submit button).
# A fill is benign keystroke entry — it does not commit, so it is NOT gated.
_WRITE_ACTIONS: frozenset[str] = frozenset({"press", "click"})


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    target_url: str | None = None
    value: str | None = None


def requires_confirmation(action: Action) -> bool:
    return action.kind in _WRITE_ACTIONS


async def navigate(page: Any, url: str) -> Any:
    """Navigate and return the main-frame Response (None for data:/about: URLs,
    which produce no HTTP response). The caller inspects `response.status` to
    catch an error page (>=400) instead of treating every goto as success."""
    return await page.goto(url, wait_until="domcontentloaded")


async def click(locator: Any) -> None:
    await locator.click()


async def fill(locator: Any, value: str) -> None:
    await locator.fill(value)


async def press(locator: Any, key: str) -> None:
    """Press a key on the focused element (e.g. Enter on a search box to submit).
    Fills the gap where a button click can't trigger a form's submit."""
    await locator.press(key)
