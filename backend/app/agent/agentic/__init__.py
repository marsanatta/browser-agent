"""Agentic (LLM-in-loop) executor support package.

Ported from browser-pilot's pure-skill policy (pilot/cdp.py, verify_gate.py,
agent.py). Kept in its own package so the LLM-driven loop's filtered perception,
deterministic locate cascade, and verification gate do NOT collide with
browser-agent's own perceive/locate/verify (which back the plan-then-execute
Executor). The agentic loop operates on the Playwright `page` the BrowserProvider
supplies — never connect_over_cdp.
"""
