# Audit: Claimed-Working vs Actually-Functional (10-agent panel)

**Date:** 2026-06-26
**Method:** 10 independent read-only auditor agents, identical mission — read the intended flow
(DESIGN.md / ANALYSIS.md / module docstrings), then walk the code function-by-function with concrete
execution traces, and report only **claim-vs-reality gaps** (a function/flow that reads as working but is a
no-op, stub, mis-wired, context-free, dead, failure-masking, or silently weaker than its claim). Honestly
disclosed seams (`NotImplementedError`, the ANALYSIS §4 WRONG_PAGE gap) and the four already-known issues
(replan no-op, prod no `verify_hook`, open-loop planner, autocomplete-submit) were excluded from new
findings.

**"Conf." = how many of the 10 agents independently found it.** Severity is the panel consensus.
**Status** is filled by the human-led re-verification pass (don't trust the agents, especially low-conf).

> Unifying root cause: the agent's **self-reported** signals (per-step `CHANGED`, `REGROUND`/`REPLAN`
> events, TCR, `expect_abstain` "verified") are wired to weak or absent observations. The **only** thing that
> actually catches errors is the task-level independent `state_check` — which production `/agent/run` does
> not even wire in. Strip the theater and the real reliability surface is one independent post-state
> assertion: present in eval, absent in prod.

---

## Findings (ranked)

| # | Finding | Conf. | Sev | Evidence | Status |
|---|---|---|---|---|---|
| 1 | **`consistency_check` is dead code, falsely listed under "REAL (run in this report)"**. DESIGN §6 sells "3 stacked silent-failure signals"; only `state_check` runs (SEP is an honest seam; consistency is built+unit-tested but never called). `report.py` hardcodes it in the REAL block of a report that claims it "never fabricates." | 10/10 | CRIT | `consistency.py:37` (zero callers in `harness.py`/`run_live_tier.py`); `report.py:99-101` | _re-verify_ |
| 2 | **`expect_abstain` scored "verified" on ANY `ask_user`, not on block-detection.** `verified = asked and not nominal`; `ask_user` fires on the bot-wall route AND on generic local-exhaustion — so "couldn't find the search box" is credited as a correct route-don't-evade abstain. `blocked` is computed but unused. Hollows the route-don't-evade eval proof. | 1/10 | HIGH | `harness.py:176-179`; `ask_user` at `executor.py:120` and `:141` | _re-verify_ |
| 3 | **click/press per-step verify-after-act is a near-tautology.** The element-specific `target_effect` channel is wired only for `fill`; click/press diff the whole-body `innerHTML` hash → any churn = CHANGED. Repo's own `silent_wrong_pick_readmore` fixture: clicking the WRONG link → CHANGED → nominal=True; only task-level CuP catches it. | 4/10 | HIGH | `executor.py:308,311`; `verify.py:159-162` | _re-verify_ |
| 4 | **`REGROUND` hardcodes `progressed=True`.** "Retry only on a NEW observation" guard never fires for NOT_FOUND (the commonest failure); re-perceives the same static page up to 4× and fires up to 4 identical L2 LLM calls (dents the "0-token / LLM-out-of-hot-path" cost claim). Does NOT cause false success (ends in honest ask_user). | 4/10 | HIGH | `executor.py:336-337` | _re-verify_ |
| 5 | **confirm-before-submit gate wired to `fill` (never submits), absent on `press`/`click` (which do).** Gated with a hardcoded constant `kind="fill"`; `"submit"` action never emitted (dead). Masked today by autopilot-approve default; inverts the safety claim the moment a real hook is added. | 5/10 | HIGH (latent) | `act.py:15`; `executor.py:289-291` vs `:306-311` | _re-verify_ |
| 6 | **TCR is wrong three ways.** (a) `text_contains` over full body checked after `navigate` → passes from the landing page before the agent acts; (b) zero-key-node `expect_abstain` rows score 1.0; (c) `step_hook` runs only at sub-task boundaries, missing transient states — not "ANY point" as claimed. | 3/10 | HIGH | `scoring.py:43-46`; `state.py:43-46`; `harness.py:119-123` | _re-verify_ |
| 7 | **`navigate` has NO verify-after-act at all.** Yields `_Outcome(True)` after only `detect_block`; never checks landed URL, yet emits `verdict=CHANGED`. (Deeper than the disclosed WRONG_PAGE classification gap.) | 2/10 | MED | `executor.py:174-186` | _re-verify_ |
| 8 | **`perceive().markdown` (AgentOccam observe-first) is dead output.** Computed every step, read by nobody, reaches no LLM; and only `<table>` is rendered — the "lists" half is never implemented. | 2/10 | MED | `perceive.py:66,131-148` (no `.markdown` reader) | _re-verify_ |
| 9 | **`classify_exception` collapses to `STALE_TIMING`.** Stale-hint branch and fallthrough both return it; documented 4-class taxonomy is really 2-class; an ambiguity/strict-mode error gets a no-op state-wait. No UNKNOWN class. | 2/10 | MED | `classify.py:72-79` | _re-verify_ |
| 10 | **`init_observability()` is a no-op skeleton.** No TracerProvider/Langfuse/spans; deps declared but unused; the "trajectory store feeding the anomaly trip-wire" doesn't exist. (Semi-disclosed in the docstring; DESIGN presents it as first-class.) | 3/10 | MED | `tracing.py:116-130` | _re-verify_ |
| 11 | **L2 ships only its middle stage.** DESIGN's "fingerprint(LCS+attr)→LLM re-rank→vision"; only re-rank exists, with no seam marker (unlike the honest `NotImplementedError` seams). | 1/10 | MED | `locate.py:225-262` | _re-verify_ |

### Minor (doc overstatement, not hollow code)
- REPORT.md "never a loose `text_contains`" is true only of the **live** tier; the **sandbox** tier (the
  headline `n`) uses `text_contains` finals (e.g. `tasks.yaml:149,237,258,321`). (auditor-4)

---

## ⚠️ Disputes — flag, do NOT resolve by vote (need a concrete test)

- **D1 — L2-heal cache poisoned?** Poisoned (auditors 3, 6: cached under the pseudo-target key, so a
  re-lookup rebuilds `get_by_role(name="Sign In")` → 0 → L2 re-fires) **vs** works (auditors 4, 7, 9).
  `test_l2_fallback.py:59` only asserts the entry *exists*, never that a 2nd `locate` makes **0** gateway
  calls. **Resolution: a two-call test** — `locate` a synonym target twice, assert the 2nd makes 0 gateway
  calls. (locate.py:225-262, the `_cascade(build_el=chosen, store_el=el)` line)
- **D2 — pseudo-target tier-2 `role` substring silent wrong-pick?** auditor-10 (`exact=False` substring
  match silently picks "Member Sign In Now" for "Sign In", bypassing L2/abstain) **vs** auditor-4
  (ambiguity→abstain is real, tier-2 reachable-not-dead). **Resolution: a fixture test** — pseudo-target
  "Sign In" on a page with a single "Member Sign In Now" control; assert abstain, not a silent pick.
  (locate.py:188-190 tier-2 `role` `exact=False`)

---

## Cleared as genuinely solid (panel cross-checked)
`redact()` (real, applied at SSE/serialization boundary) · `state_check` independent ground truth
(non-vacuous; empty assertion → False) · `silent_failure_gap`/CuP + `pass^k` math + budget-matched baseline
(`gateway=None`, `max_attempts=1`) · `detect_block` route-don't-evade on the **agent** side (the scoring
side is finding #2) · deterministic locator cascade + self-healing (`test_self_healing.py`).

---

## Honest note (this undercuts the autoresearch rounds)
Findings **#2 and #3 contradict things autoresearch rounds 1-2 reported as solid** — the route-don't-evade
"proof" (the rounds leaned on `expect_abstain` scoring that credits any `ask_user`) and the per-step
verification story. Those rounds optimized **breadth** and never audited whether the verification/recovery
**mechanisms** were real. In several places they aren't — and the hollowness was hiding *inside the
verification layer* the project sells as its differentiator.

---

## Re-verification & triage (2026-06-26, human-led)

All targeted (low-confirmation + disputed) findings were re-traced against the code. **None were false
alarms.** Both disputes resolved:
- **D1 (L2-heal cache) → POISONED is correct** (auditors 3,6 right; 4,7,9 wrong). `make_l2_fallback` caches
  the heal under `store_el=el` (the pseudo "Sign In") at `locate.py:256`; the 2nd `locate(el)` rebuilds
  `_build("role_name", el)` = `get_by_role(name="Sign In")` → 0 → invalidate → L2 re-fires. L2 heals never
  cache-hit → the "healed locator cached, hit = 0 token" claim is hollow.
- **D2 (pseudo-target tier-2 substring) → SILENT-PICK is real** (auditor 10 right; 4 wrong). Tiers 1-2 use
  `el.role`+`el.name` (NOT `attrs`); tier-2 `role` is `get_by_role(name=el.name)` with `exact=False`
  (substring), so pseudo "Sign In" resolves "Member Sign In Now" at tier 2, bypassing L2. The docstring's
  "empty attrs so the cascade misses / never a silent pick" (`executor.py:237-239`) is false.

### BUG → fix (this eng-pipe batch, TDD)
#1 consistency listed under REAL · #2 `expect_abstain` credits any `ask_user` · #4 REGROUND fake progress ·
#5 confirm-gate on `fill` not `press`/`click` · #6 TCR (exclude zero-key-node rows + soften the ANY-point
claim) · #7 navigate post-check (minimal: not-an-error landing) · #8 dead `perceive().markdown` compute · #9
`classify_exception` dead branch · #10 observability → seam (doc) · #11 L2 fingerprint/vision → seam (doc) ·
D1 L2-heal cache representation · D2 pseudo-target skips fuzzy deterministic tiers.

### NOT-A-BUG → Round-3 (needs experimentation; unifying root = the planner is open-loop)
#3 per-step verify-after-act for click (needs predict-then-verify) · #7-full expected-url diff (ANALYSIS §4:
naive wiring destabilizes the loop) · #8-full observe-first markdown actually fed to the LLM · D2-tradeoff
(re-add cheap substring heals with confidence scoring instead of always L2) · #6-data (key-node spec
redefinition in the YAML) · + the earlier **replan no-op**. **Round-3 charter: close the
perceive→predict→verify→replan loop.**
