"""PERCEIVE: fused accessibility-tree + DOM -> indexed interactive elements.

Grounded in docs/architecture/02 §2.1 (ARIA role+name is the stable user-facing
contract) and §1.4 / AgentOccam (observe-first: merge co-labeled elements, render
tables/lists as Markdown, keep only interactive/pivotal nodes). We never dump raw
DOM (token blowup); the accessibility snapshot is the spine, the DOM supplies
locator-grade attributes (id / data-testid / aria-label / href / class).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_INTERACTIVE_ROLES = {
    "button",
    "link",
    "textbox",
    "searchbox",
    "checkbox",
    "radio",
    "combobox",
    "menuitem",
    "tab",
    "switch",
    "slider",
    "option",
    "spinbutton",
}


@dataclass
class IndexedElement:
    index: int
    role: str
    name: str
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class Perception:
    url: str
    elements: list[IndexedElement]
    markdown: str


async def perceive(page: Any) -> Perception:
    rows = await _scan_interactive(page)
    raw = [(r["role"], r["name"]) for r in rows if r["role"] in _INTERACTIVE_ROLES and r["name"]]
    merged = _merge_co_labeled(raw)
    attrs_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for r in rows:
        key = (r["role"], r["name"])
        attrs_by_key.setdefault(key, {
            "id": r["id"],
            "testid": r["testid"],
            "aria_label": r["ariaLabel"],
            "href": r["href"],
            "cls": r["cls"],
        })
    elements = [
        IndexedElement(i, role, name, attrs_by_key.get((role, name), {}))
        for i, (role, name) in enumerate(merged)
    ]
    markdown = await _tables_lists_markdown(page)
    return Perception(url=page.url, elements=elements, markdown=markdown)


def _merge_co_labeled(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Observe-first: collapse duplicate (role, name) pairs to one pivotal node."""
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str]] = []
    for role, name in items:
        if (role, name) in seen:
            continue
        seen.add((role, name))
        merged.append((role, name))
    return merged


async def _scan_interactive(page: Any) -> list[dict[str, str]]:
    """One pass over interactive DOM nodes computing ARIA role + accessible name
    (the user-facing contract per docs/architecture/02 §2.1) plus locator-grade
    attributes, so PERCEIVE and LOCATE share vocabulary. Replaces the removed
    Playwright `page.accessibility` API with an equivalent DOM-computed scan."""
    return await page.evaluate(
        """() => {
            const sel = 'a,button,input,textarea,select,[role]';
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
                (el.id && document.querySelector(`label[for="${el.id}"]`)?.innerText) ||
                el.value || el.innerText || el.getAttribute('title') || ''
            ).trim();
            const out = [];
            for (const el of document.querySelectorAll(sel)) {
                const role = roleOf(el);
                const name = nameOf(el);
                if (!role || !name) continue;
                out.push({
                    role, name,
                    id: el.id || '',
                    testid: el.getAttribute('data-testid') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    href: el.getAttribute('href') || '',
                    cls: (typeof el.className === 'string' ? el.className : '') || '',
                });
            }
            return out;
        }"""
    )


async def _tables_lists_markdown(page: Any) -> str:
    """Render tables/lists as Markdown (AgentOccam observe-first), capped to keep
    the observation compact. Returns '' when the page has none."""
    return await page.evaluate(
        """() => {
            const parts = [];
            for (const t of Array.from(document.querySelectorAll('table')).slice(0, 3)) {
                const rows = Array.from(t.querySelectorAll('tr')).slice(0, 30);
                for (const tr of rows) {
                    const cells = Array.from(tr.querySelectorAll('th,td'))
                        .map(c => c.innerText.trim().replace(/\\|/g, ' '));
                    if (cells.length) parts.push('| ' + cells.join(' | ') + ' |');
                }
                parts.push('');
            }
            return parts.join('\\n').trim();
        }"""
    )
