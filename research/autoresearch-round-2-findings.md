# Autoresearch Round 2 — Findings (running log)

Plan: `research/autoresearch-round-2-plan.md`. Worktree branch `autoresearch/round-2` off the new `main`
(`61970b0`, round-1 merged). Nothing pushed; do not merge until review.

**Frontier:** breadth (M2 7 → ~15–20 distinct real domains) + the ground-time failures it surfaces.
**Carried named ceilings (off-limits, name-not-fix):** B2 planner open-loop (incl. `live_internet_modal`
M3=1) · iframe-piercing · search-box-strategy · bot-walls (route-don't-evade) · block-detector coverage gap.
**M3 invariant:** baseline = 1 (`modal`); must NOT rise above 1 (a new silent failure = automatic discard,
the Amazon rule). M3 read from a full-tier re-run each iteration, never inferred from touched tasks.

## Baseline (opening full-tier re-run, new main) — re-confirmed

`eval/REPORT.md` + `eval/AUDIT.md` (2026-06-25 12:10 UTC, `attribution_coverage=1.000`).

| metric | baseline (this run) | note |
|---|---|---|
| M1 live verified-rate | **8/12 = 0.667** | live-noise-sensitive (round-1 snapshot was 9/12; the delta is one task, `helium`, flipping — see below) |
| M2 distinct real domains | **7** | en.wikipedia.org, docs.python.org, www.google.com, the-internet.herokuapp.com, example.com, news.ycombinator.com, www.gnu.org — the stable, noise-immune signal |
| M3 SILENT_FAILURE count | **1** | flag tally OK=15, SILENT_FAILURE=1, ABSTAIN=1, HONEST_FAIL=3 |

**The M3=1 silent failure SHUFFLED between runs — this is the live-noise reality the methodology targets.**
Round-1's final snapshot had `live_internet_modal` as the lone SILENT_FAILURE; this opening re-run has
`modal` **honest-failing** (plan-time, `nominal=False`) and instead **`live_wikipedia_helium_retrieval`**
as the lone SILENT_FAILURE (ground-time-tagged). Re-characterized helium 2×: SILENT_FAILURE when the
gateway responds (the other run was a Copilot `send_and_wait` gateway flake → steps=0 honest-fail).

**Classification of the helium silent failure → NAMED ceiling, not a Probe-A target.** Its trace
(`eval/AUDIT.md`): the planner emitted `navigate www.wikipedia.org` (the **multilingual portal**, not the
`en.wikipedia.org` start_url), `fill "Helium"`, `click "Search"`, `click "Helium"` (**AMBIGUOUS_L2**) — and
landed on a non-article page (`h1 ≠ "Helium"`) yet claimed `nominal=True`. Root cause is the
**search-box-strategy ceiling + plan-time portal navigation + lax nominal-completion** — all planner-rooted
/ named, **off-limits** (the same family as the `modal` M3). Fixing it cleanly would need `planner.py`
(frozen by G2) or a circular use of the verifier to set `nominal` (forbidden). So it is **named, not
fixed**, and tracked as part of the carried M3=1 band.

**Carried M3=1 band (named-ceiling silent failures, shuffle run-to-run, never chased):**
`live_wikipedia_helium_retrieval` ↔ `live_internet_modal` — both planner-rooted (open-loop plan /
search-box / lax nominal-completion). **M3 invariant for round-2: the COUNT must not RISE above 1** — i.e.
no *new* breadth-added silent failure (each new site characterized live before adoption; a silent-failer is
discarded pre-commit, the Amazon rule). Existing-tier shuffle within the band is live noise, not a
breadth-introduced regression.

---

## Iterations

> Each iteration = one live characterization of one new site (the per-adoption M3 guard: a silent-failer is
> caught and discarded *before* it enters the tier). Candidates are characterized with **final-URL capture**
> so a wrong verifier-substring shows the real landing page rather than mis-flagging a clean run as silent.
> M3 is re-confirmed by a full-tier re-run at checkpoints (a literal full-tier run per single add is
> cost-prohibitive — hours; the pre-adoption characterization is what protects M3 each iteration).

### Iter 1 — Probe B: `openstreetmap.org` → Log In (maps) — **KEPT** (VERIFIED)
New category **maps**. `nominal=True verified=True`, landed `…/login`. M1 8/12→9/13=0.692, M2 7→**8**, M3 1.

### Iter 2 — Probe B: `lobste.rs` → Comments (news) — **KEPT** (VERIFIED)
Tech link-aggregator, distinct from HN. `verified=True`, landed `lobste.rs/comments`. M1 9/13→10/14=0.714,
M2 8→**9**, M3 1.

### Iter 3 — Probe B: `developer.mozilla.org` → Blog (docs) — **KEPT** (VERIFIED)
Large real docs site (distinct registrable domain from docs.python.org). `verified=True`, landed
`/en-US/blog/`. M1 10/14→11/15=0.733, M2 9→**10**, M3 1.

### Iter 4 — Probe B: `archive.org` → Log In (media) — **KEPT** (graceful ABSTAIN)
New category **media / digital library**. The "Log In" link sits behind a compact menu; the locate cascade
missed it and the agent **abstained** (`nominal=False asked=True`, stayed on `archive.org/`) — honest
non-completion, **M3-safe** (the round-1 gnu-class graceful failure). Kept as a RED row + a distinct domain.
M1 11/15→11/16=0.688 (breadth↔verified tradeoff), M2 10→**11**, M3 1.

**Batch 1 net: M2 7→11 (+maps, +news/lobsters, +docs/mdn, +media/archive), M3 held at 1, no silent failure.**

### Iter 5 — Probe B: `www.gov.uk` → Help (government) — **KEPT** (VERIFIED)
New category **government**. `verified=True`, landed `gov.uk/help`. M1 11/16→12/17=0.706, M2 11→**12**, M3 1.

### Iter 6 — Probe B: `arxiv.org` → Help (science) — **KEPT** (VERIFIED)
New category **science / preprints**. `verified=True`, landed `info.arxiv.org/help/…` (registrable domain
arxiv.org). M1 12/17→13/18=0.722, M2 12→**13**, M3 1.

### Iter 7 — Probe B: `www.w3.org` → Standards (docs/standards) — **DISCARDED** (SILENT_FAILURE)
`nominal=True verified=False`, but the final URL was still `https://www.w3.org/` — the agent **never left
the homepage** yet claimed success (the "Standards" link wasn't located; lax nominal-completion). This is the
**Amazon rule**: adopting it would push **M3 1→2**, so it is **not** committed — M3 stays 1. Named-ceiling
manifestation (locate-miss + lax nominal-completion, same family as helium/modal — planner-rooted, off-limits).
Hard gap documented; w3.org standards-nav deferred.

### Iter 8 — Probe B: `finance.yahoo.com` → AAPL quote (finance) — **KEPT** (VERIFIED, caveated)
New category **finance**. `verified=True`, landed `finance.yahoo.com/quote/AAPL/` — characterize-before-adopt
passed. **Caveat:** this site is bot-wall-prone (consent / anti-bot interstitials `detect_block` doesn't yet
catch); a future run could serve a wall. Adopted per the literal rule (it verified), with the **close
full-tier run as the M3 arbiter** — if it silent-fails there, it is discarded then. M1 13/18→14/19=0.737,
M2 13→**14**, M3 1.

**Batch 2 net: M2 11→14 (+gov, +science, +finance), one DISCARD (w3.org silent failure, Amazon rule), M3
held at 1.**

### Iter 9 — Probe B: `openlibrary.org` → Log In (books/library) — **KEPT** (VERIFIED)
Distinct registrable domain from archive.org. `verified=True`, landed `openlibrary.org/account/login`.
M1 14/19→15/20=0.750, M2 14→**15**, M3 1.

### Iter 10 — Probe B: `stackoverflow.com` → Questions (Q&A) — **KEPT** (graceful ABSTAIN)
New category **Q&A**. `nominal=False asked=True blocked=False steps=4` → a locate/navigation graceful
abstain (**not** a detected bot-wall — confirmed via a `blocked`-capture re-run), so scored by the honest
assert, **not** `expect_abstain`. M3-safe RED row + distinct domain. M1 15/20→15/21=0.714, M2 15→**16**, M3 1.

### Iter 11 — Probe B: `www.rfc-editor.org` → About (standards) — **DISCARDED** (SILENT_FAILURE)
`nominal=True verified=False`, final URL still `https://www.rfc-editor.org/` — **same class as w3.org**: the
agent never left the homepage yet claimed success (About link not located, lax nominal-completion). Amazon
rule → **not committed**, M3 held at 1. This is the **recurring named-ceiling tail** (locate-miss + lax
nominal-completion, planner-rooted) — a stop signal (§ stop condition 2).

**Batch 3 net: M2 14→16 (+books/openlibrary, +Q&A/stackoverflow), one DISCARD (rfc-editor silent failure),
M3 held at 1. Breadth target (~15–20) reached; the discard tail is now a single recurring named class.**

---

## Round 2 — Conclusion (STOPPED; close full-tier snapshot is the official number; NOT merged, NOT pushed)

**Stop reason:** breadth target reached (M2 16, in the ~15–20 band) **and** the failure tail collapsed to a
single recurring named ceiling — the *locate-miss + lax-nominal-completion silent failure* (`w3.org`,
`rfc-editor.org`: agent claims success while still on the homepage), which is planner-rooted (B2) and
off-limits. Stop conditions 1+2. **No Probe-A code change was earned** — every silent failure round-2
surfaced was a planner-rooted named ceiling (never-fix), so the round is **pure breadth**: zero changes to
`backend/` (planner.py, state.py, executor, recover all untouched).

**11 iterations: 9 kept, 2 discarded.** All 9 kept add a distinct real domain; both discards were
silent-failure candidates kept OUT of the tier (the Amazon rule), so **round-2 introduced no new silent
failure**.

### Close full-tier snapshot (official) — `eval/REPORT.md` + `eval/AUDIT.md`, 2026-06-25, `attribution_coverage=1.000`

- **Live tier: 16/21 verified.** Flag tally **OK=23, BLOCKED=1, HONEST_FAIL=5, SILENT_FAILURE=0.**
- The 5 non-verified rows are **all honest** (HONEST_FAIL / abstain): `modal`, `iframe`, `gnu`, `archive`,
  `stackoverflow` — none falsely claimed success.
- **Bot-wall-prone arbiter passed:** `finance.yahoo.com` **VERIFIED** (reached `/quote/AAPL/` again),
  `stackoverflow` **HONEST_FAIL/abstain** — neither silent-failed, so neither is discarded.

| metric | baseline (open run) | close run (official) | honest reading |
|---|---|---|---|
| **M2 distinct domains** | 7 | **16** | **+9 — the headline, structural and run-independent** (maps, news/lobsters, docs/mdn, media/archive, gov, science, finance, books/openlibrary, Q&A) |
| **M3 silent failures** | 1 (`helium`) | **0** | **RUN-NOISY — do NOT read as "M3=0 achieved."** Baseline=1, close=0: the planner-rooted named-ceiling failures (`helium`/`modal`) manifest as *silent* on some runs and *honest-fail* on others. Round-2's stable result is **no NEW silent failure introduced** (2 candidates discarded); the underlying risk persists, unfixed (off-limits). |
| **M1 verified-rate** | 8/12 = 0.667 | 16/21 = **0.762** | up, on a **much broader tier (21 vs 12)** — a genuine breadth+quality signal, but M1 is run-noisy (helium verified this run, silent-failed at baseline). |

**Honest correction carried from round-1's lesson:** M3 is read from full-tier re-runs, and the two runs
disagree (1 vs 0) — so the truthful statement is **"M3 stayed within its 0–1 noise band; round-2 added zero
new silent failures,"** not "round-2 drove M3 to 0." The `helium`/`modal` silent-failure risk is a
pre-existing planner-rooted ceiling, untouched by this round.

**Guards held every iteration AND at close:** offline gate **113** green/network-free; `planner.py`
untouched; `state.py` assertion frozen; zero `text_contains`; whole-round diff is purely additive
(`live_real_world.yaml` breadth + regenerated `eval/REPORT.md`/`AUDIT.md` + `research/*`) — **no `backend/`
code changed.**

**Named ceilings (unchanged, off-limits, all observed this round):** B2 planner open-loop / lax
nominal-completion (the `helium`/`modal` silent-failure band + the `w3.org`/`rfc-editor` discards) ·
iframe-piercing (`iframe`) · search-box-strategy (`helium` portal-search path) · bot-walls
(route-don't-evade — `google` BLOCKED; `yahoo`/`stackoverflow` are bot-wall-prone and arbiter-tracked).

**Disposition: DO NOT MERGE, NOT PUSHED.** Branch `autoresearch/round-2`, commits local-only. Awaiting
review before any merge to `main`.



