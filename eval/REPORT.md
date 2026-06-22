# M3 Eval Report

Generated from a REAL run on 2026-06-22 12:55 UTC. Metrics are computed by independent
programmatic assertions on the live page (eval/01 §4) — never the agent's
self-report. Per the ablation rule (architecture/03 §4) a budget-matched vanilla
baseline (max_attempts=1, no L2 heal) runs alongside the full agent.

- Tasks: 12 (4 held-out on quotes.toscrape.com, a site
  never used in dev — generalization test, eval/01 §5.3)
- Approx Copilot calls (this run): **28**
- Wall time: 343s
- Held-out TSR: 1.000

## Headline metrics

| metric | agent | budget-matched baseline |
|---|---|---|
| TCR (key-node completion) | 1.000 | 1.000 |
| TSR (task success) | 0.917 +/- 0.080 | 0.917 +/- 0.080 |
| silent-failure gap (CuP) | 0.000 | 0.000 |
| pass^3 (side-effect tasks) | 1.000 | n/a |

Definitions: TCR = mean key-nodes hit per task (partial credit); TSR = fraction
of tasks whose independent assertion passed; silent-failure gap (CuP) = fraction
where the agent claimed success but verification failed; pass^k = fraction of
side-effecting tasks that verified on ALL 3 runs (reliability, eval/02 §C1).
SE is Bernoulli sqrt(p(1-p)/n) — independent-item; clustered SE would be larger
because tasks share sites (eval/02 §C2).

## Per-task results

| task | type | held-out | key-nodes | agent verified | baseline verified | nominal | silent? |
|---|---|---|---|---|---|---|---|
| internet_form_auth_nav | action |  | 1/1 (100%) | PASS | PASS | PASS |  |
| internet_login_page_reached | action |  | 2/2 (100%) | PASS | PASS | PASS |  |
| internet_login_submit | side_effect |  | 1/1 (100%) | PASS | PASS | PASS |  |
| internet_dropdown_nav | action |  | 1/1 (100%) | PASS | PASS | PASS |  |
| internet_checkboxes_nav | action |  | 1/1 (100%) | PASS | PASS | PASS |  |
| books_open_light_in_attic | retrieval |  | 1/1 (100%) | FAIL | FAIL | FAIL |  |
| books_open_travel_category | action |  | 1/1 (100%) | PASS | PASS | PASS |  |
| books_price_visible | retrieval |  | 1/1 (100%) | PASS | PASS | PASS |  |
| quotes_open_einstein_author | retrieval | yes | 1/1 (100%) | PASS | PASS | PASS |  |
| quotes_einstein_born_location | retrieval | yes | 2/2 (100%) | PASS | PASS | PASS |  |
| quotes_open_login | action | yes | 1/1 (100%) | PASS | PASS | PASS |  |
| quotes_tag_love | action | yes | 1/1 (100%) | PASS | PASS | PASS |  |

## What is REAL vs SEAM

REAL (run in this report):
- Full agent loop (perceive/locate/act/verify) via the Copilot-backed LLM planner.
- Independent programmatic state assertion on the live final page (`eval/verify/state.py`).
- Nominal-vs-verified silent-failure gap (CuP).
- Consistency check (`eval/verify/consistency.py`) — unit-tested; a Semantic-
  Entropy-style sampling signal (run extraction n times, flag disagreement).
- Budget-matched vanilla baseline column.
- pass^3 for side-effecting tasks.

SEAM (designed-for, not built — `eval/verify/seams.py`, raise NotImplementedError):
- SVDD trajectory-anomaly trip-wire (needs a normal-trace corpus; eval/01 §4.2).
- Inspect AI sandbox adapter (eval/02 §D1).
- Full REAL deterministic-replica state-diff via agisdk (architecture/03 §3.2).
- Hidden-state Semantic Entropy Probe (Copilot gateway exposes no logits; we ship
  the sampling approximation instead — eval/02 §B3).

## Honest caveats

- n=12 is far below the ~1,000 items needed to detect a 3% delta at 80%
  power (eval/02 §C2). These numbers are directional, not statistically powered —
  the SE columns make the uncertainty explicit.
- Live seed sites can change or rate-limit; a task FAIL may be a site change, not
  an agent regression. Re-run to distinguish.
- The judge/LLM is used only for PLANNING here; success is graded programmatically,
  so judge bias does not enter the headline metrics.
- Key-node TCR counts a checkpoint hit if it was observable at ANY step
  (step_hook), matching WebCanvas trajectory semantics.
