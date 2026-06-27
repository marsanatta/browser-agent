"""predict-then-verify: the silent-failure fix, verified deterministically.

Each case is a `data:` trap page where a tempting WRONG action changes the page
(DOM or URL) but does NOT reach the goal. A MockPlanner FORCES that wrong action, so
the outcome is deterministic (no live site, no Copilot, no planner variance):

  CONTROL (no `expect`) -> the change is read as success -> nominal=True, verified=False
                           == the SILENT FAILURE reproduced.
  FIX     (goal `expect`) -> the executor's goal gate sees the goal unmet -> the step
                           fails -> the agent does NOT claim success -> nominal=False
                           == the silent failure AVOIDED (M3 protected).

`verified` is computed by an INDEPENDENT, test-side check (separate code from the
agent's in-loop `verify._goal_satisfied`) so this is real ground truth, not the agent
grading itself.
"""

import urllib.parse

import pytest

from app.agent.executor import Executor
from app.agent.planner import MockPlanner, SubTask
from app.browser.provider import PlaywrightProvider
from app.stream.events import EventType


def _url(html: str) -> str:
    return "data:text/html," + urllib.parse.quote(html)


# Independent (test-side) ground-truth checks — deliberately a DIFFERENT mechanism
# from the agent's in-loop verify._goal_satisfied (scoped inner_text equality and the
# Playwright text-locator engine, never body-innerText-substring), so this is real
# independent ground truth, not the agent grading itself.
async def _sel_text_eq(page, css, value):
    loc = page.locator(css).first
    return await loc.count() > 0 and (await loc.inner_text()).strip() == value


async def _text_seen(page, text):
    return await page.get_by_text(text, exact=False).count() > 0


# (id, html, trap-target, goal-expect, independent verify_hook)
CASES = [
    (
        "modal_dismiss",
        "<body><div id=m><h3 class=t>MODAL TITLE</h3></div>"
        "<button onclick=\"document.getElementById('m').remove()\">Close</button></body>",
        "Close",
        {"text_visible": "MODAL TITLE"},
        lambda p: _sel_text_eq(p, "h3.t", "MODAL TITLE"),
    ),
    (
        "wrong_similar_element",
        "<body><button onclick=\"o.innerText='Submitted!'\">Submit</button>"
        "<button onclick=\"o.innerText='Cancelled'\">Cancel</button><p id=o>idle</p></body>",
        "Cancel",
        {"text_visible": "Submitted!"},
        lambda p: _sel_text_eq(p, "#o", "Submitted!"),
    ),
    (
        "premature_success",
        "<body><button onclick=\"s.style.display='block'\">Search</button>"
        "<div id=s style='display:none'>Loading...</div></body>",
        "Search",
        {"text_visible": "Results"},
        lambda p: _text_seen(p, "Results"),
    ),
    (
        "navigated_away",
        "<body><a href='#other' onclick=\"app.innerText='OTHER'\">Go</a>"
        "<div id=app>TARGET</div></body>",
        "Go",
        {"text_visible": "TARGET"},
        lambda p: _sel_text_eq(p, "#app", "TARGET"),
    ),
    (
        "overlay_dismiss",
        "<body><div id=ov>cookies "
        "<button onclick=\"document.getElementById('ov').remove()\">Accept</button></div>"
        "<p>Please complete the survey</p></body>",
        "Accept",
        {"text_visible": "Survey done"},
        lambda p: _text_seen(p, "Survey done"),
    ),
]


async def _run(html, trap_subtask, vhook):
    planner = MockPlanner(
        [SubTask(action="navigate", url=_url(html)), trap_subtask],
        replan_subtasks=[],  # no recovery plan -> the trap either succeeds or abstains
    )
    box = {"v": False}

    async def verify_hook(page):
        box["v"] = await vhook(page)
        return box["v"]

    ex = Executor(PlaywrightProvider(headless=True), planner, gateway=None, verify_hook=verify_hook)
    fin = next(
        e for e in [e async for e in ex.run("task")] if e.type == EventType.RUN_FINISHED
    )
    return fin.payload["nominal_completion"], fin.payload["verified_completion"]


@pytest.mark.anyio
@pytest.mark.parametrize("cid,html,target,goal,vhook", CASES, ids=[c[0] for c in CASES])
async def test_control_reproduces_silent_failure(cid, html, target, goal, vhook):
    # No `expect`: the wrong action changes the page -> read as success though the
    # goal is unmet == the silent failure (nominal=True, verified=False).
    nominal, verified = await _run(html, SubTask(action="click", target=target), vhook)
    assert nominal is True and verified is False, f"{cid}: expected a silent failure"


@pytest.mark.anyio
@pytest.mark.parametrize("cid,html,target,goal,vhook", CASES, ids=[c[0] for c in CASES])
async def test_fix_avoids_silent_failure(cid, html, target, goal, vhook):
    # With the goal `expect`: the goal gate sees it unmet -> the step fails -> the
    # agent does NOT claim success. Silent failure avoided (nominal=False).
    nominal, verified = await _run(html, SubTask(action="click", target=target, expect=goal), vhook)
    assert nominal is False, f"{cid}: agent still claimed success on a goal-unmet action"
    assert verified is False  # the trap never reaches the goal either way


def test_dict_field_keeps_frozen_dataclasses_hashable():
    # Regression guard (review nit #1): a dict expect/goal on a frozen dataclass must
    # not break __hash__ — else a future set/dict-key/dedup throws only when populated.
    from app.agent.verify import Expectation

    hash(SubTask(action="click", target="x", expect={"text_visible": "y"}))
    hash(Expectation(goal={"text_visible": "y"}))


@pytest.mark.anyio
async def test_correct_action_with_expect_still_succeeds():
    # Guard against over-strict expectations: the RIGHT action whose goal IS met must
    # still succeed (no false failure). Click "Submit" -> "Submitted!" appears.
    html = (
        "<body><button onclick=\"o.innerText='Submitted!'\">Submit</button>"
        "<p id=o>idle</p></body>"
    )
    nominal, verified = await _run(
        html,
        SubTask(action="click", target="Submit", expect={"text_visible": "Submitted!"}),
        lambda p: _sel_text_eq(p, "#o", "Submitted!"),
    )
    assert nominal is True and verified is True
