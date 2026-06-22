"""FastAPI entry: health + SSE step streams.

`/sse/stream` is the M0 placeholder (no browser, no LLM). `/agent/run` drives the
real M1 loop (NL -> plan -> perceive/locate/act/verify) and streams real events.
All payloads serialize through `redact()` inside `Event.to_sse()`.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.agent.executor import Executor
from app.agent.models import LLMGateway
from app.agent.planner import LLMPlanner
from app.browser.provider import PlaywrightProvider
from app.obs.tracing import init_observability
from app.stream import events


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_observability()
    yield


app = FastAPI(title="browser-agent", version="0.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


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


@app.get("/agent/run")
async def agent_run(task: str):
    """Drive the real M1 loop. The planner lazy-connects to Copilot on first use;
    without a live Copilot server it emits a RUN_ERROR event (the stream still
    opens — no auth needed to reach this endpoint)."""
    executor = Executor(PlaywrightProvider(headless=True), LLMPlanner(LLMGateway()))

    async def gen():
        async for event in executor.run(task):
            yield event.to_sse()

    return EventSourceResponse(gen())
