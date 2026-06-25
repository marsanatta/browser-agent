# Autoresearch Round 1 — Plan (REVIEW DOC, not for execution)

**Status: awaiting your review. Nothing here is executed; no code is touched until this passes.**

Eval-driven Modify→Verify→Keep/Discard loop on `browser-agent`, grown from the **current clean
`main`** as baseline. Grounded in the domain brain (`ITERATION-PLAYBOOK-browser-agent.md`), my own
code, and the audit trace I just built (`eval/AUDIT.md`). The audit's **plan-time vs ground-time
attribution is the targeting system** — it decides what is climbable vs a named ceiling.

> The playbook predates recent work; this plan follows its **discipline** (metric=verified-not-nominal,
> guard, failure buckets, keep/discard, stop-at-ceiling) but updates the **numbers** to current main
> (offline gate is 110 now, not 84; the `_current_locator`/L2 gap it lists as open is already fixed;
> the audit trace + attribution now exist).

---

## 0. Baseline (measured, current clean main)

- **Offline gate:** 110 passed, network-free (`pytest -m "not live"`).
- **Live tier:** `eval/eval_set/live_real_world.yaml` — 9 tasks, **4 distinct real domains** (en.wikipedia.org ×4, docs.python.org, the-internet.herokuapp.com, www.google.com). **6/9 verified.**
- **Audit attribution (`eval/AUDIT.md`, `attribution_coverage = 1.000`):**
  - `live_internet_lazyload` → **SILENT_FAILURE, ground-time** ← clean first fix target.
  - `live_internet_modal` → HONEST_FAIL, **plan-time** (planner emits a bogus `navigate "this page"`; also a CSS-`text-transform` verifier-timing artifact — a NAMED ceiling, not a fix).
  - `live_internet_iframe` → HONEST_FAIL, **plan-time** by the heuristic, but the *root cause* is the **iframe-piercing perception ceiling** (the target exists but `perceive`/`locate` only see the top frame) — NAMED ceiling, deferred (high regression risk).
  - `live_google_search_steam` → **BLOCKED** (route-don't-evade, correctly abstained).
  - 13 OK.

> **Attribution honesty note (must stay in the loop):** the tag is a *first-order* heuristic —
> "first targeted step `NOT_FOUND`" is bucketed **plan-time**, but it can also be a **perception
> ceiling** (target exists, isn't perceived — the iframe case). So a plan-time tag is "do not chase
> with a planner change"; the human checkpoint (§7) classifies it further into B2-planner vs a named
> perception/grounding ceiling. ground-time tags (grounded-then-failed-later, e.g. lazyload) are the
> unambiguous climbable targets.

---

## 1. The loop (one line)

> baseline → bucket every failure by the audit attribution → ONE attribution-targeted treatment →
> re-measure on the **real harness, above live noise** → keep iff a **real independent signal flips
> AND the guard passes**, else discard + document as a hard gap → repeat → stop at the named ceiling/budget.

---

## 2. Climbable metrics — three INDEPENDENT signals (the anti-Goodhart core)

Every metric is re-derived from the **live final page by a page-specific check the agent cannot
influence** — never `nominal` (the agent's own claim), never a self-consistent number.

| Metric | What | How measured | Why it is INDEPENDENT (not gameable) |
|---|---|---|---|
| **M1 — live verified-rate** | fraction of live-tier tasks whose **independent** page-state check passes (`url_contains` / `h1_equals` / `selector_text_equals` / `iframe_text_equals`; **zero `text_contains`**) | `verified` count over the live tier, **re-run ≥2× to beat live noise**, report the delta vs baseline; held-out sub-slice = structurally-distinct non-practice domains | The check inspects the page the agent *left behind*; the agent **cannot pass by claiming success** (it's not `nominal`). The verifier is page-specific, so a wrong page fails (the books-price false-pass is already closed). |
| **M2 — breadth of distinct real domains** | count of distinct registrable real domains exercised by the live tier | `sorted(set(netloc))` over `live_real_world.yaml`, **human-audited** that each is structurally different (not another toscrape/practice clone) | A pure **structural count, orthogonal to agent behavior** — the agent doing *anything* can't change it. It only grows by ADDING a genuinely-distinct real site, and only counts after the human-audit checkpoint (§7). |
| **M3 — CuP / SILENT_FAILURE count = 0** (safety invariant) | `nominal ∧ ¬verified` count (the audit `SILENT_FAILURE` flag) | the audit already computes it; read the `flag tally` in `AUDIT.md` | It is the **divergence** between the agent's claim and the independent check — it uses *both* signals and fires exactly where they disagree. The agent can't game it (the check is ground truth); the loop can't game it by over-abstaining, because abstaining **lowers M1** (a separately tracked signal). |

**Why the three can't all be moved by one trick (the independence triangle):**
- **M1 ↑ vs M3=0:** a risky change can lift verified-rate AND create a silent failure — they move in *opposite* directions, so a kept change must raise M1 **without** raising M3. (This is exactly the scout's discarded iteration 8: it made GitHub "no longer abstain" but produced `nominal=True/verified=False` — strictly worse, discarded.)
- **M2 ↑ vs M1:** adding diverse real sites *lowers* verified-rate (real sites are hard / bot-walled), so breadth and verified-rate **trade off** — no single trick inflates both.
- All three are anchored to the **independent state check**, never `nominal` — so none is the blind/self-consistent number the playbook §0 forbids.

**Explicitly NOT metrics:** `nominal`, any task-pass-count the agent inflates by *claiming* success, token counts (reported for transparency, never minimized — minimizing tokens by over-abstaining would game M1), and `pass^k` (only 1 side-effecting task exists → not yet real signal; growing side-effecting tasks to ≥5 is a *prerequisite*, tracked but not climbed this round).

---

## 3. Guard — what must NEVER regress (revert if it does)

| Guard | How checked, every iteration AND at merge |
|---|---|
| **G1 — offline gate green AND network-free, ≥110** | `cd backend && python -m pytest -m "not live" -q` → exit 0, **≥110 passed**. Network-free verified two ways: (a) the live tier is a **separate file + runner** (`run_live_tier.py`) never collected by `-m "not live"`; (b) every new/changed *gate* test uses an inline `data:` URL / `MockGateway` / synthetic event — grep the diff'd test files for `http`/`@pytest.mark.live` and reject any network dependency in the gate. |
| **G2 — `planner.py` untouched** | `git diff main -- backend/app/agent/planner.py` is **empty** at every iteration and at merge. The planner's open-loop label-guessing is the **B2 named ceiling** — disclosed, never rewritten. |
| **G3 — no verifier loosened** | Diff-review every change to `eval/eval_set/*.yaml` asserts and `eval/verify/state.py`. A verifier may be **tightened** or **corrected to the actual rendered text** (e.g. the modal `text-transform` uppercase fix) but **never weakened** and **never** has a `text_contains` added to make a task pass. New live tasks must carry a page-specific assert (url / h1 / scoped-selector / iframe), zero `text_contains`. |

**G3 sub-clause — verify-path boundary (closes the circularity).** Probe A lists the verify path as
fixable, which overlaps what G3 protects, so the boundary is explicit: a fix may touch verify-after-act
**orchestration / timing** (when or whether to *settle* before the check) but must **NEVER** touch the
**independent state-check ASSERTION** that judges the task — the `url` / `h1` / `selector` / `iframe`
check in `eval/verify/state.py`. The per-task assertion is **frozen** during a fix; only the timing /
orchestration around it may change. **Any change to `state.py`'s assertion logic (or a task's `assert:`)
made *to pass a failing task* is an automatic discard** — fixing a failure by changing the ruler that
judges it is circular. (Tightening or correcting an assertion to the actual rendered page is allowed,
but it is logged as a *verifier fix*, never counted as a capability KEEP.)

A treatment that lifts M1/M2 but trips any guard is **reverted** — one-change discipline.

---

## 4. Per-iteration scope — what ONE probe looks like

**One change per iteration.** A probe is exactly one of:

- **Probe A — attribution-targeted GROUND-TIME fix.** Use the audit tags: pick a **ground-time**
  failure (the agent grounded + acted, then failed later — these are the agent's own fixable gaps).
  The fix lives in the **executor / recover / perceive / locate** path, or in verify-after-act
  **orchestration / timing** (when or whether to *settle* before the check) — **never `planner.py`**,
  and **never the independent state-check assertion** (the frozen ruler — see the G3 sub-clause).
  It ships with — and is **KEPT on** — a **deterministic offline test that reproduces the specific
  failure** (for lazyload: a `data:` URL fixture whose target appears after a delay with **no** spinner)
  and asserts the fix makes it pass. That deterministic green is the **primary keep signal** (§5); the
  noisy live-row flip is corroboration only.
  *Concrete first candidate (already tagged ground-time):* `live_internet_lazyload` — the result
  renders ~5 s after the click and the agent has no wait, so verify-after-act races it (SILENT_FAILURE).
  Fix = a bounded post-action **settle** (wait for a visible generic loading indicator to clear before
  verify-after-act), in `recover`/`executor`. Expected: M3 `SILENT_FAILURE` 1→0 **and** M1 +1 on that
  row. (This is the scout's kept `settle_loading` fix, re-derived here against current main — recorded
  in ANALYSIS §5 as a candidate; this round is where it would actually be earned.)

- **Probe B — eval breadth on a diverse real site.** Add **one** task on a structurally-distinct real
  domain (the tier is Wikipedia-heavy → cap Wikipedia, widen categories: shopping, news, docs, gov,
  maps, finance, …). Requirements: **page-specific verifier, zero `text_contains`**; a bot-wall is
  routed **BLOCKED→abstain** (`detect_block`, never solved/evaded) and scored `expect_abstain`;
  **throttled / polite** (one task, real navigation, no hammering). This climbs M2 and surfaces new
  failure *classes* (which then become Probe-A targets or named ceilings).

- **Plan-time failures → NAME, never fix.** A **plan-time** tag means the planner aimed at something
  that doesn't resolve (open-loop guessing) — the **B2 ceiling**. Name it in the findings (with the
  concrete site/target), do **not** fix it, **never touch `planner.py`**. Likewise the perception/
  grounding **named ceilings**: iframe-piercing, the search-box-strategy ceiling (unnamed/verbose/
  autocomplete search boxes), SPA-no-spinner AJAX, CSS-anim verifier-artifact, and bot-walls.

---

## 5. Keep / Discard rule

- **KEEP a Probe-A (ground-time fix)** iff: its **deterministic offline test goes green** — the test
  reproduces the *specific* failure (e.g. a no-spinner delayed-target fixture) and asserts the fix makes
  it pass — **AND** all three guards pass **AND** M3 stays 0. The deterministic green is the **primary,
  noise-immune keep signal**; the live re-run is **supporting evidence only**. A lucky live-row flip is
  **never** the basis for a keep (that is exactly the false signal we are avoiding: live rows flip
  run-to-run). If the deterministic test cannot be written, the fix is not yet earnable — defer it.
- **KEEP a Probe-B (breadth task)** iff: it adds **+1 distinct, human-audited real domain** (§7) with a
  sound **page-specific verifier, zero `text_contains`** — **AND** the guards pass **AND** M3 stays 0.
  Probe-B's keep signal is the **structural M2 count + the human-audit**, not a verified flip: a new
  real-site task may legitimately land RED / abstain, and that is kept evidence (a new failure *class*),
  not a discard.
- **DISCARD** iff: it moves no independent signal, OR it trips a guard, OR — the cardinal sin — it
  **converts an honest abstain into a silent failure** (M3 must stay 0; a nicer-looking M1 never
  justifies a new silent failure).
- **Every discard is documented as a hard gap** in the findings (treatment, why it failed, what it
  would take to do safely) — the iteration-8 discipline. A discard is data, not a deletion.

---

## 6. Stop conditions (bounded)

Stop and disclose when ANY holds:
1. **Every remaining live-tier failure traces to plan-time (B2 open-loop planner) or a NAMED ceiling**
   (iframe-pierce · search-box-strategy · SPA-no-spinner · CSS-anim verifier-artifact · bot-wall) —
   the failure tail decomposes entirely into known classes, none a new unexplained defect.
2. **M1 / M3 plateau across 2+ iterations** (no independent signal moves above noise).
3. **Budget: ~25 iterations** (hard cap).

---

## 7. Human-in-the-loop checkpoints (non-negotiable)

- Before trusting a new breadth task: confirm the site is **structurally distinct** (not a practice
  clone) and the verifier is sound (page-specific, can actually fail) — a green from a mislabeled task
  is worse than a red.
- Every "red" gets **one trace eyeballed** to classify it: real ground-time defect vs verifier
  artifact (the modal CSS-anim race) vs plan-time/ceiling. The attribution tag is the first cut; the
  human makes the final call on plan-time vs named-ceiling.
- A **Probe-A KEEP rests on its deterministic offline test** (§5), never on a live row — the live
  re-run is corroboration only (live rows flip run-to-run; never gate a keep on a single lucky flip).
  A **Probe-B KEEP** rests on the structural M2 count + this audit, not on any single verified row.

---

## 8. Where findings are written · isolation · NEVER pushed

- **Per-iteration findings (human narrative)** → `research/autoresearch-round-1-findings.md`
  (co-located with this plan) (running log: iter, treatment, before/after **independent** signal,
  KEEP/DISCARD + why; discards documented as hard gaps) + a one-line per-iteration record into the
  worktree's `prompts/`. A **breadth snapshot** (distinct domains × categories × outcome-class) is
  regenerated from the live YAML.
- **Structured progress ledger (machine-readable twin)** → `research/round-1-progress.json` —
  **append-only**: exactly one record is appended per iteration, so partial progress survives a crash
  and the loop's mid-run state is queryable + resumable (not just prose). The markdown findings stay
  as the human narrative; this JSON is its structured state-of-record. **Schema, one record per iteration:**
  ```json
  {
    "iter": 1,
    "probe_type": "A",
    "target": "live_internet_lazyload",
    "metrics_before": { "M1_verified_rate": 0.667, "M2_distinct_domains": 4, "M3_silent_failures": 1 },
    "metrics_after":  { "M1_verified_rate": 0.778, "M2_distinct_domains": 4, "M3_silent_failures": 0 },
    "decision": "kept",
    "reason": "deterministic no-spinner settle fixture went green; M3 1->0; guards pass",
    "guards_ok": true
  }
  ```
  `probe_type` ∈ {`A`,`B`} · `target` = task id (Probe A) or domain (Probe B) · `decision` ∈
  {`kept`,`discarded`} · `guards_ok` = all of G1/G2/G3 passed this iteration.
- **Isolation:** execution runs in an **isolated git worktree branched from `main`**; reviewed, then
  merged back to `main`. **Nothing is pushed** — ever, at any stage.
- **Source of truth for every metric:** the **real harness** (`python -m eval.run_live_tier` → live
  `REPORT.md` + `AUDIT.md`); the audit attribution drives targeting.

---

## 9. Self-check against your review bar

- **Every metric independent (no Goodhart)?** Yes — M1/M2/M3 each anchored to the independent state
  check (never `nominal`); the independence triangle (§2) shows no single trick moves all three
  favorably (verified-rate vs CuP=0 oppose; breadth vs verified-rate trade off).
- **Guard protects the offline gate AND the planner AND the ruler?** Yes — G1 (≥110 green +
  network-free, two concrete checks), G2 (`git diff … planner.py` empty), G3 (verifier diff-review,
  zero `text_contains`) **plus the G3 sub-clause**: a fix may touch verify-after-act timing/orchestration
  but the per-task state-check assertion in `state.py` is **frozen** — changing the ruler to pass a
  failing task is an automatic discard (no circularity).
- **"Above noise" operationalized (no lucky-flip keeps)?** Yes — a Probe-A KEEP is anchored on a
  **deterministic offline test that reproduces the specific failure**; the noisy live re-run is
  corroboration only, never the gate (§4/§5/§7).
- **Mid-run state survives a crash?** Yes — `research/round-1-progress.json` is an append-only,
  machine-readable twin of the markdown findings (one record per iteration; resumable).
- **Stop conditions real?** Yes — failure-tail-all-named-ceiling, 2-iteration plateau, 25-iteration cap.
- **Scope bounded?** Yes — one change per iteration; exactly two probe types; plan-time = name-don't-fix.
- **Discards documented honestly?** Yes — §5 requires every discard recorded as a hard gap; the cardinal
  rule is M3=0 (an honest-abstain→silent-failure conversion is an automatic discard regardless of M1).
