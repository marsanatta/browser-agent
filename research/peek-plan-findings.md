# Peek-Plan Round — Findings (powered + paired)

Execution per research/peek-plan-round-plan.md v2. Worktree off main c814cca.
Two locks: capability free; honesty gates frozen (state_check arbiter, M3 must not rise,
keep only on a measured improvement with SEPARATED intervals, never nominal). Never pushed.

## Step 0 — setup
- Worktree off c814cca. Implemented peek-plan as a RUNTIME TOGGLE (Executor.peek_plan + start_url; blind keeps plan-before-launch byte-identical; peek does launch->navigate->perceive->plan_with_observation). planner.py: _PEEK_PLAN_PROMPT + plan(observation=); MockPlanner peek_subtasks + plan_calls. harness: _run_once(peek_plan=), RunRecord.replanned (from REPLAN in the reduced trace). main _StartUrlPlanner kept consistent.
- Deterministic anchor test_peek_plan.py = 2 passed (blind misses absent element + no observation; peek navigates/perceives/grounds -> success, observation reached plan()).
- Runner peek_paired.py (resumable JSONL): PAIRED interleaved blind/peek per task; single-page k=5 (5 silent_* + modal + lazyload/hackernews/example), multi-step k=8 (pydocs, wikipedia search/signin/helium). Analysis peek_analyze.py: Wilson CI per arm, paired McNemar Δverified + interval separation, 2x2 cost {blind-replanned}x{single/multi}, modal probe, M3.

## Step 1 — offline gate (regression check) then paired runs
- Offline gate 177 passed (blind byte-identical). Paired runner launched.
- EARLY SIGNAL (n=1, silent_modal_dismiss pair0): blind nominal=F verified=T REPLANNED calls=4 AIU=29.9 ; peek nominal=T verified=T calls=1 AIU=7.7 -> peek ~4x cheaper + cleaner (blind paid plan+replan; peek one grounded call). Powered run in progress to confirm with separated intervals.

## PAIRED RESULT (154 runs, k=5 single / k=8 multi) — TRUSTWORTHY
Verified-rate (paired McNemar / paired-diff 95% CI — the correct test for the paired design;
per-arm Wilson CIs touch/overlap but the paired test SEPARATES):
- ALL:    peek-only-win 18 vs blind-only 3, Δ=+0.19, CI [+0.08,+0.31] -> SEPARATES (p~0.001)
- single: 9 vs 2, Δ=+0.16, CI [+0.01,+0.30] -> separates
- multi:  9 vs 1, Δ=+0.25, CI [+0.06,+0.44] -> separates
Cost (AIU/task): ALL blind 10.7 vs peek 8.9 (Δ-1.8, peek net CHEAPER). 2x2 {blind-replanned?}x{single/multi}:
- first-try-success: peek slightly MORE (+0.5..+2.5, the always-paid observation tokens)
- needed-replan:     peek MUCH cheaper (-7.6..-9.7, avoids plan+replan double-pay)
- replan-rate 0.34->0.17 ; calls/task 1.92->1.23
Modal probe (named): blind silent 4/5 (verified 0/5) -> peek silent 0/5 (verified 5/5) -> CLEARED.
M3 (paired): 0.208 -> 0.078 (thirds the silent-failure rate). 1/154 transient planner-JSON error.

CONCLUSION (pending full-tier M3): peek-plan is a KEEP — net cheaper, verified-rate up with
separated paired intervals, M3 down, modal cleared. Blind-plan does NOT save cost; the only
cell where peek costs more is easy first-try-success (small, +1-2.5 AIU).

## FULL-TIER M3 (1 run/arm, 21 tasks) — honest aggregate (fix 5)
- blind: M3(silent)=1/21=0.048 (silent = live_internet_modal), verified=16/21
- peek:  M3(silent)=0/21=0.000 (ZERO silent), verified=18/21
- per-task: peek FIXED modal + archive_login + stackoverflow (+3); REGRESSED openlibrary_login
  (blind v=T -> peek v=F, single-run -> FLAG, needs paired confirmation, not conclusive). Net +2 verified, M3 0.

## DECISION: KEEP (clear, trustworthy win)
Decision matrix: AIU <= baseline (net cheaper, replan-avoidance dominates) AND verified-rate UP
with SEPARATED paired-difference intervals (ALL/single/multi) AND M3 NOT up (it DROPPED 0.048->0,
paired 0.208->0.078) AND the named modal probe CLEARED (4/5 silent -> 0/5, 0->5/5 verified).
- Answers your headline question: blind-plan does NOT save cost; peek-plan is net cheaper.
- The ONLY cell where peek costs more: easy first-try-success (+1..2.5 AIU, the always-paid observation).
HONEST FLAGS: (1) openlibrary single-run regression — confirm with a paired run before trusting.
(2) peek sees only the FIRST page (multi-page partial), yet multi-step gained the most (replan-rate 0.38->0).
(3) 1/154 transient planner-JSON error.
