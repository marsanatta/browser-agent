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
