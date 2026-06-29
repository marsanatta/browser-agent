"""Programmatic state assertions on the live page — independent ground truth.

These functions inspect the actual DOM/URL of the page the agent left behind,
NOT the agent's claimed output (eval/01 §4: "an agent cannot pass by lying").
Each assertion is a one-key dict from the eval-set data; this maps it to a real
check against `page`. Returns a plain bool so the harness can record verified
completion deterministically.

Supported primitives (must match eval/eval_set/tasks.yaml):
  url_contains: <substr>
  text_contains: <substr>              (case-insensitive over body innerText)
  h1_equals: <str>
  selector_text_equals: {css, value}
  iframe_text_equals: {frame, css, value}
  input_value_equals: {css, value}     (form-control .value — mutated input state)
  element_count: {css, count|min|max}  (locator match count; count==0 asserts absence)
"""

from __future__ import annotations

from typing import Any


async def _body_text(page: Any) -> str:
    try:
        return await page.inner_text("body")
    except Exception:
        try:
            return await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            return ""


async def _first_text(page: Any, css: str) -> str | None:
    loc = page.locator(css).first
    try:
        if await loc.count() == 0:
            return None
        return (await loc.inner_text()).strip()
    except Exception:
        return None


async def _first_value(page: Any, css: str) -> str | None:
    loc = page.locator(css).first
    try:
        if await loc.count() == 0:
            return None
        return (await loc.input_value()).strip()
    except Exception:
        return None


async def _count(page: Any, css: str) -> int:
    try:
        return await page.locator(css).count()
    except Exception:
        return 0


def _eq_text(got: str | None, value: Any) -> bool:
    """Full-string equality, case-insensitive. `inner_text()` returns the RENDERED text,
    which reflects CSS `text-transform` (e.g. the-internet `entry_ad` modal's <h3>
    renders UPPERCASE while its source is mixed case), so a case-SENSITIVE match
    false-fails a correct read. Case-folding keeps this an EXACT match (not a
    substring) — it only ignores letter casing."""
    return got is not None and got.casefold() == str(value).casefold()


async def _check_one(page: Any, kind: str, spec: Any) -> bool:
    if kind == "url_contains":
        return str(spec).lower() in page.url.lower()
    if kind == "text_contains":
        return str(spec).lower() in (await _body_text(page)).lower()
    if kind == "h1_equals":
        return _eq_text(await _first_text(page, "h1"), spec)
    if kind == "selector_text_equals":
        return _eq_text(await _first_text(page, spec["css"]), spec["value"])
    if kind == "iframe_text_equals":
        # Frame-aware check: pierce a real iframe and assert on an element inside it.
        try:
            loc = page.frame_locator(spec["frame"]).locator(spec["css"]).first
            if await loc.count() == 0:
                return False
            return _eq_text((await loc.inner_text()).strip(), spec["value"])
        except Exception:
            return False
    if kind == "input_value_equals":
        return _eq_text(await _first_value(page, spec["css"]), spec["value"])
    if kind == "element_count":
        # count==0 asserts ABSENCE — but a typo'd css ALSO matches 0 elements, so a
        # bad selector silently passes. Never use count==0 as the sole assert: pair it
        # with a positive signal (text_contains / selector_text_equals) that proves
        # both the right page and the mutation. AND-ed keys in state_check enforce this.
        n = await _count(page, spec["css"])
        if "count" in spec:
            return n == int(spec["count"])
        if "min" in spec:
            return n >= int(spec["min"])
        if "max" in spec:
            return n <= int(spec["max"])
        raise ValueError("element_count requires one of: count, min, max")
    raise ValueError(f"unknown assertion primitive: {kind!r}")


async def state_check(page: Any, assertion: dict[str, Any]) -> bool:
    """Evaluate a one-key assertion dict against the live page. Multiple keys are
    ANDed (all must hold), though the eval set uses one key per assertion."""
    if not assertion:
        return False
    for kind, spec in assertion.items():
        if not await _check_one(page, kind, spec):
            return False
    return True


async def key_node_check(page: Any, node: dict[str, Any]) -> bool:
    """A key-node checkpoint uses the same primitives as a final assertion
    (WebCanvas key nodes are observable intermediate states, architecture/03 §3.1)."""
    return await state_check(page, node)
