"""REGROUND must only count as progress when re-perception produced a NEW
observation (docs/architecture/02 §1.3). On a STATIC page where the target is
absent, re-perceiving yields the same fingerprint every attempt, so the ladder
must stop early (`if not progressed and attempt>=2: break`) instead of burning
all max_attempts. On a page that MUTATES between attempts, the fingerprint
changes and the ladder keeps retrying.

Deterministic + network-free: data: URLs; we count perceive() calls.
"""

import urllib.parse

import pytest

from app.agent import executor as executor_mod
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


@pytest.fixture
def perceive_counter(monkeypatch):
    real = executor_mod.perceive
    calls = {"n": 0}

    async def counting(page):
        calls["n"] += 1
        return await real(page)

    monkeypatch.setattr(executor_mod, "perceive", counting)
    return calls


_STATIC_ABSENT = '<button>Other</button>'  # target "Missing" never present


@pytest.mark.anyio
async def test_static_absent_target_stops_early(perceive_counter):
    data_url = "data:text/html," + urllib.parse.quote(_STATIC_ABSENT)
    plan = [
        SubTask(action="navigate", url=data_url),
        SubTask(action="click", target="Missing", role="button"),
    ]
    max_attempts = 4
    ex = Executor(PlaywrightProvider(headless=True), MockPlanner(plan), max_attempts=max_attempts, max_replans=1)

    regrounds = 0
    async for ev in ex.run("click missing"):
        if ev.type == EventType.RECOVERY and ev.payload.get("recovery") == "REGROUND":
            regrounds += 1

    # NOT_FOUND -> REGROUND, fingerprint identical every attempt -> the subtask
    # stops after attempt 2 (2 regrounds/run). One replan re-runs the click subtask
    # once, so <=4 total; the buggy unconditional-True version ran all 4 attempts
    # per run = 8 regrounds and 16 perceives.
    assert regrounds <= 4
    assert perceive_counter["n"] < 16


# A page that adds the (still-not-the-target) DOM on each perceive: the
# fingerprint changes, so REGROUND is real progress and the ladder runs longer.
_MUTATING = (
    '<button>Other</button>'
    '<script>let n=0;const o=window.__defineGetter__?null:null;'
    'document.addEventListener("DOMContentLoaded",()=>{});</script>'
)


@pytest.mark.anyio
async def test_mutating_page_keeps_retrying(perceive_counter):
    # Inject a node on each perceive via a counter incremented by JS the page runs
    # when queried. We mutate from the test harness side instead: a page whose
    # button label cycles so each fingerprint differs.
    html = (
        '<button id="b">L0</button>'
        '<script>let i=0;setInterval(()=>{i++;'
        'document.getElementById("b").textContent="L"+i;}, 50);</script>'
    )
    data_url = "data:text/html," + urllib.parse.quote(html)
    plan = [
        SubTask(action="navigate", url=data_url),
        SubTask(action="click", target="Missing", role="button"),
    ]
    max_attempts = 4
    ex = Executor(PlaywrightProvider(headless=True), MockPlanner(plan), max_attempts=max_attempts, max_replans=1)

    regrounds = 0
    async for ev in ex.run("click missing on mutating page"):
        if ev.type == EventType.RECOVERY and ev.payload.get("recovery") == "REGROUND":
            regrounds += 1

    # fingerprint keeps changing -> progressed stays True -> ladder runs the full
    # attempt budget (a recovery on each of the first max_attempts-1 attempts).
    assert regrounds >= max_attempts - 1
