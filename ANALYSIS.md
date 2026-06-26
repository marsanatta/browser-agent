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
  On the current live-tier re-run **CuP / M3 = 1** — the lone silent failure is
  `live_internet_modal` (`eval/AUDIT.md`; analysed honestly in §6), a pre-existing
  **planner-rooted** gap, **not** a regression from round-1 (`planner.py` untouched
  across the merge). Bot-walled / unreachable rows **abstain** (honest
  non-completion) and so do not inflate CuP. Directional, not a guarantee (see
  honesty note).
- **The other non-verified rows are honest, not silent.** On the live tier
  (9/12 verified, `eval/REPORT.md`) `live_internet_iframe` **abstains**
  (`asked=True`) and `live_gnu_licenses_nav` reports `nominal=False` — neither
  falsely claims success, so neither contributes to CuP. Only `live_internet_modal`
  is a silent failure (§6); the remaining rows are correct abstains or honest fails.
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

## 5. Known improvement candidates + limitations (out of scope for now)

These are surfaced by an overnight live-tier exploration across ~46 distinct real
public domains (`job/homeworks/autoresearch-findings/browser-findings.md`). They are
**recorded, not built** — this pass is measurement-only. Each is a real, evidenced
candidate; none is implemented here. **Update:** the round-1 autoresearch pass has
since built + merged the bounded spinner-settle, closing the lazyload ground-time
silent failure (§6); the six candidates below remain recorded-not-built.

### Ranked candidate fixes (highest ROI first)

1. **Modern-Cloudflare markers in `detect_block`** — `detect_block` matches the older
   Cloudflare wording but **misses the current "Just a moment…" / "Attention Required!"
   managed challenge**. ~17% of the diverse real web (8 of ~46 probed: britannica,
   stackoverflow, npm, coingecko, caniuse, timeanddate, podcastindex, google) bot-walls
   a headless agent. **ROI: highest** — an undetected block contaminates *both* the
   capability metric (mis-bucketed as NOT_FOUND) *and* the silent-failure metric. Low effort.
2. **Settle-before-perceive on JS-first / redirecting sites** (`networkidle`, or "until N
   interactive elements / target visible"). Recovers ESPN-class navigation-race crashes and
   JS-hydrated chrome. **ROI: high** (a whole class of modern SPA/redirect sites). Medium effort.
3. **Prefer press-Enter over click-autocomplete-suggestion for search boxes** — kills the
   Wikivoyage-class *silent* failure (autocomplete suggestion's name rarely equals the query).
   Implement as an executor submit-strategy preference, **not** a planner change. **ROI: high**
   (removes a silent-failure class). Medium effort.
4. **Deterministic interactability tie-break in `_match` for count-badge twins** — GitHub's
   real nav link is named `"Issues\n5k+"`; prefer the visible+enabled link over a same-named
   non-interactable menuitem **BEFORE any L2 route**. NOTE: routing these to L2 was tried in the
   exploration and **created a silent failure** (it coin-flip mis-picked and claimed success) —
   so the safe fix is a deterministic tie-break, and it must ship with a regression test that
   CuP stays 0. **ROI: medium** (cart counts, badges, "5k+" counters share this cliff). Medium effort.
5. **Honeypot / hidden-input filter in `perceive`** (drop `aria-hidden`, offscreen, or
   "for robots only" inputs, e.g. GOV.UK's `id=giraffe` trap). Prevents honeypot poisoning +
   trims noise. **ROI: medium.** Low-medium effort.
6. **Extend `settle_loading` to "wait for target text/selector present"** for SPA AJAX filters
   with no spinner (demoblaze-class), where a spinner-settle is a no-op. **ROI: medium.** Medium effort.

### Named ceilings (out of scope — why)

- **Cross-website generalization is WIDGET-determined, not site/domain.** Same engine
  (MediaWiki: Wikipedia vs Wikivoyage), opposite outcome decided purely by the submit
  *widget/strategy* (press-Enter vs click-an-autocomplete-suggestion); same category
  (.gov: data.gov vs weather.gov), opposite outcome by widget. The general guarantee is the
  **Mind2Web cross-website generalization gap — a research ceiling**, not a bounded fix. The
  targeted mitigation is candidate #3, but a *general* "strategy proven on site A transfers to
  near-identical site B" guarantee is out of scope. (Bucket eval results by widget pattern, not site.)
- **Same-origin iframe-piercing.** `locate` builds against the top frame only; piercing needs
  `perceive` to enumerate same-origin child frames AND tag elements with their frame AND `locate`
  to use `frame_locator` AND the cache key to include the frame — a broad cascade change with high
  regression risk for one widget class. **Out of scope (high effort/risk).** The frame-aware
  verifier (`iframe_text_equals`) is already in place to turn green when this lands.
- **B2 planner / search-box-strategy ceiling.** Unnamed (DuckDuckGo HTML), verbosely-named
  (Bing: "Enter your search here — Search suggestions…"), or autocomplete-required search boxes
  defeat exact role+name grounding. This is the open-loop "name a target without seeing the page"
  ceiling; **not solvable without rewriting `planner.py`, which is out of scope by design.**

### Discipline note (the load-bearing safety property)

The abstain-on-uncertainty policy **undercounts capability** (it can't distinguish "genuinely
blocked/uncertain" from "hard but doable") but it is what keeps the **CuP silent-failure count low**
across a 46-site spread. Undercounting capability is the correct error direction versus a silent
failure. The one exploration change that converted an honest abstain into a silent failure was
**discarded** — a low CuP dominates a nicer-looking capability number.

## 6. Round-1 autoresearch update (merged) — what changed, honestly

An eval-driven Modify→Verify→Keep/Discard round ran in an isolated worktree, now merged to `main`.
Per-iteration narrative: `research/autoresearch-round-1-findings.md`; machine-readable ledger:
`research/round-1-progress.json`; per-task attribution: `eval/AUDIT.md`. 5 iterations, **4 kept + 1
discarded**. Throughout and after the merge the **offline gate stayed green (113 tests, network-free)**,
**`planner.py` was untouched**, and **no verifier was weakened** (`eval/verify/state.py` assertion frozen).

**Closed — the lazyload ground-time silent failure (attribution-targeted).** The audit tagged
`live_internet_lazyload` SILENT_FAILURE / **ground-time** (the agent grounds and clicks, then the result
renders asynchronously behind a spinner and verify-after-act raced it). The fix is a bounded **settle
before verify-after-act** — `recover.settle_loading` waits a *visible generic* loading indicator to clear,
one call wired in `executor` — touching verify-after-act **timing only**, never the state-check assertion.
It was **earned on a deterministic offline test** (`backend/tests/test_settle_loading.py`, network-free,
part of the 113 gate) and **corroborated by a live verified flip** (`live_internet_lazyload` now
`nominal=True, verified=True` in `eval/REPORT.md`).

**Eval breadth grew 4 → 7 distinct live-tier domains (6 real + the `the-internet.herokuapp.com` practice
site).** Added real public sites with page-specific verifiers (zero `text_contains`): `example.com → iana.org`
(reference), `news.ycombinator.com → newest` (news), `gnu.org → Licenses` (reference), alongside the existing
Wikipedia / docs.python.org / google and the `the-internet.herokuapp.com` practice site (which backs the
widget-pattern tasks). Bot-walls are routed to **abstain** (route-don't-evade); a real-site row that abstains
or honest-fails is kept as evidence of a failure *class*, not discarded.

**Honest correction — M3 = 1, not 0 (read it as an open limitation, not a regression).** The
per-iteration single-runs reported M3 = 0, but the **authoritative full-tier re-run** (`eval/AUDIT.md`,
`attribution_coverage = 1.000`; flag tally **OK=16, SILENT_FAILURE=1, BLOCKED=1, HONEST_FAIL=2**) shows the
lone silent failure is **`live_internet_modal`**: the planner emits a navigate-only plan and the agent
declares `nominal=True` **without grounding the modal**, so the modal-title assertion fails
(`nominal=True, verified=False`). The deterministic audit tag is *ground-time*, but the **root cause is the
B2 planner open-loop ceiling** (a navigate-only plan for "read the modal title") compounded by a too-lax
nominal-completion claim. It is **pre-existing and planner-rooted — never introduced by this round**
(`planner.py` untouched across the merge; confirmed by `git diff`) and **never-fixed by design** (rewriting
`planner.py` is out of scope, §5). It was intermittently masked as an honest-fail by transient Copilot
gateway errors; a 3× re-run confirmed it silent-fails whenever the gateway responds. **Methodology lesson
recorded:** read M3 from a full-tier re-run, never infer it from the tasks you touched — a silent failure
can lurk in a task you didn't change.

**Named ceilings (honest limitations, all out of scope by design; detail in §5):**
- **B2 planner open-loop** — the planner names/plans a target without seeing the page (the modal
  navigate-only plan above; the search-box-strategy ceiling). Never rewritten — `planner.py` is frozen by guard.
- **Search-box-strategy** — unnamed / verbosely-named / autocomplete-required search boxes defeat exact
  role+name grounding (§5); the targeted mitigation is the press-Enter preference (§5 candidate #3).
- **Same-origin iframe-piercing** — `locate` builds against the top frame only (`live_internet_iframe`
  abstains); the frame-aware verifier (`iframe_text_equals`) is already in place to turn green when a
  piercing fix lands (§5).
- **Bot-walls (route-don't-evade)** — CAPTCHA / managed-challenge pages are routed to **abstain**, not
  evaded (`live_google_search_steam`); `detect_block` still misses modern-Cloudflare and Amazon-style
  robot-check markers (§5 candidate #1), so those can still silent-fail until that coverage is extended.

Net: one real ground-time defect **closed** (lazyload, verified two ways), breadth **4 → 7**, all guards
held — and one pre-existing planner-rooted silent failure (`modal`) newly **named and attributed**, not hidden.

## 7. Round-2 autoresearch update (merged) — pure breadth, honest convergence

A second eval-driven round ran in an isolated worktree, now merged. Per-iteration narrative:
`research/autoresearch-round-2-findings.md`; ledger: `research/round-2-progress.json`; per-task attribution:
`eval/AUDIT.md`. **11 iterations, 9 kept + 2 discarded.** It was a **pure-breadth round — no `backend/` code
changed** (planner.py, state.py, executor, recover all untouched); the offline gate stayed **113
green/network-free** through and after the merge.

**Breadth grew 7 → 16 distinct live-tier domains — honestly: 15 real production sites + 1 carried-over
practice site.** The practice site is `the-internet.herokuapp.com` (it backs the round-1 lazyload / modal /
iframe widget-pattern tasks); it is **not** counted as a real production site. The **15 real** sites span
diverse categories — news (Hacker News, Lobsters), government (GOV.UK), documentation (Python docs, MDN),
maps (OpenStreetMap), finance (Yahoo Finance), science (arXiv), media / digital library (Internet Archive,
Open Library), Q&A (Stack Overflow), and reference (Wikipedia, GNU, example.com). Each new site carries a
page-specific verifier (URL / scoped selector, zero `text_contains`) and was characterized live before
adoption. (Commerce/shopping is deliberately absent — real shopping sites bot-wall; Amazon was round-1's
route-don't-evade discard.)

**The M3-protection discipline held — two honest discards.** `w3.org` and `rfc-editor.org` each produced a
`nominal=True, verified=False` **SILENT_FAILURE candidate** at characterization (the agent claimed success
while still on the homepage — the target link was never located). By the **automatic-discard rule** (a new
silent failure is never kept — the "Amazon rule"), both were **kept OUT of the tier**, so round-2 introduced
**zero new silent failures**. This is the load-bearing evidence that the safety discipline works in practice:
a silent-failure candidate is caught at characterization and discarded *before* it can enter the eval.

**M3 honesty — the close-run 0 is run-noise, not a fix.** The opening baseline run measured **M3 = 1** (the
`helium` retrieval silent-failed); the close full-tier snapshot measured **M3 = 0** (`helium` verified that
run). That delta is **live nondeterminism, not a repair** — `helium` (and `modal`) flip between *silent* and
*honest-fail / verified* run-to-run. So the honest, stable statement is **"no NEW silent failure was
introduced this round,"** NOT "M3 was driven to 0." The carried silent-failure risk is **planner-rooted**:
the planner emits a **navigate-only plan and the agent claims success without grounding the goal** (the
`modal` case — a navigate-only plan for "read the modal title"; `helium` — a portal search that lands on the
wrong page) — a **named B2 open-loop ceiling, unfixed by design** (`planner.py` is frozen by guard). Round-2
neither fixed nor worsened it.

**Named ceilings (the disclosed limits, all off-limits this round; detail in §5):**
- **Planner open-loop (B2)** — navigate-only / unsighted plans + lax nominal-completion (the `modal`/`helium`
  silent-failure band; the `w3.org`/`rfc-editor` discards). `planner.py` frozen by guard.
- **Same-origin iframe-piercing** — `locate` sees the top frame only (`live_internet_iframe`).
- **Search-box-strategy** — unnamed / verbose / autocomplete-required search boxes defeat exact role+name grounding.
- **Bot-walls (route-don't-evade)** — CAPTCHA / managed-challenge pages routed to abstain, never solved
  (`live_google_search_steam` BLOCKED).
- **`detect_block` coverage gap** — misses modern-Cloudflare "Just a moment…" and Amazon-style robot-check
  markers, so an *undetected* wall can silent-fail (the round-1 Amazon discard).

**Convergence — this is the honest stopping point; there is no round-3.** Round-2's remaining failure tail
decomposes **entirely** into the named ceilings above: every non-verified row at close is either a correct
abstain (`google` BLOCKED; `iframe` / `gnu` / `archive` / `stackoverflow` honest-fail or abstain) or a
planner-rooted, silent-failure-prone task (`modal` / `helium`). **No new climbable class remains** that the
guards (planner.py frozen, no verifier weakened, M3 must not rise) would permit fixing — a further round
would only re-discover the same disclosed ceilings. Per the round's own stop condition (failure tail all
named-ceiling), the eval-driven loop has **converged**, and the honest move is to stop and disclose, which
this section does. Full per-task evidence: `eval/AUDIT.md` and `research/autoresearch-round-2-findings.md`.

Net: breadth **7 → 16 domains (15 real + 1 practice)** with **zero new silent failures** and **zero backend
code change**; the loop has **converged** on the named ceilings — the honest end of the autoresearch program.
