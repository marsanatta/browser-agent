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
_VALID_ABSTAIN_REASONS = {"blocked", "impossible"}
_VALID_SPLITS = {"dev", "holdout", "sealed"}
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
    # Why the correct outcome is to abstain. "blocked" = a bot-wall must actually be
    # hit (scored asked AND not nominal AND blocked), so a generic local-exhaustion
    # ask_user does NOT count. "impossible"/None keep the outcome-only scoring.
    abstain_reason: str | None = None
    # A task that is GREEN on the current code tests nothing about today's gaps, but
    # guards against future regressions. Flag it so the harness keeps it OUT of the
    # headline success rate (it would only inflate it) while still running it.
    regression_anchor: bool = False
    # Three-way generalization split (eval-expansion plan). dev = drives engine changes
    # (RCA'd per-case); holdout = selection keep-gate (scored every round, never RCA'd);
    # sealed = the once-only honest final metric, scored a single time at the very end and
    # never used for any keep decision. Splits are disjoint BY SITE.
    split: str = "dev"
    # The DISTINCT capability or failure-mode this case exists to test (e.g. intent_drift_decoy,
    # modal_handling, synonym_locate, loginwall_abstain). Makes the set self-documenting and
    # lets the harness report purpose coverage; redundant same-purpose-same-site filler is out.
    purpose: str = ""


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
        abstain_reason = it.get("abstain_reason")
        if abstain_reason is not None and abstain_reason not in _VALID_ABSTAIN_REASONS:
            raise ValueError(
                f"{tid}: bad abstain_reason {abstain_reason!r} "
                f"(valid: {_VALID_ABSTAIN_REASONS})"
            )
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
        # `split` is authoritative when present (it derives held_out); else fall back to
        # the legacy `held_out` bool (held_out -> holdout, otherwise dev). Sealed and
        # holdout are both "unseen" so both set held_out=True.
        split = it.get("split")
        if split is not None:
            if split not in _VALID_SPLITS:
                raise ValueError(f"{tid}: bad split {split!r} (valid: {_VALID_SPLITS})")
            held_out = split in {"holdout", "sealed"}
        else:
            held_out = bool(it.get("held_out", False))
            split = "holdout" if held_out else "dev"
        tasks.append(
            EvalTask(
                id=tid,
                instruction=it["instruction"],
                start_url=start_url,
                domain=it["domain"],
                task_type=it["task_type"],
                difficulty=it["difficulty"],
                held_out=held_out,
                key_nodes=list(it.get("key_nodes", [])),
                assertion=assertion,
                expect_abstain=expect_abstain,
                abstain_reason=abstain_reason,
                regression_anchor=bool(it.get("regression_anchor", False)),
                split=split,
                purpose=str(it.get("purpose", "")),
            )
        )
    return tasks


def select_splits(tasks: list[EvalTask], *, include_sealed: bool = False) -> list[EvalTask]:
    """Filter tasks for a run. SEALED is the once-only final set: it is EXCLUDED unless
    `include_sealed` is explicitly True, so sealed tasks can never leak into a routine
    dev/holdout run. With `include_sealed=True` ONLY sealed tasks are returned (the final
    pass scores them in isolation, then they are never touched again)."""
    if include_sealed:
        return [t for t in tasks if t.split == "sealed"]
    return [t for t in tasks if t.split in {"dev", "holdout"}]
