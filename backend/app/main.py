"""FastAPI entry: health + SSE step stream (M0 scaffold).

The SSE endpoint streams placeholder AG-UI step events so the frontend and the
event contract are exercisable WITHOUT a live Copilot connection (the real agent
loop is M1). All payloads serialize through `redact()` inside `Event.to_sse()`.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

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
