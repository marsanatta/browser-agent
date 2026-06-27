"""Offline unit tests for the eval-set loader: schema validation + held-out ratio."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.loader import load_tasks, select_splits


def _write_split_yaml(tmp_path):
    p = tmp_path / "split.yaml"
    p.write_text(
        "tasks:\n"
        "  - {id: d1, instruction: i, start_url: 'http://a', domain: x, task_type: action,\n"
        "     difficulty: single, split: dev, key_nodes: [], assert: {url_contains: a}}\n"
        "  - {id: h1, instruction: i, start_url: 'http://b', domain: x, task_type: action,\n"
        "     difficulty: single, split: holdout, key_nodes: [], assert: {url_contains: b}}\n"
        "  - {id: s1, instruction: i, start_url: 'http://c', domain: x, task_type: action,\n"
        "     difficulty: single, split: sealed, key_nodes: [], assert: {url_contains: c}}\n"
        "  - {id: legacy, instruction: i, start_url: 'http://d', domain: x, task_type: action,\n"
        "     difficulty: single, held_out: true, key_nodes: [], assert: {url_contains: d}}\n",
        encoding="utf-8",
    )
    return p


def test_split_parsing_and_held_out_derivation(tmp_path):
    by_id = {t.id: t for t in load_tasks(_write_split_yaml(tmp_path))}
    assert by_id["d1"].split == "dev" and by_id["d1"].held_out is False
    assert by_id["h1"].split == "holdout" and by_id["h1"].held_out is True
    # sealed is "unseen" too, so held_out is derived True
    assert by_id["s1"].split == "sealed" and by_id["s1"].held_out is True
    # legacy held_out:true with no split -> derived to holdout
    assert by_id["legacy"].split == "holdout" and by_id["legacy"].held_out is True


def test_bad_split_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "tasks:\n"
        "  - {id: x, instruction: i, start_url: u, domain: d, task_type: action,\n"
        "     difficulty: single, split: train, key_nodes: [], assert: {url_contains: a}}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_tasks(bad)


def test_select_splits_seals_off_sealed_by_default(tmp_path):
    tasks = load_tasks(_write_split_yaml(tmp_path))
    # default: dev + holdout only, sealed EXCLUDED (cannot leak into a routine run)
    routine = select_splits(tasks)
    assert {t.id for t in routine} == {"d1", "h1", "legacy"}
    assert all(t.split != "sealed" for t in routine)
    # explicit final pass: ONLY sealed
    final = select_splits(tasks, include_sealed=True)
    assert {t.id for t in final} == {"s1"}


def test_eval_set_loads_and_is_modest():
    tasks = load_tasks()
    assert 12 <= len(tasks) <= 60  # modest now; upper bound headroom for autoresearch growth


def test_held_out_at_least_20_percent():
    tasks = load_tasks()
    held = [t for t in tasks if t.held_out]
    assert len(held) / len(tasks) >= 0.20
    # held-out site must be one never used in dev (quotes.toscrape.com)
    assert all("quotes.toscrape.com" in t.start_url for t in held)


def test_every_task_has_assertion_and_key_nodes():
    for t in load_tasks():
        if t.expect_abstain:
            # abstain tasks are scored by outcome (asked AND not nominal), not by a
            # page-state assertion, so they legitimately carry no assert/key_nodes
            assert not t.assertion, f"{t.id} expect_abstain should have no assert"
            continue
        assert t.assertion, f"{t.id} missing assertion"
        assert t.key_nodes, f"{t.id} missing key nodes"


def test_expect_abstain_task_present_and_assert_optional():
    tasks = load_tasks()
    abstain = [t for t in tasks if t.expect_abstain]
    assert abstain, "expected at least one expect_abstain task"
    assert all(not t.assertion for t in abstain)


def test_domains_and_types_are_diverse():
    tasks = load_tasks()
    assert len({t.domain for t in tasks}) >= 3
    assert {"action", "retrieval", "side_effect"} & {t.task_type for t in tasks}
    assert "side_effect" in {t.task_type for t in tasks}  # for pass^k


def test_unique_ids():
    tasks = load_tasks()
    assert len({t.id for t in tasks}) == len(tasks)


def test_bad_primitive_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "tasks:\n"
        "  - id: x\n"
        "    instruction: i\n"
        "    start_url: u\n"
        "    domain: d\n"
        "    task_type: action\n"
        "    difficulty: single\n"
        "    key_nodes: []\n"
        "    assert: {not_a_primitive: 1}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_tasks(bad)
