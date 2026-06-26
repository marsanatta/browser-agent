# Round-3 Reframe: Free Capability, Unchanged Honesty Gates

- **Datetime:** 2026-06-26 19:01:26
- **Summary:** Rewrite the Round-3 plan as a free, time-boxed capability round to make the currently-failing real tasks actually pass — lifting ALL file/scope locks while keeping ALL the measurement/honesty gates (independent state-check frozen, M3 must not rise, keep only on a real verified-flip).

## Prompt

> i reviewed research/round-3-replan-plan.md. the diagnosis is right (the replan really is a context-free no-op, i re-verified executor.py:128-138 myself) and unfreezing planner.py is the right call. but the plan is too narrow for what i actually want now — i want this round to go FREE, not be a single bounded change. we don't have much time, so chase the real goal directly.
>
> so rewrite the round-3 plan with this reframe. the goal isn't "fix the replan" — it's the broader thing: make the real tasks that currently fail actually pass — the flaky multi-step / search-box / synonym ones (python deep-nav, wikipedia search/login, google multi-step) AND the gnu_licenses click-grounding case that fails 0/5 silently. close-the-loop replan is just one tool toward that, not the whole round.
>
> here's the key thing, and i want you to get the distinction exactly right because it's the whole point. there are two kinds of "lock" in this plan and they are NOT the same:
>
> lift all of these (scope/file locks) — go free: no off-limits files. you may touch planner.py, locate.py, act.py, perceive.py, executor.py, anything. you may make as many capability changes as the goal needs, not one. drop the "#3/#7/#8 are out of scope" line — if they help the failing tasks pass, do them. pursue the goal however the code needs it.
>
> keep all of these (the measuring instruments) — do NOT lift them, and don't treat them as "restrictions on what you can build": the independent staverified/not-verified — you do NOT editthe verifier or its assertion to make things pass (that's grading your own exam). M3 (silent-failure count) must NOT rise — a replan/heal that confidently produces a wrong-but-plausible plan (nominal=True, verified=False) is an automatic discardhis round must not introduce. keep achange ONLY if it shows a real independent verified-flip (state-check, never nominal); discard anything whose only "win" is a number with no independte the discard down as a hard gap.
>
> the reason i'm drawing this line hard: we spent all of today cleaning up exactly the opposite mistake — offline gate green + breadth looked "converged", then every easy task failed live. a free autoresearch that also drops the honesty gates just manufactures fake wins faster. so: "what you can touch" = wide open; "how  you prove it helped" = unchanged and no
>
> practical stuff: work in a fresh worktree off the latest main, move fast (time-boxed), keep the offline gate green and network-free, log what you trearch/round-3-findings.md +
> progress.json, review before merge, nev just-the-replan, and don't touchstate.py's assertion or the state_check to chase a pass. when you've rewritten the plan, show me the new version before you start executing. /save-prompt

## What I Did

- Rewrote the Round-3 plan as `research/round-3-plan.md` (removed the superseded `round-3-replan-plan.md`).
- Made the **two-locks distinction §1 the centre of the plan**, exactly as asked:
  - **LIFTED (capability/scope/files):** no off-limits files — `planner.py`/`locate.py`/`act.py`/`perceive.py`/`executor.py`/`verify.py`/`recover.py`/prompts all fair game; as many capability changes as the goal needs; the previously-deferred items (#3 predict-then-verify, #7-full expected-url, #8-full observe-first, D2 substring tradeoff, press-Enter submit, close-the-loop replan, planner-sees-page) are IN SCOPE if they help a target task pass.
  - **KEPT (measuring instruments, not build-restrictions):** `eval/verify/state.py` assertion + `state_check` are the frozen arbiter (never edited/retuned to make a task pass — "grading your own exam"); **M3 must not rise** (a confident wrong-but-plausible plan = `nominal=True, verified=False` = automatic discard); keep a change ONLY on a real independent **verified-flip** (state-check, never nominal); discard any number-only win and write it down as a hard gap; offline gate green/network-free (≥143); never pushed.
- Stated the **goal as the bar**: make python deep-nav, wikipedia search-submit, wikipedia Sign-In synonym, google multi-step, and gnu Licenses click **reproducibly verify** (2–3×) on the independent check.
- Carried the **why** verbatim in spirit: today we cleaned up the opposite mistake (green gate + "converged" breadth, then everything failed live; hollow verification) — so capability is free but the honesty proof is unchanged.
- Practical: fresh worktree off `f1165d4`, time-boxed, log to `research/round-3-findings.md` + append-only `round-3-progress.json`, review before merge, never push.
- **Did NOT execute** — per the instruction, the plan is presented for review first. No code touched this turn.
