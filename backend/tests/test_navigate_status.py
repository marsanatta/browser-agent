"""navigate post-check (minimal, conservative): a goto whose HTTP response is an
error status (>=400) is a FAILURE, not unconditional success. No expected-url
matching — just the status. A data: URL (no HTTP response) stays OK.

Network-free: a Playwright route fulfils requests locally with a chosen status.
"""

import urllib.parse

import pytest

from app.agent import act
from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


@pytest.mark.anyio
async def test_navigate_ok_on_data_url():
    data_url = "data:text/html," + urllib.parse.quote("<h1>ok</h1>")
    plan = [SubTask(action="navigate", url=data_url)]
    ex = Executor(PlaywrightProvider(headless=True), MockPlanner(plan))

    statuses = []
    async for ev in ex.run("open"):
        if ev.type == EventType.STEP_FINISHED:
            statuses.append((ev.payload["status"], ev.payload.get("failure_category")))
    assert statuses == [("ok", None)]


@pytest.mark.anyio
async def test_navigate_error_status_is_failure():
    class _RoutingProvider(PlaywrightProvider):
        async def new_page(self):
            pg = await super().new_page()
            await pg.route(
                "**/missing",
                lambda route: route.fulfill(status=404, content_type="text/html", body="nope"),
            )
            return pg

    plan = [SubTask(action="navigate", url="https://example.test/missing")]
    ex = Executor(_RoutingProvider(headless=True), MockPlanner(plan))

    finished = None
    async for ev in ex.run("open missing"):
        if ev.type == EventType.STEP_FINISHED:
            finished = ev.payload
    assert finished is not None
    assert finished["status"] == "failed"
    assert finished["failure_category"] == "NOT_FOUND"
