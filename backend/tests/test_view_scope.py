"""Dense-page view-scope repro (the Amazon "click the first result" failure).

Root cause (proved in /eng-debug): the observation handed to the planner LLM is
truncated to the first N DOM-order elements, so on a dense page the real result
links (deep in the DOM) are never seen — the planner can only target what it can
SEE, so it guesses a non-existent "first search result" and never recovers.

This models the LLM's dependency on the observation with a stub planner that can
ONLY target an element actually present in the observation string it receives.
With a fixed small window the product links stay hidden and the run abstains;
with failure-driven view widening the replan observation reveals them and the
agent clicks the first product.

Network-free: a data: URL + stub planner (no Copilot, no live site).
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import PlanResult, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType

# 43 chrome links (index 0-42) THEN the product result links (index 43+), so the
# products fall past the default 40-element observation window — exactly the
# Amazon-results shape. Clicking PRODUCT 1 mutates the DOM (a real CHANGED).
_CHROME = "".join(f'<a href="/n{i}">nav {i}</a>' for i in range(43))
_PRODUCTS = (
    '<a href="/dp/1" onclick="r.innerText=\'OPENED\'">PRODUCT 1</a>'
    '<a href="/dp/2" onclick="r.innerText=\'OPENED\'">PRODUCT 2</a>'
)
_HTML = f"<body>{_CHROME}{_PRODUCTS}<p id=r>list</p></body>"


def _data() -> str:
    return "data:text/html," + urllib.parse.quote(_HTML)


def _first_product_in(observation: str, prefix: str = "PRODUCT") -> str | None:
    # Extract the first product NAME the observation actually reveals (the LLM can
    # only pick what it can see). Observation lines look like: link "PRODUCT 1" -> /dp/1
    for line in observation.splitlines():
        if prefix in line and '"' in line:
            return line.split('"')[1]
    return None


class _ObsReadingPlanner:
    """Faithfully models the LLM's reliance on the observation: it targets the
    first product ONLY if a product link appears in the observation it is given;
    otherwise it repeats the doomed guess. The initial (blind) plan guesses a
    non-existent "first search result" — the real failure trigger."""

    def __init__(self, url: str) -> None:
        self._url = url

    async def plan(self, task, start_url=None, observation=None) -> PlanResult:
        return PlanResult(
            [SubTask(action="navigate", url=self._url),
             SubTask(action="click", target="first search result")],
            '[{"action":"navigate"},{"action":"click","target":"first search result"}]',
        )

    async def replan(self, task, failure_log, observation) -> PlanResult:
        product = _first_product_in(observation)
        target = product or "first search result"
        return PlanResult([SubTask(action="click", target=target)],
                          f'[{{"action":"click","target":"{target}"}}]')


async def _run(**executor_kwargs) -> dict:
    planner = _ObsReadingPlanner(_data())
    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, **executor_kwargs)
    fin = None
    async for ev in ex.run("click the first search result"):
        if ev.type == EventType.RUN_FINISHED:
            fin = ev.payload
    return fin


@pytest.mark.anyio
async def test_dense_page_first_result_is_reachable():
    # The product links sit past the default window. The fix (failure-driven view
    # widening) must reveal them on replan so the agent clicks the first product.
    fin = await _run()
    assert fin is not None
    assert fin["nominal_completion"] is True, (
        "dense-page first result not reachable — the product links never entered "
        "the planner's observation window"
    )
