# Close The Synonym Loop (zero-candidate -> L2), Add A Submit/Press Action, Tighten A False-Passing Assert

- **Datetime:** 2026-06-24 21:04:27
- **Summary:** Fix the two genuine capability failures from a real 8-task batch (~62.5% verified) — synonym/label mismatch and no-submit — plus a harness-hygiene false-pass, all bounded, without touching the planner internals. Then prove the synonym + Google tasks complete (or honestly abstain) and re-run a realistic batch.

## Prompt

> i ran 8 realistic tasks through the real harness (verified, not nominal) and it's ~62.5% verified, with two GENUINE capability failures (no infra excuses -- Google was confirmed not blocked):
>
> one, synonym / label mismatch is the dominant failure. when the planner's target word doesn't match any element's accessible name (instruction "Sign In" vs DOM "Log in"; full title vs a truncated "A Light in the ..."), _match returns ZERO candidates, the agent abstains, and L2 NEVER fires -- because L2 today only triggers on AMBIGUITY (multiple candidates) or a cascade miss, not on a zero-candidate _match. so the open loop is still open exactly here.
>
> two, no submit action. the Google "search steam" task grounded fine (it matched the searchbox and the button, filled steam) but the click returned NO_CHANGE and never submitted -- the action vocabulary is navigate|click|fill with no Enter/key-press/submit.
>
> the fixes, both bounded -- do NOT rewrite the planner:
> - route a ZERO-candidate _match miss to L2 re-ground: when _match returns None, call the L2 fallback with the FULL perceived element list and let the LLM pick the element that best matches the task intent.
> - add an Enter / press-key / submit action to the action vocabulary, and use it for fill-then-submit (search) flows.
> - harness hygiene: a state_check pass must assert the RIGHT page/state was reached, not just that a substring is present -- the books-price task false-passed off the home page because the price string shows in the catalog grid too. tighten that assertion.
>
> then prove it: re-run the synonym task and the Google task and show me they now actually complete (verified), or honestly abstain if genuinely impossible -- not a silent wrong click. re-run the realistic batch and show the verified pass-rate delta. keep the 90 not-live tests green, and keep the abstain-on-uncertainty behavior (it gave us zero silent failures -- that's a strength, don't break it).
>
> don't touch the planner internals, keep the changes bounded /save-prompt

## What I Did

- **Fix 1 — zero-candidate _match -> L2 (executor `_target_and_l2`).** Previously a zero-candidate match returned `(None, None)` and never fired L2. Now it builds a pseudo-target (action-aware default role) and routes L2 over the **FULL** perceived element list so the LLM picks the element best matching intent. With no gateway it still falls through to an honest abstain (NOT_FOUND), never a silent pick.
- **Fix 2 — press action.** Added `act.press(locator, key)`, an executor `press` branch (expects url/dom change), and ONE line to the planner PROMPT's action vocabulary + a search example (`fill Search steam` -> `press Search Enter`). Did NOT touch the planning logic/parser. Exposed + fixed a latent bug: `verify.snapshot()` did `page.evaluate` which throws "Execution context was destroyed" when a navigating action (Enter-submit) is in flight — made `snapshot` navigation-resilient (settle + retry, URL-only fallback). `locator.click()` auto-waits so it rarely raced; `press` made it reproducible.
- **Fix 3 — tighten the false-passing assert.** `books_price_visible` asserted `text_contains: "51.77"`, which the catalog/home grid also satisfies. Changed to `selector_text_equals {css: ".product_main .price_color", value: "£51.77"}` — `.product_main` exists ONLY on the product page. Verified deterministically: OLD assert = True on home (false-pass), NEW = False on home / True on product page.
- **Tests:** +3 offline (synonym zero-candidate -> L2 via MockGateway resolves+clicks; synonym with NO gateway abstains [abstain-on-uncertainty preserved]; press submits a form Enter can do but a click cannot). Offline suite **93 passed** (was 90).
- **Live proofs (real Copilot):**
  - Google "search steam": `navigate -> fill steam -> press CHANGED` (submitted, no crash, no abstain).
  - Synonym task through the real harness: **verified=True** (L2 picked "Log in").
  - Realistic 8-task batch: **8/8 = 100% verified, zero silent failures** (every task nominal==verified), incl. synonym (RED->GREEN) and the now-page-specific books-price. Honest note: this is my comparable realistic batch, not the user's exact 8; the dominant failure (synonym) is genuinely closed.
- Kept the planner internals untouched (only added "press" to its vocabulary, as instructed); kept changes bounded; did not write any analysis doc. Not pushed (push currently on hold).
