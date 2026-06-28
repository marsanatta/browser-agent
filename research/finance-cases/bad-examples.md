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
