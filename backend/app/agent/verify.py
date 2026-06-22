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
    as CHANGED; all-unchanged is NO_CHANGE.

    `target_locator` + `target_effect` add a deterministic, element-specific
    channel (docs/architecture/02 §1.4): a fill should leave the field holding
    its value; a click that toggles state should make the target attached/
    detached/visible. This is stronger than a page-wide DOM-length heuristic
    because it survives unrelated DOM churn and catches the case where the page
    mutated elsewhere but the intended element did not change."""

    url_changes: bool = False
    url_contains: str | None = None
    dom_changes: bool = True
    target_locator: Any = None
    target_effect: str | None = None  # "value" | "detached" | "visible_enabled"
    target_value: str | None = None


@dataclass(frozen=True)
class StateSnapshot:
    url: str
    dom_len: int
    dom_hash: int


async def snapshot(page: Any) -> StateSnapshot:
    body = await page.evaluate(
        "() => document.body ? document.body.innerHTML : ''"
    )
    return StateSnapshot(url=page.url, dom_len=len(body), dom_hash=hash(body))


async def _target_satisfied(expect: Expectation) -> bool:
    loc = expect.target_locator
    if loc is None or expect.target_effect is None:
        return False
    try:
        if expect.target_effect == "value":
            return (await loc.input_value()) == (expect.target_value or "")
        if expect.target_effect == "detached":
            return await loc.count() == 0
        if expect.target_effect == "visible_enabled":
            return await loc.is_visible() and await loc.is_enabled()
    except Exception:
        return False
    return False


async def verify_after_act(
    page: Any, before: StateSnapshot, expect: Expectation
) -> VerifyResult:
    after = await snapshot(page)

    if expect.url_contains is not None:
        return VerifyResult.CHANGED if expect.url_contains in after.url else VerifyResult.NO_CHANGE

    if await _target_satisfied(expect):
        return VerifyResult.CHANGED

    if expect.url_changes and after.url != before.url:
        return VerifyResult.CHANGED

    # DOM-mutation: length OR content hash change. Hash catches same-length
    # mutations (e.g. a class/attribute flip) the coarse length diff missed.
    if expect.dom_changes and (
        after.dom_len != before.dom_len or after.dom_hash != before.dom_hash
    ):
        return VerifyResult.CHANGED

    if not expect.url_changes and not expect.dom_changes and expect.target_effect is None:
        # Nothing was predicted to change; treat a stable page as success.
        return VerifyResult.CHANGED

    return VerifyResult.NO_CHANGE
