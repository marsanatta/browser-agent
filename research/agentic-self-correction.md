# Autoresearch findings — agentic engine self-correction

Branch `agentic/llm-loop-improvement` (off `main` `c04d20d`). Targets the **agentic**
LLM-in-loop engine only; legacy `executor.py` untouched. Not pushed.

## What was the gap

The engine already had strong **self-maintenance** (ASSIGNMENT.md sense: detect UI/selector
changes → adjust locators) via the 7-tier locate cascade + per-action re-grounding (no
selector cache → UI class/id changes don't break it). The gap was **self-correction**
(diagnose the cause on failure → try a *different strategy*): a filtered `observe` returns
empty when the control is renamed/hidden, and the skill told the agent to give up after 2
misses — so it looped tactically and never stepped back to change approach.

## Changes (all agentic-only, surgical)

| # | change | ASSIGNMENT axis | file |
|---|---|---|---|
| #3a | on a locate miss, do ONE **wide (unfiltered) observe** before giving up; block-abstain stays immediate | self-correction (+ extends self-maintenance to renamed/hidden) | `agentic/skill.py` |
| #2 | distinguish **AMBIGUOUS vs ABSENT** on a miss → different agent message (disambiguate vs wide-observe) | self-correction (diagnose cause → different strategy) | `agentic_executor.py` |
| #1 | **stagnation** detect (3× same action+target) → SOFT strategy nudge, never force-finish | self-correction (retry→strategy-switch ladder, deterministic) | `agentic_executor.py` |
| #4a | verify must be **discriminating + two-signal AND**, no pre-action token | silent-failure prevention | `agentic/skill.py` |
| #4b | production caller criterion into the **finish gate** (eval-clean) — the amazon wrong-page fix | silent-failure prevention / correctness | `agentic_executor.py`, `main.py` |
| #0 | controlled **diagnostic set** (12 inline_html probes, 4 sealed) + `passk_diag.py` k-loop runner (pass^k + per-purpose + bootstrap CI), `harness.py` untouched | eval-set depth / measurement (#5,#6) | `eval/eval_set/diagnostic.yaml`, `eval/passk_diag.py` |

## Measured result (independent ground truth, never self-report)

| | pass^k | false_success (CuP) | cost |
|---|---|---|---|
| baseline (before) | 0.875 (7/8) | 0 | 170 calls |
| after #3a | 1.000 | 0 | 146 calls |
| after #2+#4a+#1 | 1.000 | 0 | 150 calls |
| **sealed (once-only, held-out)** | **1.000 (4/4)** | **0** | $0.14 |

- The one failing case (`hidden_menu`) was fixed; the expensive recovery (`renamed` 14→6
  calls) got cheaper → **total cost DOWN** (self-correction that is cost-positive).
- Guards held every iteration: offline gate green (220), G2 cost non-regression, G3
  abstain-correctness non-regression. The first #3a attempt **bled into abstain**
  (false_success 0→1, the documented iter3 failure mode) — the diagnostic caught it and it
  was reworked before keeping.

## Honest validity caveat

- **Internal validity: strong.** dev 0.875→1.0, sealed 4/4 (generalizes to unseen
  same-class perturbations, not memorized pages), 0 silent failures, cost down, all guards
  green.
- **External validity: UNPROVEN.** The diagnostic is a small **self-built** probe — I wrote
  both the test and the fix, so passing it is internal validity only. The probe has
  **converged at 1.0**, so it can no longer measure further gains. The remaining honest step
  is one **live dev-39 run** (the plan's real evolve target) to confirm the mechanism helps
  real sites and the cost stays flat (G2). Until then these are "validated on a controlled
  probe", not "proven on the live metric".
- #4b verified by offline gate + a wiring test + code trace; the full live amazon replay is
  deferred (flaky/costly).

## Not done (deliberate)

- **#7** runtime impossible/excluded flag — plan-deferred (touches judgment).
- **Live dev-39 external-validity run** — a money decision left to the user.
