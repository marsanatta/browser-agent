"""FastAPI entry: health + SSE step streams.

`/sse/stream` is the M0 placeholder (no browser, no LLM). `/agent/run` drives the
real M1 loop (NL -> plan -> perceive/locate/act/verify) and streams real events.
All payloads serialize through `redact()` inside `Event.to_sse()`.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.agent.executor import Executor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.obs.tracing import init_observability
from app.security import TokenAuthMiddleware, is_configured, issue_cookie, valid
from app.stream import events, screenshots


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
    yield events.run_finished(run_id, nominal=True, verified=True)


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

    async def plan(self, task: str) -> list[SubTask]:
        subtasks = await self._inner.plan(task)
        if subtasks and subtasks[0].action == "navigate":
            return subtasks
        return [SubTask(action="navigate", url=self._start_url, description="open start URL"), *subtasks]


@app.get("/agent/run")
async def agent_run(task: str, url: str | None = None):
    """Drive the real M1 loop. The planner lazy-connects to Copilot on first use;
    without a live Copilot server it emits a RUN_ERROR event (the stream still
    opens — no auth needed to reach this endpoint). An optional `url` seeds a
    navigate sub-task so the run starts from the user-provided page."""
    gateway = LLMGateway()
    planner = LLMPlanner(gateway)
    if url:
        planner = _StartUrlPlanner(planner, url)
    executor = Executor(PlaywrightProvider(headless=True), planner, gateway=gateway)

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
