"""Offline tests for the locate cascade's same-destination disambiguation
(agentic/cdp.py). When role+name matches several VISIBLE elements that all point to
the SAME href they are not a genuine ambiguity — clicking any one reaches the identical
page (Wikipedia links the same article from both the infobox and the body), so locate
picks the first. Differing or placeholder hrefs stay ambiguous (no silent wrong pick)."""

from __future__ import annotations

import pytest

from app.agent.agentic import cdp


class _El:
    def __init__(self, href, *, visible=True, enabled=True) -> None:
        self._href = href
        self._visible = visible
        self._enabled = enabled

    async def is_visible(self) -> bool:
        return self._visible

    async def is_enabled(self) -> bool:
        return self._enabled

    async def get_attribute(self, name: str):
        return self._href if name == "href" else None


class _Loc:
    def __init__(self, els) -> None:
        self._els = els

    async def all(self):
        return list(self._els)


@pytest.mark.anyio
async def test_single_visible_returns_it(anyio_backend):
    els = [_El("/a")]
    assert await cdp._lone_visible(_Loc(els)) is els[0]


@pytest.mark.anyio
async def test_same_href_duplicates_collapse_to_first(anyio_backend):
    els = [_El("/wiki/Periodic_table"), _El("/wiki/Periodic_table")]
    assert await cdp._lone_visible(_Loc(els)) is els[0]


@pytest.mark.anyio
async def test_differing_href_stays_ambiguous(anyio_backend):
    assert await cdp._lone_visible(_Loc([_El("/a"), _El("/b")])) is None


@pytest.mark.anyio
async def test_placeholder_hash_stays_ambiguous(anyio_backend):
    assert await cdp._lone_visible(_Loc([_El("#"), _El("#")])) is None


@pytest.mark.anyio
async def test_no_href_buttons_stay_ambiguous(anyio_backend):
    assert await cdp._lone_visible(_Loc([_El(None), _El(None)])) is None


@pytest.mark.anyio
async def test_invisible_duplicate_reduces_to_single(anyio_backend):
    els = [_El("/a", visible=False), _El("/a")]
    assert await cdp._lone_visible(_Loc(els)) is els[1]
