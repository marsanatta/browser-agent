# Phase B — Round 1: Honest-Goal-Criterion (silent-failure) — REJECTED with evidence

Failure-driven engine-improvement loop on the curated live set (eval-expansion off main).
Honesty gates frozen; worktree-local; never pushed. Engine fix experimented in worktree
`ba-goal` (branch `fix/agent-goal-criterion`, off main 4f920d8); measured by cherry-pick
onto `eval-expansion` and reverted on rejection. Raw per-case data: `phase_b_dev_round{0..3}.json`.

## Baseline (round 0): dev 35/39 verified (89%), M3 silent = 3/39 (8%)
Silent failures (nominal=True, verified=False) — the agent claimed success without achieving
the goal:
- `wikipedia_oxygen_search` (supported retrieval) — reached a wrong page, claimed done.
- `wikipedia_watchlist_abstain` (login wall) — 1-step navigate to Special:Watchlist ->
  login redirect; claimed done.
- `wikipedia_signup_captcha_abstain` (captcha wall) — claimed done without reaching/abstaining.
(`internet_iframe` fails too but HONESTLY — asked=True — a known locator-can't-pierce-iframe gap.)

## RCA (deterministic, traced in real code)
`nominal = all_ok` = "all planned actions executed", NOT "goal achieved". A goal gate exists
(`verify_after_act` on `expect.goal`) but (a) the planner omits the goal (prompt made `expect`
optional), and (b) the **navigate path never checked `expect.goal`** (only click/press did).
First-principles: the agent self-check (`expect{goal}`/`_goal_satisfied`) and the independent
eval arbiter (`state_check`) are DELIBERATELY separate (the nominal-vs-verified gap = the
silent-failure metric; merging them destroys it). So the only honest lever is the planner
reliably emitting an accurate self-goal.

## Fix experimented + 3 measured iterations
Executor: navigate path now gates on `expect.goal` (symmetric with click/press) — proven
RED->GREEN deterministically (`test_goal_criterion_navigate.py`), offline gate 192 green.
Planner prompt iterated to make it emit the task-completion goal.

| round | prompt | dev verified | M3 | what happened |
|---|---|---|---|---|
| 0 | baseline | 35/39 | 3 | oxygen/watchlist/signup silent |
| 1 | "emit task-completion goal" | 34/39 | 3 | broke `modal` (mixed-case text goal vs UPPERCASE render); fixed nothing |
| 2 | "prefer DISCRIMINATING url_contains" | 35/39 | 2 | **fixed oxygen**; still broke `modal` (text goal on a read-task) |
| 3 | "+ omit goal for read-on-page tasks" | 34/39 | 2 | oxygen fixed; modal STILL broke; **NEW** break `books_sapiens_stock` |

## Verdict: REJECT (reverted)
No iteration produced a clean, no-regression win — each prompt change just **shifts which
passing case breaks** (modal -> modal -> modal+sapiens_stock). The planner cannot reliably
emit accurate, discriminating goal predicates a-priori. This is the **B2 planner-open-loop
ceiling**, conclusively demonstrated over 3 controlled iterations.

Two structurally distinct sub-causes, both unfixable by a-priori planner goals:
1. **Wall overclaim (watchlist, signup)** — the wall MIMICS success: the logged-out
   `Special:Watchlist` redirects to `...UserLogin?returnto=Special:Watchlist`, so the target
   token appears in BOTH the wall's text AND its URL. No positive a-priori predicate
   discriminates success from the wall.
2. **Predicate fragility (modal, sapiens_stock)** — guessed text/value predicates mis-state
   case/phrasing/timing -> false failures on previously-passing cases.

## Honest conclusion / direction
Agent-level `nominal` honesty via planner-emitted goals is NOT reliably achievable by
prompt-tuning. The system is already honest at the layer that matters: the INDEPENDENT
verifier (`verified`) catches every silent failure, M3 MEASURES the residual, and the
production fix (main `e45d612`) never displays "verified" without an independent goal check.
A genuine agent-level fix would need a goal source NOT guessed a-priori (observed-state
grounded, or task-semantic wall detection that separates "task wants the login page" from
"task wants something behind it") — a larger open problem, not a prompt tweak.
