import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def test_app_imports():
    assert app.title == "browser-agent"


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_sse_yields_at_least_one_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/sse/stream?task=smoke") as resp:
            assert resp.status_code == 200
            events = []
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    events.append(json.loads(line[len("data:") :].strip()))
                    break
    assert len(events) >= 1
    assert events[0]["type"] == "RUN_STARTED"
    assert events[0]["payload"]["task"] == "smoke"
