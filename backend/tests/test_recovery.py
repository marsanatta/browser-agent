"""Per-class recovery + bounded escalation (docs/architecture/02 §1.2/§1.3).

Failure class is decided from OBSERVABLE browser state (is_visible/is_enabled,
exception text), never the LLM. Each class maps to a fixed recovery; retries are
bounded and only continue on a NEW observation; on local exhaustion the ladder
escalates replan -> ask_user.

These run on real Playwright with local HTML (no network) for determinism, plus
one live stale/timing case on a real seed page.
"""

import pytest

from app.agent import act, recover
from app.agent.classify import (
    FailureClass,
    Recovery,
    classify_exception,
    recovery_for,
)
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import BrowserProvider, PlaywrightProvider
from app.stream.events import EventType

BASE = "https://the-internet.herokuapp.com"


class _LocalProvider(BrowserProvider):
    """Real Chromium serving fixed HTML — exercises the full executor offline."""

    def __init__(self, html: str) -> None:
        self._html = html
        self._pw = self._browser = self._ctx = None

    async def launch(self) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._ctx = await self._browser.new_context()

    async def new_page(self):
        pg = await self._ctx.new_page()
        await pg.set_content(self._html)
        return pg

    async def close(self) -> None:
        if self._ctx:
            await self._ctx.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()


async def _drive(provider, plan, task):
    ex = Executor(provider, MockPlanner(plan))
    recoveries, asks, finished = [], [], None
    async for ev in ex.run(task):
        if ev.type == EventType.RECOVERY:
            recoveries.append(ev.payload)
        elif ev.type == EventType.ASK_USER:
            asks.append(ev.payload)
        elif ev.type == EventType.RUN_FINISHED:
            finished = ev.payload
    return recoveries, asks, finished


async def _collect(ex, task, *types):
    out = {ty: [] for ty in types}
    async for ev in ex.run(task):
        if ev.type in out:
            out[ev.type].append(ev.payload)
    return out


# ---- unit: exception -> class mapping (Playwright ground-truth text) ----

@pytest.mark.parametrize("msg,expected", [
    ("element is not enabled", FailureClass.NOT_INTERACTABLE),
    ("Element is outside of the viewport", FailureClass.NOT_INTERACTABLE),
    ("Element is not visible", FailureClass.NOT_INTERACTABLE),
    ("locator.click: Timeout 5000ms exceeded", FailureClass.STALE_TIMING),
    ("element is not attached to the DOM", FailureClass.STALE_TIMING),
])
def test_classify_exception(msg, expected):
    assert classify_exception(Exception(msg)) is expected


def test_recovery_mapping():
    assert recovery_for(FailureClass.NOT_FOUND) is Recovery.REGROUND
    assert recovery_for(FailureClass.NOT_INTERACTABLE) is Recovery.WAIT_SCROLL_DISMISS
    assert recovery_for(FailureClass.WRONG_PAGE) is Recovery.REPLAN
    assert recovery_for(FailureClass.STALE_TIMING) is Recovery.STATE_WAIT


# ---- not-interactable: permanently disabled -> bounded escalation -> ask_user ----

_DISABLED = """
<html><body>
<button aria-label="Place Order" disabled>Place Order</button>
</body></html>
"""


@pytest.mark.anyio
async def test_not_interactable_bounded_escalation_to_ask_user():
    plan = [SubTask(action="click", target="Place Order", role="button")]
    recoveries, asks, finished = await _drive(_LocalProvider(_DISABLED), plan, "click disabled")

    classes = {r["failure_class"] for r in recoveries}
    assert classes == {FailureClass.NOT_INTERACTABLE.value}
    assert any(r["recovery"] == Recovery.WAIT_SCROLL_DISMISS.value for r in recoveries)
    assert any(r["recovery"] == Recovery.REPLAN.value for r in recoveries)  # escalated
    assert asks, "bounded ladder must terminate at ask_user"
    assert finished["nominal_completion"] is False
    # bound: even with one replan the ladder is finite (no infinite loop)
    assert len(recoveries) < 12


# ---- replan path emits its own PHASE(planning): the re-plan is a silent LLM gap too ----

@pytest.mark.anyio
async def test_replan_emits_second_planning_phase():
    """Local recovery exhaustion triggers a global replan — a second planner LLM
    call, i.e. another silent gap. It must emit PHASE(planning) before that re-plan,
    just like the initial plan, so the live view never goes dark during a replan."""
    plan = [SubTask(action="click", target="Place Order", role="button")]
    ex = Executor(_LocalProvider(_DISABLED), MockPlanner(plan))

    seq = []
    async for ev in ex.run("click disabled"):
        if ev.type in (EventType.PHASE, EventType.RECOVERY):
            seq.append((ev.type, ev.payload.get("phase") or ev.payload.get("recovery")))

    phases = [name for t, name in seq if t == EventType.PHASE]
    assert phases.count("planning") == 2  # initial plan + replan
    assert phases.count("launching") == 1

    replan_idx = next(
        i for i, (t, n) in enumerate(seq) if t == EventType.RECOVERY and n == Recovery.REPLAN.value
    )
    assert any(
        t == EventType.PHASE and n == "planning" and i > replan_idx
        for i, (t, n) in enumerate(seq)
    ), "the replan's PHASE(planning) must follow the REPLAN recovery"


# ---- replan emits a second PLAN_READY carrying the new (reconciled) subtasks ----

@pytest.mark.anyio
async def test_replan_emits_second_plan_ready():
    """After local exhaustion, the global replan must surface its output as a
    second PLAN_READY so the live view can show what the replan produced — the
    initial PLAN_READY (planning) + one more after the REPLAN recovery."""
    plan = [SubTask(action="click", target="Place Order", role="button")]
    ex = Executor(_LocalProvider(_DISABLED), MockPlanner(plan))
    out = await _collect(ex, "click disabled", EventType.PLAN_READY)
    plans = out[EventType.PLAN_READY]

    assert len(plans) == 2, "initial plan + replan output"
    assert all(p["run_id"] == plans[0]["run_id"] for p in plans), "same run, not a fresh run"
    # MockPlanner re-emits the same fixed plan; i=0 so the reconciled list == new plan.
    assert plans[1]["plan"] == [{"action": "click", "target": "Place Order"}]


# ---- enriched recovery payload carries the per-attempt detail ----

@pytest.mark.anyio
async def test_recovery_event_carries_attempt_detail():
    """The recovery event is enriched (observe-only) with what was attempted and a
    machine 'why' token, plus the locator tier/strategy when one resolved."""
    plan = [SubTask(action="click", target="Place Order", role="button")]
    recoveries, _, _ = await _drive(_LocalProvider(_DISABLED), plan, "click disabled")

    local = [r for r in recoveries if r["recovery"] != Recovery.REPLAN.value]
    assert local, "at least one local-recovery event"
    r = local[0]
    assert r["tried"] == "click 'Place Order'"
    # disabled button -> resolved locator but not interactable -> tier/strategy present
    assert r["tier"] is not None and r["strategy"]
    assert r["detail"] == "not_visible_or_enabled"


# ---- replan AFTER a completed step: PLAN_READY carries the full reconciled plan ----

class _TwoPlanner:
    """Returns a different plan on the replan call so a tail-only emission is
    distinguishable from the full reconciled (prefix + new tail) one."""

    def __init__(self, first, second):
        self._plans = [first, second]
        self.calls = 0

    async def plan(self, task):
        p = self._plans[min(self.calls, len(self._plans) - 1)]
        self.calls += 1
        return list(p)


_STEP1_OK_STEP2_DISABLED = """
<html><body>
<button aria-label="Step One" onclick="document.body.innerHTML += '<p>ok</p>'">Step One</button>
<button aria-label="Place Order" disabled>Place Order</button>
</body></html>
"""


@pytest.mark.anyio
async def test_replan_plan_ready_includes_completed_prefix():
    """When the replan fires AFTER a completed step (i>0), the second PLAN_READY must
    carry the FULL reconciled plan — done prefix + new tail — not just the new tail.
    That prefix is what lets the live view keep the finished rows and append the new
    ones. A tail-only emission would drop 'Step One' and fail this test."""
    first = [
        SubTask(action="click", target="Step One", role="button"),
        SubTask(action="click", target="Place Order", role="button"),
    ]
    second = [SubTask(action="click", target="Retry Order", role="button")]
    ex = Executor(_LocalProvider(_STEP1_OK_STEP2_DISABLED), _TwoPlanner(first, second))
    out = await _collect(ex, "two step", EventType.PLAN_READY)
    plans = out[EventType.PLAN_READY]

    assert len(plans) == 2, "initial plan + replan output"
    assert plans[1]["plan"] == [
        {"action": "click", "target": "Step One"},  # completed prefix, preserved
        {"action": "click", "target": "Retry Order"},  # the replan's new tail
    ]


# ---- not-interactable that resolves: recovery succeeds, action retried ----

_TRANSIENT = """
<html><body>
<button id="cta" aria-label="Submit" disabled
        onclick="document.body.innerHTML += '<p>done</p>'">Submit</button>
<script>setTimeout(() => document.getElementById('cta').removeAttribute('disabled'), 800)</script>
</body></html>
"""


@pytest.mark.anyio
async def test_not_interactable_recovers_then_succeeds():
    plan = [SubTask(action="click", target="Submit", role="button")]
    recoveries, asks, finished = await _drive(_LocalProvider(_TRANSIENT), plan, "click once enabled")

    assert recoveries, "the first attempt must observe NOT_INTERACTABLE"
    assert recoveries[0]["failure_class"] == FailureClass.NOT_INTERACTABLE.value
    assert recoveries[0]["recovery"] == Recovery.WAIT_SCROLL_DISMISS.value
    assert not asks
    assert finished["nominal_completion"] is True  # wait recovery -> retry succeeds


# ---- stale / timing: state_wait re-attaches a re-rendered node (live) ----

@pytest.mark.live
@pytest.mark.anyio
async def test_state_wait_reattaches_rerendered_node():
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    pg = await provider.new_page()
    try:
        await act.navigate(pg, BASE + "/add_remove_elements/")
        await pg.get_by_role("button", name="Add Element").click()
        delete = pg.get_by_role("button", name="Delete")
        assert await delete.count() == 1
        assert await recover.state_wait(pg, delete) is True
    finally:
        await provider.close()
