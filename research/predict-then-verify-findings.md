# predict-then-verify — findings (eng-pipe)

Goal: fix silent failures (nominal=True ∧ verified=False), with a RELIABLE verification
of effectiveness, more silent-failure cases, and no regression to the existing eval set.

## What was built
- **Mechanism** (backward-compatible / opt-in): `SubTask.expect` (planner-declared
  goal) → `Expectation.goal` → `verify_after_act` GATE (a declared goal must hold, else
  NO_CHANGE) with an INDEPENDENT in-loop `_goal_satisfied` (text_visible / selector_visible
  / url_contains), deliberately separate code from the eval `state_check`.
- **5 silent-failure eval cases** (`tasks.yaml`, inline_html): modal-dismiss,
  wrong-similar-element, premature-success, navigated-away, overlay-dismiss.
- **Reliable deterministic verification** (`test_predict_then_verify.py`): per pattern a
  CONTROL (no expect → nominal=T,verified=F = silent reproduced) + a FIX (expect →
  nominal=F = silent avoided), + a positive case (correct action + expect still succeeds)
  + a frozen-dataclass dict-hash regression guard. **Offline gate: 175 passed, network-free.**
- Independent fresh-context review: APPROVE-WITH-NITS; all 4 nits fixed (dict-hash trap,
  empty-goal over-strict, multi-key AND, test-side independence).

## Reliable result (deterministic) — the MECHANISM works
When a correct goal `expect` is present, predict-then-verify catches the silent failure
on all 5 patterns (12/12 tests). Backward-compatible: no goal → behavior byte-identical,
existing tests unaffected.

## Honest result (live) — effectiveness NOT yet demonstrated
Live M3 did **not** drop with either prompt:
- Conservative (opt-in) prompt: no regression (wikipedia/lazyload/hackernews all pass),
  but premature/overlay/modal stay silent — the planner often **omits** `expect`.
- Directive prompt: still 2/5 silent AND introduced over-strict false-failures
  (modal-dismiss verified T→F, wikipedia signin nominal T→F). Reverted.

**Root cause (traced):** the planner emits `expect` **a-priori, before seeing the page**,
so for cases whose success text is not predictable ("results appear") it either omits the
goal (no catch) or guesses it wrong (false failure). predict-then-verify's *planner-emitted*
variant is bounded by a-priori goal predictability.

## Disposition
- **Proven + safe foundation:** mechanism correct, deterministically verified, no
  regression. Ship-able as a foundation; does NOT yet reduce live silent failures.
- **Do NOT claim live effectiveness** — not demonstrated.
- **Next design (future):** derive the goal from OBSERVED post-action state instead of
  a-priori prediction (peek-then-goal, tied to the peek-replan), and/or a deterministic
  executor-derived expect for known patterns (modal/overlay). That is where live M3 should
  actually move; this change is the foundation it builds on.
