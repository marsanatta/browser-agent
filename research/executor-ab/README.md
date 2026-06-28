# executor-ab — supporting evidence

Primary data + build history behind the engine switch documented in
[`../executor-ab-plan-mode-vs-llm-in-loop.md`](../executor-ab-plan-mode-vs-llm-in-loop.md)
(the summary writeup — start there). This folder preserves the raw records that the summary
distills, so the conclusion is auditable from first-hand data.

## Contents

- **`agentic-build-ledger.md`** — how the LLM-in-loop (agentic) engine was built and tuned:
  the iteration-by-iteration KEEP/DISCARD ledger (abstain-wiring fix → strict-verify →
  iframe support; the give-up tweak that regressed and was reverted) and the final scorecard.

- **`raw-build-iters/`** — eval snapshots captured per build iteration (`report-iter{0,1,2,4}.md`
  + `report-sealed.md`). iter3 is absent because it regressed and was discarded.

- **`raw-ab-eval/`** — the raw per-config eval outputs that back the head-to-head table in the
  summary. One `report-*` (per-task verified/nominal/abstained) and one `audit-*` (per-task
  steps/calls/tokens incl `nano_aiu` cost) for each of the 3 configs × 2 split-groups:
  - config: **a-haiku** (plan-mode, haiku planner) · **a-opus** (plan-mode, opus planner) ·
    **b** (agentic, haiku)
  - split-group: **dev-holdout** (dev 39 + holdout 21) · **sealed** (20, once-only)

All runs share one eval set (sha `7dd278b7…`), one harness/verifier, one
`PlaywrightProvider(headless=True)`; `verified` is an independent state_check, cost is
`Σ total_nano_aiu / 1e11`. Reproduction steps are in the summary writeup.
