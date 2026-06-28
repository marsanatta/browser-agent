"""Offline tests for the LLM-in-loop AgenticExecutor (no live Copilot, no network).

Covers the three fixes the reviewer flagged:
  (a) the callback->queue->yield bridge emits events in order and terminates on the
      _DONE sentinel, INCLUDING the R2 path where a non-timeout driver error still
      reaches RUN_FINISHED (ledger preserved) after a RUN_ERROR;
  (b) the finish gate: finish(success=true) is REJECTED unless the last verify was
      satisfied AND the page is not blocked, and Y1's reset makes a click between a
      passing verify and finish re-require verify;
  (c) R1: an int-typed gateway.calls is incremented by the session call count, while
      a list-typed gateway.calls (the live LLMGateway) is left untouched.

(b) drives the REAL tool closures by faking the Copilot SDK: define_tool is patched to
capture raw handlers, and create_session/send_and_wait let a scripted callback invoke
them with real Pydantic params.
"""

from __future__ import annotations

import asyncio

import pytest

from app.agent import verify as verify_mod
from app.agent.agentic_executor import AgenticExecutor, _DONE
from app.browser.provider import BrowserProvider
from app.stream import events
from app.stream.events import EventType


# --- shared fakes -----------------------------------------------------------
class _FakePage:
    """Minimal page: only the surface verify.detect_block / _goal_satisfied touch."""

    def __init__(self, url: str = "https://example.test/", body: str = "hello world") -> None:
        self.url = url
        self._body = body

    async def inner_text(self, _sel: str) -> str:
        return self._body

    def locator(self, _sel: str):
        return _FakeLocator()


class _FakeLocator:
    @property
    def first(self):
        return self

    async def count(self) -> int:
        return 0

    async def is_visible(self) -> bool:
        return False


class _FakeProvider(BrowserProvider):
    def __init__(self, page: _FakePage) -> None:
        self._page = page
        self.launched = False
        self.closed = False

    async def launch(self) -> None:
        self.launched = True

    async def new_page(self):
        return self._page

    async def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _copilot_token(monkeypatch):
    # run() bails early with RUN_ERROR if no Copilot token is present; provide one so
    # the offline tests exercise the real drive/bridge path.
    monkeypatch.setenv("GH_TOKEN", "offline-test-token")
    yield


def _new_executor(provider, gateway=None, verify_hook=None):
    return AgenticExecutor(provider, gateway=gateway, verify_hook=verify_hook)


# --- (a) + (c): bridge ordering, sentinel termination, R2 error path, R1 calls ----
@pytest.mark.anyio
async def test_bridge_emits_in_order_and_terminates_on_sentinel(monkeypatch):
    page = _FakePage()
    provider = _FakeProvider(page)
    executor = _new_executor(provider)

    async def fake_drive(self, task, run_id, page, state, ledger, emit, loop):
        try:
            emit(events.step_started(f"{run_id}-s1", "observe: x"))
            emit(events.step_finished(f"{run_id}-s1", "ok"))
            ledger["calls"] = 4
            state["success"] = True
        finally:
            emit(_DONE)

    monkeypatch.setattr(AgenticExecutor, "_drive", fake_drive)

    seq = [ev.type async for ev in executor.run("do x")]

    assert seq[0] == EventType.RUN_STARTED
    assert seq[-1] == EventType.RUN_FINISHED
    # the handler-emitted events appear in order, between start and finish, and the
    # stream terminated on the sentinel (no hang).
    assert seq.index(EventType.STEP_STARTED) < seq.index(EventType.STEP_FINISHED)
    assert seq.index(EventType.STEP_FINISHED) < seq.index(EventType.RUN_FINISHED)
    assert provider.closed is True


@pytest.mark.anyio
async def test_r2_driver_error_still_reaches_run_finished_with_tokens(monkeypatch):
    page = _FakePage()
    provider = _FakeProvider(page)
    executor = _new_executor(provider)

    async def failing_drive(self, task, run_id, page, state, ledger, emit, loop):
        # mirror real _drive: the finally enqueues _DONE even though the body raises.
        try:
            ledger["calls"] = 2
            ledger["input_tokens"] = 100
            ledger["output_tokens"] = 50
            raise RuntimeError("sdk connection reset")
        finally:
            emit(_DONE)

    monkeypatch.setattr(AgenticExecutor, "_drive", failing_drive)

    payloads = {}
    seq = []
    async for ev in executor.run("do x"):
        seq.append(ev.type)
        payloads[ev.type] = ev.payload

    # A non-timeout driver error emits RUN_ERROR carrying the message...
    assert EventType.RUN_ERROR in seq
    assert "sdk connection reset" in payloads[EventType.RUN_ERROR]["error"]
    # ...and STILL falls through to RUN_FINISHED so the ledger is preserved and the
    # stream terminates cleanly (frontend does not hang, cost is accrued).
    assert seq[-1] == EventType.RUN_FINISHED
    toks = payloads[EventType.RUN_FINISHED]["tokens"]
    assert toks["input_tokens"] == 100
    assert toks["output_tokens"] == 50
    assert payloads[EventType.RUN_FINISHED]["nominal_completion"] is False


@pytest.mark.anyio
async def test_r1_int_gateway_calls_bridged_list_gateway_untouched(monkeypatch):
    page = _FakePage()

    async def drive_with_calls(self, task, run_id, page, state, ledger, emit, loop):
        ledger["calls"] = 7
        emit(_DONE)

    monkeypatch.setattr(AgenticExecutor, "_drive", drive_with_calls)

    # int-typed gateway.calls (the harness _CountingGateway path) IS incremented.
    class _IntGateway:
        def __init__(self) -> None:
            self.calls = 3
            self.tokens = {"input_tokens": 0, "output_tokens": 0,
                           "reasoning_tokens": 0, "total_nano_aiu": 0}

    int_gw = _IntGateway()
    async for _ in _new_executor(_FakeProvider(page), gateway=int_gw).run("t"):
        pass
    assert int_gw.calls == 3 + 7  # bridged

    # list-typed gateway.calls (the live LLMGateway, which appends prompts) is NOT
    # corrupted by the bridge.
    class _ListGateway:
        def __init__(self) -> None:
            self.calls = ["prompt-a"]
            self.tokens = {"input_tokens": 0, "output_tokens": 0,
                           "reasoning_tokens": 0, "total_nano_aiu": 0}

    list_gw = _ListGateway()
    async for _ in _new_executor(_FakeProvider(page), gateway=list_gw).run("t"):
        pass
    assert list_gw.calls == ["prompt-a"]  # untouched


# --- (b): finish gate + Y1 stale-verify reset, driving the REAL tool closures -----
class _FakeSession:
    def __init__(self, script):
        self._script = script

    def on(self, _cb):
        pass

    async def send_and_wait(self, _prompt, timeout=None):
        # The "LLM": run a scripted sequence of raw tool-handler calls.
        await self._script()

    async def disconnect(self):
        pass


class _FakeClient:
    """Captures raw tool handlers (by name) and hands the scripted session back."""

    _script = None  # set per-test before run()

    def __init__(self):
        self.handlers = {}

    async def start(self):
        pass

    async def stop(self):
        pass

    async def create_session(self, **kwargs):
        for tool in kwargs["tools"]:
            self.handlers[tool.name] = tool._raw_handler
        return _FakeSession(lambda: type(self)._script(self.handlers))


def _install_fake_sdk(monkeypatch):
    import copilot
    import copilot.tools as ctools

    real_define = ctools.define_tool

    def capturing_define(name, *, handler=None, **kw):
        tool = real_define(name, handler=handler, **kw)
        tool._raw_handler = handler  # stash the un-wrapped handler for direct calls
        return tool

    monkeypatch.setattr(ctools, "define_tool", capturing_define)
    monkeypatch.setattr(copilot, "CopilotClient", _FakeClient)


async def _run_with_script(monkeypatch, page, script):
    _install_fake_sdk(monkeypatch)
    _FakeClient._script = staticmethod(script)
    provider = _FakeProvider(page)
    executor = _new_executor(provider)
    payloads = {}
    async for ev in executor.run("task"):
        payloads.setdefault(ev.type, []).append(ev.payload)
    return payloads


def _last_finished(payloads):
    return payloads[EventType.RUN_FINISHED][-1]


@pytest.mark.anyio
async def test_finish_rejected_without_prior_satisfied_verify(monkeypatch):
    from app.agent.agentic_executor import _Finish

    page = _FakePage()

    async def script(h):
        # finish(success=true) with NO prior verify -> last_verify_ok is False -> reject.
        await h["finish"](_Finish(success=True, note="claim"))

    payloads = await _run_with_script(monkeypatch, page, script)
    assert _last_finished(payloads)["nominal_completion"] is False
    assert EventType.ASK_USER in payloads


@pytest.mark.anyio
async def test_finish_accepted_when_verify_satisfied_and_unblocked(monkeypatch):
    from app.agent.agentic_executor import _Finish, _Verify

    # body contains the goal text -> _goal_satisfied passes; not a bot-wall -> unblocked.
    page = _FakePage(url="https://example.test/done", body="order confirmed")

    async def script(h):
        await h["verify"](_Verify(text_visible="order confirmed"))
        await h["finish"](_Finish(success=True, note="done"))

    payloads = await _run_with_script(monkeypatch, page, script)
    assert _last_finished(payloads)["nominal_completion"] is True


@pytest.mark.anyio
async def test_finish_rejected_when_blocked_even_with_satisfied_verify(monkeypatch):
    from app.agent.agentic_executor import _Finish, _Verify

    page = _FakePage(url="https://example.test/done", body="order confirmed")

    async def script(h):
        await h["verify"](_Verify(text_visible="order confirmed"))
        await h["finish"](_Finish(success=True))

    # Force detect_block to report a bot-wall at finish time.
    async def fake_block(_page):
        return "text:are you a robot"

    monkeypatch.setattr(verify_mod, "detect_block", fake_block)

    payloads = await _run_with_script(monkeypatch, page, script)
    assert _last_finished(payloads)["nominal_completion"] is False
    assert EventType.ASK_USER in payloads


@pytest.mark.anyio
async def test_y1_click_resets_stale_verify_then_finish_rejected(monkeypatch):
    """verify passes on page A, then a click -> Y1 resets last_verify_ok, so a
    subsequent finish(success=true) is REJECTED (the page moved, verify is stale)."""
    from app.agent.agentic_executor import _Finish, _Target, _Verify
    from app.agent.agentic import cdp

    page = _FakePage(url="https://example.test/a", body="step one done")

    # Stub the CDP click path so the real click handler runs offline and reaches the
    # Y1 reset at its top (the reset happens before any cdp call, but keep it clean).
    async def fake_snapshot(_p):
        return {}

    async def fake_ground(_p, _t):
        return object()  # non-None locator -> click proceeds

    async def fake_click(_loc):
        return None

    def fake_changed(_a, _b):
        return True

    monkeypatch.setattr(cdp, "snapshot", fake_snapshot)
    monkeypatch.setattr(cdp, "ground", fake_ground)
    monkeypatch.setattr(cdp, "click", fake_click)
    monkeypatch.setattr(cdp, "changed", fake_changed)

    async def script(h):
        await h["verify"](_Verify(text_visible="step one done"))  # passes on page A
        await h["click"](_Target(target="Next"))                  # Y1: resets last_verify_ok
        await h["finish"](_Finish(success=True))                  # must be REJECTED

    payloads = await _run_with_script(monkeypatch, page, script)
    assert _last_finished(payloads)["nominal_completion"] is False
    assert EventType.ASK_USER in payloads
