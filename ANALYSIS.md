# Analysis — browser-agent

What this system is, how fast and cheap it runs **with real numbers**, how it is built to extend,
and — the part that matters most — **how it checks its own correctness without trusting the
agent's word**. Every number here is produced by the eval harness over a self-built 80-task live
set; the architecture numbers come from a controlled A/B experiment. Reproduce with
`[AGENT_MODE=…] python -m eval.run_live_tier` and `python -m pytest -m "not live" -q`.

The design in one line: **LLM-in-loop, deterministic verify gate.** One language-model session
drives the browser step by step (the *agentic* engine); a deterministic check — never the model's
self-report — decides success. This was not the first design. The project began with a
deterministic "plan-then-execute" engine ("keep the LLM out of the loop"), then **switched after a
controlled measurement showed the agentic loop was both more reliable and not more expensive**
(§2). The old engine is kept, selectable with `AGENT_MODE=script-orchestration`, but it is no
longer the default (`backend/app/main.py`).

> **Two terms, used throughout.** *Nominal* success = the agent ended the task claiming success.
> *Verified* success = an independent check confirmed the goal on the final page. The gap between
> them is the **silent-failure rate** (also called CuP) — the headline reliability number.

---

## 0. What the numbers are measured on

A self-built **live eval set of 80 tasks across 19 real domains**
(`eval/eval_set/live_real_world.yaml`, sha256 `7dd278b7…`), split **by site** into
**dev 39 / holdout 21 / sealed 20** so the three sets share no site — "generalization" is real,
not site-memorization. The sealed split is scored **once**, never used to tune anything. Each task
ships a hand-written, discriminating assertion (a URL path, a goal-unique landmark) that is true
**only if** the task is actually done. Tasks behind login / CAPTCHA / anti-bot walls are scored on
whether the agent **abstains honestly**, not on faking success.

`n = 80` is small, so per-split rates are **directional, not statistically powered**; live public
sites also flake by a few tasks per run. Headline *deltas* below (tens of points, 18× ratios) are
far outside that noise band; small per-split differences are not.

---

## 1. Efficiency (runtime)

The browser is cheap; the language-model round-trips are what cost wall-time. The agentic engine
runs **one Copilot tool-calling session per task** and makes about **10 tool-calling round-trips
per task** (measured: 832 calls over 80 tasks ≈ 10.4/task). Each round-trip is one model decision;
the Playwright actions between them run in milliseconds.

What keeps ~10 calls/task affordable is **filtered perception**: the `observe` tool returns only
the interactive elements whose accessibility name relates to the target, never the whole page, so
each call's input stays small (`backend/app/agent/agentic/cdp.py`). The loop is **bounded** so a
stuck task ends cleanly rather than running forever (`backend/app/agent/agentic/skill.py`):

| Bound | Value | Why |
|-------|-------|-----|
| Tool-call budget | 25 calls | force a wrap-up before the wall-clock |
| Session timeout | 120 s | hard cap per task |
| Per-handler timeout | 15 s | one wedged navigation cannot stall the session |

**Contrast with the old plan-then-execute engine.** Plan-mode makes *fewer* calls per task (~3.4
on the same cheap model) because the model only plans and replans — but each call re-sends a
**full-page** perception, so fewer-but-larger calls do not win on cost (§2). The honest efficiency
cost of the agentic loop is its **failure tail**: when it cannot find a target it retries up to the
25-step budget (~$0.08–0.10/task), whereas plan-mode gives up after a few calls. Agentic failures
are therefore more expensive than plan-mode failures, which partly offsets its per-call cheapness.

---

## 2. Cost

**The GitHub Copilot subscription is flat-rate, not per-token.** All language-model calls route
through the Copilot SDK used as a model gateway, so there is no per-token bill. The metric that
actually binds is **requests per task** (~10), bounded by the Copilot premium-request quota and
rate limit — not dollars.

For comparison only, cost is **modeled** from Copilot's own token ledger (`Σ total_nano_aiu / 1e11`
≈ USD). The decisive evidence is a controlled A/B over the full 80-task set, run in one worktree so
the eval set, harness, verifier, browser, and cost formula are byte-identical and **only the
executor differs** (`research/executor-ab-plan-mode-vs-llm-in-loop.md`):

| Engine | Model | Verified | Silent failures (CuP) | Cost | Calls/task | $/task |
|--------|-------|----------|-----------------------|------|-----------|--------|
| Plan-then-execute | haiku | 0.500 (40/80) | 18 | $3.85 | 3.4 | $0.048 |
| Plan-then-execute | opus planner | 0.762 (61/80) | 10 | $9.39 | 1.9 | $0.117 |
| **LLM-in-loop (default)** | **haiku** | **0.900 (72/80)** | **1** | **$3.24** | **10.4** | **$0.040** |

(`internet_modal` was counted as a silent failure in every column but was later found to be a
verifier case bug, not a real failure — engine-independent, so the deltas are unaffected; the
corrected default figure is 73/80, CuP 0.)

Reading the table:

- **At equal model (haiku vs haiku), the agentic engine is ~16% cheaper** *and* far more reliable —
  filtered per-step perception beats plan-mode's full-page perception even though it makes 3× more
  calls.
- **The old belief that plan-mode was "~5× cheaper" was ~90% the model choice, not the
  architecture.** Decomposing the $9.39 → $3.24 gap: swapping the expensive `opus` planner for
  `haiku` accounts for **−$5.54 (≈90%)**; the architecture swap accounts for **−$0.61 (≈10%)**.
- Under the flat subscription the marginal dollar cost is ≈ 0; the real ceiling is the
  **request quota / rate limit**. Plan-mode-with-opus also loses on *quota* terms once you count the
  silent failures it ships.

Dollar figures from the pre-build research are different-model estimates on a different task
distribution and are **not** quoted here as facts.

---

## 3. Extensibility

The system is built so the expensive, risky parts are swappable behind stable seams.

- **Two executor engines behind one interface.** `AgenticExecutor` (default) and `Executor`
  (plan-then-execute) share the exact same constructor and the same
  `run(task) -> AsyncIterator[Event]` event stream, selected at construction by `AGENT_MODE`
  (`backend/app/main.py`). The frontend and the eval harness consume either engine **unchanged**.
  This is what made the §2 A/B clean science: the only variable was the executor. It also means a
  third engine could be added the same way.
- **Swappable browser runtime.** `BrowserProvider` (`backend/app/browser/`) wraps the browser, with
  headless Playwright as the default and a **CDP (Chrome DevTools Protocol) escalation seam** for a
  real stealth browser (Steel.dev / Browserbase tier). This seam is what turns a genuinely-blocking
  anti-bot wall (a Cloudflare / DataDome 403, e.g. g2.com) from a hard stop into a recoverable case
  (a real browser over CDP loads a page a headless client is served a 403 for).
- **Model tier is a per-session choice, not baked in.** The agentic loop runs one model per session
  (`claude-haiku-4.5` by default); the gateway accepts any Copilot model, and the judge for any LLM
  scoring is a different model family from the actor.
- **One shared verify arbiter.** The independent success check (`app.verify.state`) is shared
  code: the eval harness and production both grade through it, so a correctness fix lands in one
  place. The agentic loop's in-loop `verify` tool is a *separate* deterministic check
  (`app.agent.verify`) — deliberately not the same code, so the agent never grades itself with the
  arbiter's own formula (§4).
- **Stateless, ephemeral browser per task.** Each task opens its own browser context (~300–500 MB)
  and recycles it on close, so no state leaks between tasks. Horizontal scale is therefore just
  "run more workers" — there is no shared session to coordinate. The binding ceiling is the Copilot
  rate limit, not browser RAM.

**Honest limit.** The single-desktop deployment (self-host + a Cloudflare tunnel) is what exists
today; a work-queue + autoscale shape is **designed-for, not built**.

---

## 4. How correctness is evaluated (the crux)

The hard problem in agent reliability is that **the agent cannot be trusted to grade itself.** A
model that ran all its steps will happily report success on a page it never checked. So every
check below is **independent of the agent's claim**, layered from a per-step gate to an independent
post-hoc assertion.

1. **A deterministic in-loop verify gate.** The agent must call `verify(goal)` and may only
   `finish(success=true)` if that deterministic check passes on the live DOM/URL **and** the page is
   not blocked (`backend/app/agent/agentic/skill.py`, `app/agent/verify.py`). The model's word alone
   is never accepted as success. This stops the most common false claim at the source.

2. **An independent assertion grades the run — separate code, separate goal.** The eval harness
   re-derives success from the actual DOM/URL the agent left, using a **hand-authored** assertion
   from the eval data, evaluated by **separate code** that never reads the agent's claimed output
   (`eval/verify/state.py`). *An agent cannot pass by lying.* This is deliberately not the same
   formula as the in-loop verify — because the in-loop goal is **chosen by the model**, and a loose,
   model-chosen goal can pass on the wrong page. The independent, discriminating assertion is what
   catches that.

3. **Nominal vs verified (CuP) is the headline metric.** `eval/scoring.py` counts tasks where the
   agent claimed success (`nominal`) but the independent assertion failed (`verified=false`). On the
   default agentic engine this is **0**. (An earlier run reported 1 — the `internet_modal` task —
   but that was a **verifier case-sensitivity bug**: the modal title renders UPPERCASE via CSS
   `text-transform` while the assertion expected the mixed-case source text, so a correct read
   false-failed. With the verifier fixed, `internet_modal` verifies.) The delta between nominal
   (~what the agent claims) and verified is
   the number that matters; abstained walled tasks do not inflate it (an honest give-up is not a
   silent failure).

4. **Reported per split, never pooled.** Pooling lets easy tasks hide hard ones:

   | Split | Tasks | Verified | Silent failures |
   |-------|-------|----------|-----------------|
   | dev | 39 | 0.923 | 0 |
   | holdout | 21 | 0.810 | 0 |
   | sealed (scored once) | 20 | 1.000 | 0 |
   | **Total** | **80** | **0.913 (73/80)** | **0** |

5. **Two-pass eval admission.** Every task was admitted only after (1) a real-browser probe
   confirmed its assertion holds at the solution page and the path is wall-free, and (2) an
   independent reviewer confirmed the assertion is true *only if* the task is done. Weak
   "the value appears somewhere on the page" assertions were dropped.

6. **Discipline carried from the start.** A **budget-matched baseline** column accompanies
   improvement claims, so a gain cannot hide extra token spend (the non-negotiable ablation rule);
   **pass^k** (all k runs must verify) is the reliability bar for side-effecting tasks; and the
   verifier is never weakened to make a change pass.

**Production verification is opt-in and labeled honestly.** The deployed app applies the same
independent check, but only when the caller supplies a success criterion (a `url_contains` /
`selector_text_equals` assertion — a loose body-text match is rejected). With one, "verified ✓"
means that check actually ran and passed on the final page; a silent failure shows as
`verified=false` even when the agent claims success. **Without a criterion there is nothing to
assert against**, so no check runs and the run is shown as **"actions completed — not
goal-verified"**, deliberately distinct from a verified pass. We do **not** claim a blanket
production "verified" guarantee.

**Caveats.** This is a single A/B run (live sites flake ±2–3 tasks); `n = 80` is directional, not
powered; and the independent check can only be as discriminating as the assertion behind it — the
two-pass admission (#5) is what keeps those assertions strict.

---

## 5. Honest limitations (named, not hidden)

- **No silent failures on the eval set.** (An earlier reported 1, `internet_modal`, was a verifier
  case-sensitivity bug — the modal title renders uppercase via CSS — now fixed; the agent reads the
  title correctly and it verifies.)
- **Login / CAPTCHA / anti-bot walls are abstained, not solved.** The agentic loop *sees* the wall
  at each step and gives up on the first sign (route, don't evade). Concrete probes (a reCAPTCHA
  demo, g2.com's DataDome 403) with status codes and element counts are in
  [`README.md`](./README.md) (Known limitations) and `backend/probe_unsupported.py`.
- **Bot-wall detection is incomplete.** `detect_block` misses the modern "Just a moment…" Cloudflare
  managed challenge, so a small fraction of sites can slip past as a generic miss rather than a
  labeled abstain — a known gap, with the probe script as the seed for a pre-flight detector.
- **iframe contents.** Grounding builds against the top frame only, so a rich-text editor inside an
  iframe is not actionable; the agent abstains honestly.
- **Queue + autoscale not built** (§3); single-desktop deploy.

The earlier plan-then-execute engine and its eval-driven autoresearch rounds (breadth-building,
settle-before-verify timing fixes) are recorded in `research/` — that work mapped the failure tail
and fed the decision to build and measure the agentic engine, then switch to it.

---

## Reproduce

```powershell
# offline unit tests (scoring, verify, loader) — network-free, no Copilot
python -m pytest -m "not live" -q

# the live eval, per engine (default = agentic; set AGENT_MODE for plan-mode):
python -m eval.run_live_tier            # dev + holdout
python -m eval.run_live_tier --sealed   # the once-only sealed split
AGENT_MODE=script-orchestration python -m eval.run_live_tier   # the legacy engine
```

Headline reliability/cost numbers are from `research/executor-ab-plan-mode-vs-llm-in-loop.md` (the
controlled A/B); the eval set and its splits are in `eval/eval_set/live_real_world.yaml`.
