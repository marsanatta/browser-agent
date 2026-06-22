"""VERIFY-AFTER-ACT: predict expected effect -> act -> diff actual vs predicted.

docs/architecture/02 §1.4/§1.6: the correction signal must be grounded in
OBSERVABLE BROWSER STATE (URL change, DOM change), never the LLM's self-report.
We snapshot a cheap state fingerprint before the action, predict what should
change, then diff. NO_CHANGE is the re-ground trigger.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class VerifyResult(str, Enum):
    CHANGED = "CHANGED"
    NO_CHANGE = "NO_CHANGE"


@dataclass(frozen=True)
class Expectation:
    """What the agent predicts the action will do. Any satisfied channel counts
    as CHANGED; all-unchanged is NO_CHANGE."""

    url_changes: bool = False
    url_contains: str | None = None
    dom_changes: bool = True


@dataclass(frozen=True)
class StateSnapshot:
    url: str
    dom_len: int


async def snapshot(page: Any) -> StateSnapshot:
    dom_len = await page.evaluate("() => document.body ? document.body.innerHTML.length : 0")
    return StateSnapshot(url=page.url, dom_len=int(dom_len))


async def verify_after_act(
    page: Any, before: StateSnapshot, expect: Expectation
) -> VerifyResult:
    after = await snapshot(page)

    if expect.url_contains is not None:
        return VerifyResult.CHANGED if expect.url_contains in after.url else VerifyResult.NO_CHANGE

    if expect.url_changes and after.url != before.url:
        return VerifyResult.CHANGED

    if expect.dom_changes and after.dom_len != before.dom_len:
        return VerifyResult.CHANGED

    if not expect.url_changes and not expect.dom_changes:
        # Nothing was predicted to change; treat a stable page as success.
        return VerifyResult.CHANGED

    return VerifyResult.NO_CHANGE
