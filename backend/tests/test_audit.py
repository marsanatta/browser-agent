"""Audit instrumentation: per-task trace, deterministic attribution, token ledger.

All offline + network-free: synthetic events / MockGateway, inline data: URL pages.
"""

import sys
import urllib.parse
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agent.executor import Executor
from app.agent.models import LLMGateway, LLMResponse, MockGateway, _usage_from_event
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream import events
from app.stream.events import EventType

from eval import audit
from eval.harness import _CountingGateway


# --- tokens: extraction + accrual (offline, synthetic) --------------------------


def test_usage_from_event_real_and_synthetic_shapes():
    # Mirrors the real AssistantUsageData: token fields on event.data, total_nano_aiu
    # nested under copilot_usage.
    real = SimpleNamespace(data=SimpleNamespace(
        input_tokens=10, output_tokens=20, reasoning_tokens=5,
        copilot_usage=SimpleNamespace(total_nano_aiu=35000)))
    assert _usage_from_event(real) == {
        "input_tokens": 10, "output_tokens": 20, "reasoning_tokens": 5, "total_nano_aiu": 35000}
    # synthetic dict on event.data
    dictish = SimpleNamespace(data={"output_tokens": 7, "input_tokens": 3})
    assert _usage_from_event(dictish) == {"output_tokens": 7, "input_tokens": 3}


@pytest.mark.anyio
async def test_mock_gateway_emits_synthetic_tokens():
    gw = MockGateway(lambda p: "hello world foo")
    resp = await gw.complete("a b c")
    assert resp.output_tokens == 3                 # 3 words of content
    assert resp.usage["input_tokens"] == 3         # 3 words of prompt
    assert resp.usage["output_tokens"] == 3


@pytest.mark.anyio
async def test_counting_gateway_accrues_token_ledger():
    gw = _CountingGateway(MockGateway(lambda p: "one two three four"))
    await gw.complete("a b")
    await gw.complete("a b c")
    assert gw.tokens["output_tokens"] == 8         # 4 + 4 content words
    assert gw.tokens["input_tokens"] == 5          # 2 + 3 prompt words


# --- reduce_events / wellformedness / attribution / flag (pure) -----------------


def _ok_stream():
    return [
        events.run_started("t", "r1"),
        events.plan_ready("r1", [
            {"action": "navigate", "url": "https://x.test"},
            {"action": "click", "target": "Go"},
        ]),
        events.step_started("r1-s1", "navigate"),
        events.tool_call_start("r1-s1", "navigate", "c1"),
        events.tool_call_args("c1", {"action": "navigate", "url": "https://x.test"}),
        events.step_finished("r1-s1", "ok", verdict="CHANGED"),
        events.step_started("r1-s2", "click Go"),
        events.tool_call_start("r1-s2", "click", "c2"),
        events.tool_call_args("c2", {"action": "click", "target": "Go"}),
        events.locator_resolved("r1-s2", 1, "role_name", "RESOLVED"),
        events.step_finished("r1-s2", "ok", verdict="CHANGED"),
        events.run_finished("r1", nominal=True, verified=True),
    ]


def test_reduce_events_builds_plan_and_steps():
    r = audit.reduce_events(_ok_stream())
    assert len(r["plan"]) == 2
    assert [s["action"] for s in r["steps"]] == ["navigate", "click"]
    assert r["steps"][1]["target"] == "Go"
    assert r["steps"][1]["ground"] == "RESOLVED"
    assert r["steps"][1]["verdict"] == "CHANGED"
    assert r["blocked"] is False


def test_reduce_events_marks_not_found_and_blocked():
    stream = [
        events.plan_ready("r", [{"action": "click", "target": "Ghost"}]),
        events.step_started("r-s1", "click Ghost"),
        events.tool_call_start("r-s1", "click", "c1"),
        events.tool_call_args("c1", {"action": "click", "target": "Ghost"}),
        events.step_finished("r-s1", "failed", failure_category="NOT_FOUND"),
    ]
    r = audit.reduce_events(stream)
    assert r["steps"][0]["ground"] == "NOT_FOUND"
    blocked_stream = [
        events.step_started("r-s1", "x"),
        events.tool_call_start("r-s1", "press", "c1"),
        events.tool_call_args("c1", {"action": "press", "target": "Search"}),
        events.step_finished("r-s1", "failed", failure_category="BLOCKED"),
    ]
    assert audit.reduce_events(blocked_stream)["blocked"] is True


def test_plan_wellformed_rules():
    assert audit.plan_wellformed([])[0] is False
    assert audit.plan_wellformed([{"action": "navigate", "url": "ftp://x"}])[0] is False
    assert audit.plan_wellformed([{"action": "frobnicate"}])[0] is False
    assert audit.plan_wellformed([{"action": "click"}])[0] is False  # missing target
    assert audit.plan_wellformed([
        {"action": "press", "target": "Box", "value": "Enter"}])[0] is False  # press unfilled
    assert audit.plan_wellformed([
        {"action": "navigate", "url": "https://x"},
        {"action": "fill", "target": "Box", "value": "hi"},
        {"action": "press", "target": "Box", "value": "Enter"},
    ])[0] is True


def test_attribute_plan_time_vs_ground_time():
    # passing task -> no attribution
    assert audit.attribute([{"action": "navigate", "url": "https://x"}], [], True) is None
    # malformed plan -> plan-time
    assert audit.attribute([{"action": "click"}], [], False) == "plan-time"
    # wellformed but first target NOT_FOUND -> plan-time
    plan = [{"action": "click", "target": "Ghost"}]
    steps = [{"action": "click", "target": "Ghost", "ground": "NOT_FOUND"}]
    assert audit.attribute(plan, steps, False) == "plan-time"
    # wellformed + first target grounded, failure later -> ground-time
    steps2 = [{"action": "click", "target": "Real", "ground": "RESOLVED"}]
    plan2 = [{"action": "click", "target": "Real"}]
    assert audit.attribute(plan2, steps2, False) == "ground-time"


def test_audit_flag_and_coverage():
    assert audit.audit_flag(True, True, False, False) == "OK"
    assert audit.audit_flag(True, False, False, False) == "SILENT_FAILURE"
    assert audit.audit_flag(False, True, True, True) == "BLOCKED"
    assert audit.audit_flag(False, True, True, False) == "ABSTAIN"
    assert audit.audit_flag(False, False, True, False) == "HONEST_FAIL"

    def tr(verified, attribution):
        return audit.TaskTrace("t", [], [], {}, 0, 0, False, verified, False, "x", attribution)

    traces = [tr(True, None), tr(False, "plan-time"), tr(False, "ground-time")]
    assert audit.attribution_coverage(traces) == 1.0  # every FAILING task tagged


# --- end-to-end: the executor's real events reduce to a trace (inline page) ------


@pytest.fixture
async def provider():
    p = PlaywrightProvider(headless=True)
    await p.launch()
    yield p
    await p.close()


_CLICK = ('<button id="go">Go</button><div id="out">none</div>'
          "<script>document.getElementById('go').onclick=function(){"
          "document.getElementById('out').textContent='CLICKED'};</script>")


@pytest.mark.anyio
async def test_executor_emits_plan_and_ground_resolved():
    data_url = "data:text/html," + urllib.parse.quote(_CLICK)
    planner = MockPlanner([SubTask(action="navigate", url=data_url),
                           SubTask(action="click", target="Go")])
    ex = Executor(PlaywrightProvider(headless=True), planner)
    evs = [ev async for ev in ex.run("click go")]
    assert any(e.type == EventType.PLAN_READY for e in evs)
    r = audit.reduce_events(evs)
    click = next(s for s in r["steps"] if s["action"] == "click")
    assert click["ground"] == "RESOLVED"
    tr = audit.build_trace("t", plan=r["plan"], steps=r["steps"], tokens={"output_tokens": 0},
                           calls=0, nsteps=2, nominal=True, verified=True, asked=False, blocked=False)
    assert tr.flag == "OK"
    assert "click" in audit.render_md([tr], "now")


_SYNONYM = ('<button id="b">Log in</button><div id="out">none</div>'
            "<script>document.getElementById('b').onclick=function(){"
            "document.getElementById('out').textContent='SUBMITTED'};</script>")


# --- frontend token surfacing: gateway accrual + RUN_FINISHED carries tokens --------


def test_llm_gateway_accrues_token_ledger():
    gw = LLMGateway()  # lazy; no Copilot connection at construction
    assert gw.tokens == {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                         "total_nano_aiu": 0}
    gw._accrue(LLMResponse("m", "x", output_tokens=5, usage={
        "input_tokens": 10, "output_tokens": 5, "reasoning_tokens": 2, "total_nano_aiu": 17000}))
    gw._accrue(LLMResponse("m", "y", output_tokens=3, usage=None))  # output-only fallback
    assert gw.tokens == {"input_tokens": 10, "output_tokens": 8, "reasoning_tokens": 2,
                         "total_nano_aiu": 17000}


class _FakeGateway:
    """Gateway double exposing a fixed .tokens ledger (the executor surfaces it)."""
    tokens = {"output_tokens": 42, "input_tokens": 100, "reasoning_tokens": 7, "total_nano_aiu": 5000}

    async def complete(self, *a, **k):
        return LLMResponse("m", "")

    async def judge(self, *a, **k):
        return LLMResponse("m", "")


@pytest.mark.anyio
async def test_run_finished_carries_gateway_tokens():
    data_url = "data:text/html," + urllib.parse.quote(_CLICK)
    planner = MockPlanner([SubTask(action="navigate", url=data_url),
                           SubTask(action="click", target="Go")])
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=_FakeGateway())
    fin = next(ev for ev in [e async for e in ex.run("go")]
               if ev.type == EventType.RUN_FINISHED)
    assert fin.payload["tokens"] == _FakeGateway.tokens


@pytest.mark.anyio
async def test_run_finished_tokens_empty_without_gateway():
    data_url = "data:text/html," + urllib.parse.quote(_CLICK)
    planner = MockPlanner([SubTask(action="navigate", url=data_url),
                           SubTask(action="click", target="Go")])
    ex = Executor(PlaywrightProvider(headless=True), planner)  # gateway=None
    fin = next(ev for ev in [e async for e in ex.run("go")]
               if ev.type == EventType.RUN_FINISHED)
    assert fin.payload["tokens"] == {}


@pytest.mark.anyio
async def test_executor_ground_ambiguous_l2_via_synonym():
    # "Sign In" matches no element -> zero-candidate -> L2 picks "Log in" -> via=l2.
    data_url = "data:text/html," + urllib.parse.quote(_SYNONYM)
    planner = MockPlanner([SubTask(action="navigate", url=data_url),
                           SubTask(action="click", target="Sign In")])
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=MockGateway(lambda _p: "0"))
    evs = [ev async for ev in ex.run("sign in")]
    r = audit.reduce_events(evs)
    click = next(s for s in r["steps"] if s["action"] == "click")
    assert click["ground"] == "AMBIGUOUS_L2"
