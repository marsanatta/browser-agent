# Analysis — browser-agent

This report covers the four things the assignment asks an analysis to address:
**runtime performance, cost, scalability, and how correctness is verified.** The last is the hard
one — an autonomous agent will happily *claim* success on a page it never checked. System design
lives in the [README](README.md); this document is only the analysis.

*The design in one line (full design in README):* **one language-model session drives the browser
step by step (the *agentic* engine), and a deterministic check — never the model's word — decides
success.** This was not the first design. The project began with a deterministic
**`script-orchestration`** engine (a plan-then-execute design: the model writes a plan once, then
Python executes it step by step — "keep the LLM out of the loop"), then **switched after a
controlled measurement showed the agentic loop was both more reliable and not more expensive**
([§2](#2-cost)). The old engine is kept, selectable with `AGENT_MODE=script-orchestration`, but is
no longer the default (`backend/app/main.py`).

*Where the numbers come from.* **Reliability** ([§4](#4-how-correctness-is-verified-the-agent-cannot-grade-itself)):
the eval harness over a self-built **93-task live set** (`eval/eval_set/live_real_world.yaml`) on
the current default `claude-opus-4.8` (thinking medium) engine. **Cost** ([§2](#2-cost)): a
controlled A/B (`research/executor-ab-plan-mode-vs-llm-in-loop.md`) — a `claude-haiku-4.5`-era
measurement that isolates *architecture from model*; its dollar figures are model-dependent and
have not been re-measured on opus. **Runtime** ([§1](#1-runtime-performance)): a live instrumented
run of 4 representative tasks against the deployed container, timing real emitted events. Reproduce
with `python -m eval.run_live_tier` and `python -m pytest -m "not live" -q`.

> **Two terms, used throughout.** *Nominal* success = the agent ended claiming success. *Verified*
> success = an independent check confirmed the goal on the final page. The gap between them is the
> **silent-failure rate** (CuP) — the headline reliability number.

---

## 1. Runtime performance

**Wall-time is dominated by the language model, not the browser.** The agentic engine runs one
tool-calling session per task; between each model decision the Playwright action runs in
milliseconds. To see *where* the time actually goes, a live run instrumented 4 representative
tasks against the deployed container and bucketed wall-time by real event timestamps (browser
launch → LLM round-trips → Playwright tool-exec):

![Runtime distribution: ~86% LLM round-trips, ~10% browser actions, ~4% launch](docs/runtime-distribution.svg)

| Task (live, measured) | Total | Launch | LLM round-trips | Tool-exec | Calls | LLM % |
|---|---|---|---|---|---|---|
| docs.python.org (2-hop nav) | 20.9 s | 3.0 s | 17.2 s | 0.7 s | 3 | 83% |
| Wikipedia (autocomplete) | 36.2 s | 1.0 s | 33.5 s | 1.7 s | 7 | 92% |
| GOV.UK (2-hop browse) | 54.8 s | 1.6 s | 43.1 s | 10.1 s | 8 | 79% |
| amazon.com (search + click) | 67.9 s | 1.5 s | 61.2 s | 5.2 s | 13 | 90% |
| **Average / task** | **44.9 s** | **1.8 s (4%)** | **38.8 s (86%)** | **4.4 s (10%)** | **7.8** | **86%** |

> *These wall-times were instrumented on the `claude-haiku-4.5`-era default; absolute seconds are
> **model-dependent** (opus-4.8 has a higher per-call latency) and have not been re-measured. The
> structural finding is model-independent: **time = calls × per-call**, and the model round-trip —
> not the browser — is the unit of wall-time.*

- **The bottleneck is the model round-trip: ~86% of wall-time, ~5.2 s per call × ~8 calls.** The
  Playwright actions (click/fill/navigate/observe + screenshot) are only ~10%, and browser launch
  ~4%. Task time scales with the **number of model calls**, not page weight — the 3-call task
  finishes in 21 s, the 13-call task in 68 s.
- **What keeps the call count down is filtered perception.** `observe` returns only the
  interactive elements whose accessibility name relates to the target, never the whole page
  (`backend/app/agent/agentic/cdp.py`), so each round-trip's input stays small and the loop needs
  ~8 calls, not 30.
- **The loop is bounded** so a stuck task ends cleanly instead of running forever
  (`backend/app/agent/agentic/skill.py`):

  | Bound | Value | Why |
  |---|---|---|
  | Tool-call budget | 25 calls | force a wrap-up before the wall-clock |
  | Session timeout | 120 s | hard cap per task |
  | Per-handler timeout | 15 s | one wedged navigation can't stall the session |

- **Where future speed-ups are — and aren't.** Because 86% of the time is the model, the only
  levers that matter are **(a) fewer round-trips** (smarter perception / a model that needs fewer
  steps), **(b) a lower-latency model per call**, and **(c) prompt caching** to cut per-call
  latency. Optimizing the browser side (the 10%) or launch (the 4%) cannot move the headline.
  This is the same lever that drives cost ([§2](#2-cost)): the model call is the unit of both time
  and spend.

*Aside — the offline path is sub-second.* The deterministic pieces (perception filtering, the
verify gate, `detect_block`) are local DOM/arithmetic work; the unit suite of 238 tests runs
network-free in minutes. The wall-time above is entirely the model + the live network.

---

## 2. Cost

**The GitHub Copilot subscription is flat-rate, not per-token.** Every model call routes through
the Copilot SDK used as a gateway, so there is no per-token bill. The resource that actually binds
is **requests per task** (~8–10), against the Copilot premium-request quota and rate limit — not
dollars. Dollar figures below are *modeled* from Copilot's own token ledger
(`Σ total_nano_aiu / 1e11 ≈ USD`) for comparison only.

### 2.1 The experiment — and why we migrated from `script-orchestration`

The switch from `script-orchestration` to the agentic engine was an evidence decision, not a taste
one. It rests on **a controlled A/B** (`research/executor-ab-plan-mode-vs-llm-in-loop.md`) designed
to answer one precise question: *for the same task set, which executor **architecture** wins on
verified-rate, silent-failure (CuP), and cost — and how much of any cost gap is **architecture**
versus **model choice**?*

**The design — three configs, to disentangle model from architecture.** A naive "old vs new" run
would confound the architecture with the model (`script-orchestration` plans with the expensive
`claude-opus-4.8`; the agentic engine runs one cheap `claude-haiku-4.5` session). So the legacy
engine was run **twice**, giving three configs:

| Config | Architecture | Planner model | Exec model | What it isolates |
|---|---|---|---|---|
| **A-haiku** | `script-orchestration` | haiku | haiku | **model held identical** → the architecture's own worth vs B |
| **A-opus** | `script-orchestration` | opus | haiku | the engine's production config + a faithfulness anchor |
| **B** | agentic (LLM-in-loop) | — (self-plans) | haiku | the agentic engine, unchanged |

`A-haiku vs B` is the clean-science number (same model, only the architecture differs);
`A-opus vs A-haiku` is what the expensive planner alone buys.

**The invariants — what makes it clean science.** Both engines were placed in **one worktree** so
the eval set (sha256 `7dd278b7…`), harness, scoring, browser provider, and cost formula are
byte-identical; **only the executor differs**, selected at runtime by `AGENT_MODE`. Success is
graded by the **independent** `eval/verify` state-check — *never* the agent's self-report — for
every config. As a faithfulness anchor, **A-opus reproduced a prior independent head-to-head to the
cent** ($9.39), confirming the platform is a faithful reproduction.

![Cost A/B: the $9.39->$3.24 gap is ~90% model choice, ~10% architecture](docs/cost-decomposition.svg)

| Engine | Model | Verified | Silent failures (CuP) | Cost | Calls/task | $/task |
|---|---|---|---|---|---|---|
| `script-orchestration` | haiku | 0.500 (40/80) | 18 | $3.85 | 3.4 | $0.048 |
| `script-orchestration` | opus planner | 0.762 (61/80) | 10 | $9.39 | 1.9 | $0.117 |
| **agentic (default)** | **haiku** | **0.900 (72/80)** | **1** | **$3.24** | **10.4** | **$0.040** |

*(`internet_modal` was counted as a silent failure in every column but was later found to be a
verifier case bug — engine-independent, so the deltas are unaffected; the corrected default is
73/80, CuP 0.)*

**The result, in three readings:**

1. **Architecture alone (A-haiku vs B, model held):** verified **0.500 → 0.900 (+40 pp)**, silent
   failures **18 → 1 (18× fewer)**, and **~16% cheaper** *despite 3× more calls* — filtered
   per-step perception keeps each call small, where `script-orchestration` re-sends a full-page
   perception.
2. **What the opus planner buys (A-haiku → A-opus):** +26 pp verified, but **2.4× the cost** — and
   it *still loses* to agentic-on-haiku (0.762 vs 0.900) at ~2.9× the price.
3. **Decomposing the old "`script-orchestration` is ~5× cheaper" belief** ($9.39 → $3.24): the model swap
   (opus → haiku) is **−$5.54 ≈ 90%** of the gap; the architecture swap is **−$0.61 ≈ 10%**. The
   apparent cost win was *mostly the model*, not the architecture.

**Why `script-orchestration` silently fails — the structural reason.** Its planner commits to
a-priori steps from a *full-page* snapshot, then Python executes them blind to what each step
actually lands on. When a step hits a login wall or the wrong page, the engine runs its plan and
**claims success against state it never re-checked** — `nominal=True, verified=False`. This is the
**planner-open-loop ceiling**, and it is why CuP scales with planner weakness (B 1, A-opus 10,
A-haiku 18). The localized step-repair fix the engine carries closes a *different* hole (replan
dropping a future goal), not this one. The agentic loop avoids the ceiling **by construction**: it
sees the live page at every step, so it adapts and, on a wall, abstains honestly.

So we migrated because the agentic engine is **more reliable *and* not more expensive at equal
model**; the loser is kept selectable for honest comparison.

### 2.2 A cost lever we have NOT measured yet (future exploration)

Every figure above is on **one model — `claude-haiku-4.5`.** We have **not** run a model sweep, and
§1 says why that matters: **cost and time are both `calls × per-call`.** A more expensive but more
capable model might reach the goal in a **more efficient trajectory** — fewer round-trips, fewer
dead-end retries — and so be *cheaper and faster overall* despite a higher per-call price. The
A-opus row hints at the opposite extreme (pricey *and* the wrong kind of calls), but the middle is
unmapped. The honest next step is a per-model sweep (haiku → sonnet → opus as the *in-loop* model)
scored on verified-rate **and** calls/task **and** $/task together — a more capable model is a win
only if its trajectory shrinks enough to pay for its price. Noted as future work, not claimed.

Since this experiment, the **default in-loop model has moved to `claude-opus-4.8` (thinking
medium)** — its reliability is refreshed in [§4.2](#42-results) (0.957 verified, 0 silent failures
over 93 tasks). Its per-task **cost** has *not* been A/B'd against haiku, so every dollar figure in
this section remains the haiku-era reference, not a claim about the current default.

---

## 3. Scalability

"Scalability" here means three different things; the system is honest about each.

### (a) Runtime / throughput

- **Stateless, one ephemeral browser per task.** Each task opens its own browser context
  (~300–500 MB) and recycles it on close (`backend/app/browser/`), so no state leaks between tasks
  and workers are independent. Horizontal scale is just "run more workers" — there is no shared
  session to coordinate.
- **The ceiling is the model rate limit, not CPU/RAM.** Since 86% of a task is model round-trips
  (§1), throughput is bounded by the **Copilot premium-request quota**, not browser memory. Adding
  workers helps only until the quota binds.
- **The eval harness exploits this directly — process-isolated parallel runs.** Because each case
  is an independent ephemeral browser + its own Copilot CLI session, the set runs **N cases
  concurrently as isolated subprocesses** (`research/run_eval_parallel.py`: an
  `asyncio.Semaphore(jobs)` over `eval.run_one` children — deliberately *not* in-process concurrent
  sessions, which intermittently drop the Copilot session; one isolated subprocess per case is the
  reliable unit). Default **jobs=8** is tuned from three converging sources: a sibling project's
  historically-validated Copilot batch concurrency (6, ramping to 8-10), the SDK's ~100-concurrent
  429 threshold (copilot-sdk #299), and local probes at N=6 and N=12 that ran clean (0 session-drops,
  ~0.36 GB/run). Effect: the 125-run pass^k sweep finishes in **~3-4 min** versus the ~30-45 min a
  sequential one-at-a-time loop takes — the "workers are independent, just run more" property applied
  to the eval itself.
- **Honest limit:** the deployment is a single Azure Container Apps replica today; a work-queue +
  autoscale shape is **designed-for, not built**.

### (b) Code extensibility — can the structure absorb more perception, more checks, more recovery?

The expensive, risky parts sit behind stable seams; the report is honest about which are clean
plug-ins and which are coupling.

- **A new executor engine — clean.** The agentic and `script-orchestration` executors share the
  exact constructor and the same `run(task) -> AsyncIterator[Event]` stream, selected by
  `AGENT_MODE` (`backend/app/main.py`). The frontend and eval harness consume either **unchanged** —
  this is what made the §2 A/B clean science (only the executor varied), and a third engine slots in
  the same way.
- **A new bot-wall / block signal — clean, already proven.** `detect_block` (`app/agent/verify.py`)
  is four ordered marker lists (URL / visible widget / body text / challenge-host-in-HTML). Two
  signals were added this way with no structural change: the modern Cloudflare "Just a moment…"
  interstitial (two body-text markers) and DataDome (the `captcha-delivery.com` challenge host,
  gated on an empty body). Each new wall type is a list entry, not a rewrite.
- **A new verification check — clean.** Success is graded by small deterministic primitives
  (`url_contains` / `selector_text_equals` / `text_visible`) in `app/verify/state.py`; a new check
  is a new primitive + one branch, and it is **shared** by the eval harness and production so a fix
  lands once.
- **A swappable browser runtime — clean.** `BrowserProvider` wraps the browser with headless
  Playwright as default and a **CDP escalation seam** for a real stealth browser (Steel.dev /
  Browserbase tier) — the seam that would turn a genuine 403 wall into a recoverable case.
- **Failure-handling strategy — partly clean.** Failure *categories* are an enum (`classify.py`) and
  the `script-orchestration` engine has an explicit recovery module (`recover.py`); the agentic
  engine's recovery is driven by the in-loop prompt (`skill.py`) + the finish gate + a
  rejected-finish abstain cap. Adding a *category* is clean; changing the *agentic recovery policy*
  means editing the prompt contract — honest coupling, because the model (not a dispatch table)
  chooses the next strategy.

### (c) Eval toolchain — can `eval/` grow cheaply?

Yes; this scales better than any single engine seam.

- **More cases — append-only YAML, no code change.** `eval_set/*.yaml` are pinned task specs;
  `run_live_tier.py` and `loader.py` consume them, so adding cases is data, not code.
- **Designed by *purpose*, not volume.** Every case carries a `purpose` tag (the one capability or
  failure-mode it tests); redundant same-purpose filler was pruned (147 → 80). Per-purpose scoring
  comes from a generic group-by, so a **new purpose is one tag** and a new failure-mode family is a
  new file (`mechanisms.yaml`, `diagnostic.yaml`) — not a harness edit.
- **The splits are enforced in code.** dev / holdout / sealed are disjoint **by site**, and the
  loader **refuses to score the sealed split** except an explicit `--sealed` pass — a guard against
  accidental peeking / selection over-fit, not just a convention.
- **Standard, repeatable scoring.** `scoring.py` (nominal-vs-verified / CuP), `passk_diag.py`
  (pass^k, k=5), `report.py`, `audit.py` give one standard way to score any new case set, and the
  two-pass admission probe (`validate_candidates.py`) is reused to admit new cases. Exploring a new
  capability is "add tagged YAML → run the standard harness" — exactly the loop used to grow the set
  to 80.
- **A rubric-targeted hard-case set probes the three graded behaviours directly.** Five `live_*`
  widget cases: **silent-failure** (todomvc — URL-invariant client state read from `.todo-count`),
  **self-correction** (disabledinput / ajax / dynamic_controls — disabled-then-enable, async state
  waits), and **self-maintenance** (add_remove — locate dynamically-generated, id-less Delete
  buttons). They needed two new **eval-only verify primitives** (`input_value_equals`,
  `element_count` — used by the harness state-check, deliberately NOT added to the production
  criterion allowlist, anti-gaming) and surfaced two real **engine** gaps now fixed — a
  `getByPlaceholder` locator tier and `fill` pressing Enter on a trailing newline (Enter-to-submit
  inputs with no button). Every assertion was confirmed *discriminating* on the live page first
  (`research/selector_probe*.py`).
- **One run per process for agentic eval (`passk_live.py`).** Running many agentic sessions in one
  long-lived process intermittently drops the Copilot agent-mode session (`JSON-RPC -32603 … Session
  not found`); a subprocess per run mirrors production (one task per request) and is reliable. The
  agentic engine and the deployed system are unaffected — this was a test-harness batching artifact,
  not a product reliability bug.

---

## 4. How correctness is verified (the agent cannot grade itself)

The hard problem in agent reliability is that **the agent that ran all the steps will report
success on a page it never checked.** So the whole verification design follows one rule:
**self-report is never accepted as success.** Every check below is independent of the agent's claim,
layered from a per-step gate to an independent post-hoc assertion to a multi-run bar:

![Verification stack: in-loop gate, independent assertion, CuP, per-split, pass^k](docs/verify-stack.svg)

### 4.1 Why "success" needs a supplied criterion — and where it comes from

A natural-language browser task has **no universal ground truth.** "Open the json module page",
"find this book's price", "reach Ask HN" — each has a *different*, task-specific definition of done.
With no task-specific check, the only signal available is the agent's own claim — **nominal**
success — which is exactly the signal we do not trust. **The one thing that turns *nominal* into
*verified* is a deterministic, discriminating, task-specific success check.** So the system always
gets that check from outside the agent, in both places it runs:

- **In the eval harness, the task author writes it.** Each of the 80 cases ships a hand-authored
  assertion (`url_contains` / `h1_equals` / `selector_text_equals`) that is true **only if** the
  task is actually done, admitted by the two-pass gate (§4.4).
- **In production, the user supplies it** (the success-criterion field in the frontend) — because
  only the caller knows what "done" means for *their* task. `backend/app/main.py` validates it
  (`_parse_criterion`) and wraps it (`_make_verify_hook`) to run **the same `state_check` the eval
  harness uses** on the live final page. Two design choices make it trustworthy rather than
  decorative:
  - **It can't be gamed into an accidental pass.** Only deterministic, *discriminating* keys are
    accepted; a loose body-text `text_contains` (or any unknown key) is **rejected with HTTP 400**.
    A criterion that would "pass on the wrong page" is refused at the door.
  - **It also gates the agent's own finish.** Production threads the criterion into the agentic
    **finish gate** (#4b): the agent may not even `finish(success=true)` unless the user's criterion
    holds on the live page — not just its own model-chosen verify.

This is why the verdict is labeled honestly: **with** a criterion, "verified ✓" means that
independent check actually ran and passed (and a silent failure shows as `verified=false` even when
the agent claims success); **without** one there is nothing to assert against, so the run is shown
as **"actions completed — not goal-verified"** — deliberately *not* a verified pass. We make no
blanket production "verified" guarantee, because verification is only as real as the criterion
behind it.

### 4.2 Results

| Measure | Result | Scope |
|---|---|---|
| Verified rate, single run | **0.957 (89/93)** | all 93 tasks, one run (pass@1) |
| Silent-failure rate (CuP), pass@1 | **0/93** | in *that* run every miss was an honest abstain / give-up, no false claim |
| pass^k, targeted hard set (k=5) | **1.000 (25/25)**, 95% CI [0.87, 1.0], 0/125 false-success | 25 adversarial + side-effecting tasks |
| **pass^k, full set (k=5)** | **0.957 (89/93)**, 95% CI [0.90, 0.98]; **1 silent failure** (1/465 runs) | all 93 tasks × 5 runs each |

Per split, never pooled (pooling lets easy tasks hide hard ones):

| Split | Tasks | Verified | Silent failures |
|---|---|---|---|
| dev | 52 | 0.962 | 0 |
| holdout | 21 | 0.905 | 0 |
| sealed (scored once) | 20 | 1.000 | 0 |
| **Total** | **93** | **0.957 (89/93)** | **0** |

**Silent-failure rate is the headline metric:** the system is allowed to be wrong only when it
*says so*. A silent failure = a claimed success that an independent check refutes; a single pass@1
run shows **none** — but that is the lucky-draw number, and **pass^k is what catches the rest**
(the full-set pass^k below surfaces exactly one). **pass^k** raises the bar for reliability under
repetition — across **25 tasks**
(12 deterministic diagnostic contrast-pairs: renamed / hidden-menu / control selector perturbations,
dead-button and impossible-goal stagnation, synonym-locate; 8 Wikipedia intent-drift decoys; and 5
side-effecting form tasks — `todomvc / disabledinput / ajax / dynamic_controls / add_remove`) —
**all 5 of 5 runs verified, 0 false successes (0/125 runs)**. The point estimate is 1.000, but at
this n the honest interval is what matters: the 95% **Wilson** interval is **[0.87, 1.0]**
(Clopper-Pearson exact lower bound 0.863) — a binomial CI, deliberately **not** a bootstrap, which
collapses to a misleading [1,1] when every task passes. Expanding the pool from 8 → 25 tasks — and
adding the side-effecting tasks the pass^k discipline most cares about — tightened that lower bound
from **0.63 → 0.86**; pushing it materially higher needs a larger deterministic pool (≈35 tasks for
0.90), noted but not claimed. The runs were executed in parallel (see [§3(a)](#a-runtime--throughput)).

**The full-set pass^k is the more honest number — and it found a silent failure that pass@1 missed.**
Running all **93 tasks at k=5 (465 runs)** gives a task-level pass^k of **0.957 (89/93)**, 95% Wilson
[0.90, 0.98]. Of the four tasks that don't clear all five runs, three are **honest** (the
`internet_iframe` editor limitation and two site/anti-bot nav failures — 0/5 verified, but never a
false claim). The fourth, **`govuk_vat_rates`, is a true silent failure on 1 of its 5 runs**: the
agent drifted to a *sibling* gov.uk page (`/guidance/vat-rates-on-different-goods-and-services`)
instead of the asked `/vat-rates`, and its **self-chosen in-loop verify — which adapts to whatever
page it lands on — could not catch the wrong page**; only the independent `h1_equals "VAT rates"`
assert did. This is a concrete instance of the **intent-drift limitation the project mitigates but
does not claim to solve**, and the clearest argument for its own rule to **report pass^k, not
pass@1**: the single run scored 0 silent failures by drawing the good page; pass^k exposed the real
~20% wrong-page rate on this one (mildly ambiguous) task. Over all 465 runs the false-success rate is
**1/465 ≈ 0.2%** (95% upper bound ~1.2%) — not zero, and stated as such.

### 4.3 The independent checks (why a claim can't pass by lying)

| Check | What it proves | Why it's independent |
|---|---|---|
| In-loop verify gate (`app/agent/verify.py` + `skill.py`) | the agent may only `finish(success=true)` if a deterministic check passes on the live DOM/URL **and** the page is not blocked | the model's word alone is never accepted; stops the most common false claim at the source |
| Independent post-hoc assertion (`eval/verify/state.py`) | the goal actually holds on the final page the agent left | **separate code**, a **hand-authored** discriminating assertion that never reads the agent's claimed output — and deliberately *not* the in-loop formula (the in-loop goal is model-chosen, and a loose one can pass on the wrong page) |
| Nominal-vs-verified / CuP (`eval/scoring.py`) | counts claimed-success-but-refuted | the delta between the agent's claim and the independent check |
| Per-split, sealed scored once (`loader.py`) | generalization, not memorization | the loader refuses to score sealed except `--sealed` |
| pass^k (`passk_diag.py`) | reliability under repetition for side-effecting tasks | all k runs must independently verify |
| Two-pass admission (`validate_candidates.py`) | the *assertions themselves* are strict | a real-browser probe + an independent reviewer confirmed each assert is true **only if** the task is done (the two reviewers agreed 100%); weak "value shows on a listing" asserts were dropped |

A consequence of this design, carried from the start: **a fix is kept only when an independent check
improves while the controls stay unchanged** — a change is never made to "pass" by loosening the
check it is measured against, and improvement claims carry a **budget-matched baseline** so a gain
can't hide extra spend.

### 4.4 What it can't do yet (honest list — flagged, never silently wrong)

| Case | Behaviour | Status |
|---|---|---|
| Login / CAPTCHA / anti-bot wall (e.g. g2.com DataDome 403) | the agent detects the wall and **abstains honestly** — never a false success, never a fingerprint spoof (route, don't evade) | correctly handled; CDP-stealth seam designed, not built |
| iframe contents (rich-text editor in an iframe) | grounding builds against the top frame only, so it is not actionable → honest abstain | known limit |
| Bot-wall detection is **post-action, not pre-flight** | `detect_block` catches anti-bot/CAPTCHA after acting; a plain login wall or an interactive-checkbox variant can still slip to a generic miss | a pre-flight detector is future work |
| Long failure tail | when a target can't be found, the agentic loop retries to its 25-step budget (~$0.08–0.10/task), more expensive than `script-orchestration`'s early give-up | the honest cost of per-step reliability (§1–§2) |

### 4.5 Honest scoping of the numbers

`n = 93` is a **coverage** check, not a population estimate; per-split rates are directional. The
runtime numbers (§1) are 4 representative tasks on one deployment, so they characterize *where* the
time goes (the 86% model share is robust) rather than a precise per-task SLA. Live public sites
flake by a few tasks per run, and the A/B is a single run — so we trust the large deltas (40→72
verified, 18→1 silent failures) and explicitly do **not** over-read small per-split differences.

---

## Reproduce

```powershell
# offline unit tests (scoring, verify, loader) — network-free, no Copilot
python -m pytest -m "not live" -q

# the live eval, per engine (default = agentic; set AGENT_MODE for script-orchestration)
python -m eval.run_live_tier            # dev + holdout
python -m eval.run_live_tier --sealed   # the once-only sealed split
python -m eval.passk_diag               # pass^k (k=5) on the adversarial diagnostic set
AGENT_MODE=script-orchestration python -m eval.run_live_tier   # the legacy engine
```

The controlled A/B is `research/executor-ab-plan-mode-vs-llm-in-loop.md`; the eval set and its
by-site splits are in `eval/eval_set/live_real_world.yaml`; the pass^k ledger is `eval/PASSK_DIAG.md`.

---

## Appendix — the eval set, case by case

This is the per-case detail of the **§2 A/B run** (`claude-haiku-4.5`-era snapshot): the **80**
cases scored there carry the default agentic engine's per-case verdict; **8 newer dev cases**
(finance / form-fill, added after that run) are marked `(not in A/B run)`. The live set has since
grown to **93 cases**, and the current default-engine headline (`claude-opus-4.8`: **0.957**
verified, **0** silent failures) is in [§4.2](#42-results) — the per-case verdicts below are the
haiku A/B snapshot, not the latest run (e.g. `internet_modal`'s verifier bug is fixed there, and the
Wikipedia sign-up case is relabeled to the achievable nav it is). Each row is the literal
**mission**, its independent success **criterion** (the assertion checked on the final page — never
the agent's word), the one capability or failure-mode the case is designed to **measure** (its
`purpose`), and the **result**.

**Result legend.** `verified ✓` — the independent check passed. `abstained ✓` — a login / bot-wall
case the agent **correctly abstained** on (honest, scored as pass). `honest give-up (gap)` — the
agent abstained or could not locate the target and the goal was not met (a real capability gap, not
a false claim). `honest miss/flake` — a non-completion or a transient external failure. `SILENT
FAILURE` — a claimed success the independent check refuted; the **one** here (`internet_modal`) was
a verifier case-sensitivity bug (the title renders uppercase via CSS), now fixed, so it verifies
and the corrected silent-failure count is **0** (§4).
### Split: dev (47)
| Case | Mission | Success criterion | Measures (purpose) | Result |
|---|---|---|---|---|
| `wikipedia_helium_retrieval` | On Wikipedia, find and open the article about the chemical element Helium to read its atomic number. | `h1_equals=Helium` | basic_retrieval | verified ✓ |
| `pydocs_json_nav` | On docs.python.org, open The Python Standard Library, then open the documentation page for the json module. | `url_contains=library/json` | multistep_nav | verified ✓ |
| `google_search_steam` | On google.com, search for steam and submit the search. | `(none — abstain case)` | botwall_abstain | abstained ✓ |
| `wikipedia_signin_synonym` | On Wikipedia, click the Sign In link to go to the login page. | `url_contains=UserLogin` | synonym_locate | verified ✓ |
| `wikipedia_search_submit` | On Wikipedia, type 'Oxygen' in the search box and press Enter to open the article. | `h1_equals=Oxygen` | search_submit | verified ✓ |
| `wikipedia_autocomplete` | On Wikipedia, type 'Argon' into the search box and choose 'Argon' from the autocomplete suggestions that appear, to open its article. | `h1_equals=Argon` | autocomplete_select | verified ✓ |
| `internet_lazyload` | On this Dynamic Loading page, click Start and wait for the hidden text to finish loading. | `selector_text_equals={'css': '#finish h4', 'value': 'Hello World!'}` | lazyload_wait | verified ✓ |
| `internet_modal` | Open this page where a modal window appears, and read the modal window's title. | `selector_text_equals={'css': '.modal-title h3', 'value': 'This is a modal window'}` | modal_handling | SILENT FAILURE |
| `internet_iframe` | On this page, type 'browser agent was here' into the rich-text editor inside the iframe. | `iframe_text_equals={'frame': 'iframe#mce_0_ifr', 'css': 'body', 'value': 'browser agent was here'}` | iframe_pierce | honest give-up (gap) |
| `hackernews_newest_nav` | On Hacker News, click the 'new' link in the top navigation to open the newest submissions page. | `url_contains=newest` | single_nav | verified ✓ |
| `internet_status_code_200` | Start on the Status Codes page and click the link for the 200 status code, then confirm the resulting page. | `text_contains=This page returned a 200 status code` | single_nav | verified ✓ |
| `internet_challenging_dom_intro` | Open the Challenging DOM page and report the static introductory description shown about finding the best locators. | `text_contains=The hardest part in automated web testing is finding the best locators` | basic_retrieval | verified ✓ |
| `books_sapiens_price` | Find the book 'Sapiens: A Brief History of Humankind' and report its price. | `text_contains=£54.23` | extract_detail | verified ✓ |
| `books_open_mystery_category` | Open the Mystery book category from the homepage sidebar. | `h1_equals=Mystery` | single_nav | verified ✓ |
| `books_sapiens_stock` | Open the product page for 'Sapiens: A Brief History of Humankind' and report how many copies are in stock. | `text_contains=In stock (20 available)` | extract_detail | verified ✓ |
| `books_grand_design_price` | Find the price of the book 'The Grand Design' by Stephen Hawking on this site. | `text_contains=£13.76` | extract_detail | verified ✓ |
| `books_dune_price` | Go to the Science Fiction category, find 'Dune (Dune #1)', and report its price. | `text_contains=£54.86` | extract_detail | verified ✓ |
| `books_page2_pagination` | From the catalogue, go to the second page of the full book listing. | `text_contains=Page 2 of 50` | pagination | verified ✓ |
| `wikipedia_oxygen_search` | On Wikipedia, find and open the article about the chemical element Oxygen. | `h1_equals=Oxygen` | basic_retrieval | verified ✓ |
| `wikipedia_periodic_table_nav` | Open Wikipedia's article on Oxygen, then from there navigate via a link to the article describing the tabular arrangement of all the chemical elements. | `h1_equals=Periodic table` | multistep_nav | honest give-up (gap) |
| `wikipedia_einstein_body_text` | Search Wikipedia for the person famous for the equation E = mc^2 and open his article. | `url_contains=/wiki/Albert_Einstein` | basic_retrieval | verified ✓ |
| `pydocs_tutorial_nav` | From the Python 3 documentation home page, open 'The Python Tutorial' index page. | `h1_equals=The Python Tutorial` | single_nav | verified ✓ |
| `hackernews_show_then_ask` | On Hacker News, use the small links in the top bar (new, past, comments, ask, show, jobs) — NOT the article headlines in the list below. First click the 'show' link to open the Show HN page, then on that page click the 'ask' link in the same top bar to open the Ask HN page. | `url_contains=/ask` | multistep_nav | verified ✓ |
| `wikipedia_jupiter` | Find and open the Wikipedia article for the largest planet in the Solar System, the fifth planet from the Sun. | `h1_equals=Jupiter` | basic_retrieval | verified ✓ |
| `books_fiction_page2` | Open the 'Fiction' category, then go to the second page of results using the 'next' button. | `url_contains=fiction_10/page-2.html` | pagination | verified ✓ |
| `wikipedia_preferences_abstain` | On Wikipedia, open your account's Preferences page and change your interface language setting. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `wikipedia_watchlist_abstain` | On Wikipedia, open your personal watchlist to see your tracked pages. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `github_settings_abstain` | On GitHub, open your account settings page and update your profile bio. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `github_notifications_abstain` | On GitHub, open your notifications inbox and mark all as read. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `github_new_repo_abstain` | On GitHub, start creating a new repository named 'demo'. | `(none — abstain case)` | loginwall_abstain | honest miss/flake |
| `wikipedia_decoy_mercury_planet` | On Wikipedia, open the article about Mercury the planet — the smallest planet in the Solar System and the closest to the Sun (not the chemical element or the Roman god). | `h1_equals=Mercury (planet)` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_python_snake` | On Wikipedia, open the article about Python the snake genus — the group of constricting snakes (not the Python programming language). | `h1_equals=Python (genus)` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_java_proglang` | On Wikipedia, open the article about Java the programming language (not the Indonesian island of Java). | `h1_equals=Java (programming language)` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_phoenix_city` | On Wikipedia, open the article about Phoenix, the capital city of the U.S. state of Arizona (not the mythological firebird). | `h1_equals=Phoenix, Arizona` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_apple_company` | On Wikipedia, open the article about Apple Inc., the technology company that makes the iPhone (not the fruit). | `h1_equals=Apple Inc.` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_turkey_bird` | On Wikipedia, open the article about the turkey — the large bird in the genus Meleagris (not the country Turkey). | `h1_equals=Turkey (bird)` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_saturn_god` | On Wikipedia, open the article about Saturn, the Roman god of agriculture and time (not the planet Saturn). | `h1_equals=Saturn (mythology)` | intent_drift_decoy | verified ✓ |
| `wikipedia_decoy_amazon_rainforest` | On Wikipedia, open the article about the Amazon rainforest in South America (not Amazon the company or the Amazon River). | `h1_equals=Amazon rainforest` | intent_drift_decoy | verified ✓ |
| `wikipedia_signup_captcha_abstain` | On Wikipedia, open the account creation (sign-up) page. | `(none — abstain case)` | botwall_abstain | abstained ✓ |
| `sa_aapl_balancesheet_nav` | On stockanalysis.com, open Apple's stock page and then navigate to its Balance Sheet under the Financials section. | `url_contains=financials/balance-sheet` | financial_statement_drilldown | (not in A/B run) |
| `cmc_apple_marketcap` | On companiesmarketcap.com, find Apple in the largest-companies ranking and open Apple's market-cap detail page. | `url_contains=/apple/marketcap` | ranking_list_to_detail | (not in A/B run) |
| `cmc_nvda_vs_aapl_compare` | On companiesmarketcap.com, determine whether NVIDIA or Apple has the larger market capitalization, then open the market-cap detail page of whichever is larger. | `url_contains=/nvidia/marketcap` | compare_then_act | (not in A/B run) |
| `screenerin_magic_formula` | On screener.in, open the stock screens directory and open the 'Magic Formula' screen. | `url_contains=/screens/59/` | directory_to_named_item | (not in A/B run) |
| `screenerin_tcs_roce_deepdive` | On screener.in, search for Tata Consultancy Services (TCS), open its company page, and read its ROCE figure. | `url_contains=/company/TCS` | search_to_company_metric | (not in A/B run) |
| `screenerin_sort_loginwall_abstain` | On screener.in, open the 'Highest Dividend Yield Shares' screen and sort the result table by P/E ratio. | `(none — abstain case)` | loginwall_abstain | (not in A/B run) |
| `sa_compare_pe_then_balancesheet` | On stockanalysis.com, determine whether NVIDIA (NVDA) or JPMorgan Chase (JPM) has the higher P/E ratio, then open the Balance Sheet (under the Financials section) of whichever company has the higher P/E. | `url_contains=/nvda/financials/balance-sheet` | compare_reason_then_drilldown | (not in A/B run) |
| `httpbin_pizza_form` | On this pizza order form, fill in Customer name 'Ada Lovelace', Telephone '5551234', E-mail address 'ada@example.com', choose Pizza Size 'Large', check the 'Bacon' and 'Mushroom' toppings, set Delivery instructions to 'leave at the door', then submit the order. | `text_contains=Ada Lovelace` | multi_field_form_fill | (not in A/B run) |

### Split: holdout (21)
| Case | Mission | Success criterion | Measures (purpose) | Result |
|---|---|---|---|---|
| `example_more_info_nav` | On example.com, click the 'More information...' link to follow it to its destination page. | `url_contains=iana.org` | cross_domain_nav | verified ✓ |
| `gnu_licenses_nav` | On gnu.org, click the 'Licenses' link in the navigation to open the licenses page. | `url_contains=licenses` | single_nav | honest miss/flake |
| `osm_login_nav` | On OpenStreetMap, click 'Log In' to open the login page. | `url_contains=login` | single_nav | verified ✓ |
| `lobsters_comments_nav` | On Lobsters, open the 'Comments' page from the navigation. | `url_contains=comments` | single_nav | verified ✓ |
| `mdn_blog_nav` | On MDN Web Docs, open the Blog. | `url_contains=blog` | single_nav | verified ✓ |
| `archive_login_nav` | On the Internet Archive, click 'Log In' to open the sign-in page. | `url_contains=login` | single_nav | honest give-up (gap) |
| `govuk_help_nav` | On GOV.UK, open the 'Help' page from the site navigation. | `url_contains=help` | single_nav | verified ✓ |
| `arxiv_help_nav` | On arXiv, open the 'Help' page. | `url_contains=help` | single_nav | verified ✓ |
| `stackoverflow_questions_nav` | On Stack Overflow, open the 'Questions' page from the navigation. | `url_contains=questions` | single_nav | honest give-up (gap) |
| `mdn_html_input` | On MDN Web Docs, navigate to the reference page for the HTML <input> element. | `url_contains=Elements/input` | multistep_nav | verified ✓ |
| `mdn_css_flex` | On MDN Web Docs, find the reference page for the CSS flex shorthand property. | `url_contains=Properties/flex` | multistep_nav | verified ✓ |
| `govuk_bank_holidays` | Go to GOV.UK and find the page listing the upcoming UK bank holidays for England and Wales, Scotland, and Northern Ireland. | `url_contains=bank-holidays` | basic_retrieval | verified ✓ |
| `govuk_vat_rates` | On GOV.UK, navigate to the guidance page that explains the different VAT rates (standard, reduced and zero rates) and what they apply to. | `h1_equals=VAT rates` | basic_retrieval | honest give-up (gap) |
| `govuk_min_wage` | Find the GOV.UK guidance page that gives the current National Minimum Wage and National Living Wage rates. | `h1_equals=National Minimum Wage and National Living Wage rates` | basic_retrieval | verified ✓ |
| `govuk_check_uk_visa` | On GOV.UK, reach the tool that lets you check whether you need a UK visa based on your nationality and reason for travel. | `h1_equals=Check if you need a UK visa` | basic_retrieval | verified ✓ |
| `govuk_driving_licences` | Starting from the GOV.UK homepage, open the 'Driving and transport' browse section, then go into its 'Driving licences' subtopic. | `url_contains=browse/driving/driving-licences` | multistep_nav | verified ✓ |
| `arxiv_attention_paper` | Open the abstract page for the paper 'Attention Is All You Need' on arXiv. | `url_contains=abs/1706.03762` | multistep_nav | verified ✓ |
| `gitlab_profile_abstain` | On GitLab, open your user profile settings page. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `gitlab_new_project_abstain` | On GitLab, start creating a new project. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `arxiv_account_abstain` | On arXiv, open your user account page to manage your submissions. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `bitbucket_account_abstain` | On Bitbucket, open your personal account settings page. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |

### Split: sealed (20)
| Case | Mission | Success criterion | Measures (purpose) | Result |
|---|---|---|---|---|
| `scrapethissite_goto_simple` | From the Web Scraping Sandbox page list, open the 'Countries of the World: A Simple Example' sandbox page. | `url_contains=pages/simple` | single_nav | verified ✓ |
| `scrapethissite_goto_forms` | From the sandbox page list, open the 'Hockey Teams: Forms, Searching and Pagination' page. | `url_contains=pages/forms` | single_nav | verified ✓ |
| `scrapethissite_search_boston` | Open the Hockey Teams sandbox page and use the 'Search for Teams' box to search for the team 'Boston'. Submit the search. | `url_contains=q=Boston` | search_submit | verified ✓ |
| `scrapethissite_forms_page2` | Open the Hockey Teams sandbox page and navigate to the second page of results using the pagination controls. | `url_contains=page_num=2` | pagination | verified ✓ |
| `rfceditor_open_http11` | On the RFC Editor site, open the information page for RFC 2616. | `url_contains=info/rfc2616` | single_nav | verified ✓ |
| `rfceditor_title_rfc8259` | Find the title of RFC 8259 on the RFC Editor site and open its info page. | `text_contains=The JavaScript Object Notation (JSON) Data Interchange Format` | extract_detail | verified ✓ |
| `rfceditor_open_ip` | Navigate to the RFC Editor information page for RFC 791 (the Internet Protocol specification). | `url_contains=info/rfc791` | single_nav | verified ✓ |
| `rfceditor_title_rfc1149` | Look up RFC 1149 on the RFC Editor site and open its info page to read its title. | `text_contains=A Standard for the Transmission of IP Datagrams on Avian Carriers` | extract_detail | verified ✓ |
| `rfceditor_title_rfc3986` | Find the official title of RFC 3986 on the RFC Editor site and open its info page. | `text_contains=Uniform Resource Identifier (URI): Generic Syntax` | extract_detail | verified ✓ |
| `rfceditor_title_rfc2046` | Look up RFC 2046 on the RFC Editor site and open its info page to read its title. | `text_contains=Multipurpose Internet Mail Extensions (MIME) Part Two: Media Types` | extract_detail | verified ✓ |
| `webscraper_nav_laptops` | From the e-commerce test site home page, navigate to the Computers category and then open the Laptops subcategory listing. | `url_contains=computers/laptops` | multistep_nav | verified ✓ |
| `webscraper_nav_tablets` | From the e-commerce test site home page, navigate to the Computers category and then open the Tablets subcategory listing. | `url_contains=computers/tablets` | multistep_nav | verified ✓ |
| `webscraper_nav_phones` | From the e-commerce test site home page, open the Phones category listing. | `url_contains=/phones` | single_nav | verified ✓ |
| `webscraper_open_ipad_mini_product` | Navigate to the Computers > Tablets subcategory and open the product page for the 'IdeaTab A3500L' tablet, then confirm you are on its product detail page. | `url_contains=/product/15` | multistep_nav | verified ✓ |
| `webscraper_nav_phones_touch` | Navigate to the Phones category and then open its 'Touch' subcategory listing of touchscreen phones. | `url_contains=phones/touch` | multistep_nav | verified ✓ |
| `reddit_settings_abstain` | On Reddit, open your account settings page. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `reddit_inbox_abstain` | On Reddit, open your private message inbox. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `x_notifications_abstain` | On X (twitter.com), open your notifications page. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `codeberg_settings_abstain` | On Codeberg, open your account settings page. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
| `x_messages_abstain` | On X (twitter.com), open your direct messages inbox. | `(none — abstain case)` | loginwall_abstain | abstained ✓ |
