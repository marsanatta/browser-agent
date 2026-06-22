"""LOCATE: zero-cost deterministic 10-tier locator cascade (no LLM).

Order is verbatim from docs/architecture/02 §2.4 (arXiv:2603.20358) and aligned
with Playwright's own stability ladder (§2.1): ARIA role+name is the most stable
because it is a user-facing contract, CSS/visible-text are last-resort.

    1 role + accessible name      6 aria-label (contains)
    2 role only                   7 href fragment
    3 data-testid                 8 CSS class (exact)
    4 id                          9 CSS class (contains)
    5 aria-label (exact)         10 visible text

A locator "resolves" only when it matches exactly one element (count == 1) — an
ambiguous match is treated as a miss so the cascade keeps narrowing. The first
resolving tier wins and is written to a 2-layer in-memory cache (hit = 0 work).

L2 (LLM re-rank of a shortlist, then vision) is the documented fallback on a full
cascade miss; the seam is `l2_fallback` and is left unwired for M1 (returns None).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.agent.perceive import IndexedElement


@dataclass(frozen=True)
class Located:
    locator: Any
    tier: int
    strategy: str


L2Fallback = Callable[[Any, IndexedElement], Awaitable[Located | None]]


class LocatorCache:
    """2-layer cache seam. M1 ships the in-memory layer; a persistent layer
    (e.g. sqlite) plugs in behind the same get/put without touching callers."""

    def __init__(self) -> None:
        self._mem: dict[tuple[str, str, str], tuple[int, str]] = {}

    def get(self, page_key: str, el: IndexedElement) -> tuple[int, str] | None:
        return self._mem.get((page_key, el.role, el.name))

    def put(self, page_key: str, el: IndexedElement, tier: int, strategy: str) -> None:
        self._mem[(page_key, el.role, el.name)] = (tier, strategy)

    def invalidate(self, page_key: str, el: IndexedElement) -> None:
        self._mem.pop((page_key, el.role, el.name), None)


async def _resolves(locator: Any) -> bool:
    try:
        return await locator.count() == 1
    except Exception:
        return False


def _page_key(page: Any) -> str:
    url = page.url
    return url.split("?", 1)[0].split("#", 1)[0]


async def locate(
    page: Any,
    el: IndexedElement,
    cache: LocatorCache | None = None,
    l2_fallback: L2Fallback | None = None,
) -> Located | None:
    """Return the first resolving locator for `el`, or None on full miss."""
    cache = cache or _DEFAULT_CACHE
    key = _page_key(page)

    cached = cache.get(key, el)
    if cached is not None:
        tier, strategy = cached
        loc = _build(page, strategy, el)
        if loc is not None and await _resolves(loc):
            return Located(loc, tier, strategy)
        cache.invalidate(key, el)

    for tier, strategy in enumerate(_TIERS, start=1):
        loc = _build(page, strategy, el)
        if loc is None:
            continue
        if await _resolves(loc):
            cache.put(key, el, tier, strategy)
            return Located(loc, tier, strategy)

    if l2_fallback is not None:
        try:
            l2_fallback._cache = cache  # let the fallback write its hit back
        except (AttributeError, TypeError):
            pass
        return await l2_fallback(page, el)
    return None


_TIERS = (
    "role_name",
    "role",
    "testid",
    "id",
    "aria_exact",
    "aria_contains",
    "href",
    "css_exact",
    "css_contains",
    "text",
)


def _build(page: Any, strategy: str, el: IndexedElement) -> Any:
    a = el.attrs
    if strategy == "role_name":
        return page.get_by_role(el.role, name=el.name, exact=True)
    if strategy == "role":
        return page.get_by_role(el.role, name=el.name)
    if strategy == "testid":
        return page.get_by_test_id(a["testid"]) if a.get("testid") else None
    if strategy == "id":
        return page.locator(f"#{a['id']}") if a.get("id") else None
    if strategy == "aria_exact":
        return page.locator(f'[aria-label="{a["aria_label"]}"]') if a.get("aria_label") else None
    if strategy == "aria_contains":
        return page.locator(f'[aria-label*="{a["aria_label"]}"]') if a.get("aria_label") else None
    if strategy == "href":
        return page.locator(f'a[href="{a["href"]}"]') if a.get("href") else None
    if strategy == "css_exact":
        cls = _first_class(a.get("cls", ""))
        return page.locator(f"{_tag(el.role)}.{cls}") if cls else None
    if strategy == "css_contains":
        cls = _first_class(a.get("cls", ""))
        return page.locator(f'[class*="{cls}"]') if cls else None
    if strategy == "text":
        return page.get_by_text(el.name, exact=True)
    return None


_L2_PROMPT = """You are a locator expert for a browser-automation agent.
The deterministic selector cascade could not uniquely resolve this target:

    target role: __ROLE__
    target name: __NAME__

Here is a shortlist of candidate elements currently on the page (index: role | name):
__CANDIDATES__

Reply with ONLY the integer index of the single best matching candidate, or -1
if none match. No prose."""


def make_l2_fallback(gateway: Any, candidates: list[IndexedElement]) -> L2Fallback:
    """Wire the documented L2 LLM re-rank (docs/architecture/02 §2.5, Healwright
    pattern): on a FULL deterministic miss, hand the LLM a compact <=5-candidate
    shortlist (minimal JSON, never raw HTML) and let it pick one; we then resolve
    the chosen candidate through the same deterministic cascade and cache it.

    The shortlist is pre-filtered by accessible-name overlap so the LLM only ever
    sees a small, relevant set (cost + accuracy)."""

    async def fallback(page: Any, el: IndexedElement) -> Located | None:
        shortlist = _shortlist(el, candidates, limit=5)
        if not shortlist:
            return None
        prompt = (
            _L2_PROMPT.replace("__ROLE__", el.role)
            .replace("__NAME__", el.name)
            .replace(
                "__CANDIDATES__",
                "\n".join(f"{i}: {c.role} | {c.name}" for i, c in enumerate(shortlist)),
            )
        )
        resp = await gateway.complete(prompt)
        idx = _parse_index(resp.content)
        if idx is None or not (0 <= idx < len(shortlist)):
            return None
        chosen = shortlist[idx]
        for tier, strategy in enumerate(_TIERS, start=1):
            loc = _build(page, strategy, chosen)
            if loc is not None and await _resolves(loc):
                if cache := getattr(fallback, "_cache", None):
                    cache.put(_page_key(page), el, tier, strategy)
                return Located(loc, tier, strategy)
        return None

    return fallback


def _shortlist(
    el: IndexedElement, candidates: list[IndexedElement], limit: int
) -> list[IndexedElement]:
    target = el.name.strip().lower()
    toks = set(target.split())

    def score(c: IndexedElement) -> int:
        name = c.name.strip().lower()
        s = 0
        if c.role == el.role:
            s += 2
        if toks & set(name.split()):
            s += 2
        if target and (target in name or name in target):
            s += 1
        return s

    ranked = sorted(candidates, key=score, reverse=True)
    return [c for c in ranked if score(c) > 0][:limit]


def _parse_index(content: str) -> int | None:
    s = content.strip()
    try:
        return int(s)
    except ValueError:
        pass
    for tok in s.replace(",", " ").split():
        try:
            return int(tok)
        except ValueError:
            continue
    try:
        val = json.loads(s)
        return int(val) if isinstance(val, (int, float, str)) else None
    except (ValueError, TypeError):
        return None


def _first_class(cls: str) -> str:
    parts = cls.split()
    return parts[0] if parts else ""


def _tag(role: str) -> str:
    return {"link": "a", "button": "button", "textbox": "input"}.get(role, "*")


_DEFAULT_CACHE = LocatorCache()
