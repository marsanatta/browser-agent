"""Honesty: the report's "REAL (run in this report)" block must not list the
Consistency check — it is built & unit-tested but NOT wired into the harness run,
so it belongs under a separate "BUILT & UNIT-TESTED, NOT WIRED" heading.

Renders the real report module with minimal synthetic data (no browser, no LLM).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval import report as report_mod


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def test_real_block_has_no_consistency_check(tmp_path, monkeypatch):
    out = tmp_path / "REPORT.md"
    monkeypatch.setattr(report_mod, "REPORT_PATH", out)

    summary = {
        "agent_tcr": 0.0, "agent_tsr": 0.0, "agent_tsr_se": 0.0, "agent_cup": 0.0,
        "baseline_tcr": 0.0, "baseline_tsr": 0.0, "baseline_tsr_se": 0.0, "baseline_cup": 0.0,
        "passk": 0.0, "held_out_tsr": None, "n": 0, "n_held_out": 0,
        "n_regression_anchors": 0, "regression_anchors_verified": 0, "copilot_calls": 0,
    }
    data = {"agent": [], "baseline": [], "passk_runs": {}, "k": 3, "copilot_calls": 0}

    report_mod.write_report([], data, summary, 1.0)
    body = out.read_text(encoding="utf-8")

    real_block = _between(body, "REAL (run in this report):", "BUILT & UNIT-TESTED")
    assert "Consistency check" not in real_block
    # it still appears in the report, under the not-wired heading
    assert "BUILT & UNIT-TESTED, NOT WIRED" in body
    assert "Consistency check" in body
