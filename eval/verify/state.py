"""Programmatic state assertions on the live page — independent ground truth.

The arbiter now lives in the shipped backend package (`app.verify.state`) so the
deployed `/agent/run` can goal-verify with the SAME deterministic check the eval
harness uses (the eval package is not shipped in the container). This module
re-exports it unchanged so the harness and its tests keep importing from here.
"""

from app.verify.state import key_node_check, state_check

__all__ = ["state_check", "key_node_check"]
