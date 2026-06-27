"""FastAPI entry: health + SSE step streams.

`/sse/stream` is the M0 placeholder (no browser, no LLM). `/agent/run` drives the
real M1 loop (NL -> plan -> perceive/locate/act/verify) and streams real events.
All payloads serialize through `redact()` inside `Event.to_sse()`.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.agent.executor import Executor, VerifyHook
from app.agent.models import (
    EFFORT_DEFAULTS,
    ROLE_DEFAULTS,
    THINKING_LEVELS,
    LLMGateway,
    available_models,
    resolve_effort,
    resolve_model,
)
from app.agent.planner import LLMPlanner, PlanResult, SubTask
from app.browser.provider import PlaywrightProvider
from app.obs.tracing import init_observability
from app.security import TokenAuthMiddleware, is_configured, issue_cookie, valid
from app.stream import events, screenshots
from app.verify.state import state_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_observability()
    yield


app = FastAPI(title="browser-agent", version="0.0.0", lifespan=lifespan)

app.add_middleware(TokenAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


class _TokenIn(BaseModel):
    token: str


@app.post("/auth")
async def auth(body: _TokenIn, request: Request):
    """Exchange the shared access token for an httponly cookie. The cookie then
    rides along on SSE and screenshot requests automatically (those can't send
    headers). Returns 503 if the operator hasn't configured a token."""
    if not is_configured():
        raise HTTPException(status_code=503, detail="AGENT_ACCESS_TOKEN not configured")
    if not valid(body.token):
        raise HTTPException(status_code=401, detail="invalid token")
    resp = JSONResponse({"ok": True})
    # Behind the Cloudflare tunnel TLS terminates at the edge and the app sees
    # http; trust X-Forwarded-Proto so the public leg gets a Secure cookie while
    # plain-http localhost still works.
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    issue_cookie(resp, body.token, secure=proto == "https")
    return resp


def _placeholder_run(task: str):
    run_id = uuid.uuid4().hex[:8]
    yield events.run_started(task, run_id)
    for i, desc in enumerate(("perceive page", "locate element", "act"), start=1):
        step_id = f"{run_id}-s{i}"
        yield events.step_started(step_id, desc)
        yield events.step_finished(step_id, "ok")
    # Placeholder demo: no real page, so no independent goal check ran.
    yield events.run_finished(run_id, nominal=True, verified=None, goal_checked=False)


@app.get("/sse/stream")
async def sse_stream(task: str = "demo task"):
    async def gen():
        for event in _placeholder_run(task):
            yield event.to_sse()
            await asyncio.sleep(0.2)

    return EventSourceResponse(gen())


class _StartUrlPlanner:
    """Prepend a navigate sub-task for the optional start URL so the LLM plan
    starts from the user-chosen page (it would otherwise have to guess the URL)."""

    def __init__(self, inner, start_url: str) -> None:
        self._inner = inner
        self._start_url = start_url

    async def plan(
        self, task: str, start_url: str | None = None, observation: str | None = None
    ) -> PlanResult:
        if observation is not None:
            return await self._inner.plan(task, observation=observation)  # peek: no prepend
        result = await self._inner.plan(task, start_url=self._start_url)
        subtasks = result.subtasks
        if subtasks and subtasks[0].action == "navigate":
            return result
        prepended = [SubTask(action="navigate", url=self._start_url, description="open start URL"), *subtasks]
        return PlanResult(prepended, result.raw)

    async def replan(self, task: str, failure_log: list[dict], observation: str) -> PlanResult:
        # Re-plan from the CURRENT page — do not re-prepend the start URL (the page
        # is already loaded; the peek-replan plans the suffix from here).
        return await self._inner.replan(task, failure_log, observation)


_MODEL_MENU_CACHE: list[str] | None = None


async def _model_menu() -> list[str]:
    """The active model dropdown, cached per process: the live Copilot list when a
    token is configured, else the MODEL_MENU fallback. A short-lived gateway is
    started just to query the list (mirrors the run's own gateway lifecycle)."""
    global _MODEL_MENU_CACHE
    if _MODEL_MENU_CACHE is None:
        gateway = LLMGateway()
        try:
            _MODEL_MENU_CACHE = await available_models(gateway)
        finally:
            await gateway.close()
    return _MODEL_MENU_CACHE


@app.get("/models")
async def models() -> dict:
    """The selectable model menu, thinking levels, and per-role defaults, so the UI
    picker stays in sync with the backend's routing. The menu is the live Copilot
    list when a token is configured, else the static fallback. Public (no secrets)
    — the picker renders before a run."""
    return {
        "menu": await _model_menu(),
        "defaults": ROLE_DEFAULTS,
        "thinking_levels": list(THINKING_LEVELS),
        "thinking_defaults": EFFORT_DEFAULTS,
    }


_ALLOWED_CRITERION_KEYS = {"url_contains", "h1_equals", "selector_text_equals"}


def _parse_criterion(criterion: str | None) -> dict | None:
    """Parse + validate the optional user success criterion into the dict shape
    state_check understands. Restricted to deterministic, scoped primitives — a
    loose body-text `text_contains` (or any unknown key) is REJECTED so a supplied
    criterion can never weaken into a check that passes by accident. Returns None
    when no criterion is given; raises 400 on a malformed/disallowed one."""
    if criterion is None or not criterion.strip():
        return None
    try:
        parsed = json.loads(criterion)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="criterion must be valid JSON")
    if not isinstance(parsed, dict) or not parsed:
        raise HTTPException(status_code=400, detail="criterion must be a non-empty object")
    bad = set(parsed) - _ALLOWED_CRITERION_KEYS
    if bad:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported criterion key(s) {sorted(bad)}; allowed: {sorted(_ALLOWED_CRITERION_KEYS)}",
        )
    if "selector_text_equals" in parsed:
        spec = parsed["selector_text_equals"]
        if not (isinstance(spec, dict) and isinstance(spec.get("css"), str) and "value" in spec):
            raise HTTPException(status_code=400, detail="selector_text_equals requires {css, value}")
    return parsed


def _make_verify_hook(criterion: dict) -> VerifyHook:
    """Wrap the validated criterion as a verify_hook that runs the SAME independent
    deterministic state_check the eval harness uses (eval/harness.py), on the live
    final page. A page-level error verifies as False (honest non-verification)."""

    async def verify_hook(page):
        try:
            return await state_check(page, criterion)
        except Exception:
            return False

    return verify_hook


def _build_executor(
    url: str | None,
    *,
    plan_model: str,
    exec_model: str,
    replanner_model: str,
    plan_effort: str,
    exec_effort: str,
    replanner_effort: str,
    max_replans: int = 5,
    verify_hook: VerifyHook | None = None,
) -> Executor:
    gateway = LLMGateway(
        workhorse_model=exec_model,
        replanner_model=replanner_model,
        workhorse_effort=exec_effort,
        replanner_effort=replanner_effort,
    )
    planner: object = LLMPlanner(gateway, model=plan_model, reasoning_effort=plan_effort)
    if url:
        planner = _StartUrlPlanner(planner, url)
    # peek-plan is the default (autoresearch KEEP: more verified, net cheaper, M3->0).
    # It activates only when a start URL is given (something to peek); else blind.
    # verify_hook is set only when the caller supplies a success criterion: with it,
    # `verified` is a real independent state_check; without it the run is self-report
    # only (verified=None) — never falsely shown as "verified".
    return Executor(PlaywrightProvider(headless=True), planner, gateway=gateway,
                    peek_plan=True, start_url=url, max_replans=max_replans,
                    verify_hook=verify_hook)


@app.get("/agent/run")
async def agent_run(
    task: str,
    url: str | None = None,
    model_plan: str | None = None,
    model_exec: str | None = None,
    model_replanner: str | None = None,
    think_plan: str | None = None,
    think_exec: str | None = None,
    think_replanner: str | None = None,
    max_replans: int = 5,
    criterion: str | None = None,
):
    """Drive the real M1 loop. The planner lazy-connects to Copilot on first use;
    without a live Copilot server it emits a RUN_ERROR event (the stream still
    opens — no auth needed to reach this endpoint). An optional `url` seeds a
    navigate sub-task so the run starts from the user-provided page. Per-role model
    and thinking-level overrides are validated (MODEL_MENU / THINKING_LEVELS) and
    fall back to the role default when unknown. An optional `criterion` (JSON in the
    state_check shape) turns on independent goal-verification on the live final page;
    without it the run is reported as self-report only, never as "verified"."""
    verify_hook = None
    parsed_criterion = _parse_criterion(criterion)  # raises 400 on malformed/disallowed
    if parsed_criterion is not None:
        verify_hook = _make_verify_hook(parsed_criterion)
    menu = await _model_menu()
    executor = _build_executor(
        url,
        plan_model=resolve_model(model_plan, "plan", menu),
        exec_model=resolve_model(model_exec, "exec", menu),
        replanner_model=resolve_model(model_replanner, "replanner", menu),
        plan_effort=resolve_effort(think_plan, "plan"),
        exec_effort=resolve_effort(think_exec, "exec"),
        replanner_effort=resolve_effort(think_replanner, "replanner"),
        max_replans=max(0, min(int(max_replans), 10)),  # clamp to a sane range
        verify_hook=verify_hook,
    )

    async def gen():
        async for event in executor.run(task):
            yield event.to_sse()

    return EventSourceResponse(gen())


app.mount(
    screenshots.ROUTE_PREFIX,
    StaticFiles(directory=screenshots.store_dir(), check_dir=False),
    name="screenshots",
)

_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
