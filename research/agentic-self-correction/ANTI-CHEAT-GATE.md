# Anti-cheat gate — round-3 mechanism experiments (MUST follow)

The same agent authors the eval probes (`mechanisms.yaml`) AND implements the mechanisms
that should pass them. That is a conflict of interest, and it already bit us once: #3a named
the diagnostic's renamed/hidden labels in the prompt, and #4a named two live tasks' exact
`url_contains` answer-keys. These gates exist so it cannot happen again. **No mechanism is
kept unless every gate below passes.**

## G-FREEZE — probes frozen before code
`mechanisms.yaml` is committed BEFORE any mechanism implementation commit (git history is the
proof). The probe set is a MEASURE, never an evolve target — the code is implemented from the
mechanism's PRINCIPLE, then measured once. No "tweak code → rerun probe → tweak" loop. The
evolve target stays the real live dev set.

## G-LEAK — zero probe vocabulary in any diff
Before keep, `grep` every code/prompt diff for probe-specific tokens: markers (`A2_OK`,
`B1_OK`, `C1_PRODUCT_OPENED`, …), labels (`Authenticate`, `Fetch results`, `Deluxe Widget`,
`Go`, …), and structural specifics. Must be ZERO. This is the exact mechanical check that
catches the #3a/#4a class.

## G-LIVE — the real arbiter is the set I did NOT author
`live_real_world.yaml` is pre-existing and READ-ONLY. A mechanism counts only if it
improves (or does not regress) the LIVE set — especially the real failure it targets
(③ must help `vat_rates`; ② must not regress live cost). The synthetic probes only MOTIVATE
and diagnose; live VALIDATES. A mechanism that wins on my probes but not live is exposed as
probe-flattering and is discarded.

## G-INDEP — an independent context does the check I can't
A fresh-context subagent (no implementation context) adversarially reviews (a) the probe set
for self-flattering / strawman design and (b) each mechanism diff for leakage and overfit,
BEFORE keep. Findings are addressed, not waved off.

## G-NULL — honest null results, objective cost
If a mechanism does not help, that is the finding — reported, not goalpost-moved. The ②
cost numbers (Copilot calls, input_tokens, nano_aiu) are objective ground truth reported
whether or not they confirm the prior "index-all regresses cost" prediction.

## Carry-over (unchanged from prior rounds)
- AGENTIC-only; never touch `executor.py` (legacy) or the frontend.
- Deterministic verify gate stays the success oracle; never an LLM judge.
- eval `harness.py`/`scoring.py`/`verify`/`live_real_world.yaml` are READ-ONLY.
- Offline pytest gate stays green before any keep.
