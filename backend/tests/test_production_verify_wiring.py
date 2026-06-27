"""Production goal-verification wiring (the /agent/run honesty fix).

Proves the deployed app no longer reports self-report as "verified":

  - With a success criterion, the SAME independent deterministic state_check the
    eval harness uses runs on the live final page. It confirms a real pass AND
    catches a silent failure (agent claims success, page disagrees).
  - Without a criterion, NO goal check runs: goal_checked is False and
    verified_completion is None — the run is self-report only, never "verified".
  - The criterion allowlist rejects a loose `text_contains` / unknown key, so a
    supplied criterion can never weaken into a check that passes by accident.

Network-free: data: URLs + a MockPlanner (no Copilot, no live site), so this runs
in the offline gate (`pytest -m "not live"`). The criterion is parsed and wrapped
through the REAL production functions (`_parse_criterion`, `_make_verify_hook`).
"""

import urllib.parse

import pytest
from fastapi import HTTPException

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.main import _build_executor, _make_verify_hook, _parse_criterion
from app.stream.events import EventType

# Page whose click nominally "succeeds" (DOM changes) but the H1 stays "Home" —
# so a goal of H1=="Cart" is a SILENT FAILURE the independent check must catch.
_SILENT = (
    "<body><h1>Home</h1>"
    "<button onclick=\"o.innerText='clicked'\">Go</button><p id=o>idle</p></body>"
)
# Same shape but the H1 genuinely equals "Cart" — a real verified pass.
_PASS = (
    "<body><h1>Cart</h1>"
    "<button onclick=\"o.innerText='clicked'\">Go</button><p id=o>idle</p></body>"
)


def _data(html: str) -> str:
    return "data:text/html," + urllib.parse.quote(html)


async def _run(html: str, verify_hook):
    planner = MockPlanner(
        [SubTask(action="navigate", url=_data(html)), SubTask(action="click", target="Go")]
    )
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, verify_hook=verify_hook)
    fin = next(e for e in [e async for e in ex.run("task")] if e.type == EventType.RUN_FINISHED)
    return fin.payload


@pytest.mark.anyio
async def test_criterion_runs_real_state_check_and_verifies_pass():
    # A supplied criterion that holds -> the real state_check runs on the live page
    # and the run is genuinely goal-verified.
    hook = _make_verify_hook(_parse_criterion('{"h1_equals": "Cart"}'))
    payload = await _run(_PASS, hook)
    assert payload["goal_checked"] is True
    assert payload["nominal_completion"] is True
    assert payload["verified_completion"] is True


@pytest.mark.anyio
async def test_criterion_catches_silent_failure():
    # The agent nominally "succeeds" (DOM changed) but the goal (H1=="Cart") is not
    # met -> the independent check ran and disagreed: nominal True, verified False.
    hook = _make_verify_hook(_parse_criterion('{"h1_equals": "Cart"}'))
    payload = await _run(_SILENT, hook)
    assert payload["goal_checked"] is True
    assert payload["nominal_completion"] is True
    assert payload["verified_completion"] is False  # silent failure surfaced, not hidden


@pytest.mark.anyio
async def test_criterion_via_scoped_selector_runs():
    # selector_text_equals is wired through the same path (scoped, deterministic).
    hook = _make_verify_hook(
        _parse_criterion('{"selector_text_equals": {"css": "#o", "value": "clicked"}}')
    )
    payload = await _run(_SILENT, hook)
    assert payload["goal_checked"] is True
    assert payload["verified_completion"] is True  # #o becomes "clicked" after the click


@pytest.mark.anyio
async def test_no_criterion_is_not_goal_verified():
    # No criterion -> no goal check ran: self-report only, never shown as verified.
    payload = await _run(_PASS, None)
    assert payload["goal_checked"] is False
    assert payload["verified_completion"] is None
    assert payload["nominal_completion"] is True


def test_build_executor_forwards_verify_hook():
    sentinel = object()
    common = dict(
        plan_model="x", exec_model="x", replanner_model="x",
        plan_effort="medium", exec_effort="medium", replanner_effort="medium",
    )
    assert _build_executor(None, verify_hook=sentinel, **common)._verify_hook is sentinel
    assert _build_executor(None, **common)._verify_hook is None


def test_parse_criterion_rejects_loose_and_unknown():
    # The hard rule: a loose body-text check or any unknown key cannot become a
    # "verified" pass. Each must 400 rather than silently weaken the assertion.
    for bad in ('{"text_contains": "x"}', '{"bogus": 1}', "not json", "{}", "[]",
                '{"selector_text_equals": {"css": "#o"}}',
                '{"selector_text_equals": "just a string"}'):
        with pytest.raises(HTTPException) as exc:
            _parse_criterion(bad)
        assert exc.value.status_code == 400


def test_parse_criterion_accepts_allowed_primitives():
    assert _parse_criterion(None) is None
    assert _parse_criterion("   ") is None
    assert _parse_criterion('{"url_contains": "/cart"}') == {"url_contains": "/cart"}
    assert _parse_criterion('{"h1_equals": "Cart"}') == {"h1_equals": "Cart"}
    assert _parse_criterion('{"selector_text_equals": {"css": "#o", "value": "v"}}') == {
        "selector_text_equals": {"css": "#o", "value": "v"}
    }
