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
ambiguous match is treated as a miss so the cascade keeps narrowing. The one
exception is tier 1 (role+name): when it matches several LIVE elements we narrow
by interactability (visible + enabled + in-viewport); a lone survivor wins, but
genuine ambiguity stops the cascade — we do NOT fall through to the attribute
tiers, which would silently resolve the perceive-merged first node's href/id —
and defer to L2. The first resolving tier wins and is written to a 2-layer
in-memory cache (hit = 0 work).

L2 on a full cascade miss is the LLM re-rank of a <=5-candidate shortlist — that is
what `make_l2_fallback` implements and is wired in prod (main.py) and the eval
harness. The heuristic fingerprint pre-rank and the vision tier are documented
seams (not built); only the LLM re-rank runs.
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
    via: str = "cascade"  # observe-only grounding outcome: "cascade" | "l2"


L2Fallback = Callable[[Any, IndexedElement], Awaitable[Located | None]]


class LocatorCache:
    """2-layer cache seam. M1 ships the in-memory layer; a persistent layer
    (e.g. sqlite) plugs in behind the same get/put without touching callers.

    A hit is normally rebuilt from the lookup key's own element. The L2 case is
    different: the lookup key is the pseudo-target (whose name is unresolvable),
    so we ALSO record the LLM-chosen real `build_el` and rebuild the locator from
    THAT — otherwise every re-lookup misses and re-fires the (token-costing) L2."""

    def __init__(self) -> None:
        self._mem: dict[tuple[str, str, str], tuple[int, str]] = {}
        self._build_el: dict[tuple[str, str, str], IndexedElement] = {}

    def get(self, page_key: str, el: IndexedElement) -> tuple[int, str] | None:
        return self._mem.get((page_key, el.role, el.name))

    def build_el_for(self, page_key: str, el: IndexedElement) -> IndexedElement | None:
        return self._build_el.get((page_key, el.role, el.name))

    def put(
        self,
        page_key: str,
        el: IndexedElement,
        tier: int,
        strategy: str,
        build_el: IndexedElement | None = None,
    ) -> None:
        k = (page_key, el.role, el.name)
        self._mem[k] = (tier, strategy)
        if build_el is not None and build_el is not el:
            self._build_el[k] = build_el
        else:
            self._build_el.pop(k, None)

    def invalidate(self, page_key: str, el: IndexedElement) -> None:
        k = (page_key, el.role, el.name)
        self._mem.pop(k, None)
        self._build_el.pop(k, None)


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
        build_el = cache.build_el_for(key, el)
        loc = _build(page, strategy, build_el or el)
        if loc is not None and await _resolves(loc):
            return Located(loc, tier, strategy, via="l2" if build_el is not None else "cascade")
        cache.invalidate(key, el)

    located = await _cascade(page, el, cache, key, el)
    if located is not None:
        return located

    if l2_fallback is not None:
        try:
            l2_fallback._cache = cache  # let the fallback write its hit back
        except (AttributeError, TypeError):
            pass
        return await l2_fallback(page, el)
    return None


async def _cascade(
    page: Any, build_el: IndexedElement, cache: LocatorCache, key: str, store_el: IndexedElement
) -> Located | None:
    """Run the deterministic tiers for `build_el`, caching a hit under `store_el`.

    Tier 1 (role+name) is the identity tier and the only place we tolerate an
    initial count > 1: we narrow by interactability and take a lone survivor, but
    on genuine ambiguity we STOP (return None) rather than fall through to the
    attribute tiers — those would resolve the perceive-merged element's first-node
    href/id and silently pick the wrong one. The narrowed survivor is position-
    dependent (not reproducible via `_build`) so it is deliberately not cached.

    A pseudo-target (index == -1: ambiguity / synonym placeholder, empty attrs) is
    restricted to tier-1 EXACT role+name. Its name is the planner's word, which may
    be a substring of an unrelated element's name (e.g. "Sign In" in "Member Sign In
    Now"); letting the fuzzy tier-2 role substring (or attribute/text tiers) resolve
    it would be a SILENT wrong pick. On a tier-1 miss we abstain and route to L2."""
    tiers = _TIERS[:1] if build_el.index == -1 else _TIERS
    for tier, strategy in enumerate(tiers, start=1):
        loc = _build(page, strategy, build_el)
        if loc is None:
            continue
        if strategy == "role_name":
            try:
                n = await loc.count()
            except Exception:
                n = 0
            if n == 1:
                cache.put(key, store_el, tier, strategy, build_el=build_el)
                return Located(loc, tier, strategy)
            if n > 1:
                live = await _interactable(page, loc)
                if len(live) == 1:
                    return Located(live[0], tier, strategy)
                return None
            continue
        if await _resolves(loc):
            cache.put(key, store_el, tier, strategy)
            return Located(loc, tier, strategy)
    return None


async def _interactable(page: Any, loc: Any) -> list[Any]:
    """The live matches of `loc` that are visible, enabled, and within the
    viewport — the narrowing applied when role+name is ambiguous (count > 1)."""
    try:
        viewport = page.viewport_size
    except Exception:
        viewport = None
    try:
        candidates = await loc.all()
    except Exception:
        return []
    out: list[Any] = []
    for cand in candidates:
        try:
            if not (await cand.is_visible() and await cand.is_enabled()):
                continue
            if viewport is not None:
                box = await cand.bounding_box()
                if box is None:
                    continue
                if box["y"] + box["height"] <= 0 or box["y"] >= viewport["height"]:
                    continue
                if box["x"] + box["width"] <= 0 or box["x"] >= viewport["width"]:
                    continue
            out.append(cand)
        except Exception:
            continue
    return out


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
        cache = getattr(fallback, "_cache", None) or _DEFAULT_CACHE
        # Resolve the LLM's pick through the SAME tier-1 ambiguity handling as the
        # main cascade: if the chosen element is itself ambiguous on the page (e.g.
        # perceive-merged duplicates), this returns None and we abstain instead of
        # silently resolving the first node's attributes.
        resolved = await _cascade(page, chosen, cache, _page_key(page), el)
        if resolved is None:
            return None
        # Tag the grounding outcome as L2 (observe-only) for the audit trace.
        return Located(resolved.locator, resolved.tier, resolved.strategy, via="l2")

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
