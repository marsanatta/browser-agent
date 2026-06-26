# Round 3 — Make the 5 Failing Real Tasks Verify (REVIEW DOC, not for execution)

**Status: awaiting review. Nothing is executed; show the user before starting.**
**Execution: driven by the `/autoresearch` skill (eval-driven Modify→Verify→Keep/Discard), NOT hand-rolled.**

A **free, time-boxed capability round, focused ONLY on the on-target fix**: make the 5 named failing tasks
**verify on their first attempt**. Agent memory + staleness are **deferred to a later round** (designed, not
built — see the bottom): they address repeat-run cost/speed + cached-strategy drift, which is **not** why any
of these 5 fail.

---

## 0. Goal (the bar)

The 5 tasks reproducibly **verify** (independent `state_check` = `True`, never `nominal`; confirm 2–3× — flaky):
- **python deep-nav** — docs.python.org Standard Library → `json` module.
- **wikipedia search-submit** — "Oxygen" + Enter → the article.
- **wikipedia Sign In synonym** — "Sign In" link is "Log in" → reach UserLogin.
- **google multi-step** — search 台北天氣 → submit → open first result (search-box, NOT bot-wall).
- **gnu.org Licenses click** — reach the licenses page (content-heavy click-grounding).

These fail on the **FIRST attempt, with no memory in play** — so the fix lives in the live
grounding / planning / recovery path, not in cross-run memory.

---

## 1. TWO LOCKS — the whole point (this distinction IS the plan)

### 🔓 LIFTED — capability / scope / file locks (go FREE)
- **No off-limits files.** `planner.py` / `locate.py` / `act.py` / `perceive.py` / `executor.py` / `verify.py`
  (timing) / `recover.py` / agent prompts — all fair game. As many capability changes as the goal needs.
- The audit's deferred items (#3 predict-then-verify, #7-full expected-url, #8-full observe-first, D2,
  press-Enter submit, close-the-loop replan, planner-sees-page) are **IN SCOPE** if they help a target pass.

### 🔒 KEPT — the measuring instruments (do NOT lift; NOT restrictions on what you build)
- **The independent `state_check` is the frozen arbiter.** Do NOT edit `eval/verify/state.py`'s assertion, or
  retune/loosen an existing `assert:`, to make a task pass — that is grading your own exam. (A NEW task with a
  sound page-specific verifier, zero `text_contains`, is allowed; weakening an existing one is an auto-discard.)
- **M3 (silent-failure count) must NOT rise.** Any change that produces `nominal=True, verified=False`
  (a confident wrong-but-plausible result) is an AUTOMATIC DISCARD — the cardinal sin.
- **Keep a change ONLY on a real independent verified-flip** (`state_check`, never `nominal`), confirmed 2–3×.
  A **cost/speed-only or number-only "win" with no accuracy flip is discarded** and written down as a hard gap.
- **Offline gate stays green & network-free** (≥143). **Never pushed.**

### Why the line is hard (today's lesson)
We spent all day cleaning the OPPOSITE mistake: green gate + "converged" breadth while every easy task failed
live, and a verification layer that read real but was hollow. A free round that ALSO drops the honesty gates
just manufactures fake wins faster. **What you can touch = wide open; how you prove it helped = unchanged.**

---

## 2. Methodology — implement in pieces, then PROVE with before/after

1. **Implement the on-target work in INDEPENDENTLY-MEASURABLE pieces** — so a kept change is *attributable*
   and dead complexity isn't shipped (a single whole-flow before/after is confounded).
2. **Baseline first:** the target tasks + the **full live tier verified-rate + M3** on current `main`.
3. **For each piece, a before/after experiment** on the independent `state_check`:
   - **Anchor on a deterministic offline test** reproducing the mechanism (noise-immune keep signal); and
   - **repeat the live measurement 2–3×** (these tasks are flaky — a single flip is not a keep); and
   - measure the **FULL live tier**, not only the 5 targets — a piece that flips a target green but breaks a
     working task is a **net discard** (regression-aware).
4. **KEEP the piece iff** a real verified-flip on a target **AND** no regression **AND** M3 does not rise.
   **DISCARD otherwise**, documenting the discard as a hard gap.

---

## 3. The on-target capability work (trace first, never guess)

Per failing task: **trace WHY it fails** (read the code + the live run) → make the capability change the trace
demands → measure. Candidate tools — use **whichever the actual traces demand**:
- **Peek-the-page close-the-loop replan** — replace the context-free no-op: feed the planner the failed step +
  failure class + the **current page's compact `role|name` list** (never raw DOM); splice the **suffix**
  (keep the done prefix); emit the reconciled `PLAN_READY` the frontend already renders; bounded attempts.
- **Search-submit press-Enter strategy** — after `fill`, prefer press-Enter over hunting an
  autocomplete-covered submit button (Google + Wikipedia search ceiling). Executor-level.
- **Click-grounding on content-heavy pages** (gnu Licenses, wikipedia Sign In) — strengthen the locate
  cascade / L2 to find the nav link it currently misses (feed `perceive`'s observation to L2; vision-fallback
  seam if needed).
- **Predict-then-verify for clicks (#3)** — give clicks an element-grounded expectation so verify-after-act is
  meaningful (also closes a silent-failure surface → M3-protective).
- **Let the planner see the page** — the shared root of several ceilings.

Files wide open (any file incl `planner.py`). **Do NOT build `memory.py` / `memory.db` / staleness scoring
this round** (deferred — see bottom).

---

## 4. Experiments (before/after — the proof)

Baseline the full live tier verified-rate + M3 first. Then **one before/after experiment per capability piece**
(the actual set is whatever the traces demand). Concrete examples:

| Piece | Deterministic anchor (keep signal) | Live before/after (2–3×) | Pass = |
|---|---|---|---|
| peek-replan | `data:` fixture: first plan fails (named target absent) but the correct element is present under a different name; closed-loop peek-replan resolves it where the no-op can't | gnu / google / wikipedia targets verify-flip vs baseline | ≥1 verified-flip, no regression, M3 flat |
| press-Enter submit | `data:` fixture: a search box where press-Enter submits but a button-click is autocomplete-covered | google / wikipedia search verify-flip | verified-flip, no regression, M3 flat |
| click-grounding | `data:` fixture: a nav link the current cascade misses; the strengthened locate finds it | gnu Licenses / wikipedia Sign In verify-flip | verified-flip, no regression, M3 flat |

Report the before/after table + M3 before/after for **every** kept and discarded piece.

---

## 5. Keep / Discard

- **KEEP** a piece iff: its deterministic anchor is green (where applicable) **AND** a real verified-flip on a
  target (2–3×) **AND** no full-tier regression **AND** M3 does not rise.
- **DISCARD** iff: no verified-flip, OR a **cost/speed-only or number-only "win"** with no accuracy flip, OR
  any regression, OR M3 rises, OR a gate/verifier was weakened. Document every discard as a hard gap.

---

## 6. Guards (the kept instruments — the only "restrictions")

| Guard | Check |
|---|---|
| **G1 — offline gate green, network-free, ≥143** | `pytest -m "not live" -q` exit 0; new tests inline `data:`/Mock, no network. |
| **G2 — the honesty arbiter is FROZEN** | `git diff` shows no change to `state.py`'s assertion / no loosened existing `assert:`; `state_check` stays the arbiter; **M3 must not rise** (full-tier re-run); keep only on an independent verified-flip; never `nominal`. |

There is deliberately **no "files frozen" guard** — that lock is lifted (§1). G2 is the entire safety surface.

---

## 7. Time-box & stop
Time-boxed. Stop when: the 5 targets verify reproducibly; the time-box is hit; or a remaining failure is a
genuine research ceiling (document honestly as a hard gap — never fake a pass).

---

## 8. Isolation · execution · findings · never pushed
- **Execution via the `/autoresearch` skill**, with §1's two locks as its operating contract.
- Fresh git worktree off the latest `main` (`f1165d4`); `main` untouched directly. Baseline the full live tier
  + M3 first, then before/after each piece.
- Running log → `research/round-3-findings.md`; append-only ledger → `research/round-3-progress.json`
  (per piece: change, before/after verified state, M3, decision kept/discarded, reason). Discards = hard gaps.
- Reviewed, then merged back to `main`. **Nothing pushed — ever.**

---

## 9. Self-check against the bar
- On-target only, capability free, honesty gates kept? Yes (§1/§3/§6).
- Before/after proves real *accuracy* improvement, attributable per piece, regression-aware, cost/speed-only
  excluded? Yes (§2/§4/§5).
- Guards against today's failure mode (fake convergence / hollow verification)? Yes — free to touch, unchanged proof.

---

## Deferred to a LATER round — Agent memory + staleness (designed, NOT built this round)

**Why deferred (internalised, not just cut):** the 5 targets fail on the **first attempt with no memory in
play**, so memory pre-warm (a cache hit) only helps the **2nd+ run**, and staleness self-heal only fires when a
**cached** strategy breaks because a **site changed** — neither is why any of the 5 fail. Memory + staleness
solve a **different problem** (repeat-run cost/speed + cached-strategy drift), not the first-attempt **accuracy**
this round measures — and §5 explicitly does not count a cost/speed-only win. They are also a **big build**
(SQLite store, projections, fingerprinting, write-back, staleness scoring) that would eat the time the on-target
fix needs, and **memory logically depends on peek-replan working first** — you can only remember a strategy once
something makes the first run succeed. **So: peek-replan first; memory is a layer for a later round.**

**The design (good — keep for then):**
- **Storage (weighted matrix vs ASSIGNMENT factors):** one `memory.db` (`sqlite3`, WAL) — `locator_memory`
  + `action_stats` projections + an **append-only `episode`** event-log; rebuildable projections, honest audit,
  no CQRS ceremony. Plain SQLite won (139/150); KG (88) and K/V (107) lose; `sqlite-vec` is the v2 semantic
  add-on; a bounded `recall(intent,k)` agentic-RAG tool is v2, gated. (Full record: the memory prompt + research.)
- **Staleness:** a computed score (recency decay × Wilson success-rate), `verify-after-act NO_CHANGE` as the
  drift signal, a `page_fingerprint` checked at the peek step, → hard-demote + treat-fresh + self-heal write-back,
  with the same honesty guard (memory success/fail from the VERIFIED outcome; a stale hit can never become a
  silent failure). (Full record: the staleness prompt.)
