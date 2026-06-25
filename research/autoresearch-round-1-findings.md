# Autoresearch Round 1 — Findings (running log)

Baseline (current clean main @ HEAD): offline gate **110** green/network-free; live tier **6/9 verified**,
**4 distinct domains** (en.wikipedia.org ×4, docs.python.org, the-internet.herokuapp.com, www.google.com);
M3 SILENT_FAILURE count = **1** (`live_internet_lazyload`, tagged ground-time). Worktree branch
`autoresearch/round-1` off `main`; nothing pushed.

| metric | baseline |
|---|---|
| M1 live verified-rate | 6/9 = 0.667 |
| M2 distinct real domains | 4 |
| M3 SILENT_FAILURE count | 1 |

---

## Iteration 1 — Probe A: lazy-load settle (ground-time fix) — **KEPT**

**Target:** `live_internet_lazyload` SILENT_FAILURE (audit-tagged ground-time). The click triggers a
spinner, the result renders async; verify-after-act raced the spinner → target absent → `verified=False`
while the DOM did change → `nominal=True`: a textbook silent failure.

**Change (verify-after-act TIMING/orchestration only — never an assertion):**
- `recover.settle_loading(page)` — bounded wait (≤8s) for a *visible generic* loading indicator
  (`#loading`, `[aria-busy]`, `[role=progressbar]`, `.loading/.spinner/.loader`) to go hidden; fast no-op
  when none is visible.
- `executor.py` — one call inserted between the act try/except and `verify.verify_after_act`. The
  state-check assertion in `state.py` is untouched (plan G3 sub-clause: timing may move, the ruler may not).

**KEEP signal (primary = deterministic offline):** `tests/test_settle_loading.py` (3 tests) reproduces the
spinner-race on a `data:` fixture with **no network** and asserts the run goes nominal **AND** verified
(not silent). Green only with the settle wired; reverting it turns the e2e test red.

**Independent signals:**
| metric | before | after | how measured |
|---|---|---|---|
| M1 live verified-rate | 6/9 = 0.667 | 7/9 = 0.778 | live re-run of the lazyload row → `nominal=True verified=True asked=False` (corroboration; the deterministic test is the basis) |
| M2 distinct real domains | 4 | 4 | no new domain (not a breadth probe) |
| M3 SILENT_FAILURE count | 1 | **0** | the only silent-failure row now verifies; **M3 invariant now holds at 0** |

**Guards:** G1 offline gate **113** green/network-free (110 + 3 new). G2 `git diff main -- planner.py`
empty. G3 `git diff main -- eval/verify/state.py` empty — assertion frozen.

**Decision: KEPT.** Real independent signal flipped (deterministic test green + M3 1→0, live-corroborated),
all three guards pass. Files changed vs main: `backend/app/agent/recover.py`, `backend/app/agent/executor.py`,
`backend/tests/test_settle_loading.py`.

---

## Iteration 2 — Probe B: breadth `example.com → iana.org` (reference) — **KEPT**

**Why this domain:** the tier was Wikipedia-heavy (4 domains, en.wikipedia.org ×4). example.com is a
structurally-distinct **reference** domain whose only link leaves the site (`More information...` →
`iana.org`) — a clean cross-domain navigation, ultra-stable, no bot-wall.

**Task (page-specific verifier, zero `text_contains`):** `live_example_more_info_nav` —
`assert: url_contains "iana.org"`. The agent cannot pass by claiming success: the check reads the URL it
actually landed on.

**Live characterization:** `nominal=True verified=True asked=False blocked=False steps=2` → **VERIFIED**.

**Independent signals:**
| metric | before | after | how |
|---|---|---|---|
| M1 live verified-rate | 7/9 = 0.778 | 8/10 = 0.800 | new row verifies live |
| M2 distinct real domains | 4 | **5** | +example.com (reference); also exercises iana.org |
| M3 SILENT_FAILURE count | 0 | **0** | verified, not silent |

**Guards:** G1 offline gate unaffected (live tier is separate from `-m "not live"`; re-confirmed 113 green
at round end). G2 planner.py untouched. G3 only a YAML add with a page-specific `url_contains` verifier;
`state.py` frozen, zero `text_contains`.

**Decision: KEPT.** +1 distinct human-audited real domain with a sound page-specific verifier, guards pass,
M3 stays 0. File changed vs main: `eval/eval_set/live_real_world.yaml`.

---

## Iteration 3 — Probe B: breadth `news.ycombinator.com → newest` (news) — **KEPT**

**Why this domain:** a structurally-distinct **news aggregator** — server-rendered, automation-tolerant,
no bot-wall, different task shape (top-nav click) from the reference/info domains already present.

**Task (page-specific verifier, zero `text_contains`):** `live_hackernews_newest_nav` —
`assert: url_contains "newest"`.

**Live characterization:** `nominal=True verified=True asked=False blocked=False steps=2` → **VERIFIED**.

**Independent signals:**
| metric | before | after | how |
|---|---|---|---|
| M1 live verified-rate | 8/10 = 0.800 | 9/11 = 0.818 | new row verifies live |
| M2 distinct real domains | 5 | **6** | +news.ycombinator.com (news) |
| M3 SILENT_FAILURE count | 0 | **0** | verified, not silent |

**Guards:** G1 offline gate unaffected. G2 planner.py untouched. G3 page-specific `url_contains`, `state.py`
frozen, zero `text_contains`.

**Decision: KEPT.** +1 distinct human-audited real domain, sound verifier, guards pass, M3 stays 0.
File changed vs main: `eval/eval_set/live_real_world.yaml`.

---

## Iteration 4 — Probe B: breadth `amazon.com` (shopping) — **DISCARDED** (named ceiling)

**Why this domain:** a real commercial **shopping** site, the breadth category most likely to bot-wall —
deliberately probed to surface the route-don't-evade boundary.

**Task probed (not committed):** `live_amazon_search` — search "usb cable", `assert: url_contains "k=usb"`.

**Live characterization:** `nominal=True verified=False asked=False blocked=False steps=5` → **SILENT_FAILURE**.
Amazon serves a bot/robot-check interstitial to headless automation; `verify.detect_block` does **not**
recognize that page (it catches Google's `/sorry/` interstitial, not Amazon's robot-check), so the agent
neither abstained nor reached results — it **silently claimed success** (`nominal=True`) while the
independent URL check correctly read `verified=False`. (The page-specific verifier did its job: it caught
the divergence. The defect is upstream — the block detector and the nominal-completion claim.)

**Decision: DISCARDED — the cardinal sin (a silent failure).** Adding this task would push **M3 0→1**, so
it is **not** committed to the tier; M3 stays 0. This is a route-don't-evade outcome that the agent gets
*wrong*: it should abstain (BLOCKED), but the block goes undetected.

**Named ceiling (new this round): block-detector coverage gap.** `verify.detect_block` covers Google's
interstitial but not Amazon-style robot-check / "Continue shopping" walls, so such walls become silent
failures instead of honest abstains. **Not fixed this round** — and deliberately so: tuning `detect_block`
to a specific commercial wall is overfitting-prone and **high regression risk** (a too-eager block
heuristic would *false-abstain* on legitimate pages and **lower M1** on the 6 verified domains). The
correct fix is a future **Probe A**: a deterministic offline fixture reproducing an Amazon-style block page,
assert `detect_block` classifies it BLOCKED → agent abstains, **plus** a live regression check that the
verified domains don't start false-abstaining. Earned in a future round, not rushed here. This belongs in
the honest `UNSUPPORTED_SITES` disclosure (real commercial bot-walls → unsupported).

**Independent signals:** M1 unchanged (8/10 → not added), M2 unchanged (5 — discarded), M3 **0** (held).

---

## Iteration 5 — Probe B: breadth `gnu.org → Licenses` (reference) — **KEPT** (graceful-abstain class)

**Why this domain:** a distinct **reference/org** domain with a sidebar-nav target — probed to test the
locate cascade on a real, content-heavy navigation (not a practice page).

**Task (honest page-specific verifier, zero `text_contains`):** `live_gnu_licenses_nav` —
`assert: url_contains "licenses"`. Deliberately **not** `expect_abstain`: gnu.org/licenses is a public
page the agent *should* reach, so scoring an abstain as "success" would be dishonest. It lands as an honest
non-verified row.

**Live characterization:** `nominal=False verified=False asked=True blocked=False steps=4` → **ABSTAIN**.
The locate cascade did not find the "Licenses" link, and the agent **honestly abstained** (`ask_user`)
instead of claiming success. **Not** a silent failure — `nominal=False`, so M3 is untouched.

**Independent signals:**
| metric | before | after | how |
|---|---|---|---|
| M1 live verified-rate | 9/11 = 0.818 | 9/12 = 0.750 | new RED row (honest abstain) — the **breadth↔verified tradeoff** the plan predicts (§2) |
| M2 distinct real domains | 6 | **7** | +gnu.org (reference) |
| M3 SILENT_FAILURE count | 0 | **0** | abstain is `nominal=False` — the agent failed *safely*, did not lie |

**Named ceiling (this row): locate-on-real-nav.** The cascade can miss a nav link on a content-heavy real
page; the desirable property is that the agent then **abstains** (M3-safe) rather than silently failing.
This is the *good* failure mode — contrast iter-4 (Amazon), where the same inability produced a silent
failure because a bot-wall masked it.

**Decision: KEPT.** Probe-B keep rests on the structural **M2 +1** + this audit (§5/§7), not on the
(noisy) verified flag; the verifier is sound (page-specific, can fail); guards pass; M3 stays 0. The RED row
is kept evidence of a graceful-failure class. File changed vs main: `eval/eval_set/live_real_world.yaml`.

---

## Round 1 — Conclusion (STOPPED on condition 1; NOT merged, NOT pushed — for review)

**Stop reason (plan §6, condition 1):** the live-tier failure tail decomposes **entirely** into known
classes — `modal` (plan-time planner open-loop), `iframe` (perception/iframe-pierce ceiling), `gnu`
(locate-on-real-nav, graceful abstain), `google` (correct BLOCKED abstain). The one *new* observation,
Amazon's silent failure, was **named** (block-detector coverage gap) and **discarded**. No remaining
unexplained defect → stop. (Conditions 2/3 not reached: M2 still climbing, 5 of ~25 iterations used.)

**5 iterations: 4 kept, 1 discarded.**

| iter | probe | target | outcome | M1 | M2 | M3 | decision |
|---|---|---|---|---|---|---|---|
| 0 | — | baseline (clean main) | — | 0.667 | 4 | 1 | — |
| 1 | A | lazyload settle (ground-time fix) | deterministic test green; live VERIFIED | 0.778 | 4 | **0** | **kept** |
| 2 | B | example.com→iana.org (reference) | VERIFIED | 0.800 | 5 | 0 | kept |
| 3 | B | news.ycombinator.com→newest (news) | VERIFIED | 0.818 | 6 | 0 | kept |
| 4 | B | amazon.com (shopping) | SILENT_FAILURE (undetected block) | 0.818 | 6 | 0 | **discarded** |
| 5 | B | gnu.org→Licenses (reference) | ABSTAIN (graceful) | 0.750 | **7** | 0 | kept |

> ⚠️ **CORRECTION (authoritative consolidated re-run).** The per-iteration M3 values in the table above are
> single-run measurements of the *touched* tasks only; I carried `modal`'s stale baseline tag instead of
> re-measuring it. The full-tier `run_live_tier` snapshot (below) shows **M3 = 1, not 0** — `live_internet_modal`
> is itself a SILENT_FAILURE. The headline is corrected accordingly. This is the methodology lesson of the
> round: **M3 must be read from a full-tier re-run, never inferred from touched tasks** — a silent failure can
> lurk in a task you didn't change.

**Headline (corrected, honest):** Iteration 1 **eliminated the lazyload silent failure** — verified two
independent ways (deterministic offline test green; `lazyload = OK/verified` in the authoritative snapshot).
But **global M3 = 0 was NOT achieved**: the consolidated re-run shows the pre-existing `modal` task is *also*
a silent failure (the agent claims success on a planner-emitted navigate-only plan **without grounding the
modal**; intermittently masked as HONEST_FAIL by transient Copilot gateway errors — see the 3× re-run). So
the silent-failure **count is unchanged at 1**, but it moved from a *deterministically fixable* defect
(lazyload, now fixed) to a *planner-rooted* one (modal — the B2 open-loop ceiling, **never-fix** by guard G2).
Net: one real defect fixed; one pre-existing silent failure newly **named**, not introduced by this round.

**Independent deltas (corrected):**
- **M3 (silent failures): 1 → 1** — lazyload's silent failure eliminated (real, deterministic + verified),
  but the consolidated re-run reveals `modal` silent-fails → count holds at 1. **Not a regression** (planner.py
  + state.py untouched; the modal defect is pre-existing and planner-rooted). *Newly named target* for a
  future round, not earnable here without touching the planner ceiling.
- **M2 (distinct real domains): 4 → 7** — +example.com (reference), +news.ycombinator.com (news),
  +gnu.org (reference); the tier is no longer Wikipedia-dominated. (iana.org additionally exercised as
  iter-2's verified destination.) **Solid — structural, run-independent.**
- **M1 (verified-rate): 0.667 → 0.750** — consolidated snapshot confirms **9/12 verified**. Rose on iters
  1–3, deliberate honest dip at iter 5 (gnu graceful-fail) — the breadth↔verified tradeoff (§2). Net up, on a
  broader, harder tier.

**Guards held every iteration AND at round end:** G1 offline gate **113** green/network-free; G2
`planner.py` untouched; G3 `state.py` assertion frozen, zero `text_contains` added. Whole-round diff is
surgical: `recover.py` + `executor.py` + `test_settle_loading.py` (capability), `live_real_world.yaml`
(breadth), `research/*` (artifacts). Nothing else.

**New named ceilings surfaced (feed `UNSUPPORTED_SITES` / future rounds):**
1. **Modal navigate-only silent failure** (the corrected headline) — on `live_internet_modal` the planner
   emits a navigate-only plan and the agent declares `nominal=True` **without grounding the modal**, so the
   modal-title assertion fails → SILENT_FAILURE. Rooted in the planner's open-loop behaviour (**B2 ceiling,
   never-fix** under G2) compounded by a too-lax nominal-completion claim. A future **Probe A** could tighten
   nominal-completion (don't claim done when verify-after-act shows the goal element was never grounded)
   **without** touching planner.py or the assertion — but it is real, deferred, and high-care.
2. **Block-detector coverage gap** — `verify.detect_block` catches Google's `/sorry/` interstitial but not
   Amazon-style robot-check walls, so those become *silent* failures rather than honest abstains. Future
   **Probe A**: deterministic block-page fixture + `detect_block` classifies it BLOCKED, **gated on** a live
   regression check (a too-eager heuristic false-abstains and lowers M1). Deferred — high regression risk.
3. **Locate-on-real-nav** — the cascade can miss a nav link on a content-heavy real page; the desirable
   property (demonstrated by gnu) is that the agent **abstains** rather than silently failing.

**Pre-existing named ceilings (unchanged, never touched):** plan-time planner open-loop (`modal`),
iframe-piercing perception (`iframe`), search-box-strategy, SPA-no-spinner, CSS-anim verifier-artifact,
bot-wall route-don't-evade (`google`).

**Disposition: DO NOT MERGE.** Branch `autoresearch/round-1` off `main`, commits local-only, nothing
pushed. Awaiting human review before any merge back to `main`.

### Consolidated authoritative snapshot (`eval/REPORT.md` + `eval/AUDIT.md`, single full-tier `run_live_tier`)

Regenerated at round end — the plan's named source of truth (§8). `attribution_coverage = 1.000`.

- **Live tier: 9/12 verified.** OK rows: helium, pydocs-json, wiki-signin, wiki-search-submit,
  wiki-autocomplete, **lazyload** (✓ iter-1 fix), **example→iana** (✓ iter-2), **HN→newest** (✓ iter-3),
  + google (BLOCKED→correct abstain, scored verified). Non-verified: **modal (SILENT_FAILURE, ground-time)**,
  iframe (HONEST_FAIL, plan-time, abstained), gnu (HONEST_FAIL — this run it honest-failed without asking;
  still `nominal=False`, M3-safe).
- **Flag tally (20 = 12 live + 8 day-3 regression batch): OK=16, SILENT_FAILURE=1, BLOCKED=1, HONEST_FAIL=2.**
- **M3 = 1** (the lone SILENT_FAILURE = `modal`). **This is the authoritative number; it supersedes the
  per-iteration M3=0 bookkeeping above.**
- `modal` 3× re-run characterization: HONEST_FAIL (gateway error, steps=0) · **SILENT_FAILURE** (steps=1) ·
  HONEST_FAIL (gateway error, steps=0) — i.e. **when the gateway responds, modal silent-fails**; the
  HONEST_FAILs are transient Copilot `send_and_wait` errors, not a different agent behaviour.

**What is solid vs what is corrected:**
- *Solid:* iter-1 lazyload fix (verified two ways), M2 4→7 (structural), M1→0.750 (9/12), all guards held,
  surgical diff, the Amazon discard (correctly kept out to protect M3).
- *Corrected:* the M3=0 / "held at 0" claim. True M3=1; the round did **not** reach global zero silent
  failures — `modal` is a pre-existing, planner-rooted silent failure the full re-run exposed.

---
