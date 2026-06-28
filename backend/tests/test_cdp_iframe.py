"""Offline tests for the iframe fallback in agentic/cdp.py (no browser, no network).

Proves the HARD constraint: child-frame search is FALLBACK ONLY. A main-frame hit
must short-circuit before any frame is touched (byte-identical main-frame behaviour);
only a main-frame miss descends into child frames. Also proves the rich-text editor
host (which _SCAN_JS misses) is surfaced from a child frame and that fill() falls back
to a DOM set when the contenteditable host rejects loc.fill().
"""

from __future__ import annotations

import pytest

from app.agent.agentic import cdp


class _FakeLocator:
    """count()==1 resolves; fill() raises the contenteditable error so cdp.fill's
    JS-set fallback is exercised; evaluate() records the fallback ran."""

    def __init__(self, n: int = 1, fill_raises: bool = False) -> None:
        self._n = n
        self._fill_raises = fill_raises
        self.dom_set = None

    async def count(self) -> int:
        return self._n

    async def fill(self, value, timeout=None):
        if self._fill_raises:
            raise RuntimeError(
                "Locator.fill: Error: Element is not an <input>, <textarea> or "
                "[contenteditable] element"
            )

    async def evaluate(self, _js, value):
        self.dom_set = value  # the _EDITABLE_SET_JS fallback path


class _Scope:
    """A page-like or frame-like scope. `rows` is what _SCAN_JS returns; `editor_rows`
    is what _EDITOR_SCAN_JS returns. A locator factory maps the resolved id to a
    _FakeLocator so the locate cascade's id tier resolves count==1."""

    def __init__(self, rows, editor_rows=None, loc_for_id=None) -> None:
        self._rows = rows
        self._editor_rows = editor_rows or []
        self._loc_for_id = loc_for_id or {}
        self.scan_calls = 0
        self.editor_calls = 0

    async def evaluate(self, js, *args):
        if js is cdp._SCAN_JS:
            self.scan_calls += 1
            return list(self._rows)
        if js is cdp._EDITOR_SCAN_JS:
            self.editor_calls += 1
            return list(self._editor_rows)
        return None

    # locate cascade surface — only the id tier is needed for these tests.
    def locator(self, sel):
        if sel.startswith("#"):
            return self._loc_for_id.get(sel[1:], _FakeLocator(n=0))
        return _FakeLocator(n=0)

    def get_by_role(self, role, name=None, exact=False):
        return _FakeLocator(n=0)

    def get_by_text(self, text, exact=False):
        return _FakeLocator(n=0)

    def get_by_test_id(self, tid):
        return _FakeLocator(n=0)


class _FakePage(_Scope):
    """A Page is a Scope that also exposes main_frame + frames (the child-frame loop)."""

    def __init__(self, rows, child_frames=None, **kw) -> None:
        super().__init__(rows, **kw)
        self.main_frame = object()
        self._children = child_frames or []

    @property
    def frames(self):
        return [self.main_frame, *self._children]


_EDITOR_ROW = {
    "role": "textbox", "name": "Rich Text Area", "id": "tinymce",
    "testid": "", "aria_label": "Rich Text Area", "href": "", "cls": "",
}
_LINK_ROW = {
    "role": "link", "name": "Helium", "id": "", "testid": "",
    "aria_label": "", "href": "/wiki/Helium", "cls": "",
}


@pytest.mark.anyio
async def test_main_frame_hit_never_touches_child_frames(anyio_backend):
    """Zero-regression: when the main frame yields a match, no child frame is scanned."""
    child = _Scope([], editor_rows=[_EDITOR_ROW])
    page = _FakePage([_LINK_ROW], child_frames=[child])

    els = await cdp.perceive(page, "Helium")

    assert [(e.role, e.name) for e in els] == [("link", "Helium")]
    assert child.scan_calls == 0  # the child frame was never touched
    assert child.editor_calls == 0


@pytest.mark.anyio
async def test_perceive_falls_back_to_child_editor_host(anyio_backend):
    """Main frame empty -> child-frame fallback surfaces the rich-text editor host
    that _SCAN_JS misses (no role / not an input tag)."""
    child = _Scope([], editor_rows=[_EDITOR_ROW])
    page = _FakePage([], child_frames=[child])

    els = await cdp.perceive(page, "rich-text editor")

    assert [(e.role, e.name, e.attrs["id"]) for e in els] == [
        ("textbox", "Rich Text Area", "tinymce")
    ]
    assert child.editor_calls == 1


@pytest.mark.anyio
async def test_ground_resolves_editor_in_child_frame(anyio_backend):
    """ground falls through to the child frame and the id-tier locate resolves the
    editor uniquely (count==1) — the locator is the child frame's, so fill acts inside."""
    editor_loc = _FakeLocator(n=1)
    child = _Scope([], editor_rows=[_EDITOR_ROW], loc_for_id={"tinymce": editor_loc})
    page = _FakePage([], child_frames=[child])

    loc = await cdp.ground(page, "rich-text editor")

    assert loc is editor_loc


@pytest.mark.anyio
async def test_fill_falls_back_to_dom_set_on_contenteditable(anyio_backend):
    """A contenteditable host rejects loc.fill(); cdp.fill must DOM-set instead."""
    loc = _FakeLocator(n=1, fill_raises=True)
    await cdp.fill(loc, "browser agent was here")
    assert loc.dom_set == "browser agent was here"


@pytest.mark.anyio
async def test_fill_reraises_non_contenteditable_errors(anyio_backend):
    """The fallback is scoped: an unrelated fill failure (e.g. timeout) must propagate,
    not be swallowed by the DOM-set path."""
    class _TimeoutLoc(_FakeLocator):
        async def fill(self, value, timeout=None):
            raise RuntimeError("Locator.fill: Timeout 8000ms exceeded")

    loc = _TimeoutLoc()
    with pytest.raises(RuntimeError, match="Timeout"):
        await cdp.fill(loc, "x")
    assert loc.dom_set is None
