"""ACT: execute a browser action via a Playwright page.

docs/architecture/02 §1.3: distinguish read actions (safe to auto-run) from
write/submit actions (require confirmation). `requires_confirmation` is the
confirm-before-submit seam; M1 has no human-in-the-loop yet, so an autopilot
default approves it, but the classification is real for M2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ActionKind = Literal["navigate", "click", "fill", "submit"]
_WRITE_ACTIONS: frozenset[str] = frozenset({"fill", "submit"})


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    target_url: str | None = None
    value: str | None = None


def requires_confirmation(action: Action) -> bool:
    return action.kind in _WRITE_ACTIONS


async def navigate(page: Any, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")


async def click(locator: Any) -> None:
    await locator.click()


async def fill(locator: Any, value: str) -> None:
    await locator.fill(value)
