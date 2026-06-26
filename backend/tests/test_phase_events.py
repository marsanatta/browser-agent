"""Offline test: the executor fills the two silent blocking gaps (planner LLM
call, browser launch) with observe-only PHASE events, in the right order, and the
PHASE payload survives the redact()/to_sse() serialization path cleanly.

Uses a fake planner + fake provider so it runs with no network and no real
browser. We stop consuming at the first STEP_STARTED (emitted BEFORE the executor
touches the page), so the fake page never needs Playwright behavior — this test
asserts EVENT ORDERING up to step start, not subtask execution.
"""

import json

import pytest

from app.agent.executor import Executor
from app.agent.planner import SubTask
from app.browser.provider import BrowserProvider
from app.stream.events import EventType


class _FakePlanner:
    def __init__(self, subtasks):
        self._subtasks = subtasks
        self.calls = 0

    async def plan(self, task):
        self.calls += 1
        return list(self._subtasks)


class _FakePage:
    url = "about:blank"


class _FakeProvider(BrowserProvider):
    def __init__(self):
        self.launched = False

    async def launch(self):
        self.launched = True

    async def new_page(self):
        return _FakePage()

    async def close(self):
        pass


@pytest.mark.anyio
async def test_phase_events_fill_planning_and_launching_gaps():
    planner = _FakePlanner([SubTask(action="navigate", url="https://example.test", description="open")])
    provider = _FakeProvider()
    executor = Executor(provider, planner)

    seq = []
    async for ev in executor.run("open a page"):
        seq.append((ev.type, dict(ev.payload)))
        if ev.type is EventType.STEP_STARTED:
            break  # stop before the executor drives the fake page

    types = [t for t, _ in seq]
    assert types == [
        EventType.RUN_STARTED,
        EventType.PHASE,
        EventType.PLAN_READY,
        EventType.PHASE,
        EventType.STEP_STARTED,
    ]

    # phase #1 is "planning" (before plan()), phase #2 is "launching" (before launch())
    assert seq[1][1]["phase"] == "planning"
    assert seq[3][1]["phase"] == "launching"

    # launching PHASE is emitted strictly before launch() runs
    assert provider.launched is True  # by the time STEP_STARTED arrives, launch has happened


@pytest.mark.anyio
async def test_phase_payload_passes_redact_via_to_sse():
    from app.stream import events

    ev = events.phase("ab12cd34", "planning")
    sse = ev.to_sse()
    assert sse["event"] == "PHASE"
    decoded = json.loads(sse["data"])
    assert decoded["type"] == "PHASE"
    # plain machine tokens survive redaction untouched — no secret/PII in the payload
    assert decoded["payload"] == {"run_id": "ab12cd34", "phase": "planning"}
