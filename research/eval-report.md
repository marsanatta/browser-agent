# Evaluation Report — Live Eval Set, Reliability, and Honest Failure Modes

Consolidated writeup of the eval-expansion + Phase B work. Self-contained; integrate into
ANALYSIS.md after rebasing `eval-expansion` onto the latest `main`. Raw data:
`phase_b_dev_round{0..3}.json`; methodology details: `eval-expansion-plan.md`,
`phase-b-findings.md`.

## 1. The eval set — designed by PURPOSE, not volume

**80 live cases across 19 domains**, every case carrying a `purpose` tag (the ONE distinct
capability or failure-mode it tests). Redundant same-purpose-same-site filler was removed
(147 → 80) so each case earns its place; a few cross-site samples per generic purpose are
kept for held-out statistical power.

**Three-way split, disjoint BY SITE** (so "generalization" is real, not site-memorization):
- **dev (~39)** — drives engine changes; the only set RCA'd per-case.
- **holdout (~21)** — the selection keep-gate: scored to decide what to keep, never RCA'd.
- **sealed (~20)** — the once-only honest final metric: scored a single time at the very end,
  never used for any keep decision. The loader REFUSES to score it except an explicit
  `--sealed` pass (guards against accidental peeking / selection over-fit).

**15 distinct purposes**: single/multistep/cross-domain nav, synonym-locate, search-submit,
autocomplete, pagination, extract-detail, modal/lazyload/iframe widgets, intent-drift decoys,
bot-wall & login-wall abstain. ~18% are unsupported (login/captcha walls) that must route to
honest abstain — not faked success.

**Ground-truth discipline (two-pass admission):** every case passed (1) an independent
real-browser probe confirming its assert holds at the solution page and the path is
bot-wall-free, AND (2) an independent reviewer confirming the assert is true ONLY IF the task
is done (weak "value shows on a listing" asserts were dropped; the two reviewers agreed 100%).
The frozen eval arbiter (`state_check`) is DELIBERATELY separate code from the agent's in-loop
self-check — never validate with the verifier's own formula.

## 2. Reliability results (dev split, real agent via Copilot)

| metric | value | meaning |
|---|---|---|
| verified pass rate | **~37/39 (95%)** after eval cleanup | independent state-check confirms真完成 |
| nominal (self-report) | ~97% | what the agent claims |
| **M3 silent-failure** | **~1/39** after eval cleanup | nominal=True but verified=False (the agent lied) |

(holdout and sealed are intentionally unmeasured here — held-out is the keep-gate run only
when a change is kept; sealed is the once-at-the-end honest number.)

## 3. Honest findings (the substance)

### 3a. The honest-goal-criterion fix was REJECTED — B2 planner-open-loop ceiling
A failure-driven loop targeted the silent-failure cluster. Deterministic RCA: `nominal =
actions-executed`, not `goal-achieved`; the navigate path never gated on a goal. The
experimented fix (executor navigate goal-gate, proven RED→GREEN; + planner prompt to emit a
task-completion goal) was measured over **3 controlled iterations** and **rejected** — each
prompt change just shifted which passing case broke (modal → modal → modal+sapiens_stock).
The planner cannot reliably emit accurate, discriminating goal predicates a-priori; for
auth-walled tasks the wall MIMICS success in both text AND URL (e.g. logged-out
`Special:Watchlist` redirects to `...UserLogin?returnto=Special:Watchlist`). Discarded
honestly — keeping only on a measured improvement is the gate.

### 3b. 2 of 3 "silent failures" were EVAL-DESIGN ARTIFACTS
Re-scrutinising the cluster (2 live runs/case): `oxygen_search` ("...atomic number 8...")
mixed world-knowledge into a browser-nav task — reframed to the direct "open the Oxygen
article" → reliably verified. `signup` ("...create a new account") was vague/multi-step with
no a-priori-verifiable goal — reframed to "open the account-creation page" → correctly
abstains at the captcha. Only `watchlist` is a REAL silent failure (login-wall blindness).
**Lesson: validate case quality before treating M3 as a clean signal or spending engine work.**
The eval set is stronger for it; the headline M3 dropped from 3 to ~1.

## 4. Honest residual failure modes (surfaced, not hidden)

- **Login-wall blindness (`watchlist`)** — the agent claims success on a non-captcha login
  wall instead of abstaining. Fixable only with task-semantic wall detection (distinguish "the
  task WANTS the login page" from "the task wants something behind it") — an open problem.
- **iframe non-piercing (`internet_iframe`)** — the locator cascade can't act inside an iframe;
  the agent honestly abstains (not silent).
- **Intent-drift coverage is dev-only** — the 8 disambiguation decoys live on Wikipedia (a dev
  site); widget/intent-drift purposes are site-bound and can't be placed on holdout/sealed.
- **`table_lookup` has no clean live case** — sortable tables don't trigger reliably and
  static-table value asserts are weak; documented gap rather than a flaky case.
- **System-level honesty is in place** — the independent `verified` channel catches every
  silent failure, M3 measures the residual, and production (main `e45d612`) never displays
  "verified" without an independent goal check. Agent-level self-report optimism is bounded
  and measured, not eliminated.
