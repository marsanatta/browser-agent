"""VERIFY-AFTER-ACT: predict expected effect -> act -> diff actual vs predicted.

docs/architecture/02 §1.4/§1.6: the correction signal must be grounded in
OBSERVABLE BROWSER STATE (URL change, DOM change), never the LLM's self-report.
We snapshot a cheap state fingerprint before the action, predict what should
change, then diff. NO_CHANGE is the re-ground trigger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    # predict-then-verify: a goal-grounded post-state the planner declared for this
    # step (e.g. {"text_visible": "..."}). When set it GATES success — a DOM change
    # that does not meet the goal (e.g. dismissing a modal) is NO_CHANGE, not success.
    # This closes the silent-failure hole where "the page moved" was read as "done".
    # hash=False keeps this frozen dataclass hashable despite the dict field.
    goal: dict | None = field(default=None, hash=False)


@dataclass(frozen=True)
class StateSnapshot:
    url: str
    dom_len: int
    dom_hash: int


async def snapshot(page: Any) -> StateSnapshot:
    body = ""
    try:
        body = await page.evaluate("() => document.body ? document.body.innerHTML : ''")
    except Exception:
        # A navigating action (e.g. Enter-to-submit) can destroy the execution
        # context mid-flight ("Execution context was destroyed"). Let it settle and
        # retry once; if it still fails, fall back to a URL-only snapshot — the
        # url-change channel still detects the navigation as CHANGED.
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            body = await page.evaluate("() => document.body ? document.body.innerHTML : ''")
        except Exception:
            body = ""
    return StateSnapshot(url=page.url, dom_len=len(body), dom_hash=hash(body))


# Bot-wall / interstitial detection. Project policy is ROUTE, DON'T EVADE: when a
# post-action page is one of these, the agent abstains and routes it as
# blocked-unsupported — it never tries to solve the challenge. Markers are kept
# high-confidence so legitimate pages are not falsely blocked.
_BLOCK_URL_MARKERS = (
    "/sorry/",                      # google "unusual traffic" interstitial
    "challenges.cloudflare.com",    # cloudflare turnstile / managed challenge
    "/recaptcha/api2",
    "hcaptcha.com/captcha",
    "px-captcha",                   # perimeterx
    "/_incapsula_",                 # imperva/incapsula
)
_BLOCK_SELECTORS = (
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    'iframe[title*="recaptcha" i]',
    'iframe[title*="challenge" i]',
    'div.g-recaptcha',
    'div.h-captcha',
    '#challenge-running',           # cloudflare
    '#cf-challenge-running',
)
_BLOCK_TEXT_MARKERS = (
    "unusual traffic from your computer",
    "verify you are a human",
    "verify you are human",
    "are you a robot",
    "i'm not a robot",
    "complete the security check",
    "checking if the site connection is secure",  # cloudflare
    "enable javascript and cookies to continue",   # cloudflare
)


async def detect_block(page: Any) -> str | None:
    """Return a short reason if the page is a known bot-wall / CAPTCHA / challenge
    interstitial, else None. Used by the verify-after-act path so the agent does
    NOT claim success on a block; it abstains and routes blocked-unsupported. We
    never try to solve the challenge (route, don't evade)."""
    try:
        url = (page.url or "").lower()
    except Exception:
        url = ""
    for marker in _BLOCK_URL_MARKERS:
        if marker in url:
            return f"url:{marker}"
    for sel in _BLOCK_SELECTORS:
        try:
            if await page.locator(sel).count() > 0:
                return f"widget:{sel}"
        except Exception:
            continue
    try:
        text = (await page.inner_text("body"))[:6000].lower()
    except Exception:
        text = ""
    for marker in _BLOCK_TEXT_MARKERS:
        if marker in text:
            return f"text:{marker}"
    return None


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


async def _one_primitive(page: Any, kind: str, value: Any) -> bool:
    try:
        if kind == "url_contains":
            return str(value) in (page.url or "")
        if kind == "selector_visible":
            loc = page.locator(str(value)).first
            return await loc.count() > 0 and await loc.is_visible()
        if kind == "text_visible":
            # Only VISIBLE body text — a removed/hidden modal's title is not in it.
            # Case-insensitive substring so CSS text-transform (uppercase) still matches.
            body = (await page.inner_text("body")).lower()
            return str(value).lower() in body
    except Exception:
        return False
    return False  # unknown primitive -> fail-closed


async def _goal_satisfied(page: Any, goal: dict) -> bool:
    """Independent, goal-grounded post-state check for predict-then-verify. Small
    deterministic primitives (text_visible / selector_visible / url_contains) read
    from OBSERVABLE browser state. ALL keys must hold (AND), so a multi-key goal is
    not silently reduced to its first entry. DELIBERATELY separate code from the eval
    `state_check` so the agent's in-loop signal stays independent of the eval
    arbiter (engineering-rigor: never validate with the verifier's own formula)."""
    if not isinstance(goal, dict) or not goal:
        return False
    for kind, value in goal.items():
        if not await _one_primitive(page, kind, value):
            return False
    return True


async def verify_after_act(
    page: Any, before: StateSnapshot, expect: Expectation
) -> VerifyResult:
    after = await snapshot(page)

    # predict-then-verify GATE: a declared goal takes precedence over the generic
    # url/dom-change channels. The step is CHANGED only if the goal actually holds;
    # a page that moved but did not reach the goal is NO_CHANGE (the re-ground signal).
    # An empty/malformed goal ({} or non-dict) is treated as no goal (falls through).
    if expect.goal:
        return (
            VerifyResult.CHANGED
            if await _goal_satisfied(page, expect.goal)
            else VerifyResult.NO_CHANGE
        )

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
