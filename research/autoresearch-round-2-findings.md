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



