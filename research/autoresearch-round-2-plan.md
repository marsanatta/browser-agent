# Autoresearch Round 2 — Plan (REVIEW DOC, not for execution)

**Status: awaiting your review. Nothing here is executed; no code is touched until this passes.**

A **focused delta from round-1** (now merged to `main`), not a full re-author. Same eval-driven
Modify→Verify→Keep/Discard discipline, same three independent metrics, same guards, same
deterministic-test-anchored keep rule, same one-probe-per-iteration / plan-time-name-don't-fix /
document-every-discard / ~25-iteration bound. What changes is the **frontier**: round-1 closed the
lazyload ground-time silent failure and grew breadth to 7 distinct real domains; **round-2 pushes breadth
to ~15–20 distinct real domains and fixes the new ground-time failures that breadth surfaces.**

> Read this against round-1's plan (`research/autoresearch-round-1-plan.md`) — it shares the structure;
> only the baseline, the frontier (§2), and the candidate pool (§4) are new.

---

## 0. Baseline (NEW main, round-1 merged) — re-measured

Source of truth = the authoritative full-tier snapshot generated at round-1 end on this exact code
(`eval/REPORT.md` 2026-06-25, `eval/AUDIT.md` `attribution_coverage = 1.000`). Nothing changed on `main`
since except an `ANALYSIS.md` doc edit, which cannot move an eval number — so this snapshot **is** the
round-2 baseline.

| Metric | Baseline (new main) | Source |
|---|---|---|
| **M1 — live verified-rate** | **9/12 = 0.750** | `eval/REPORT.md` |
| **M2 — distinct real domains** | **7** (en.wikipedia.org, docs.python.org, www.google.com, the-internet.herokuapp.com, example.com, news.ycombinator.com, www.gnu.org) | `live_real_world.yaml` |
| **M3 — SILENT_FAILURE count** | **1** (`live_internet_modal`) | `eval/AUDIT.md` (flag tally: OK=16, SILENT_FAILURE=1, BLOCKED=1, HONEST_FAIL=2) |

- **Offline gate baseline: 113 passed, network-free** (`pytest -m "not live"`). (Round-1 added
  `test_settle_loading.py` → 110 → 113.)
- **The carried M3=1 is `live_internet_modal` — a NAMED, planner-rooted ceiling, NOT a round-2 target.**
  The planner emits a navigate-only plan and the agent claims `nominal=True` without grounding the modal
  (deterministic audit tag *ground-time*, but root cause = **B2 planner open-loop** + lax
  nominal-completion). Fixing it needs `planner.py`, which is **off-limits by guard G2**. So round-2
  carries M3=1 as a known ceiling and **must not let M3 rise above it** (§2).

**Inherited named ceilings (carried from round-1, strictly OFF-LIMITS — name, never fix):**
B2 planner open-loop (incl. the modal M3=1) · same-origin iframe-piercing · search-box-strategy
(unnamed / verbose / autocomplete-required search boxes) · bot-walls (route-don't-evade) · the
block-detector coverage gap (`detect_block` misses modern-Cloudflare "Just a moment…" and Amazon-style
robot-check markers — `ANALYSIS.md` §5 #1).

**Round-1 methodology lesson, baked into round-2 (the one process fix):** **M3 is read from a full-tier
re-run, never inferred from the tasks you touched.** Round-1's per-iteration M3=0 was wrong because it
carried `modal`'s stale tag instead of re-measuring it; the full-tier re-run caught it. Round-2's M3 check
each iteration **re-evaluates every currently-non-verified row + the carried `modal`**, and the round
closes with a fresh full-tier snapshot as the official number. Execution therefore **opens with a fresh
full-tier baseline run** to re-confirm M1/M3 (live rows flip run-to-run; the structural M2=7 is read from
the YAML and is run-independent).

---

## 1. The loop (one line)

> baseline → add ONE structurally-distinct real domain (or ONE attribution-targeted ground-time fix it
> surfaces) → re-measure the three signals on the real harness, above live noise → keep iff a real
> independent signal flips AND the guard passes AND **M3 does not rise**, else discard + document as a hard
> gap → repeat → stop at the breadth target / named-ceiling tail / budget.

---

## 2. Round-2 frontier + the three INDEPENDENT metrics (anti-Goodhart core, unchanged)

**The climbable headroom this round is M2 (breadth) and the ground-time failures it surfaces.** Round-1
took M2 from 4→7; round-2 targets **~15–20 distinct real domains** across diverse categories
(shopping · news · gov · docs · maps · finance · reference · media), capping any single domain so the tier
does not re-concentrate (round-1's lesson: it was Wikipedia-heavy).

The three metrics and their independence are **unchanged from round-1 §2** (every signal re-derived from the
live final page by a page-specific check the agent cannot influence — never `nominal`, never a
self-consistent number):

| Metric | What | Why independent (not gameable) |
|---|---|---|
| **M1 — live verified-rate** | fraction of live-tier tasks whose independent page-state check passes (`url_contains` / `h1_equals` / `selector_text_equals` / `iframe_text_equals`; **zero `text_contains`**) | inspects the page the agent left behind — can't pass by claiming success |
| **M2 — breadth of distinct real domains** | count of distinct registrable real domains in the live tier | pure structural count, orthogonal to agent behaviour; grows only by adding a genuinely-distinct real site, only after human-audit (§7) |
| **M3 — SILENT_FAILURE count** | `nominal ∧ ¬verified` count | the divergence between the agent's claim and the independent check; the loop can't game it by over-abstaining because abstaining lowers M1 |

**Independence triangle (unchanged):** M1↑ vs M3-no-rise oppose (a risky change can lift verified-rate AND
create a silent failure); M2↑ vs M1 trade off (diverse real sites are hard / bot-walled, so breadth lowers
verified-rate). No single trick moves all three favourably.

**Round-2 M3 invariant — the cardinal rule, restated for a baseline of 1:**
- M3 baseline = 1 (`modal`, named planner ceiling, **carried, never chased**).
- **M3 must NOT RISE above 1.** A breadth task that produces a NEW silent failure (`nominal=True`,
  `verified=False`) pushes M3 1→2 and is an **automatic discard** — kept out of the tier, documented as a
  hard gap (exactly the round-1 Amazon rule). If that new silent failure is *ground-time and fixable*, the
  iteration may instead become a **Probe A** (fix it on a deterministic test so the row verifies and M3
  stays 1); if not fixable this iteration, discard.
- M3 can only **fall** to 0 by fixing `modal`, which is **out of scope** (planner-rooted). So 1 is the
  round-2 floor; the work is to hold it while M2 climbs.

**Explicitly NOT metrics (unchanged):** `nominal`, any agent-inflatable pass-count, token counts (reported
for transparency, never minimized), `pass^k` (still only ~1 side-effecting task — grown but not climbed).

---

## 3. Guards — what must NEVER regress (revert if it does)

Identical to round-1 §3, numbers updated to new main:

| Guard | How checked, every iteration AND at merge |
|---|---|
| **G1 — offline gate green AND network-free, ≥113** | `cd backend && python -m pytest -m "not live" -q` → exit 0, **≥113 passed**. Network-free two ways: (a) the live tier is a separate file + runner (`run_live_tier.py`), never collected by `-m "not live"`; (b) every new/changed *gate* test uses an inline `data:` URL / `MockGateway` / synthetic event — grep diffed test files for `http`/`@pytest.mark.live` and reject any network dependency in the gate. |
| **G2 — `planner.py` untouched** | `git diff main -- backend/app/agent/planner.py` **empty** every iteration and at merge. The planner open-loop (incl. the modal M3=1) is the B2 named ceiling — disclosed, never rewritten. |
| **G3 — no verifier loosened** | diff-review every change to `eval/eval_set/*.yaml` asserts and `eval/verify/state.py`. A verifier may be tightened or corrected to the actual rendered text, **never** weakened, and **never** has a `text_contains` added to pass a task. New live tasks carry a page-specific assert (url / h1 / scoped-selector / iframe), zero `text_contains`. |

**G3 sub-clause (verify-path boundary, unchanged):** a fix may touch verify-after-act **orchestration /
timing** (e.g. `settle_loading`'s wait condition) but **NEVER** the independent state-check **assertion**
in `state.py` — that ruler is **frozen** during a fix. Any change to `state.py`'s assertion logic (or a
task's `assert:`) made *to pass a failing task* is an automatic discard.

A treatment that lifts M1/M2 but trips any guard — or raises M3 — is **reverted**. One-change discipline.

---

## 4. Per-iteration scope — what ONE probe looks like

**One change per iteration.** Exactly one of:

- **Probe B — eval breadth on a diverse real site (PRIMARY driver this round).** Add **one** task on a
  structurally-distinct real domain in a category the tier under-covers. Requirements: **page-specific
  verifier, zero `text_contains`**; a bot-wall is routed **BLOCKED→abstain** (`detect_block`, never
  solved/evaded) and scored `expect_abstain` only when abstaining is genuinely correct; **throttled /
  polite** (one task, real navigation, no hammering). Each new site is **characterized live before
  adoption** (exactly as round-1 did), so a silent-failure candidate is caught and discarded *before* it
  enters the tier (M3 protected pre-commit).

  *Candidate pool (grouped by category; each characterized live before adoption — not all will be clean):*
  - **docs:** developer.mozilla.org, www.w3.org, www.rfc-editor.org — likely clean, deterministic nav.
  - **maps:** www.openstreetmap.org — automation-tolerant, deterministic URL/search.
  - **reference:** www.gutenberg.org, archive.org — likely clean; britannica.com — likely bot-wall (r1
    finding) → abstain.
  - **gov:** www.weather.gov, www.govinfo.gov, www.sec.gov (EDGAR) — likely clean, deterministic.
  - **news:** lobste.rs, text.npr.org / apnews.com — likely clean; reuters/bloomberg/nytimes —
    bot-wall/paywall → abstain.
  - **media:** commons.wikimedia.org (distinct registrable domain + distinct content type) — likely clean.
  - **finance:** finance.yahoo.com, marketwatch.com, tradingview.com — likely bot-wall → abstain.
  - **shopping:** amazon (discarded r1), ebay, walmart — likely bot-wall → abstain (or, if `detect_block`
    misses the wall, a silent failure → **discard**, like Amazon).

  Likely-clean sites grow M2 with a verified or honest-fail row; likely-bot-wall sites grow M2 with an
  **abstain** row (route-don't-evade) **iff** `detect_block` catches the wall — and if it doesn't, they
  either become a Probe-A `detect_block` fix (below, regression-risk-flagged) or a documented discard. Both
  outcomes are kept breadth evidence; a silent failure is never kept.

- **Probe A — attribution-targeted GROUND-TIME fix.** When a breadth site surfaces a **ground-time**
  failure (the agent grounded + acted, then failed later — its own fixable gap), fix it **exactly the
  round-1 way**: the fix lives in **executor / recover / perceive / locate** or in verify-after-act
  **orchestration / timing** — never `planner.py`, never the state-check assertion — and ships with **and
  is KEPT on** a **deterministic offline test that reproduces the specific failure**. The deterministic
  green is the **primary keep signal**; the live-row flip is corroboration only.
  *Concrete candidates already evidenced (`ANALYSIS.md` §5):* settle-before-perceive on JS-first /
  redirecting sites (#2); press-Enter-over-autocomplete as an **executor submit-strategy** preference (#3,
  *not* a planner change); deterministic interactability tie-break for count-badge twins (#4); honeypot /
  hidden-input filter in `perceive` (#5); extend `settle_loading` to wait-for-target on no-spinner SPA AJAX
  (#6); modern-Cloudflare / Amazon markers in `detect_block` (#1 — **high regression risk**: a too-eager
  block heuristic false-abstains and lowers M1, so it ships with a deterministic block-page fixture **and**
  a live no-false-abstain regression check across the verified domains, or it is not earned).

- **Plan-time failures → NAME, never fix.** A plan-time tag = the planner aimed at something that doesn't
  resolve (open-loop guessing) — the B2 ceiling, including the modal M3=1. Name it in the findings with the
  concrete site/target; do **not** fix it; **never touch `planner.py`**. Likewise the perception/grounding
  named ceilings: iframe-piercing, search-box-strategy, SPA-no-spinner, bot-walls.

> **Attribution honesty note (carried):** the plan-time/ground-time tag is a *first-order heuristic*
> (`modal` is tagged ground-time but is root-caused to B2 planner). A plan-time tag means "don't chase with
> a planner change"; the human checkpoint (§7) makes the final plan-time vs named-ceiling call. Only
> grounded-then-failed-later (ground-time) failures are unambiguous Probe-A targets.

---

## 5. Keep / Discard rule

- **KEEP a Probe-A (ground-time fix)** iff: its **deterministic offline test goes green** (reproduces the
  specific failure and asserts the fix) **AND** all three guards pass **AND M3 does not rise**. The
  deterministic green is the primary, noise-immune signal; the live re-run is supporting evidence only. A
  lucky live-row flip is **never** the basis. If the deterministic test can't be written, defer the fix.
- **KEEP a Probe-B (breadth task)** iff: it adds **+1 distinct, human-audited real domain** (§7) with a
  sound page-specific verifier (zero `text_contains`) **AND** the guards pass **AND M3 does not rise**.
  Probe-B's keep signal is the structural M2 count + the human-audit, not a verified flip: a new real-site
  task may legitimately land RED / abstain, and that is kept evidence of a new failure *class*.
- **DISCARD** iff: it moves no independent signal, OR it trips a guard, OR — the cardinal sin — it
  **raises M3** (a new silent failure, like Amazon in round-1). A new silent failure is discarded the
  iteration it appears unless it is immediately convertible to a Probe-A deterministic fix.
- **Every discard is documented as a hard gap** in the findings (treatment, why it failed, what it would
  take to do safely). A discard is data, not a deletion.

---

## 6. Stop conditions (bounded)

Stop and disclose when ANY holds:
1. **Breadth target reached** — M2 ≈ **15–20 distinct real domains**, OR new additions only surface
   already-named ceilings (bot-wall not caught · iframe · search-box · planner open-loop), i.e. the
   frontier yields no new distinct clean/abstain domain.
2. **Failure tail all plan-time / named-ceiling** — every remaining live-tier non-verified row traces to a
   known class, none a new unexplained defect.
3. **M1 / M3 plateau across 2+ iterations** (no independent signal moves above noise; M2 also stalls).
4. **Budget: ~25 iterations** (hard cap).

---

## 7. Human-in-the-loop checkpoints (non-negotiable)

- Before trusting a new breadth task: confirm the site is **structurally distinct** (not a practice clone,
  not a near-duplicate of an existing domain/registrar) and the verifier is sound (page-specific, can
  actually fail).
- Every "red" gets **one trace eyeballed** to classify it: real ground-time defect (Probe-A candidate) vs
  verifier artifact vs plan-time / named ceiling. The attribution tag is the first cut; the human makes the
  final call.
- A **Probe-A KEEP rests on its deterministic offline test**, never on a live row. A **Probe-B KEEP** rests
  on the structural M2 count + this audit.
- **M3 is read from a full-tier re-run** (re-evaluate all non-verified rows + the carried `modal`), never
  inferred from the touched task — the explicit round-1 fix.

---

## 8. Where findings are written · isolation · NEVER pushed

- **Execution runs in a FRESH isolated git worktree branched off the NEW `main`** (round-1 already merged).
  `main` is never touched directly.
- **Per-iteration findings (human narrative)** → `research/autoresearch-round-2-findings.md` (running log:
  iter, probe type, target, before/after independent signals, KEEP/DISCARD + why; discards documented as
  hard gaps). A breadth snapshot (distinct domains × categories × outcome-class) is regenerated from the
  live YAML.
- **Structured progress ledger (machine-readable twin)** → `research/round-2-progress.json` —
  **append-only**, one record per iteration, **same schema as round-1**:
  ```json
  {
    "iter": 1,
    "probe_type": "B",
    "target": "<task id (Probe A) or domain (Probe B)>",
    "metrics_before": { "M1": 0.750, "M2": 7, "M3": 1 },
    "metrics_after":  { "M1": 0.762, "M2": 8, "M3": 1 },
    "decision": "kept",
    "reason": "<one line>",
    "guards_ok": true
  }
  ```
  `probe_type` ∈ {`A`,`B`} (plus a final `snapshot` record for the authoritative full-tier re-run, as in
  round-1) · `decision` ∈ {`kept`,`discarded`} · `guards_ok` = all of G1/G2/G3 passed AND M3 did not rise.
- **Source of truth for every metric:** the real harness (`python -m eval.run_live_tier` → live
  `REPORT.md` + `AUDIT.md`); the audit attribution drives targeting. The round **opens and closes** with a
  full-tier run (open = re-confirm baseline; close = official deltas).
- **After my review, merged back to `main`** (the kept work: any ground-time fixes + their deterministic
  tests, the breadth tasks, the research artifacts). **Nothing is pushed — ever, at any stage.** I push by
  hand after review.

---

## 9. Self-check against your review bar

- **Every metric independent (no Goodhart)?** Yes — M1/M2/M3 each anchored to the independent state check
  (never `nominal`); the independence triangle holds (verified-rate vs M3-no-rise oppose; breadth vs
  verified-rate trade off).
- **Guards protect the gate AND the planner AND the ruler?** Yes — G1 (≥113 green + network-free, two
  checks), G2 (`planner.py` diff empty — incl. the modal M3=1 stays unfixed), G3 (verifier diff-review,
  zero `text_contains`) + the G3 sub-clause freezing the `state.py` assertion.
- **Keep rule anchors on a deterministic test, not a lucky flip?** Yes — Probe-A KEEP is gated on a
  deterministic offline test reproducing the specific failure; the live re-run is corroboration only.
- **M3 can't silently rise?** Yes — baseline M3=1 is the floor; any new silent failure is an automatic
  discard, and M3 is re-measured from a full-tier re-run each iteration (the round-1 fix), not inferred
  from touched tasks.
- **Stop conditions real?** Yes — breadth target (~15–20), named-ceiling tail, 2-iteration plateau,
  25-iteration cap.
- **Scope bounded?** Yes — one change per iteration; two probe types; plan-time = name-don't-fix; named
  ceilings strictly off-limits.
- **Discards documented honestly?** Yes — §5 requires every discard recorded as a hard gap; the cardinal
  rule is M3-no-rise (a new silent failure is discarded regardless of a nicer-looking M1/M2).
