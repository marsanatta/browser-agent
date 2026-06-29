"""Filtered perceive/read + deterministic locate cascade for the LLM-in-loop loop.

Ported from browser-pilot pilot/cdp.py. The token thesis lives in `perceive`: it
FILTERS in-browser to the elements whose accessible name relates to the current
target, so a 5,700-link page never becomes an 85k-token dump. Filtering happens in
page.evaluate JS — it never enters an LLM context at all.

Unlike browser-pilot (which connects Playwright over CDP to an actionbook Chrome),
here every helper operates on the `page` that browser-agent's BrowserProvider
supplies (headless PlaywrightProvider). So there is no connect_over_cdp/new_page —
the provider owns the page lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    """A perceived interactive element: ARIA role + accessible name (the stable
    user-facing contract) plus locator-grade attributes for the cascade.

    `aid` + `ctx` are set ONLY by the indexed-observe path (perceive_indexed): `aid` is a
    stable per-observe index injected as `data-aid` so the agent can address ONE of several
    identically-named controls by number; `ctx` is the nearest container text (the row /
    section the control sits in) that disambiguates which same-named element is which."""

    role: str
    name: str
    attrs: dict[str, str] = field(default_factory=dict)
    aid: int | None = None
    ctx: str = ""


# Shared in-browser helpers: the interactive selector + ARIA role + accessible name.
# Factored so the filtered scan (_SCAN_JS) and the indexed observe (_OBSERVE_JS) compute
# role/name IDENTICALLY — they must never drift, or click-by-name and click-by-index would
# disagree about what an element is called.
_RN_HELPERS = r"""
  const SEL = 'a,button,input,textarea,select,[role]';
  const roleOf = (el) => {
    const r = el.getAttribute('role');
    if (r) return r.toLowerCase();
    const t = el.tagName.toLowerCase();
    if (t === 'a' && el.hasAttribute('href')) return 'link';
    if (t === 'button') return 'button';
    if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') {
      const it = (el.getAttribute('type') || 'text').toLowerCase();
      if (it === 'checkbox') return 'checkbox';
      if (it === 'radio') return 'radio';
      if (it === 'search') return 'searchbox';
      if (['submit','button','reset'].includes(it)) return 'button';
      return 'textbox';
    }
    return '';
  };
  const nameOf = (el) => (
    el.getAttribute('aria-label') ||
    (el.id && (document.querySelector('label[for="' + el.id + '"]')||{}).innerText) ||
    el.value || el.innerText || el.getAttribute('title') || el.getAttribute('placeholder') ||
    // Implicit label: <label>Name <input></label>. accname/HTML-AAM derive the name from
    // the WRAPPING <label> too — without this, label-wrapped inputs (no id, no value) get
    // name '' and are skipped, so the agent can't see them. Kept last so value-named
    // radios/checkboxes are unchanged; closest('label') is null for non-wrapped controls.
    (el.closest('label') || {}).innerText || ''
  ).trim();
  const relevantTo = (name, target) => {
    const tgt = (target || '').trim().toLowerCase();
    if (!tgt) return true;                 // no target -> keep all (capped by caller)
    const n = name.toLowerCase();
    if (n.includes(tgt) || tgt.includes(n)) return true;
    return tgt.split(/\s+/).filter(Boolean).some(t => t.length > 2 && n.includes(t));
  };
"""

# One in-browser pass: compute ARIA role + accessible name for every interactive
# node, then FILTER to those whose name overlaps the step target. The filter is the
# 0.07x token lever — it runs in the page, so an enormous link list costs zero tokens.
_SCAN_JS = "(target) => {" + _RN_HELPERS + r"""
  const out = [];
  for (const el of document.querySelectorAll(SEL)) {
    const role = roleOf(el);
    const name = nameOf(el);
    if (!role || !name) continue;
    if (!relevantTo(name, target)) continue;
    out.push({
      role, name,
      id: el.id || '',
      testid: el.getAttribute('data-testid') || '',
      aria_label: el.getAttribute('aria-label') || '',
      href: el.getAttribute('href') || '',
      placeholder: el.getAttribute('placeholder') || '',
      cls: (typeof el.className === 'string' ? el.className : '') || '',
    });
    if (out.length >= 40) break;           // hard cap: never explode the candidate set
  }
  return out;
}"""


# Indexed observe: like _SCAN_JS but (a) does NOT dedup, (b) injects a stable `data-aid`
# index per match so the agent can address ONE of several identically-named controls by
# number, and (c) returns `ctx` = the nearest container text (row/section), which is what
# disambiguates one row's action link from the identical link in another row. ONLY this path
# injects data-aid; the filtered _SCAN_JS (run on every ground) must not, or it would
# clobber the indices between observe and the click that uses them. Stale aids from a prior
# observe are cleared first so an index always refers to the LATEST observe.
_OBSERVE_JS = "(target) => {" + _RN_HELPERS + r"""
  document.querySelectorAll('[data-aid]').forEach(e => e.removeAttribute('data-aid'));
  const ctxOf = (el, name) => {
    const box = el.closest('li,tr,section,article,fieldset,nav,dd,dt');
    let t = box ? (box.innerText || '').trim() : '';
    if (name && t) t = t.split(name).join(' ');   // drop the control's own label
    return t.replace(/\s+/g, ' ').trim().slice(0, 60);
  };
  const out = [];
  let idx = 0;
  for (const el of document.querySelectorAll(SEL)) {
    const role = roleOf(el);
    const name = nameOf(el);
    if (!role || !name) continue;
    if (!relevantTo(name, target)) continue;
    el.setAttribute('data-aid', String(idx));
    out.push({ aid: idx, role, name, ctx: ctxOf(el, name) });
    idx++;
    if (out.length >= 20) break;   // match the observe display cap: every injected index is shown
  }
  return out;
}"""


# Bound the child-frame fan-out: a runaway ad/tracker page can host dozens of
# frames; scanning the first few covers real embeds (TinyMCE, sandboxed widgets)
# without letting one task explode in cost or wall-clock.
_MAX_CHILD_FRAMES = 10


# Rich-text editors (TinyMCE/CKEditor/contenteditable) live in a child frame and are
# INVISIBLE to _SCAN_JS: the editable host is a <body>/<div> with no ARIA role and not
# one of a/button/input/textarea/select. This SEPARATE pass surfaces such hosts as a
# `textbox` candidate so the locate cascade can resolve them. It runs ONLY on the
# child-frame fallback path — never against the main frame — so _SCAN_JS's main-frame
# semantics are untouched. Returns rows in the same shape as _SCAN_JS.
_EDITOR_SCAN_JS = r"""() => {
  const out = [];
  const push = (el) => {
    // Editor aria-labels often carry an instructional tail ("Rich Text Area. Press
    // ALT-0 for help.") that is a keyboard hint, not the editor's identity. Drop it so
    // the reported name is the stable label the agent will fill/observe by — and so it
    // doesn't share tokens with main-frame toolbar items ("Format", "Edit").
    let name = (el.getAttribute('aria-label') || el.getAttribute('title') ||
                el.id || 'editor').trim();
    name = name.replace(/\.\s*Press\s.*$/i, '').trim() || name;
    out.push({
      role: 'textbox', name,
      id: el.id || '',
      testid: el.getAttribute('data-testid') || '',
      aria_label: el.getAttribute('aria-label') || '',
      href: '',
      placeholder: '',
      cls: (typeof el.className === 'string' ? el.className : '') || '',
    });
  };
  for (const el of document.querySelectorAll(
      '[contenteditable=""],[contenteditable="true"],[role="textbox"]')) {
    push(el);
    if (out.length >= 5) return out;
  }
  const b = document.body;
  // designMode='on' OR a rich-text-aria body (TinyMCE toggles editability lazily, so
  // ce/designMode can read off at scan time) is still the agent's intended fill target.
  if (b && (document.designMode === 'on' || b.isContentEditable ||
            /rich text|editor/i.test(b.getAttribute('aria-label') || ''))) {
    push(b);
  }
  return out;
}"""


def _rows_to_elements(rows: list, seen: set[tuple[str, str]], elements: list[Element]) -> None:
    for r in rows:
        key = (r["role"], r["name"])
        if key in seen:
            continue
        seen.add(key)
        attrs = {k: r.get(k, "") for k in ("id", "testid", "aria_label", "href", "cls", "placeholder")}
        elements.append(Element(role=r["role"], name=r["name"], attrs=attrs))


def _child_frames(page: Any) -> list[Any]:
    """Child frames only (page.frames minus the main frame), capped. A detached or
    cross-origin frame must never crash the tool, so every access is guarded."""
    try:
        frames = list(page.frames)
        main = page.main_frame
    except Exception:
        return []
    return [f for f in frames if f is not main][:_MAX_CHILD_FRAMES]


def _is_page(scope: Any) -> bool:
    """A Playwright Page exposes main_frame; a Frame does not. The editor-host scan
    runs ONLY on frames, so it never affects main-frame _SCAN_JS semantics."""
    return hasattr(scope, "main_frame")


async def perceive(page: Any, target: str) -> list[Element]:
    """Filtered perception: only elements whose accessible name relates to `target`.
    Empty target returns a capped all-interactive list (the JS caps at 40).

    Main-frame-first with a child-frame FALLBACK: the main frame is scanned exactly
    as before (byte-identical for main-frame tasks). ONLY when it yields nothing do we
    also scan child frames (page.frames) — so an element inside an iframe (e.g. the
    TinyMCE editor body) becomes perceivable without touching main-frame behaviour.

    When called with a Frame scope (the ground fallback path), the main-frame scan IS
    that frame, and the rich-text editor-host scan is applied so an editable body with
    no ARIA role (TinyMCE) is still surfaced."""
    rows = await page.evaluate(_SCAN_JS, target or "")
    if not _is_page(page):
        # Scope is a child frame: also surface rich-text editor hosts _SCAN_JS misses.
        try:
            rows = list(rows) + await page.evaluate(_EDITOR_SCAN_JS)
        except Exception:
            pass
    seen: set[tuple[str, str]] = set()
    elements: list[Element] = []
    _rows_to_elements(rows, seen, elements)
    if elements or not _is_page(page):
        return elements
    for frame in _child_frames(page):
        try:
            frows = await frame.evaluate(_SCAN_JS, target or "")
            # Rich-text editors aren't caught by _SCAN_JS; surface their editable host.
            frows += await frame.evaluate(_EDITOR_SCAN_JS)
        except Exception:
            continue  # detached / cross-origin / not-yet-loaded frame
        _rows_to_elements(frows, seen, elements)
    return elements


async def perceive_indexed(page: Any, target: str) -> list[Element]:
    """Observe-only perception: assigns a stable `data-aid` index per matched element and a
    disambiguating `ctx` (its row/section text), and does NOT dedup same-name elements — so
    the agent can SEE and address each of several identically-named controls. Main-frame only
    for the indexed path; if the main frame yields nothing (e.g. a rich-text editor lives in a
    child frame) it falls back to the by-name perceive so iframe tasks are unaffected."""
    try:
        rows = await page.evaluate(_OBSERVE_JS, target or "")
    except Exception:
        rows = []
    out = [Element(role=r["role"], name=r["name"], aid=r["aid"], ctx=r["ctx"]) for r in rows]
    if out or not _is_page(page):
        return out
    return await perceive(page, target)


async def resolve_aid(page: Any, aid: int) -> Any | None:
    """Resolve an index from the latest indexed observe to its exact element via the injected
    data-aid — no name re-match, so it cannot pick the wrong same-named element. Returns None
    if the index is stale (the page changed since observe) so the caller can re-observe."""
    loc = page.locator(f'[data-aid="{int(aid)}"]')
    try:
        return loc if await loc.count() == 1 else None
    except Exception:
        return None


# READ: surface page TEXT (not interactive elements). perceive() only returns
# clickable/fillable nodes, so a value like a bare "£51.33" price or body prose is
# invisible to it — read_text fills that gap for retrieval/extract tasks. In-browser
# + capped, so it stays cheap — the token thesis holds.
_READ_JS = r"""(target) => {
  const tgt = (target || '').trim().toLowerCase();
  const toks = tgt.split(/\s+/).filter(t => t.length > 2);
  const out = [];
  const seen = new Set();
  const sel = 'h1,h2,h3,h4,p,td,th,li,dd,dt,span,strong,b,em,caption,label';
  for (const el of document.querySelectorAll(sel)) {
    const txt = (el.innerText || '').trim();
    if (!txt || txt.length > 240 || seen.has(txt)) continue;
    const low = txt.toLowerCase();
    if (!tgt || low.includes(tgt) || toks.some(t => low.includes(t))) {
      seen.add(txt);
      out.push(txt);
    }
    if (out.length >= 30) break;
  }
  const body = (document.body ? document.body.innerText : '').slice(0, 1200);
  return JSON.stringify({ matches: out.slice(0, 30), text_head: body });
}"""


async def read_text(page: Any, target: str) -> str:
    """Query-relevant page text + a capped head of the main text, as a JSON string."""
    try:
        return await page.evaluate(_READ_JS, target or "")
    except Exception:
        return '{"matches": [], "text_head": ""}'


# --- LOCATE: deterministic tier cascade (no LLM). count==1 resolves; ambiguity
#     STOPS rather than silently resolving the first node (the silent wrong-pick).
_TIERS = ("role_name", "role", "id", "placeholder", "testid", "aria_exact", "href", "text")


def _build(page: Any, strategy: str, el: Element) -> Any:
    a = el.attrs
    if strategy == "role_name":
        return page.get_by_role(el.role, name=el.name, exact=True)
    if strategy == "role":
        return page.get_by_role(el.role, name=el.name)
    if strategy == "placeholder":
        return page.get_by_placeholder(a["placeholder"], exact=True) if a.get("placeholder") else None
    if strategy == "id":
        return page.locator(f"#{a['id']}") if a.get("id") else None
    if strategy == "testid":
        return page.get_by_test_id(a["testid"]) if a.get("testid") else None
    if strategy == "aria_exact":
        return page.locator(f'[aria-label="{a["aria_label"]}"]') if a.get("aria_label") else None
    if strategy == "href":
        return page.locator(f'a[href="{a["href"]}"]') if a.get("href") else None
    if strategy == "text":
        return page.get_by_text(el.name, exact=True)
    return None


async def locate(page: Any, el: Element) -> Any | None:
    """First locator that resolves to exactly one element, else None. Tier-1
    role+name tolerates count>1 only by narrowing to a lone visible survivor;
    genuine ambiguity returns None so the caller can escalate (never a silent
    wrong-pick)."""
    for strategy in _TIERS:
        loc = _build(page, strategy, el)
        if loc is None:
            continue
        try:
            n = await loc.count()
        except Exception:
            continue
        if n == 1:
            return loc
        if strategy == "role_name" and n > 1:
            survivor = await _lone_visible(loc)
            if survivor is not None:
                return survivor
            return None  # real ambiguity: stop the cascade, do not fall through
    return None


async def _lone_visible(loc: Any) -> Any | None:
    try:
        cands = await loc.all()
    except Exception:
        return None
    visible = []
    for c in cands:
        try:
            if await c.is_visible() and await c.is_enabled():
                visible.append(c)
        except Exception:
            continue
    if len(visible) == 1:
        return visible[0]
    if len(visible) > 1 and await _same_destination(visible):
        # Not a genuine ambiguity: every match is the SAME link destination, so
        # clicking any one reaches the identical page (Wikipedia routinely links the
        # same article from both the infobox and the body). Picking the first is still
        # no-silent-WRONG-pick — there is no wrong choice among identical destinations.
        return visible[0]
    return None


async def _same_destination(locs: list[Any]) -> bool:
    """True iff every locator is a link to the SAME real href. Excludes non-link
    elements (href None) and '#'/empty placeholders (a bare '#' may bind different JS
    handlers), so only genuine duplicate navigation targets collapse — differing or
    placeholder hrefs stay ambiguous."""
    hrefs = set()
    for c in locs:
        try:
            hrefs.add(await c.get_attribute("href"))
        except Exception:
            return False
    if len(hrefs) != 1:
        return False
    href = next(iter(hrefs))
    return bool(href) and href != "#"


# --- ACT (Playwright on the provider-supplied page) -------------------------
async def navigate(page: Any, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")


async def click(loc: Any) -> None:
    await loc.click(timeout=8000)


async def fill(loc: Any, value: str) -> None:
    # A trailing newline is the agent's "type then submit" convention: many inputs (search
    # boxes, todo/chat fields) commit on Enter and have NO submit button. Strip trailing
    # newline(s), fill, then press Enter so those inputs actually submit.
    submit = value.endswith("\n")
    if submit:
        value = value.rstrip("\n")
    try:
        await loc.fill(value, timeout=8000)
    except Exception as exc:
        # Rich-text editors (TinyMCE/CKEditor) host a contenteditable/designMode region
        # that loc.fill() rejects ("not an <input>/<textarea>/[contenteditable]") and that
        # does not accept synthetic keyboard input headless. Fall back to a direct DOM set
        # on the resolved element. Scoped to that failure: a real input still uses fill().
        if "contenteditable" not in str(exc) and "not an <input>" not in str(exc):
            raise
        await loc.evaluate(_EDITABLE_SET_JS, value)
    if submit:
        try:
            await loc.press("Enter")
        except Exception:
            pass


# Set text into a rich-text editable host and notify the editor (TinyMCE listens on
# input). designMode is forced on first so the host is genuinely editable; a single
# wrapping <p> mirrors how these editors structure content, so the editor's own
# inner_text (what the verifier reads) equals the value exactly.
_EDITABLE_SET_JS = r"""(el, val) => {
  const doc = el.ownerDocument;
  try { doc.designMode = 'on'; } catch (e) {}
  el.focus();
  const p = doc.createElement('p');
  p.textContent = val;
  el.innerHTML = '';
  el.appendChild(p);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}"""


# --- state diff: the silent-failure guard (did the click actually do anything) --
@dataclass(frozen=True)
class Snapshot:
    url: str
    dom_hash: int


async def snapshot(page: Any) -> Snapshot:
    try:
        body = await page.evaluate("() => (document.body ? document.body.innerHTML : '').replace(/ data-aid=\"\\d+\"/g, '')")
    except Exception:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            body = await page.evaluate("() => (document.body ? document.body.innerHTML : '').replace(/ data-aid=\"\\d+\"/g, '')")
        except Exception:
            body = ""
    return Snapshot(url=page.url, dom_hash=hash(body))


def changed(before: Snapshot, after: Snapshot) -> bool:
    """True iff observable browser state moved (URL or DOM). A click the page
    ignored is not success."""
    return before.url != after.url or before.dom_hash != after.dom_hash


async def _ground_in(scope: Any, target: str) -> Any | None:
    """The unchanged perceive+locate resolution against ONE page-like scope (a Page or
    a Frame — both expose get_by_role/locator/get_by_text). Exact-name matches first;
    locate's per-scope no-silent-pick guarantee is preserved untouched."""
    cands = await perceive(scope, target)
    if not cands:
        return None
    t = target.strip().lower()
    cands.sort(key=lambda e: 0 if e.name.strip().lower() == t else 1)
    for el in cands:
        loc = await locate(scope, el)
        if loc is not None:
            return loc
    return None


async def ground(page: Any, target: str) -> Any | None:
    """Map a target string to a single Playwright locator via the SAME filtered
    perceive + deterministic locate. The agent supplies the semantics; cdp supplies
    the precise, no-silent-pick resolution. Exact-name matches are tried first.

    Main-frame-first with a child-frame FALLBACK. The main frame runs exactly as
    before (byte-identical for main-frame tasks). ONLY on a main-frame miss do we run
    the IDENTICAL cascade against each child frame and return the first frame that
    uniquely resolves — a Frame satisfies the locate interface, so the returned locator
    is already frame-bound and click/fill act inside that iframe with no further work."""
    loc = await _ground_in(page, target)
    if loc is not None:
        return loc
    for frame in _child_frames(page):
        try:
            loc = await _ground_in(frame, target)
        except Exception:
            continue  # detached / cross-origin / not-yet-loaded frame
        if loc is not None:
            return loc
    return None
