"""Offline unit tests for the M3 verification layer. No Copilot, no real browser —
a fake page supplies known state so each assertion has independent ground truth.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.verify import consistency_check, key_node_check, state_check


class _FakeLocator:
    def __init__(self, text):
        self._text = text

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self._text is not None else 0

    async def inner_text(self):
        if self._text is None:
            raise RuntimeError("no element")
        return self._text


class _FakePage:
    """Minimal page double: a URL, a body text, and a css->text map."""

    def __init__(self, url, body, selectors=None):
        self.url = url
        self._body = body
        self._sel = selectors or {}

    def locator(self, css):
        return _FakeLocator(self._sel.get(css))

    async def inner_text(self, sel):
        if sel == "body":
            return self._body
        raise RuntimeError("only body supported in fake")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_url_contains_true_and_false():
    page = _FakePage("https://x.com/login?next=1", "hello", {})
    assert await state_check(page, {"url_contains": "/login"}) is True
    assert await state_check(page, {"url_contains": "/LOGIN"}) is True  # case-insensitive
    assert await state_check(page, {"url_contains": "/secure"}) is False


@pytest.mark.anyio
async def test_text_contains_case_insensitive():
    page = _FakePage("https://x.com", "The Login Page", {})
    assert await state_check(page, {"text_contains": "login page"}) is True
    assert await state_check(page, {"text_contains": "logout"}) is False


@pytest.mark.anyio
async def test_h1_equals_exact():
    page = _FakePage("https://x.com", "body", {"h1": "A Light in the Attic"})
    assert await state_check(page, {"h1_equals": "A Light in the Attic"}) is True
    assert await state_check(page, {"h1_equals": "A Light in the ..."}) is False  # exact, not contains


@pytest.mark.anyio
async def test_selector_text_equals():
    page = _FakePage("https://x.com", "body", {"h3.author-title": "Albert Einstein"})
    assert await state_check(page, {"selector_text_equals": {"css": "h3.author-title", "value": "Albert Einstein"}}) is True
    assert await state_check(page, {"selector_text_equals": {"css": "h3.author-title", "value": "Newton"}}) is False


@pytest.mark.anyio
async def test_selector_text_equals_case_insensitive():
    # inner_text() returns CSS-RENDERED text: a title styled `text-transform: uppercase`
    # comes back UPPERCASE though its source is mixed case. The check must still pass
    # (full-string match, case ignored). This was the internet_modal false-fail.
    page = _FakePage("https://x.com", "body", {".modal-title h3": "THIS IS A MODAL WINDOW"})
    assert await state_check(
        page, {"selector_text_equals": {"css": ".modal-title h3", "value": "This is a modal window"}}
    ) is True
    # different LETTERS still fail (case-insensitive, not substring/fuzzy)
    assert await state_check(
        page, {"selector_text_equals": {"css": ".modal-title h3", "value": "A different window"}}
    ) is False


@pytest.mark.anyio
async def test_missing_selector_is_false_not_error():
    page = _FakePage("https://x.com", "body", {})
    assert await state_check(page, {"h1_equals": "anything"}) is False


@pytest.mark.anyio
async def test_key_node_check_uses_same_primitives():
    page = _FakePage("https://x.com/login", "Form Authentication", {})
    assert await key_node_check(page, {"text_contains": "Form Authentication"}) is True
    assert await key_node_check(page, {"url_contains": "/login"}) is True


@pytest.mark.anyio
async def test_unknown_primitive_raises():
    page = _FakePage("https://x.com", "body", {})
    with pytest.raises(ValueError):
        await state_check(page, {"bogus_primitive": "x"})


@pytest.mark.anyio
async def test_consistency_unanimous_agrees():
    answers = iter(["Ulm, Germany", "Ulm, Germany", "Ulm, Germany"])

    async def extract():
        return next(answers)

    r = await consistency_check(extract, n=3)
    assert r.agreed is True
    assert r.agreement == 1.0
    assert r.value == "ulm, germany"


@pytest.mark.anyio
async def test_consistency_disagreement_flagged():
    answers = iter(["Ulm", "Munich", "Ulm"])

    async def extract():
        return next(answers)

    r = await consistency_check(extract, n=3)
    assert r.agreed is False
    assert r.agreement == pytest.approx(2 / 3)
    assert r.value == "ulm"  # majority


@pytest.mark.anyio
async def test_consistency_requires_two_samples():
    async def extract():
        return "x"

    with pytest.raises(ValueError):
        await consistency_check(extract, n=1)
