"""Load + validate the eval set (data, not code).

Keeps the eval set declarative so adding a task never touches harness code. The
loader enforces the schema so a malformed assertion fails fast at load, not mid-run.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_VALID_TYPES = {"action", "retrieval", "side_effect"}
_VALID_PRIMITIVES = {
    "url_contains", "text_contains", "h1_equals", "selector_text_equals", "iframe_text_equals"
}

EVAL_SET_PATH = Path(__file__).resolve().parent / "eval_set" / "tasks.yaml"


@dataclass(frozen=True)
class EvalTask:
    id: str
    instruction: str
    start_url: str
    domain: str
    task_type: str
    difficulty: str
    held_out: bool
    key_nodes: list[dict[str, Any]] = field(default_factory=list)
    assertion: dict[str, Any] = field(default_factory=dict)
    # When True the correct outcome is to abstain (ask_user) rather than reach a
    # page state. Scored by outcome (asked AND not nominal), not by `assert`, so
    # `assert` is optional. This is what lets the harness score correct refusals
    # as success instead of as a plain failure.
    expect_abstain: bool = False
    # A task that is GREEN on the current code tests nothing about today's gaps, but
    # guards against future regressions. Flag it so the harness keeps it OUT of the
    # headline success rate (it would only inflate it) while still running it.
    regression_anchor: bool = False


def _validate_primitive(where: str, spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict) or len(spec) != 1:
        raise ValueError(f"{where}: must be a single-key primitive, got {spec!r}")
    (kind, value), = spec.items()
    if kind not in _VALID_PRIMITIVES:
        raise ValueError(f"{where}: unknown primitive {kind!r} (valid: {_VALID_PRIMITIVES})")
    if kind == "selector_text_equals":
        if not isinstance(value, dict) or "css" not in value or "value" not in value:
            raise ValueError(f"{where}: selector_text_equals needs {{css, value}}, got {value!r}")
    if kind == "iframe_text_equals":
        if not isinstance(value, dict) or not {"frame", "css", "value"} <= value.keys():
            raise ValueError(f"{where}: iframe_text_equals needs {{frame, css, value}}, got {value!r}")


def load_tasks(path: Path | str = EVAL_SET_PATH) -> list[EvalTask]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    items = raw["tasks"]
    seen: set[str] = set()
    tasks: list[EvalTask] = []
    for it in items:
        tid = it["id"]
        if tid in seen:
            raise ValueError(f"duplicate task id: {tid}")
        seen.add(tid)
        if it["task_type"] not in _VALID_TYPES:
            raise ValueError(f"{tid}: bad task_type {it['task_type']!r}")
        for node in it.get("key_nodes", []):
            _validate_primitive(f"{tid}.key_nodes", node)
        expect_abstain = bool(it.get("expect_abstain", False))
        # inline_html builds a controlled data: URL fixture (a deterministic page
        # the agent really perceives/locates/clicks) so a task can reproduce an
        # exact DOM structure - e.g. a silent wrong-pick - without depending on a
        # flaky live site. It just becomes the task's start_url.
        inline_html = it.get("inline_html")
        start_url = it.get("start_url")
        if inline_html:
            start_url = "data:text/html," + urllib.parse.quote(inline_html)
        elif not start_url:
            raise ValueError(f"{tid}: needs start_url or inline_html")
        assertion = it.get("assert") or {}
        if assertion:
            _validate_primitive(f"{tid}.assert", assertion)
        elif not expect_abstain:
            raise ValueError(f"{tid}: 'assert' is required unless expect_abstain is true")
        tasks.append(
            EvalTask(
                id=tid,
                instruction=it["instruction"],
                start_url=start_url,
                domain=it["domain"],
                task_type=it["task_type"],
                difficulty=it["difficulty"],
                held_out=bool(it.get("held_out", False)),
                key_nodes=list(it.get("key_nodes", [])),
                assertion=assertion,
                expect_abstain=expect_abstain,
                regression_anchor=bool(it.get("regression_anchor", False)),
            )
        )
    return tasks
