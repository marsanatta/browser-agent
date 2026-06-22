# Analysis — runtime, cost, scalability, correctness

The assignment requires analysis of runtime performance, cost, scalability, and
how correctness is verified. Every number below is cited to its source
(`eval/REPORT.md` from a real run, or the code). Where a figure is an estimate
rather than a measurement, it is marked **editorial/unverified**.

## 1. Runtime performance

Source: `eval/REPORT.md` (real run, 2026-06-22 12:55 UTC, n=12 tasks).

- **Wall time: 343 s for 12 tasks ≈ ~29 s/task** (343 / 12 = 28.6).
- This includes real network I/O to live seed sites and the planning/verify LLM
  loop. It is a small-n single run, so treat it as order-of-magnitude, not a
  benchmark.

**Where the time goes — the LLM loop dominates, not the browser.** The
deterministic core (perceive → 10-tier locate → act → verify, in
`backend/app/agent/`) is local Playwright work measured in tens of milliseconds
per step; the per-task latency is dominated by the **Copilot round-trips**
(planning, and any L2 LLM re-rank / judge). This is why the design pushes the LLM
*out of the hot path*: the 10-tier deterministic cascade plus the 2-layer locator
cache resolve elements with **zero tokens on a cache hit** (DESIGN §5, §11), so a
repeated locator costs no model call. Levers already in the design: batched
actions, on-demand (not every-step) perception, prune-to-last-N screenshots.

Independent corroboration that the loop is LLM-bound: the offline test subset
(`pytest -m "not live"`, no Copilot) runs **73 tests in ~29 s**, and the 8 live
Playwright integration tests (real network, still no Copilot) add only seconds —
the browser mechanics are cheap; the model calls are what cost wall-time in a real
agent run.

## 2. Cost

**The Copilot subscription is flat-rate, not per-token** (DESIGN §2 LLM layer,
§11). All LLM calls route through the GitHub Copilot SDK used as a model gateway;
there is no per-token Anthropic/OpenAI bill. Consequently the real scaling
constraint is **Copilot premium-request quota / rate limits**, and the metric that
matters is **LLM requests per task**, not $/token.

Measured request volume (source: `eval/REPORT.md`):

- **28 Copilot calls across 12 tasks ≈ ~2.3 calls/task** (28 / 12 = 2.33).
- Extrapolation (illustrative): at ~2.3 calls/task, a 100-task batch ≈ ~230
  Copilot calls; a 1,000-task batch ≈ ~2,300 calls. Whether that batch completes
  is bounded by the Copilot **premium-request allowance and rate limit**, not by
  dollars or by browser RAM.
- The ~2.3 calls/task is low *because* the locator cascade and cache keep most
  grounding deterministic (zero-token cache hits, DESIGN §5). A naive
  LLM-per-step agent would issue far more calls per task and hit the rate-limit
  ceiling much sooner — that is the architectural cost win.

**$ figures are editorial/unverified.** Any dollar-per-task numbers from the
research docs are early-2025 HAL-model estimates on a different task distribution
and are **not** quoted as facts here (DESIGN §11 caveat). Under the Copilot SDK
the honest cost statement is "flat subscription + a per-task request budget of
~2.3 calls; the ceiling is the quota/rate-limit, measured in requests".

## 3. Scalability

- **Stateless ephemeral browser per task** (DESIGN §3, §11; `PlaywrightProvider`
  opens one context per run and recycles it on close, ~300–500 MB each). State
  does not leak between tasks, so horizontal fan-out is a matter of running more
  workers — there is no shared mutable session to coordinate.
- **Single-desktop today.** The deployment is desktop self-host + a Cloudflare
  quick tunnel (DESIGN §9). The queue + autoscale shape is *designed-for, not
  built* — honestly a known limitation.
- **The ceiling moved from browser RAM to the Copilot rate limit.** Because the
  browser is cheap and stateless, you can launch many contexts on one box before
  RAM is the constraint; the binding limit is how many Copilot requests/min the
  subscription allows. At ~2.3 calls/task that is the number to plan against.

## 4. Correctness verification

The differentiator is that **success is never the agent's self-report** — it is an
**independent programmatic assertion on the live page**.

- **Independent ground truth.** `eval/verify/state.py::state_check` re-derives
  success by inspecting the actual DOM/URL the agent left behind
  (`url_contains`, `text_contains`, `h1_equals`, `selector_text_equals`). This is
  *not* self-consistency: the assertion is authored in the eval data, evaluated by
  separate code, and does not read the agent's claimed output. "An agent cannot
  pass by lying."
- **Nominal vs verified (CuP) is the headline silent-failure metric.**
  `eval/scoring.py::silent_failure_gap` counts tasks where the agent claimed
  success (`nominal`) but the independent assertion failed (`verified=False`).
  Real result: **CuP = 0.000 on n=12** (`eval/REPORT.md`) — no silent failures
  observed in this run. Directional, not a guarantee (see honesty note).
- **The one FAIL is honest, not silent.** `books_open_light_in_attic` is
  `verified=FAIL` *and* `nominal=FAIL` — the agent did not falsely claim success,
  so it contributes 0 to CuP. TSR = 0.917 ± 0.080 reflects this single real miss
  (11/12 verified; SE = √(0.917·0.083/12) ≈ 0.080, matching the report).
- **pass^3 for side-effecting tasks.** `eval/scoring.py::pass_hat_k` requires ALL
  3 runs of a side-effecting task to verify; reported **pass^3 = 1.000**
  (`eval/REPORT.md`). This is a reliability check, not a single lucky pass.
- **Budget-matched baseline (the non-negotiable ablation).** Every metric carries
  a budget-matched vanilla baseline column (max_attempts=1, no L2 heal) so an
  improvement claim cannot hide extra token spend. In this small run the full
  agent and baseline tie on TCR/TSR — reported honestly rather than inventing a
  delta.
- **Consistency / Semantic-Entropy-style signal.**
  `eval/verify/consistency.py` runs an extraction 2–3× and flags disagreement
  (sampling approximation of SEP; the hidden-state probe needs logits the Copilot
  gateway does not expose and is an explicit seam in `eval/verify/seams.py`).

**Honesty note on statistical power.** n = 12 is far below the ~1,000 items needed
to detect a 3% delta at 80% power (DESIGN §7; `eval/REPORT.md` caveats). These
numbers are **directional, not statistically powered** — the SE columns make the
uncertainty explicit, and `mean_se` uses an independent-item Bernoulli SE while
noting clustered SE would be larger because tasks share sites. A FAIL can also be
a live-site change rather than an agent regression; re-run to distinguish.

**Seams (designed-for, not built), so nothing silently passes:** SVDD
trajectory-anomaly trip-wire, Inspect AI sandbox adapter, full REAL
deterministic-replica state-diff, and the hidden-state SEP all raise
`NotImplementedError` in `eval/verify/seams.py`.

**Known gap — `WRONG_PAGE` is defined but not emitted from page state.** The
`FailureClass.WRONG_PAGE -> Recovery.REPLAN` mapping exists
(`backend/app/agent/classify.py`), but the executor never compares the landed URL
against an *expected* URL: a `navigate` sub-task unconditionally reports success,
and click/fill verification only distinguishes `CHANGED` vs `NO_CHANGE`. So a
wrong-but-changed page is not currently caught as `WRONG_PAGE` (the enum value is
reached only by the confirmation-declined path). Closing this would mean adding an
`expected_url` field to `SubTask` and a post-navigate URL check. It was scoped for
M5 but **deliberately not wired**: a mis-predicted `expected_url` would trigger
spurious replans on every task and destabilize the otherwise-green loop. It is
recorded here as a known gap rather than shipped half-done.
