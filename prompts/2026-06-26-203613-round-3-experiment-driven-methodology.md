# Round-3 Methodology: Implement the Flow, Then Prove with Before/After

- **Datetime:** 2026-06-26 20:36:13
- **Summary:** Structure Round 3 as (1) design+implement the grounded spec (updated replan/memory/staleness flow), then (2) design+run experiments comparing before/after verified accuracy; keep only what passes — evaluate the methodology and merge it into the plan.

## Prompt

> i feel this autoresearch round3 is in this way, 1. design and implement what you ground for the spec now for the updated flow then 2. to first design and test several experiements and compare before/after to see if accuracy really improve. evaluate this, merge into the plan if pass. /save-prompt

## What I Did

- **Evaluated the methodology: PASS** — it is the project's eval-driven Modify→Verify→Keep/Discard discipline (implement → prove with before/after on the independent check → keep only real improvement). Added two refinements (constructive push-back, not blockers):
  1. **Implement in independently-measurable pieces** (peek-replan / memory-prewarm / staleness-self-heal as separate experiments) so a kept change is *attributable* and dead complexity isn't shipped — a single whole-flow before/after is confounded.
  2. **Before/after must cover the FULL live tier + M3, not just the 5 targets** (a change that flips a target green but breaks a working task = net discard), and because the targets are flaky-live, anchor each experiment on a deterministic offline test (noise-immune keep signal) + repeat the live measurement 2–3×.
- **Merged it into `research/round-3-plan.md`** (full rewrite), now covering: the goal (target failing tasks verify); the two locks (capability/files free; `state_check`/M3/verified-flip honesty gates unchanged); the **§2 experiment-driven methodology**; the spec to implement (§3a peek-the-page replan flow, §3b memory v1 = one SQLite file with the weighted-matrix justification + event-log-lite, §3c the staleness self-heal strategy); a concrete **§4 before/after experiment table** (E1 peek-replan, E2 memory pre-warm, E3 staleness self-heal, each with a deterministic anchor + live corroboration); §5 keep/discard; §6 guards; §7 time-box; §8 `/autoresearch`-driven execution in a fresh worktree, never pushed.
- Did NOT execute / touch product code — plan only; will show before executing, then run via `/autoresearch` on approval.
