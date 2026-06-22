"""Independent verification layer for the M3 eval harness.

The agent's self-report is NEVER trusted (eval/01 §4, eval/02 §F4). This package
re-derives task success from OBSERVABLE browser state:

  state_check / key_node_check  programmatic state assertion on the live page
                                (REAL state-diff style, architecture/03 §3.2)
  consistency_check             Semantic-Entropy-style: run an extraction n times
                                and flag disagreement (eval/02 §B3/F4)

SEAMS (clearly marked, not built in M3): SVDD trajectory anomaly trip-wire
(eval/01 §4.2), Inspect AI sandbox harness, and full REAL replica integration.
See `seams.py`.
"""

from eval.verify.consistency import ConsistencyResult, consistency_check
from eval.verify.state import key_node_check, state_check

__all__ = [
    "state_check",
    "key_node_check",
    "consistency_check",
    "ConsistencyResult",
]
