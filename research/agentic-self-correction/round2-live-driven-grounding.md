# Round 2 (live-failure-driven) — same-destination locate collapse

The first round used the controlled diagnostic. This round is driven by the **real live
AFTER run** (52/60 verified), diagnosing each genuine failure from first-party evidence
(AUDIT.md trajectories + deterministic reproduction) rather than the report prose.

## What the live failures actually were (after correcting stale prose)

The (b) AFTER run showed 52/60. Reading the trajectories — not the caveats — corrected
three false targets:

- **iframe** (`live_internet_iframe`) — the report caveat said "locator cascade does not
  pierce iframes", but piercing was already implemented in `eb3d0eb` (child-frame fallback
  + `_EDITOR_SCAN_JS` + `_EDITABLE_SET_JS`) and offline-tested. The caveat was **stale**.
  verified=True. Not a target.
- **modal** (`live_internet_modal`) — marked SILENT_FAILURE, but it was a **verifier bug**:
  `inner_text()` returns the CSS `text-transform:uppercase` rendering ("THIS IS A MODAL
  WINDOW") while the assert was title-case. Fixed on main (`d662be2`, case-fold `_eq_text`);
  pulled in by rebasing this worktree onto main. Not an agent gap.
- **gnu** (`live_gnu_licenses_nav`) — steps=0 calls=0 tokens=0 → a `CopilotSession.send_and_wait`
  **infra error**, same noise class as bitbucket. Not a grounding fail.

After corrections, the only genuine agent gaps were **`vat_rates`** (wrong-page silent
failure after 26-step wandering) and **`periodic_table_nav`** (multistep nav, 24-step wander).

## Root cause of periodic_table_nav — a deterministic grounding bug, NOT the loop ceiling

Reproduced with a no-LLM probe on the live Oxygen page:

- The page links the same article from **two** places (infobox + body): `get_by_role("link",
  name="periodic table", exact=True)` → **count=2**, both `href=/wiki/Periodic_table`, both visible.
- `locate`'s role_name tier saw count=2 → `_lone_visible` → 2 visible → returned `None`
  ("real ambiguity"). **But this ambiguity is false** — both links go to the same place.
- The cascade then fell through to a **decoy** that merely contained the word "table"
  (`"Toggle the table of contents"`), which resolved count=1, so `ground("periodic table")`
  returned the **TOC checkbox**. The agent clicked "periodic table" → got the toggle → the
  click timed out / never navigated → it wandered its whole step budget.

This is deterministic and fixable — it is **not** the a-priori-verify-honesty ceiling.

## Fix

`_lone_visible`: when every visible role+name match shares **one real href**, they are the
same destination — clicking any one wins — so pick the first. Placeholders (`#`/`None`) and
differing hrefs stay strictly ambiguous (no silent wrong pick). `cdp.py` + `test_cdp_locate.py`.

## Validation

- **Deterministic:** `ground('periodic table')` now resolves `/wiki/Periodic_table`; clicking
  navigates Oxygen → Periodic table (h1 "Periodic table") in one hop.
- **Offline gate:** 227 passed (+6 `test_cdp_locate` cases), no regression.
- **Live pass^3:** `live_wikipedia_periodic_table_nav` 0/1 → **3/3 verified** (15–17 steps, 52 calls),
  zero abstains, zero silent failures.

## Honest remaining ceiling (not chased)

`vat_rates` is a wrong-page silent failure after long wandering — the lever is discriminating
a-priori verify, which `planner-open-loop-ceiling` proves is a multi-round-resistant dead-end
via prompt-tuning. Not chased this round. Expected live headline after the verifier rebase +
this fix ≈ 54/60 (modal + periodic_table flip), pending a full live re-run to confirm.
