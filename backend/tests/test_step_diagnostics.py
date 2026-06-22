"""M4 inspectable-failure diagnostics: the executor must emit, per acting step,
the chosen locator tier (LOCATOR_RESOLVED), an annotated screenshot referencing a
served PNG with a real highlight box (SCREENSHOT_ANNOTATED), and a failure
category on a failed step (STEP_FINISHED.failure_category).

Runs against a local set_content page (real headless Chromium, no network) so the
screenshot bytes and bounding box are real, not faked.
"""

import json
from urllib.parse import quote

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream import screenshots
from app.stream.events import EventType

_HTML = "data:text/html," + quote(
    '<button id="go" onclick="this.insertAdjacentHTML(\'afterend\','
    '\'<p id=done>done</p>\')">Go Next</button>'
)


@pytest.fixture
async def provider():
    p = PlaywrightProvider(headless=True)
    yield p
    await p.close()


@pytest.mark.anyio
async def test_acting_step_emits_locator_tier_and_screenshot(provider):
    planner = MockPlanner([
        SubTask(action="navigate", url=_HTML, description="open page"),
        SubTask(action="click", target="Go Next", role="button"),
    ])
    executor = Executor(provider, planner)

    evs = [ev async for ev in executor.run("click go next")]
    by_type = {}
    for ev in evs:
        by_type.setdefault(ev.type, []).append(ev)

    assert EventType.LOCATOR_RESOLVED in by_type
    loc = by_type[EventType.LOCATOR_RESOLVED][0].payload
    assert loc["tier"] == 1  # resolved by ARIA role+name (the most stable tier)
    assert loc["strategy"] == "role_name"

    assert EventType.SCREENSHOT_ANNOTATED in by_type
    shots = [e.payload for e in by_type[EventType.SCREENSHOT_ANNOTATED]]
    for shot in shots:
        assert shot["screenshot_ref"].startswith(screenshots.ROUTE_PREFIX + "/")
        assert shot["screenshot_ref"].endswith(".png")
    # the screenshot for the acting step highlights the clicked link -> real box
    acted = next(s for s in shots if s["highlight"]["width"] > 0)
    assert acted["highlight"]["height"] > 0

    png_id = acted["screenshot_ref"].rsplit("/", 1)[-1]
    png_path = screenshots.store_dir() / png_id
    assert png_path.is_file() and png_path.stat().st_size > 0

    finished = evs[-1].payload
    assert finished["nominal_completion"] is True


@pytest.mark.anyio
async def test_failed_step_carries_failure_category(provider):
    planner = MockPlanner([
        SubTask(action="navigate", url=_HTML, description="open page"),
        SubTask(action="click", target="Nonexistent Button", role="button"),
    ])
    executor = Executor(provider, planner)

    finished_failed = None
    async for ev in executor.run("click a missing element"):
        if ev.type == EventType.STEP_FINISHED and ev.payload["status"] == "failed":
            finished_failed = ev.payload

    assert finished_failed is not None
    assert finished_failed["failure_category"] == "NOT_FOUND"


@pytest.mark.anyio
async def test_screenshot_payload_survives_redaction_roundtrip(provider):
    planner = MockPlanner([
        SubTask(action="navigate", url=_HTML, description="open page"),
        SubTask(action="click", target="Go Next", role="button"),
    ])
    executor = Executor(provider, planner)

    shot_event = None
    async for ev in executor.run("click go next"):
        if ev.type == EventType.SCREENSHOT_ANNOTATED and ev.payload["highlight"]["width"] > 0:
            shot_event = ev
    assert shot_event is not None

    sse = shot_event.to_sse()
    payload = json.loads(sse["data"])["payload"]
    # the served ref and box are non-sensitive and must survive redaction intact
    assert payload["screenshot_ref"].endswith(".png")
    assert payload["highlight"]["width"] > 0
