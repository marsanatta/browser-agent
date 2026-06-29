# Finance-cases — documented BAD / failure-mode examples

These are cases the autoresearch loop ran live and classified as NOT clean good
cases. Each records the failure mode honestly (the eval-set discipline: surface
failure modes, don't hide them). None were force-fixed with risky autonomous
code changes — the code-improvement hypothesis is noted for human review.

---

## BE-1 — `live_sa_qqq_holdings_nav` — flaky SPA tab-click → intermittent false abstention

**Site:** stockanalysis.com  **Capability probed:** etf_holdings_drilldown
**Instruction:** "Open the QQQ ETF page and then open its full Holdings list."

**Observed (two live runs, same case):**
| run | nominal | verified | asked | steps | outcome |
|-----|---------|----------|-------|-------|---------|
| 1 | false | **true** | **true** | 26 | reached `/etf/qqq/holdings/` but ABSTAINED |
| 2 | **true** | true | false | 26 | reached holdings, finished success |

**Root cause (from captured trajectory):** clicking the "Holdings" tab/link on
the stockanalysis.com ETF page intermittently raises `click error: TimeoutError`
(Playwright actionability timeout — the tab is a JS-rendered control, likely
covered by a sticky header / re-rendering). The agent's correct recovery is to
navigate directly to `/etf/qqq/holdings/`, which it did in run 2 → success. In
run 1 the flaky clicks consumed more of the retry budget and the agent ended by
asking the user (`ASK_USER`) — **even though the final page already satisfied the
goal** (`verified=true`). A false abstention: the agent under-claimed a success.

**Why it is a BAD eval case (not promoted):** the pass/fail flips run-to-run
(`asked` vs `nominal`) on the same input, so it does not reliably measure any one
capability. A flaky case pollutes the headline numbers.

**Why it is NOT classified as a clean code bug to auto-fix:**
- The `TimeoutError` is a site-specific actionability quirk, not a logic error.
- The agent's recovery ladder *does* work (direct-nav fallback) — it just isn't
  always fast enough within budget.
- The false abstention echoes the known, proven limitation that agent-level
  self-assessment (claim vs abstain) is unreliable — see
  `memory/planner-open-loop-ceiling`. Chasing it by patching the finish-gate or
  click logic is a deeper, regression-prone change that should be designed and
  reviewed deliberately, not patched blind overnight.

**Candidate code-improvement (for human review, NOT implemented):** when a
`click` raises `TimeoutError` on a navigational control whose href/target URL is
known from the DOM, escalate to a direct `goto(href)` sooner (before exhausting
the click-retry budget). This would convert run-1-style false abstentions into
successes without touching the finish-gate's honesty logic. Needs its own
plan + code-review + regression run (do not fold into an unrelated change).

**Salvage option:** tightening the instruction to a direct nav ("navigate to the
QQQ Holdings page") sidesteps the flaky tab-click and would likely make this a
stable GOOD case — but that changes what the case tests (drill-down vs direct
nav), so it is left as a documented failure mode instead.

---

## BE-2 — `live_cmc_apple_marketcap` passes by LUCK, not by dismissing the ad

**Site:** companiesmarketcap.com  **Status:** verified 3/3 (pass^3) — but the *mechanism* is accidental.

**What actually happens (traced, 2 captured runs, identical):**
1. `click "Apple"` → URL becomes `companiesmarketcap.com/#google_vignette` — a Google Vignette interstitial ad appears.
2. `click ...` → `TimeoutError` ×2–3 — the ad overlay intercepts all pointer events.
3. `navigate` to 2–3 guessed `/aapl/`-style URLs → `error/404` each (blind flailing).
4. `navigate https://companiesmarketcap.com/` (home) → the full reload **incidentally clears the one-shot vignette**.
5. retry `click "Apple"` → `/apple/marketcap/` → success.

**Correction of an earlier false claim:** the agent does NOT "dismiss the commercial pop-up on its own". It never clicks a close/×/skip control in any run. It reaches the goal only because its flailing recovery includes a reload that happens to clear the ad. pass^3=3/3 reflects that the reload-clears-vignette mechanism is reliable, NOT that the agent handles ads.

**Root cause (code):**
- `skill.py` system prompt has zero guidance on overlays / interstitial ads / cookie walls / dismiss / reload.
- `cdp.py` `click` = `loc.click(timeout=8000)` (non-force); an overlay → bare `TimeoutError`, no "overlay detected" signal to the agent.
- The vignette close (×) is almost certainly inside a cross-origin Google ad iframe → not perceivable by `observe` (main-frame only), so "click the close button" is not even an available action.

**Recommended enhancement (prompt, low-risk, NOT yet implemented):** add one line to the executor guidance — "If `click` fails with `TimeoutError` two+ times in a row, the page is likely covered by an interstitial ad / cookie / overlay. Reload the page by navigating to its URL again (this clears one-shot interstitials), then retry; do NOT guess deep-link URLs." This converts the accidental reload into a deliberate, fast recovery and removes the 404-guessing waste. MUST be A/B-measured on the live tier + kept green on the offline gate before merge — it touches the shared system prompt for ALL tasks.
**Heavier option (code):** detect a viewport-covering high-z-index overlay on click-timeout and surface it / auto-reload; or add a press(Escape) tool. Higher regression risk; design separately.

### RESOLVED (overlay-handling prompt enhancement)
Implemented the close-first → reload-fallback ladder in `skill.py` (commit "feat(agent):
teach overlay handling"). The earlier "passes by luck" claim no longer holds: the agent
now DELIBERATELY handles the vignette —
```
click "Apple" -> #google_vignette ; verify -> satisfied=False
observe "close" -> click "Close Ad X" -> /apple/marketcap/ ; verify -> satisfied=True  (7 steps)
```
Closing the vignette continues to the originally-clicked destination. A/B: 4/4 reached the
goal (2 independently verified=true), ~7–16 steps (was ~20 lucky). Non-overlay cases
unaffected (magic_formula 7, pydocs 8); offline gate 228 passed. Correction to this BE's
own earlier note: the close control IS reachable via the agent's `cdp.ground` text-click —
my `cdp.locate`-based probe hit a decoy/cascade gap and wrongly concluded "close doesn't
work". The user's close-first instinct was correct.

### Separate latent finding — `cdp.locate` cascade gap (NOT fixed, low priority)
`cdp.perceive('close')` describes "Close Ad X" but `cdp.locate(element)` returns None,
whereas `cdp.ground('Close Ad X')` (the agent's actual text-click path) resolves it. So
text-target clicks are fine; only the perceive→Element→`locate` path (index-based
`resolve_aid`) has the gap. Root cause across cascade tiers NOT yet traced. Did not block
this case; flagged for a separate look.
