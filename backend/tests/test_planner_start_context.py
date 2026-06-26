"""planner-sees-start-url (round-3 piece B).

Deterministic offline anchor: when a start URL is known, LLMPlanner injects it into
the prompt with an instruction to stay on that page, so the LLM stops inventing a
navigate to a site's generic portal (the observed wikipedia failure). Driven through
MockGateway so it runs without Copilot or the network.
"""

import pytest

from app.agent.models import MockGateway
from app.agent.planner import LLMPlanner


@pytest.mark.anyio
async def test_plan_injects_start_url_and_stay_put_instruction():
    captured: dict = {}

    def responder(prompt: str) -> str:
        captured["prompt"] = prompt
        return '[{"action":"click","target":"Log in"}]'

    gw = MockGateway(responder)
    start = "https://en.wikipedia.org/wiki/Main_Page"
    await LLMPlanner(gw).plan("log in to wikipedia", start_url=start)

    assert start in captured["prompt"]                       # planner sees the start page
    assert "do not navigate" in captured["prompt"].lower()   # ...and is told to stay put


@pytest.mark.anyio
async def test_plan_without_start_url_has_no_start_context():
    captured: dict = {}

    def responder(prompt: str) -> str:
        captured["prompt"] = prompt
        return '[{"action":"navigate","url":"https://x"}]'

    gw = MockGateway(responder)
    await LLMPlanner(gw).plan("do something")
    assert "ALREADY loaded" not in captured["prompt"]
