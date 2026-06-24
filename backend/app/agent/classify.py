"""CLASSIFY: map an action failure to a recovery class from OBSERVABLE browser
state, never the LLM's opinion.

docs/architecture/02 §1.2 (failure-cause classification) gives the four concrete
classes and their per-class recovery; §1.6 insists the signal be grounded in
observable browser state (is_visible/is_enabled, exception type, URL check), not
self-assessment. We branch on Playwright ground truth:

    not-found        selector resolution miss     -> re-ground / heal
    not-interactable exists but is_visible/is_enabled false (occluded/disabled/
                     off-screen)                  -> wait / scroll / dismiss, retry SAME action
    wrong-page       page loaded but URL/state is not the expected one -> replan
    stale / timing   race with async render / stale handle / timeout
                                                   -> state-based wait, retry SAME action
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class FailureClass(str, Enum):
    NONE = "NONE"
    NOT_FOUND = "NOT_FOUND"
    NOT_INTERACTABLE = "NOT_INTERACTABLE"
    WRONG_PAGE = "WRONG_PAGE"
    STALE_TIMING = "STALE_TIMING"
    BLOCKED = "BLOCKED"  # bot-wall / CAPTCHA / consent interstitial -> route unsupported


class Recovery(str, Enum):
    REGROUND = "REGROUND"            # re-perceive, invalidate cache, re-run cascade / heal
    WAIT_SCROLL_DISMISS = "WAIT_SCROLL_DISMISS"  # wait, scroll into view, dismiss overlay; retry same
    STATE_WAIT = "STATE_WAIT"       # wait for stable/attached state; retry same
    REPLAN = "REPLAN"               # global replan
    ASK_USER = "ASK_USER"           # escalation exhausted


_NOT_INTERACTABLE_HINTS = (
    "not interactable",
    "outside of the viewport",
    "intercepts pointer events",
    "element is not visible",
    "element is disabled",
    "is not enabled",
)
_STALE_HINTS = (
    "stale",
    "not attached",
    "element is detached",
    "timeout",
    "timed out",
    "exceeded",
    "waiting for",
)


async def classify_located(locator: Any) -> FailureClass:
    """A locator resolved but the action may still fail. Use is_visible /
    is_enabled (the precondition signals from UFO2, §1.4) as ground truth."""
    try:
        visible = await locator.is_visible()
        enabled = await locator.is_enabled()
    except Exception:
        return FailureClass.STALE_TIMING
    if not visible or not enabled:
        return FailureClass.NOT_INTERACTABLE
    return FailureClass.NONE


def classify_exception(exc: BaseException) -> FailureClass:
    """Branch on the Playwright error text (§1.2 practitioner error classes)."""
    msg = str(exc).lower()
    if any(h in msg for h in _NOT_INTERACTABLE_HINTS):
        return FailureClass.NOT_INTERACTABLE
    if any(h in msg for h in _STALE_HINTS):
        return FailureClass.STALE_TIMING
    return FailureClass.STALE_TIMING


def recovery_for(fc: FailureClass) -> Recovery:
    return {
        FailureClass.NOT_FOUND: Recovery.REGROUND,
        FailureClass.NOT_INTERACTABLE: Recovery.WAIT_SCROLL_DISMISS,
        FailureClass.WRONG_PAGE: Recovery.REPLAN,
        FailureClass.STALE_TIMING: Recovery.STATE_WAIT,
        FailureClass.NONE: Recovery.STATE_WAIT,
        FailureClass.BLOCKED: Recovery.ASK_USER,  # never retry / solve a CAPTCHA
    }[fc]
