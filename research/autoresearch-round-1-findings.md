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
