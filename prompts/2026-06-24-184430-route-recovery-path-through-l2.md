# Route Recovery Path Through L2 + Re-prove The Three Grounding Behaviors

- **Datetime:** 2026-06-24 18:44:30
- **Summary:** Close the last grounding gap (recovery-path `_current_locator` didn't route through L2), re-prove the three ambiguity behaviors on the full code, keep the offline suite green, and commit — so the value already built actually counts for a grader who clones the repo.

## Prompt

> day 2 for the browser repo. today is about realizing the value you've already built, not building new things, because a grader clones the repo and reads the code so anything uncommitted scores zero. so the goal is simple: finish the last grounding gap, prove it works, and commit everything.
>
> context: the L2 re-ground and the _match ranking are already implemented but uncommitted. the one hole left is the recovery path, _current_locator (executor.py around 284-289) calls locate() without l2_fallback, so when the agent re-perceives after a failed step it doesn't get the L2 fallback. route that path through L2 too.
>
> then prove it for real, show me the actual outcome on each, don't tell me "should work":
> - google.com, type steam, then "click the Google Search button" resolves and clicks the right button, or honestly abstains. not NOT_FOUND.
> - silent_wrong_pick_readmore through the real harness, right pick or abstain, no silent CuP.
> - a substring case where the target resolves to a single wrong element, no longer silently clicks the wrong one.
> and run the full suite, the 84 not-live tests must stay green.
>
> done means: those three behave correctly, 84 green, and it's all committed (L2 wiring, _match rank, the reground fix, the tests) with a clear message. uncommitted = doesn't exist, so commit is the finish line.
>
> only after that's committed, and only if there's real time left, hand-add 3-4 locator-stress eval tasks (author them yourself, no loop): a synonym-label one where the instruction word differs from the dom accessible name, an inline_html fixture with a js-rendered name or a randomized id, fill the empty multi_cross_domain tier with one cross-page task, and one real side_effect beyond login so pass^k means something. acceptance for each new task: it must actually go RED on the current code, otherwise tag it a regression-anchor and keep it out of the headline rate. green-on-day-one tests nothing.
>
> don't write the analysis doc today, that's day 3 against the final state, and don't touch the planner /save-prompt

## What I Did

- **Reconciled the premise honestly:** the L2 wiring, the `_match` change, the `_cascade`, and the tests were NOT uncommitted — they were already committed + pushed yesterday as `01a5c5d`. (Also: the dead `_match` ranking was *removed* yesterday after review, not kept.) The genuine remaining hole was exactly the one named: `_current_locator` resolved without `l2_fallback`.
- **Fix (executor.py only):** extracted a shared `_target_and_l2(perception, st)` helper (maps a sub-task to `(target, l2_fallback)`, building the pseudo-target on genuine ambiguity) and used it in BOTH `_attempt` (action path) and `_current_locator` (recovery path). Now recovery re-perception routes through L2 / honest abstain. No behavior change when no gateway is wired, so offline tests are unaffected. Did not touch the planner.
- **Proved all three with real runs (actual outcomes, not "should work"):**
  - A (substring single wrong pick): `_match('log')` -> `target=None, ambiguous=['Login Page','Login','Blog login']` (old code returned `candidates[0]='Login Page'`); executor run `nominal=False, asked=True, silent_clicks=0` -> abstains, never clicks the wrong link.
  - B (silent_wrong_pick_readmore via the REAL harness, live Copilot): `nominal=False, verified=False, asked=True`, SILENT_CuP=False. 18 Copilot calls (up from 10 — recovery now also fires L2, the fix at work).
  - C (google, live): typed 'steam' (`fill -> CHANGED`), then `ask_user` (`asked=True`, no error) — honest abstain; google has two same-named "Google Search" buttons, so it refuses to guess. Per-attempt `NOT_FOUND` is the internal failure class; the run-level outcome is the explicit abstain. Never silently clicked.
- **Regression:** offline suite `pytest -m "not live"` = 90 passed (the "84" baseline + the 6 ambiguity/heal tests added yesterday). Live suite unaffected.
- **Committed** the recovery fix as `4dd5ab3` with a clear message. (Local commit; not yet pushed — flagged that a remote-cloning grader needs the push.)
- **Eval expansion (after the commit, user said "do it now"):** added a `regression_anchor` flag (loader + harness `summarize` excludes anchors from the headline TSR/CuP/pass^k + report marks them) and 4 hand-authored locator-stress tasks, each LIVE-verified through the real harness to decide RED vs anchor:
  - `synonym_label_signin_vs_login` -> **RED (headline)**: instruction "Sign In" vs DOM "Log in"; literal `_match` misses -> honest abstain (verified=False). Exposes the synonym/semantic-mapping gap.
  - `js_rendered_label_continue` -> GREEN -> regression_anchor (perceive reads JS-rendered labels).
  - `cross_domain_books_then_internet` -> GREEN -> regression_anchor (fills the previously-empty multi_cross_domain tier; cross-domain navigation works, 2/2 key-nodes).
  - `side_effect_contact_form_submit` -> GREEN -> regression_anchor (3-step form mutation; task_type=side_effect for pass^k). Honest note: it's reliably GREEN, so pass^k over it is ~1 — it does NOT add headline pass^k signal; the only genuine RED today is the synonym task.
  - 19 tasks total (16 headline + 3 anchors), held-out ratio 0.316, full offline suite 90 passed. Did not write any analysis doc; did not touch the planner.
