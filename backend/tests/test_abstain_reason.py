"""expect_abstain must not credit ANY ask_user. ask_user fires on the bot-wall
route AND on generic local-exhaustion; an abstain task tagged `abstain_reason:
blocked` is only VERIFIED when a bot-wall was actually hit (`rec.blocked`).
Default / `impossible` keep the old outcome-only scoring.

Pure, offline: exercises the harness scoring helper directly (no browser, no
Copilot). Also confirms the loader accepts + validates the new field.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.harness import score_abstain
from eval.loader import load_tasks


def test_blocked_abstain_requires_real_block():
    # asked + honest non-claim, but NO bot-wall -> generic exhaustion -> NOT verified.
    assert score_abstain("blocked", asked=True, nominal=False, blocked=False) is False
    # asked + honest non-claim + a real bot-wall -> correctly verified.
    assert score_abstain("blocked", asked=True, nominal=False, blocked=True) is True


def test_blocked_abstain_still_needs_asked_and_not_nominal():
    assert score_abstain("blocked", asked=False, nominal=False, blocked=True) is False
    assert score_abstain("blocked", asked=True, nominal=True, blocked=True) is False


def test_default_and_impossible_keep_outcome_only_scoring():
    for reason in (None, "impossible"):
        assert score_abstain(reason, asked=True, nominal=False, blocked=False) is True
        assert score_abstain(reason, asked=False, nominal=False, blocked=False) is False
        assert score_abstain(reason, asked=True, nominal=True, blocked=False) is False


def test_google_steam_task_is_tagged_blocked():
    tasks = load_tasks(
        Path(__file__).resolve().parents[2] / "eval" / "eval_set" / "live_real_world.yaml"
    )
    google = next(t for t in tasks if t.id == "live_google_search_steam")
    assert google.expect_abstain is True
    assert google.abstain_reason == "blocked"


def test_bad_abstain_reason_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "tasks:\n"
        "  - id: x\n"
        "    instruction: i\n"
        "    start_url: http://u\n"
        "    domain: d\n"
        "    task_type: action\n"
        "    difficulty: single\n"
        "    expect_abstain: true\n"
        "    abstain_reason: nonsense\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_tasks(bad)
