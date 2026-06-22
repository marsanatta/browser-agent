"""SEAMS — verification layers designed-for but NOT built in M3.

These are honest placeholders. They raise NotImplementedError so nothing silently
passes; wiring them is future work, scoped here so the architecture is explicit.
"""

from __future__ import annotations

from typing import Any


def svdd_trajectory_anomaly(trajectory: list[Any]) -> float:
    """SEAM (eval/01 §4.2): SVDD trip-wire trained on NORMAL traces only; flags
    drift/cycles. Needs a corpus of normal trajectories to fit the one-class
    boundary — not collected in M3. Path features (tool-call sequence, unique
    call count, total steps) are the documented high-importance inputs."""
    raise NotImplementedError("SVDD trajectory anomaly is an M3 seam (eval/01 §4.2)")


def inspect_ai_task(task: dict[str, Any]) -> Any:
    """SEAM (eval/02 §D1): wrap each eval task as an Inspect AI Task for sandbox
    isolation + built-in SE computation. M3 uses a direct harness; the Inspect
    adapter is future work."""
    raise NotImplementedError("Inspect AI adapter is an M3 seam (eval/02 §D1)")


def real_replica_state_diff(task: dict[str, Any]) -> bool:
    """SEAM (architecture/03 §3.2): full REAL integration — local-storage state
    diff against deterministic replicas via the agisdk. M3 asserts against live
    seed sites instead; the REAL replica harness is future work."""
    raise NotImplementedError("REAL replica state-diff is an M3 seam (architecture/03 §3.2)")
