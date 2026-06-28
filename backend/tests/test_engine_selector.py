"""The executor ENGINE is selected by AGENT_MODE at construction time. The default MUST be
the LLM-in-loop AgenticExecutor (adopted after the head-to-head in
research/executor-ab-plan-mode-vs-llm-in-loop.md); only AGENT_MODE=script-orchestration
selects the legacy plan-then-execute Executor. These tests LOCK the default so a future
change can't silently flip it back, and confirm the two are independent same-interface
engines (an engine selector, not a runtime fallback)."""

from app.agent.agentic_executor import AgenticExecutor
from app.agent.executor import Executor
from app.main import _build_executor

_MODELS = dict(
    plan_model="x", exec_model="claude-haiku-4.5", replanner_model="x",
    plan_effort="low", exec_effort="low", replanner_effort="low",
)


def test_default_engine_is_agentic(monkeypatch):
    monkeypatch.delenv("AGENT_MODE", raising=False)
    assert isinstance(_build_executor(None, **_MODELS), AgenticExecutor)


def test_script_orchestration_selects_legacy_engine(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "script-orchestration")
    assert type(_build_executor(None, **_MODELS)) is Executor


def test_unknown_agent_mode_stays_agentic(monkeypatch):
    # Only the exact "script-orchestration" string opts out; anything else is agentic.
    monkeypatch.setenv("AGENT_MODE", "plan")
    assert isinstance(_build_executor(None, **_MODELS), AgenticExecutor)
