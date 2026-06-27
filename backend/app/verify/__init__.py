"""Independent deterministic state assertions on the live page.

`state_check` is the single arbiter shared by the M3 eval harness AND the
production `/agent/run` goal-verification path (when the caller supplies a
success criterion). It lives in the shipped `app` package so the deployed
backend can import it; `eval/verify/state.py` re-exports it so the eval harness
and its tests keep the same import surface. The agent's self-report is NEVER
trusted (eval/01 §4): success is re-derived from OBSERVABLE browser state.
"""

from app.verify.state import key_node_check, state_check

__all__ = ["state_check", "key_node_check"]
