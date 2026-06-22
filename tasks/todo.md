# M3 — Evaluation set + silent-failure rigor

## Goal
Build a REAL, runnable eval harness that scores the existing agent on TCR/TSR/pass^k
and the headline nominal-vs-verified (CuP) silent-failure gap, against a budget-matched
vanilla baseline. Modest set (~12 tasks, k=3) so a full run is a few dozen Copilot calls.

## Grounding (cited, read)
- TCR = mean fraction of key-nodes hit per task; TSR = fraction of tasks hitting ALL key-nodes
  (WebCanvas, architecture/03 §3.1).
- pass^k = P(all k trials succeed); k=3 for side-effecting tasks (eval/02 §C1, §F2).
- CuP / silent-failure gap = fraction where agent reported success (nominal) but the independent
  programmatic assertion failed (verified) (eval/01 §4, DESIGN §6).
- SE = sqrt(p(1-p)/n) Bernoulli (eval/02 §C2/F3).
- REAL: action tasks = programmatic state-diff (r=1 exact), retrieval = rubric judge (architecture/03 §3.2).
- Consistency check (Semantic-Entropy-style): run extraction 2-3x, flag disagreement (eval/02 §B3/F4).
- Budget-matched baseline: every "X improves perf" claim needs a vanilla baseline at the SAME
  step budget (architecture/03 §4, DESIGN §7 non-negotiable ablation rule).
- Held-out >=20% on a site never used in dev (eval/01 §5.3).

## Plan (steps + verification)

1. **Seam in executor** (surgical): add optional `verify_hook(page) -> bool` awaited on the
   live final page BEFORE the browser closes; when set, `verified_completion` reflects its
   result instead of mirroring `nominal`. Default (no hook) = unchanged.
   Also add optional `max_attempts` so the harness can run a budget-matched baseline
   (attempts=1, no recovery ladder, no L2) vs the full agent (attempts=4 + heal).
   *Verify:* existing `test_loop_mock` stays green (hook absent → verified == nominal).

2. **Eval set as data** `eval/eval_set/tasks.yaml`: ~12 tasks. Each carries id, instruction,
   start_url, domain, task_type (action|retrieval|side_effect), difficulty, held_out flag,
   key_nodes (list of independent checkpoints), success assertion (independent ground truth:
   url_contains / h1_equals / text_contains / extract+expected). >=20% held-out (quotes.toscrape.com).
   *Verify:* loader unit test parses all tasks; schema validated.

3. **`eval/verify/` module** — independent programmatic state check + consistency check.
   - `state_check(page, assertion) -> bool`: url/h1/text/extract assertions on the LIVE page.
   - `key_node_check(page, node) -> bool`: same primitives for intermediate checkpoints.
   - `consistency_check(extract_fn, n=3) -> (value, agreed)`: run extraction n times, flag disagreement.
   These are REAL. SVDD / Inspect AI / REAL-full = clearly-marked SEAMS (TODO).
   *Verify:* unit tests with a fake page (assertion true/false/partial; consistency agree/disagree).

4. **`eval/scoring.py`** — pure math, no Copilot/browser. TaskResult dataclass; functions
   tcr, tsr, pass_hat_k, silent_failure_gap, mean_se. 
   *Verify:* unit tests with SYNTHETIC trajectories where the answer is hand-computed by
   independent ground truth (e.g. 3/5 nodes → 0.6; would FAIL on off-by-one).

5. **`eval/harness.py`** — run each task through the real Executor with the verify_hook
   wired to `eval/verify`. Two columns: agent (attempts=4+heal) and budget-matched baseline
   (attempts=1). pass^k via k=3 reruns for side_effect tasks. Counts Copilot calls.
   *Verify:* one REAL run against live sites + Copilot; emits metrics.

6. **`eval/REPORT.md`** — generated from the real run: metric table (TCR/TSR/pass^k/CuP gap,
   agent vs baseline), per-task pass/fail, approx Copilot call count, honest caveats + seams.

## Verify (paste REAL output)
- `python -m pytest -q` green (offline scoring/verify/loader tests + existing suite).
- One real eval run → paste actual REPORT.md table + real call count.
- Secret scan on eval artifacts.

## Review (after execution)

Done. All 6 steps built REAL + runnable; heavy parts wired as marked seams.

Real full-run numbers (eval/REPORT.md, 2026-06-22 12:55 UTC):
- agent TSR=0.917 +/- 0.080, TCR=1.000, CuP silent-failure gap=0.000, pass^3=1.000
- budget-matched baseline TSR=0.917, TCR=1.000, CuP=0.000
- held-out TSR (quotes.toscrape.com, 4 tasks)=1.000
- Copilot calls=28, wall time=343s

One honest failure: `books_open_light_in_attic` FAILED on both agent and baseline,
with nominal=FAIL — so correctly NOT flagged as silent. Re-running the same task in
isolation PASSED, so the cause is **LLM planner variance**: the planner sometimes emits
`click "A Light in the Attic"` (full title) instead of the truncated accessible name
`"A Light in the ..."` the link actually exposes, so `_match` finds no target. This is a
real result, not a harness bug; I did NOT cherry-pick a re-run to inflate TSR.

Agent==baseline here because the seed sites are clean (no occlusion/staleness/selector
drift), so the recovery ladder + L2 heal have nothing to fix — the ablation correctly
shows no uplift on this distribution rather than a fabricated win.

pytest: 81 passed (26 new offline eval tests + existing live suite).

Seams (NotImplementedError, eval/verify/seams.py): SVDD trajectory anomaly, Inspect AI
adapter, full REAL replica state-diff, hidden-state SEP. Consistency check ships as the
sampling approximation (real, unit-tested).
