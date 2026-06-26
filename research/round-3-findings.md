# Round-3 Findings (live)

Execution per research/round-3-plan.md. Worktree off main b9e9aca (per-role model+thinking
routing already merged). Two locks: capability free; honesty gates frozen (state_check is the
arbiter; M3 must not rise; keep only on a real verified-flip 2-3x; never nominal). Never pushed.

## Step 0 — prerequisites probe

- Prereqs OK: GH_TOKEN (account marsanatta) reaches Copilot live; network reaches targets (docs.python.org HTTP 200); live runner = `eval/run_live_tier.py`.
- Live `client.list_models()` returns 16 ids. Confirmed defaults valid: claude-opus-4.8, claude-haiku-4.5. CORRECTED stale fallback ids -> real ones are `gemini-3.1-pro-preview`, `gemini-3.5-flash` (committed to main d836b4e).
- Cost signal: an opus-4.8/high planner call on a trivial task = ~19k input tokens, ~12 AIU. reasoning_tokens=0 on that trivial prompt -> Copilot may clamp/ignore effort (research flag); re-check on a harder prompt.

## Step 0.5 — HARNESS REGRESSION found + fixed (RCA, /eng-debug)
- Symptom: first baseline showed plan=[], calls=0, aiu=0 for ALL targets (no LLM call, empty plan).
- Root cause: `eval/harness.py` `_CountingGateway.complete(self, prompt, model=None)` had a stale signature -- no `reasoning_effort`. LLMPlanner.plan() now passes reasoning_effort= -> TypeError binds the unexpected kwarg BEFORE the body (so calls never ++), planner raises, executor emits RUN_ERROR -> empty plan. A regression from the per-role routing change; offline gate uses MockGateway so it stayed green (live-only path).
- Fix (main 6c0a337): forward reasoning_effort; __getattr__ proxy for inner attrs (replanner_model/effort, needed by peek-replan); drop dead judge(); add a network-free regression test in test_audit.py.

## Step 1 — Baseline (the 5 targets, opus-4.8/high planner, 2x each) -- re-running after the fix

## Baseline (clean, opus-4.8/high planner) — 4 targets FAIL, google correctly abstains
| target | verified | trace root cause | fix piece |
|---|---|---|---|
| pydocs_json_nav | F | click "The Python Standard Library" -> NOT_FOUND (link name mismatch) | A: peek-replan |
| wikipedia_search_submit | F | opus planned `navigate www.wikipedia.org` (PORTAL) not the start_url en Main_Page -> fill Search NO_CHANGE on wrong page | B: planner-sees-start-url |
| wikipedia_signin_synonym | F | opus DID translate Sign In->Log in, but navigated to the PORTAL (no Log in there) -> NOT_FOUND | B: planner-sees-start-url |
| gnu_licenses_nav | F | TimeoutError Page.goto 30000ms on gnu.org -> flaky navigation timeout, NOT a capability gap | (flaky; re-check) |
| google_search_steam | T (abstain) | press Enter -> /sorry/ bot-wall -> abstain (correct) | none |

Two on-target pieces, each measured separately:
- **A peek-the-page replan** (executor calls planner.replan(task, failed, class, page-observation); wires replanner_model=opus-4.8/xhigh). Offline anchor test_peek_replan.py = 2 passed. Helps pydocs (and maybe wikipedia search from the portal).
- **B planner-sees-start-url** (tell plan() the start page so it stops navigating to the generic portal). Targets the two wikipedia fails.

## Piece A (peek-replan) — live after-A vs baseline
- **pydocs_json_nav: F -> T (verified)** — on the click failing, peek-replan re-planned `navigate .../library/json.html` directly. nominal=verified=True (no silent failure; M3 not raised).
- wikipedia search/signin: still F — both still navigate to the PORTAL; peek-replan from the portal can't recover -> need Piece B.
- gnu: TimeoutError (flaky nav), google: abstain (correct).
- Offline anchor green (test_peek_replan, 2). Offline gate regression: fixed _TwoPlanner (needed a replan() method) — re-running A+B gate.
- Verdict so far: A earns a real verified-flip (pydocs). Pending: 2-3x reproduce + FULL-tier regression check before final KEEP.

## Piece B (planner-sees-start-url) — live after-AB
- **wikipedia_search_submit: F -> T** — opus now navigates to en Main_Page (not the portal), fill "Search Wikipedia" + Enter -> Oxygen. nominal=verified=True.
- **wikipedia_signin_synonym: F -> T** — Main_Page, click "Log in" -> UserLogin. nominal=verified=True.
- **REGRESSION: pydocs T -> F** — start-context made opus emit RELATIVE navigate urls ("library/index.html"); page.goto rejected them ("Cannot navigate to invalid URL").
- M3 flat (pydocs is an honest fail, not silent). Offline gate A+B = 160 passed.

## Piece C (relative-URL resolution) — fixes B's regression
- act._resolve_url() resolves a site-relative navigate against the current page (urljoin); absolute/data:/about: pass through. + planner prompt now says navigate url must be ABSOLUTE.
- Offline anchor test_navigate_resolve.py = 3 passed. Re-running after-ABC to confirm pydocs back to T while wikipedia stay T.

## gnu_licenses_nav — HARD GAP: gnu.org unreachable from this environment
- curl https://www.gnu.org/ returns HTTP 000 in 0.0s (cannot connect), 3/3 + 2/2 retries. The Playwright 30s goto timeout is the SITE being unreachable here, not an agent/capability gap. The agent fails/times out honestly (never fakes success). Documented as an infra/environment hard gap; cannot be validated here.

## after-ABC summary (1x): wiki search T, wiki signin T, pydocs F (flaky), gnu timeout, google abstain
- Reproducibility batch running: pydocs x3 + wiki x2 to get rates.

## Reproducibility (final)
- wikipedia_search_submit: 3/3 verified (after-AB, after-ABC, batch) -> KEEP.
- wikipedia_signin_synonym: 3/3 verified -> KEEP.
- pydocs_json_nav: ~2/5 verified (T,F,F,F,T) -> FLAKY, does NOT meet the 2-3x bar. peek-replan improves it 0 -> ~40% but not reliably. Honest: NOT claimed as fixed.

## Decision (pending full-tier regression)
- KEEP B (planner-sees-start-url) + C (relative-URL resolution): 2 reproducible verified-flips, no regression, M3 flat, offline gate 163.
- KEEP A (peek-replan) as a sound mechanism (closes the documented context-free no-op; 0->40% on pydocs; no regression; M3 flat) but DO NOT claim pydocs as a fixed target -- flaky gap documented.
- HARD GAPS: gnu.org unreachable from this env; pydocs reliability; google bot-wall (correct abstain).

## Full-tier regression check — ISOLATED (opus model vs A/B/C)
Worktree (opus+ABC) full tier: live 14/21, day-3 7/8. Diffing vs the historical gpt-5.4 REPORT showed pydocs/example/quotes worse and internet_modal as a NEW silent failure (nominal=T verified=F). Isolation run on MAIN (opus, NO A/B/C):
- internet_modal: nominal=T verified=F — **2/2 SILENT on main(opus) too** -> caused by the OPUS MODEL UPGRADE, not A/B/C.
- example_more_info_nav: honest abstain on main(opus) too -> opus, not A/B/C.
- (baseline already showed pydocs + wikipedia FAILING on opus-no-ABC; B+C RECOVER wikipedia, A improves pydocs.)

CONCLUSION: **A/B/C introduce NO new regression and NO M3 rise.** The non-target regressions (modal silent, example/quotes abstain) are MODEL effects from the opus planner upgrade (separate change, already merged to main). The opus upgrade is a MIXED tradeoff: better at synonym planning but it navigates to site portals (broke wikipedia, recovered by B) and completes the wrong modal action (silent failure = M3 rise on main).

## FINAL round-3 disposition
- KEEP A (peek-replan), B (planner-sees-start-url), C (relative-URL resolution): offline gate 163; A/B/C anchors green; +2 reproducible verified-flips (wikipedia search + signin, 3/3); pydocs 0->~40% (flaky, NOT claimed fixed); no ABC regression; no ABC M3 rise.
- HONEST GAPS: pydocs flaky; gnu.org unreachable from this env; google bot-wall abstain (correct).
- SEPARATE FINDING for the user (opus planner default, already on main): opus raised M3 on internet_modal (silent) and regressed example/quotes vs gpt-5.4. Decision point: keep opus+B+C, or reconsider the planner default / test sonnet-4.6. Mitigation for modal = predict-then-verify (#3), a future piece.
