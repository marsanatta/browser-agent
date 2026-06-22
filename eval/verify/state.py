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


async def _check_one(page: Any, kind: str, spec: Any) -> bool:
    if kind == "url_contains":
        return str(spec) in page.url
    if kind == "text_contains":
        return str(spec).lower() in (await _body_text(page)).lower()
    if kind == "h1_equals":
        return (await _first_text(page, "h1")) == str(spec)
    if kind == "selector_text_equals":
        css = spec["css"]
        value = spec["value"]
        return (await _first_text(page, css)) == value
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
