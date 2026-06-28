# Executor Architecture A/B/C: Deterministic Plan-Mode (step-repair) vs LLM-in-Loop (agentic)

- **Date:** 2026-06-28
- **Question:** For the same browser-automation task set, which executor *architecture* wins on
  (1) independent verified-rate, (2) silent-failure rate (CuP), and (3) cost — and how much of the
  apparent cost difference is *architecture* versus *model choice*?
- **Headline:** Controlling the model (both on `claude-haiku-4.5`), the **LLM-in-loop (agentic)**
  executor beats deterministic plan-mode by **+40 percentage points verified (0.900 vs 0.500)**,
  **18× fewer silent failures (CuP 1 vs 18)**, and is **~16% cheaper**. Plan-mode loses even when
  given the expensive `opus` planner (0.762 / $9.39). The previously-reported "5.2× cheaper"
  advantage was **~90% model choice, ~10% architecture**.

---

## 1. Background — the two designs

Two executor designs share the *same* public interface (`run(task) -> AsyncIterator[Event]`,
same constructor, same Event stream) so the frontend and eval harness consume either unchanged.
Only the internal control flow differs.

- **DESIGN A — "step-repair" plan-mode (deterministic; LLM out of the hot path).**
  The LLM writes a plan once (a list of sub-tasks). Python then deterministically executes each
  sub-task in a `while i < len(subtasks)` loop. The LLM fires only at the *plan* and *replan*
  boundaries; per-step grounding/acting is deterministic. This branch carries the **localized
  step-repair** fix: on a step failure the executor splices `subtasks[:i] + repair + subtasks[i+1:]`
  (the executor — not the LLM — preserves not-yet-reached future steps, so a later goal can never
  be dropped on replan).

- **DESIGN B — "llm-in-loop" agentic (LLM in the hot path).**
  One Copilot function-calling session is opened with tools
  (`observe / read / click / fill / navigate / verify / finish`). The **LLM itself** drives the
  browser step by step — there is no Python execution loop; the loop lives inside the LLM/SDK.
  The project's own deterministic `verify.py` is exposed as a `verify` *tool*, and
  `finish(success=true)` is rejected unless that deterministic check passes (the trustable-success
  backstop). This design was developed earlier in a **separate git worktree** (an "llm-in-loop"
  experiment that ported a skill-based agent and tuned it over 5 keep/discard iterations:
  abstain-wiring fix, strict-verify, iframe support).

The tension under test: the project's stated principle is "keep the LLM out of the hot path
(cost + reliability lever)". DESIGN B deliberately inverts that. This experiment measures whether
the inversion actually costs more and whether it is less reliable.

---

## 2. Why three configs (disentangling model from architecture)

Plan-mode's production defaults use **`claude-opus-4.8`** for the initial plan and replan, while
the agentic design runs a single **`claude-haiku-4.5`** session throughout. A naive "A vs B" run
therefore confounds *architecture* with *model*. To separate them, DESIGN A was run twice:

| Config | Executor | Planner / replanner model | Execution model | Role |
|---|---|---|---|---|
| **A-haiku** | plan-mode (step-repair) | `claude-haiku-4.5` | `claude-haiku-4.5` | **model-controlled** architecture comparison vs B |
| **A-opus** | plan-mode (step-repair) | `claude-opus-4.8` | `claude-haiku-4.5` | plan-mode in its production config (matches the prior head-to-head) |
| **B** | agentic (llm-in-loop) | n/a (LLM self-plans) | `claude-haiku-4.5` | LLM-in-loop, unchanged |

- **A-haiku vs B** = the clean-science number ("what is the architecture itself worth", model held identical).
- **A-opus vs A-haiku** = how much the `opus` planner alone buys/costs inside plan-mode.
- **A-opus** also serves as a faithfulness anchor against the prior independent head-to-head.

---

## 3. Setup & invariants (the load-bearing part)

Both executors were placed in **one dedicated A/B worktree** so the eval set, harness, verifier,
provider, and cost formula are byte-identical and the *only* variable is the executor (selected at
runtime by the `AGENT_MODE` env var). Proven before any run:

| Invariant | How enforced / evidence |
|---|---|
| Same eval set | One worktree, one `eval/eval_set/live_real_world.yaml`; **sha256 `7dd278b7…`** confirmed identical to the llm-in-loop worktree's copy. Splits: **dev 39 / holdout 21 / sealed 20** (disjoint by site). |
| Same harness & scoring | Both modes run through the same `eval/harness._run_once` + `eval/scoring`; untouched. |
| Same verifier | Independent programmatic `eval/verify` state_check (URL / first-h1 / scoped selector). `verified` is **never** the agent's self-report. |
| Same browser provider | `PlaywrightProvider(headless=True)` constructed *before* the `AGENT_MODE` switch → identical for both. (Headless vanilla Playwright: clean/logged-out context per task, no stealth — so anti-bot walls are *abstained*, not evaded, equally for both.) |
| Same cost formula | `Σ total_nano_aiu / 1e11` USD via the shared counting gateway; same `claude-haiku-4.5` channel. |
| Only the executor differs | `AGENT_MODE=agentic` → agentic executor; unset → plan-mode step-repair executor (verified the deterministic splice `subtasks[:i] + new_subtasks + subtasks[i+1:]` is the live code path). For A-opus only, the planner/replanner model differs — labelled explicitly. |
| B not confounded by opus | The agentic executor selects `workhorse_model` (= haiku) and accepts `planner=None` — it **never calls the opus planner**. So switching plan-mode's planner model does not touch B. |

**Metrics (computed identically for all three):** per split (dev / holdout / sealed) and total —
- **verified-rate** = fraction whose independent state_check passed;
- **CuP (silent-failure count)** = tasks where the agent claimed success (`nominal=True`) but
  verification failed (`verified=False`);
- **cost** = `Σ total_nano_aiu / 1e11` USD, plus Copilot calls.

**Noise:** real public sites flake ±2–3 tasks/run on holdout. This round ran each config **once**
(dev+holdout + sealed). Single-run noise is flagged; the headline deltas (tens of points; 18-vs-1
silent failures) are far outside that band.

---

## 4. Results

| split | **A-haiku** (plan, haiku) | **A-opus** (plan, opus) | **B** (agentic, haiku) |
|---|---|---|---|
| dev (39) | 0.538 · CuP 10 · $1.83 | 0.872 · CuP 3 · $4.72 | 0.897 · CuP 1 · $1.62 |
| holdout (21) | 0.381 · CuP 5 · $0.99 | 0.619 · CuP 3 · $2.57 | 0.810 · CuP 0 · $0.84 |
| sealed (20) | 0.550 · CuP 3 · $1.03 | 0.700 · CuP 4 · $2.09 | 1.000 · CuP 0 · $0.78 |
| **TOTAL (80)** | **0.500 (40/80) · CuP 18 · $3.85** | **0.762 (61/80) · CuP 10 · $9.39** | **0.900 (72/80) · CuP 1 · $3.24** |
| calls (≈ /task) | 271 (≈3.4) | 148 (≈1.9) | 832 (≈10.4) |
| $ / task | $0.048 | $0.117 | $0.040 |

> Faithfulness anchor: **A-opus reproduced the prior independent head-to-head almost exactly**
> (that run reported plan-mode at `$9.39 / ~0.80`; here A-opus is `$9.39 / 0.762`, cost to the
> cent). This validates that the A/B platform is a faithful reproduction.

---

## 5. Analysis — the three questions

### (1) Pure architecture, model held identical (A-haiku vs B)
- **verified: 0.500 → 0.900 — the architecture alone is worth +40 percentage points.**
- **CuP: 18 → 1 — agentic silently fails 18× less.**
- cost: $3.85 → $3.24 — agentic is **~16% cheaper** *even though* it makes 3× more calls
  (832 vs 271), because its *filtered* per-step perception keeps each call's tokens small, whereas
  plan-mode re-sends a *full-page* perception per call.

The agentic loop sees the actual page at every step and adapts; plan-mode commits to an a-priori
plan and cannot react to what it lands on. On a weak planner (haiku) this is catastrophic for
plan-mode.

### (2) What the `opus` planner buys inside plan-mode (A-haiku → A-opus)
- verified: **+26 pp** (0.500 → 0.762) — a large lift.
- cost: **2.4× more** (+$5.54, $3.85 → $9.39).
- CuP: 18 → 10 — better plans recognize more, but silent failure stays high.
- **Yet plan-mode-with-opus (0.762) still loses to agentic-on-haiku (0.900)** — and at ~2.9× the cost.

### (3) Decomposing the prior "5.2× cheaper" cost gap (plan-opus $9.39 → agentic-haiku $3.24)
- **Model** swap (opus → haiku, within plan-mode): $9.39 → $3.85 = **−$5.54 ≈ 90% of the gap.**
- **Architecture** swap (plan-haiku → agentic-haiku; full-page → filtered perceive):
  $3.85 → $3.24 = **−$0.61 ≈ 10% of the gap.**

**The headline cost advantage previously attributed to the agentic architecture was dominantly the
model choice (an expensive `opus` planner), not the architecture.** At equal model the two
architectures cost about the same (agentic ~16% cheaper via filtered perception).

---

## 6. Failure analysis

**Silent failure is plan-mode's defining weakness.** CuP scales as model weakens:
B = 1, A-opus = 10, A-haiku = 18 (out of 80). Plan-mode's silent failures cluster on:
- **login-walled / impossible tasks** (the `*_abstain` set: settings/watchlist/account/new-repo,
  signup-CAPTCHA): plan-mode executes a plausible plan and *claims success* without recognizing it
  hit a login wall — `nominal=True, verified=False`. The agentic loop *sees* the wall each step and
  abstains honestly. This is the **planner-open-loop ceiling**: a-priori goals can't be verified
  against state the planner never sees.
- **wrong-page / weak-grounding tasks** (e.g. `internet_modal`, `wikipedia_helium_retrieval` on
  haiku): plan executes, claims done, independent check disagrees.

**step-repair does not address this.** A-opus *is* plan-mode **with** step-repair and still has
CuP 10 — because step-repair fixes replan *goal-dropping*, a different failure mode from
*silent success on unseen state*.

**B's 8 failures (dev+holdout, 52/60) are mostly honest** — 7 of 8 are honest non-completions
(the agent asked / gave up), only 1 is a true silent failure:

| task | verdict | category |
|---|---|---|
| `internet_modal` | SILENT_FAILURE | wrong-page CuP (shared ceiling — fails in all three designs) |
| `internet_iframe` | honest | capability gap (locator can't pierce iframe) |
| `wikipedia_periodic_table_nav` | honest | grounding (couldn't locate; burned step budget) |
| `govuk_vat_rates` | honest | wrong-page / can't find (documented ceiling) |
| `archive_login_nav` | honest | grounding (login-nav) |
| `github_new_repo_abstain` | honest-but-wrong | abstain-recognition miss (should have abstained) |
| `stackoverflow_questions_nav` | honest | grounding or site anti-bot |
| `gnu_licenses_nav` | crash (0 steps) | flaky/external (transient gateway failure) |

A side-cost note: agentic *failures* are expensive — when it can't find a target it keeps trying
to the step budget (~26 steps, ~$0.08–0.10/task). Plan-mode fails cheaper (gives up after a few
calls). This partly offsets agentic's per-call cheapness on the failing tail.

---

## 7. Conclusions

1. **The LLM-in-loop (agentic) architecture is decisively better** on this 80-task live set:
   highest verified (0.900), lowest silent-failure (CuP 1), and cheapest at equal model — and it
   wins the model-controlled comparison by a wide, noise-proof margin (+40 pp, 18× fewer silent
   failures).
2. **Plan-mode loses even with an expensive `opus` planner** (0.762 vs 0.900; CuP 10 vs 1; $9.39 vs
   $3.24). Its structural weakness — committing to an a-priori plan it can't verify against unseen
   state — produces many silent failures that a per-step LLM loop avoids by construction.
3. **step-repair is a valid fix to plan-mode's *goal-dropping*, but that is not the deciding axis.**
   The deciding axis is silent failure, which step-repair does not touch. If the agentic design is
   adopted, step-repair becomes moot (there is no plan→replan stage to drop a goal).
4. **The "architecture is 5× cheaper" story is mostly a model story.** Controlling the model, the
   architectures cost about the same; the genuine architectural cost lever (filtered vs full-page
   perception) is real but small (~10–16%).

**Recommendation:** treat the agentic/LLM-in-loop executor as the stronger direction for this
workload. If plan-mode is retained for any reason, step-repair remains a low-risk correctness fix
for its replan path — but it will not close the reliability gap measured here.

---

## 8. Honest caveats / threats to validity

- **Single run per config.** Live sites flake ±2–3 tasks. Per-split ±2 differences are not treated
  as signal; the headline deltas (40 pp; 18-vs-1 CuP; 2.4× cost) are far outside the noise band.
  A second dev+holdout round per config would bracket the small differences.
- **Home-advantage asymmetry.** DESIGN B (agentic) was *already tuned on this exact set* in the
  earlier experiment (abstain-wiring, strict-verify); plan-mode is its production config, untuned
  for this set. This favors B, especially on the `*_abstain` tasks. However, B's advantage also
  holds on non-abstain tasks (e.g. `helium_retrieval`, `modal`, navigation) where plan-mode
  silently fails — that part is architectural, not abstain-tuning.
- **Shared ceiling.** `internet_modal` (wrong-page) fails in all three designs — a documented
  no-oracle ceiling shared by both architectures.
- **Anti-bot / logged-out by design.** The eval browser is clean, logged-out, no-stealth headless
  Playwright; bot-walls (e.g. Google `/sorry/`) are *abstained* (route, not evade) equally for both
  designs. A logged-in / stealth (real-profile) run would measure a different thing and would
  invalidate the `*_abstain` tasks.
- **One model family.** Both ran on the Copilot `claude-haiku-4.5` channel (A-opus adds
  `claude-opus-4.8` for planning). Conclusions are within this family.

---

## 9. Reproducibility

- One A/B worktree contains both executors; the agentic executor and its `AGENT_MODE` switch were
  brought in from the separate llm-in-loop worktree; the step-repair executor/planner overlay
  DESIGN A.
- Invariant proof first: print the eval-set sha256 (`7dd278b7…`), confirm splits 39/21/20, confirm
  the deterministic splice is the live plan-mode path, confirm the provider is headless Playwright
  for both, confirm the agentic executor selects the haiku workhorse and never calls the planner.
- Run order (sequential, to avoid shared-gateway rate-limit contamination): B → A-opus under the
  default (opus) planner config; then switch planner/replanner model to `claude-haiku-4.5` and run
  A-haiku. Each config: dev+holdout, then sealed once. Save each REPORT + AUDIT per config.
- Cost is read from the per-task `nano_aiu` ledger in each AUDIT, summed per split (`/1e11` = USD);
  verified/CuP from each REPORT's per-task table (split column).
- Commands (repo-relative): `[AGENT_MODE=agentic] python -m eval.run_live_tier [--sealed]`.

*(All local filesystem paths intentionally omitted; only repo-relative code paths are referenced.)*
