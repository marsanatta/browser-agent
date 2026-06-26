# Author Round-2 Autoresearch Plan (review doc, do NOT execute)

- **Datetime:** 2026-06-25 19:17:54
- **Summary:** Author the round-2 autoresearch plan as a review-only document — a focused delta from round-1 (same discipline, new breadth-driven frontier) — written to research/autoresearch-round-2-plan.md without executing or touching code.

## Prompt

> round 1 is merged and analyzed — time to author the round-2 plan. same as before: author it as a review DOC (i'll read it, you execute only after it passes), don't execute or touch code yet. write it to research/autoresearch-round-2-plan.md.
>
> this is a focused DELTA from round-1, not a full re-author — keep the exact same discipline (the three independent metrics M1/M2/M3, the guards G1-G3 incl. planner.py untouched + state.py assertion frozen + offline gate green network-free, the deterministic-test-anchored keep rule, one probe per iteration, plan-time-name-don't-fix, keep/discard + document-discards, the ~25-iter bound). baseline is the NEW main (round-1 already merged: lazyload fixed, breadth at 7) — re-measure the three signals on it first.
>
> round-2 frontier — the climbable headroom is BREADTH and the new ground-time failures it surfaces:
> - push the live tier toward ~15-20 distinct real domains (round-1 reached 7). diverse categories — shopping, news, gov, docs, maps, finance, reference, media — cap any single domain, each a page-specific verifier with zero text_contains, bot-walls routed to abstain.
> - each new real site tends to surface a new failure CLASS. fix the GROUND-TIME ones (grounded then failed later) exactly the round-1 way: anchored on a deterministic offline test reproducing the specific failure, the live flip as corroboration only. NAME the plan-time ones.
> - the named ceilings stay strictly OFF-LIMITS — name them, never fix: the planner open-loop B2 (including the modal M3=1 silent failure, which is planner-rooted), iframe-piercing, the search-box-strategy ceiling, and bot-walls (route-don't-evade). never touch planner.py, never weaken a state.py assertion, and M3 must NOT rise (a new silent failure is an automatic discard, like amazon in round-1).
>
> execution later runs in a fresh isolated worktree off the new main, writes findings to research/autoresearch-round-2-findings.md + an append-only research/round-2-progress.json (same schema as round-1), merges back after my review, never pushed — spell that out in the plan.
>
> i'll review it against the same bar: every metric independent, guards protect the gate + planner, the keep rule anchors on a deterministic test not a lucky live flip, stop conditions real, scope bounded, discards documented. write the plan doc, don't execute. /save-prompt

## What I Did

- **Merged round-1 first** (prior step, prerequisite): fast-forwarded `autoresearch/round-1` into `main` (verified the untracked plan copy was byte-identical before dropping it), confirmed offline gate 113 green / network-free + planner.py + state.py untouched, then folded the round into `ANALYSIS.md` (§4 CuP correction to M3=1, new §6) — committed locally, not pushed.
- **Re-measured the round-2 baseline from the merged authoritative snapshot** (no execution): M1 = 9/12 = 0.750 (`eval/REPORT.md`), M2 = 7 distinct domains (counted from `live_real_world.yaml` start_urls), M3 = 1 (`eval/AUDIT.md` flag tally — the lone SILENT_FAILURE is `live_internet_modal`, planner-rooted). Confirmed the M2 domain list and M3 tally with read-only `grep`, not a live run.
- **Authored `research/autoresearch-round-2-plan.md`** as a review doc only — did NOT execute, did NOT touch code. Structured as a focused delta from round-1's plan: §0 baseline (new main, carried named ceilings, the round-1 methodology lesson baked in = read M3 from a full-tier re-run never from touched tasks), §1 loop, §2 frontier + three independent metrics with the round-2 M3 invariant (baseline 1 = floor, must NOT rise; modal carried-never-chased), §3 guards G1-G3 (offline gate ≥113) + the verify-path sub-clause, §4 per-iteration scope (Probe B breadth as primary with a concrete category-grouped candidate pool flagged clean-vs-likely-bot-wall; Probe A ground-time fixes from ANALYSIS §5 candidates; plan-time = name-don't-fix), §5 keep/discard (M3-no-rise as cardinal discard), §6 stop conditions (breadth target ~15-20 + named-ceiling tail + plateau + 25-iter cap), §7 human checkpoints, §8 fresh worktree off new main / findings + append-only progress.json same schema / merge-after-review / never pushed, §9 self-check against the review bar.
- **Did not commit** the plan (authoring is the job; the user reviews before execution). Ran `/save-prompt` as the final explicit step.
