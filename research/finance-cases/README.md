# Autoresearch: finance/stock eval cases (overnight run)

Goal: design & validate ≥5 VARIED, multi-step eval cases on **non-anti-bot**
stock/financial sites, run each live through the real browser-agent, classify
good vs bad, and (for failures) decide code-bug vs documented bad example.

## Anti-bot screening (plain WebFetch — no stealth; stealth would hide the gate)
| site | verdict | used |
|---|---|---|
| stockanalysis.com | clean (real content) | ✅ |
| companiesmarketcap.com | clean | ✅ |
| screener.in | clean (view-only; sort/query need login) | ✅ |
| macrotrends.net | **HTTP 403** (anti-bot) | ✗ excluded |
| slickcharts.com | **HTTP 403** (anti-bot) | ✗ excluded |
| finviz.com | clean for me, but blocked in user env | ✗ excluded |
| wantgoo.com | Cloudflare interstitial | ✗ excluded |

## Results — 6 GOOD + 1 BAD example, 3 sites, 7 distinct capabilities
Validated live via the official harness path (`eval/run_one.py` → `_run_once`,
independent page-state `verified`). Full log: `results.tsv`.

| case | site | capability | steps | verified | verdict |
|---|---|---|---|---|---|
| live_sa_aapl_balancesheet_nav | stockanalysis | financial-statement drill-down | 19 | ✅ | GOOD |
| live_cmc_apple_marketcap | companiesmarketcap | ranking-list → detail | 18 | ✅ | GOOD |
| live_cmc_nvda_vs_aapl_compare | companiesmarketcap | compare-then-act (reasoning) | 17 | ✅ | GOOD |
| live_screenerin_magic_formula | screener.in | directory → named screen | 7 | ✅ | GOOD |
| live_screenerin_tcs_roce_deepdive | screener.in | search → company metric | 17 | ✅ | GOOD |
| live_screenerin_sort_loginwall_abstain | screener.in | **honest abstention** (loginwall) | 11 | ✅ | GOOD |
| live_sa_qqq_holdings_nav | stockanalysis | ETF holdings drill-down | 26 | flaky | **BAD** (see bad-examples.md) |

The 6 GOOD cases are promoted into `eval/eval_set/live_real_world.yaml`.
The 1 BAD case (flaky SPA tab-click → intermittent false abstention) is
documented in `bad-examples.md` with a code-improvement hypothesis left for
human review (not auto-patched).

## Variety (the explicit ask: not similar)
- **Sites:** 3 (US stocks, global market-cap rankings, Indian stocks).
- **Task types:** action, retrieval, by-design abstention.
- **Capabilities:** in-site statement drill-down, ETF entity nav, ranking→detail,
  compare-two-then-act, directory→named-item, search→metric read, loginwall abstain.

## Reproduce
```
GH_TOKEN=$(gh auth token) PYTHONPATH=backend \
  python -m eval.run_one --only <case_id> --file research/finance-cases/candidates.yaml
```
Trajectory debug for a single case: `research/finance-cases/capture_traj.py`.

## Honesty notes
- `live_cmc_nvda_vs_aapl_compare` assert (`/nvidia/marketcap`) is correct only
  while NVIDIA > Apple by market cap (true at run time); refresh if it flips.
- All `verified` values are independent page-state checks, never agent self-report.
- This is a worktree branch (`autoresearch/finance-cases`); NOT merged to main.

## Stability check — pass^3 (k=3)
`live_cmc_apple_marketcap` re-run 3× because companiesmarketcap.com shows a
commercial/ad pop-up that initially blocks navigation. Result: **3/3 verified**
(steps 17 / 25 / 16 — run 2 fought the pop-up harder but recovered). Conclusion:
the agent reliably works around the commercial pop-up on its own; capability noted
in the gallery `why` text. No prompt/code change needed.
