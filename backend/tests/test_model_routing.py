"""Per-role model routing: validated overrides, fail-safe defaults, and the
threading from /agent/run -> gateway/planner. All offline (no Copilot, no network)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.agent.models import (
    EFFORT_DEFAULTS,
    EXECUTION_EFFORT,
    EXECUTION_MODEL,
    MODEL_MENU,
    PLANNER_EFFORT,
    PLANNER_MODEL,
    REPLANNER_EFFORT,
    REPLANNER_MODEL,
    ROLE_DEFAULTS,
    THINKING_LEVELS,
    LLMGateway,
    MockGateway,
    available_models,
    resolve_effort,
    resolve_model,
)
from app.agent.planner import LLMPlanner
from app.main import _build_executor, app


def test_role_defaults_are_all_selectable():
    # The picker shows the default as a selected <option>, so every default must
    # be in the menu.
    for role, model in ROLE_DEFAULTS.items():
        assert model in MODEL_MENU, role


def test_resolve_model_keeps_a_valid_override():
    assert resolve_model("gpt-5-mini", "plan") == "gpt-5-mini"


def test_resolve_model_validates_against_passed_menu():
    # The live Copilot list is the source of truth: a live-only id (NOT in the
    # static MODEL_MENU fallback) is accepted when it is in the menu we pass, and
    # rejected (-> role default) when validated against the static fallback.
    live_only = "claude-opus-4.9-preview"  # synthetic id present only in the live menu
    assert live_only not in MODEL_MENU
    assert resolve_model(live_only, "plan", [live_only, "claude-opus-4.8"]) == live_only
    assert resolve_model(live_only, "plan", MODEL_MENU) == PLANNER_MODEL


@pytest.mark.anyio
async def test_available_models_uses_live_list_else_falls_back():
    # MockGateway.list_models returns MODEL_MENU (stands in for a live list).
    assert await available_models(MockGateway(lambda _p: "")) == list(MODEL_MENU)

    class _Boom:
        async def list_models(self):
            raise RuntimeError("no token")

    assert await available_models(_Boom()) == list(MODEL_MENU)  # never raises


def test_resolve_model_falls_back_when_unknown_or_empty():
    assert resolve_model("not-a-real-model", "plan") == PLANNER_MODEL
    assert resolve_model(None, "exec") == EXECUTION_MODEL
    assert resolve_model("", "replanner") == REPLANNER_MODEL


def test_effort_defaults_are_valid_levels():
    for role, level in EFFORT_DEFAULTS.items():
        assert level in THINKING_LEVELS, role
    assert set(EFFORT_DEFAULTS) == set(ROLE_DEFAULTS)  # same roles for model + effort


def test_resolve_effort_keeps_valid_and_falls_back_otherwise():
    assert resolve_effort("xhigh", "replanner") == "xhigh"
    assert resolve_effort("turbo", "plan") == PLANNER_EFFORT  # not a real level
    assert resolve_effort(None, "exec") == EXECUTION_EFFORT


def test_gateway_defaults_and_overrides_per_role():
    gw0 = LLMGateway()
    assert gw0.workhorse_model == EXECUTION_MODEL
    assert gw0.replanner_model == REPLANNER_MODEL
    assert gw0.workhorse_effort == EXECUTION_EFFORT
    assert gw0.replanner_effort == REPLANNER_EFFORT
    gw = LLMGateway(
        workhorse_model="gpt-5-mini",
        replanner_model="gpt-5.5",
        workhorse_effort="medium",
        replanner_effort="high",
    )
    assert gw.workhorse_model == "gpt-5-mini"
    assert gw.replanner_model == "gpt-5.5"
    assert gw.workhorse_effort == "medium"
    assert gw.replanner_effort == "high"


def test_planner_defaults_and_overrides():
    p0 = LLMPlanner(LLMGateway())
    assert p0._model == PLANNER_MODEL
    assert p0._effort == PLANNER_EFFORT
    p = LLMPlanner(LLMGateway(), model="gemini-3.5-flash", reasoning_effort="medium")
    assert p._model == "gemini-3.5-flash"
    assert p._effort == "medium"


def test_build_executor_threads_models_and_efforts():
    ex = _build_executor(
        None,
        plan_model="gpt-5-mini",
        exec_model="claude-haiku-4.5",
        replanner_model="claude-opus-4.8",
        plan_effort="high",
        exec_effort="low",
        replanner_effort="xhigh",
    )
    assert ex._gateway.workhorse_model == "claude-haiku-4.5"
    assert ex._gateway.replanner_model == "claude-opus-4.8"
    assert ex._gateway.workhorse_effort == "low"
    assert ex._gateway.replanner_effort == "xhigh"
    assert ex._planner._model == "gpt-5-mini"
    assert ex._planner._effort == "high"


@pytest.mark.anyio
async def test_models_endpoint_is_public_and_returns_menu_and_defaults(monkeypatch):
    # Force the offline fallback so this is deterministic + network-free even on a
    # machine that has a Copilot token: drop the token/host vars and reset the cache.
    import app.main as main_module

    for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "COPILOT_HOST", "COPILOT_PORT"):
        monkeypatch.delenv(var, raising=False)
    main_module._MODEL_MENU_CACHE = None
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/models")  # /models is not a protected prefix
        assert resp.status_code == 200
        body = resp.json()
        assert body["menu"] == list(MODEL_MENU)  # offline -> static fallback
        assert body["defaults"] == ROLE_DEFAULTS
        assert body["thinking_levels"] == list(THINKING_LEVELS)
        assert body["thinking_defaults"] == EFFORT_DEFAULTS
    finally:
        main_module._MODEL_MENU_CACHE = None  # don't leak the cache to other tests
