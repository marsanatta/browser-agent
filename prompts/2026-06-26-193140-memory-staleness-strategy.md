# Memory Staleness Strategy (sites update → memory goes stale)

- **Datetime:** 2026-06-26 19:31:40
- **Summary:** A key requirement for the agent memory: websites update so stored memory goes stale — design a proper staleness strategy, where peeking the page during replan detects the drift, concludes the memory is stale, and switches to treating it the fresh way.

## Prompt

> and note one of the keypoint is the website could update so the memory could stale, must consider this. and design a proper strategy to deal with this. e.g. when replan one of the strategy is it finds there is existing memory, but when it peek the website it finds it change, then it will guess that the memory stale and will start to treat it refresh way /save-prompt

## What I Did

- Designed a layered, self-healing staleness strategy (to fold into the Round-3 memory design), with the non-negotiable rule that a stale memory must NEVER become a silent failure:
  - **(A) Passive demotion (0 LLM):** recency decay on `last_success_ts` (half-life ~7–14 days, since sites redeploy on days/weeks) × Wilson lower-bound success-rate; `verify-after-act NO_CHANGE` on a memory-sourced locator is the existing "site changed" signal (`fail_count++`, `last_outcome=no_change`); hard TTL floor. `score = recency × success_rate` → low score = don't pre-warm/trust.
  - **(B) Active drift detection — peek as the detector (the user's point):** store a cheap `page_fingerprint` (AX-role histogram + `(role,name)`-set digest, or DOM-hash à la Stagehand) per memory record. During replan's peek step: a deterministic 0-LLM pre-check (does memory's `(role,name)` still resolve? did the fingerprint diverge past a threshold?) plus the LLM's judgment from the live peek ("nav redesigned; 'Licenses' is now 'Licensing' in a menu") → conclude STALE.
  - **(C) On stale → treat fresh + self-heal:** hard-demote/invalidate that entry, switch to fresh mode (ignore the stale memory; full cascade + L2 + LLM live-peek strategies, re-ranked by success probability); on a VERIFIED success, write-back the new working strategy + reset fingerprint + bump `last_success_ts` → the memory self-heals (learns the post-redeploy locator). The old strategy is not deleted (it stays in the append-only `episode` log; the projection just supersedes it).
  - **(D) Honesty guard:** the independent `state_check` + verify-after-act remain the arbiter; memory success/fail is always recorded from the VERIFIED outcome, never `nominal`; a stale-locator "looks done but verified=False" is caught and recorded as a fail, so M3 does not rise (the project's CuP doctrine applied to memory).
- Tied it to existing code (reuse #4's `LocatorCache.invalidate` + `verify.py`'s `NO_CHANGE`), and the schema add (`page_fingerprint` column on `locator_memory`/`episode`; staleness is a computed score, not a stored boolean).
- This composes with the peek-the-page replan flow (peek feeds both "generate fresh strategies" and "detect stale"). No code changed this turn — design only; to be incorporated into `research/round-3-plan.md` when I rewrite it.
