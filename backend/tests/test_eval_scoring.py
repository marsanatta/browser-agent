"""Offline unit tests for the M3 scoring math. No Copilot, no browser.

Ground truth is hand-computed independently of the production formula (the rule:
each assertion would FAIL on an off-by-one). Synthetic trajectories only.
"""

import math
import sys
from pathlib import Path

# eval/ lives at repo root, one level above backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval import scoring
from eval.scoring import TaskResult


def _t(tid, nominal, verified, hit, total, task_type="action", held_out=False):
    return TaskResult(tid, nominal, verified, hit, total, task_type, held_out)


def test_task_tcr_partial_credit():
    # 3 of 5 key nodes -> 0.6 exactly. Off-by-one would give 0.4 or 0.8.
    assert scoring.task_tcr(_t("a", True, False, 3, 5)) == 0.6
    assert scoring.task_tcr(_t("b", True, True, 5, 5)) == 1.0
    assert scoring.task_tcr(_t("c", False, False, 0, 5)) == 0.0


def test_task_tcr_no_nodes_falls_back_to_verified():
    assert scoring.task_tcr(_t("a", True, True, 0, 0)) == 1.0
    assert scoring.task_tcr(_t("b", True, False, 0, 0)) == 0.0


def test_tcr_mean_across_tasks():
    # tcr values 0.6, 1.0, 0.0 -> mean = 1.6/3
    rs = [_t("a", True, False, 3, 5), _t("b", True, True, 5, 5), _t("c", False, False, 0, 5)]
    assert abs(scoring.tcr(rs) - (1.6 / 3)) < 1e-9


def test_tsr_is_verified_fraction_not_nominal():
    # 4 tasks, 1 verified. nominal=True on all -> TSR must be 0.25, NOT 1.0.
    rs = [
        _t("a", True, True, 1, 1),
        _t("b", True, False, 0, 1),
        _t("c", True, False, 0, 1),
        _t("d", True, False, 0, 1),
    ]
    assert scoring.tsr(rs) == 0.25


def test_silent_failure_gap_counts_nominal_true_verified_false():
    # 3 of 4 are nominal-success-but-unverified -> gap = 0.75.
    rs = [
        _t("a", True, False, 0, 1),   # silent failure
        _t("b", True, False, 0, 1),   # silent failure
        _t("c", True, False, 0, 1),   # silent failure
        _t("d", True, True, 1, 1),    # honest success, not silent
    ]
    assert scoring.silent_failure_gap(rs) == 0.75


def test_silent_failure_gap_ignores_honest_failures():
    # nominal=False & verified=False is an HONEST failure, not silent.
    rs = [_t("a", False, False, 0, 1), _t("b", False, False, 0, 1)]
    assert scoring.silent_failure_gap(rs) == 0.0


def test_pass_hat_k_all_runs_must_verify():
    runs = {
        "ok":   [_t("ok", True, True, 1, 1), _t("ok", True, True, 1, 1), _t("ok", True, True, 1, 1)],
        "flaky":[_t("f", True, True, 1, 1), _t("f", True, False, 0, 1), _t("f", True, True, 1, 1)],
    }
    # only 1 of 2 tasks passed ALL 3 runs -> pass^3 = 0.5
    assert scoring.pass_hat_k(runs) == 0.5


def test_pass_hat_k_excludes_single_run_tasks():
    runs = {"single": [_t("s", True, True, 1, 1)]}
    assert scoring.pass_hat_k(runs) == 0.0  # no task had >=2 runs


def test_mean_se_bernoulli():
    # 2 of 4 verified -> p=0.5, SE = sqrt(0.25/4) = 0.25
    rs = [_t("a", True, True, 1, 1), _t("b", True, True, 1, 1),
          _t("c", True, False, 0, 1), _t("d", True, False, 0, 1)]
    p, se = scoring.mean_se(rs)
    assert p == 0.5
    assert abs(se - 0.25) < 1e-9


def test_mean_se_zero_variance():
    rs = [_t("a", True, True, 1, 1), _t("b", True, True, 1, 1)]
    p, se = scoring.mean_se(rs)
    assert p == 1.0 and se == 0.0
