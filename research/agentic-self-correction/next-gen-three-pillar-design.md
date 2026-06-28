# Next-gen agentic engine — the three-pillar perception/grounding rewrite

A design + experiment plan for the **next** autoresearch round. Supersedes the current
patch approach (#3a/#2/#1) with a structural redesign, grounded in the OSS code read in
[`reference-mechanisms-gap.md`](./reference-mechanisms-gap.md). Agentic engine only; legacy
`executor.py` untouched.

## 0. TL;DR

Stop patching a self-inflicted blindness. Rewrite the perception/grounding layer around the
three pillars the 5 OSS agents converge on:

1. **Index-ALL interactive + deterministic structural prune** (not name-filter) — never blind.
2. **Stable-ID grounding** (pick an id assigned at perceive-time; action dereferences it) — no
   action-time name re-match → no ambiguity, no silent wrong-pick.
3. **Forced reflection + objective change signal** (evaluate-last-step + DOM-diff) — honest loop.

This is the *substantive* self-correction the assignment grades, and it **dissolves the
prompt-overfit/cheating concern** raised earlier: with the full element list always visible
and addressed by id, there is no "on a miss, go hunt for a renamed/hidden control" hint to
leak — the agent succeeds by *seeing* the control, not by being told its label.

## 1. Why (one paragraph)

Today `agentic/cdp.py` `_SCAN_JS` filters the perceived elements by the target *name*, so a
renamed/hidden control returns empty and the LLM is blind; `cdp.ground()` then re-matches the
name via the 7-tier cascade at action time, which is where ambiguity/miss happens. Our #3a/#2/#1
patch the blindness reactively (and #3a leaks test-vocabulary in its prompt examples). The
reference agents never have the blindness — see the gap doc for file:line evidence.

## 2. The three pillars — what to change in OUR code

### Pillar ② first: index-all + structural prune  (the root fix)
- **Change** `agentic/cdp.py` `_SCAN_JS` / `perceive()` from "return elements whose name relates
  to `target`" to "return **all interactive** elements" detected by behavior signals (clickable,
  input/editable, role, `tabindex`, `cursor:pointer`, event handlers), each with `{id, role,
  name}`. `target` becomes an optional **ranking/highlight** hint, never a filter.
- **Add** a deterministic pruning pass to bound cost (the reason we filtered in the first place):
  bbox-containment suppression, drop invisible/occluded, attribute allow-list, cap N (e.g. 40).
  Reference: browser-use `serializer.py:45-57`, `paint_order.py`, `views.py:18-62`.
- **Why it dissolves the cheat:** renamed/hidden/synonym are no longer special cases; the agent
  always sees the `Go`/`Log in`/menu control in the list, so no "hint" prompt is needed.

### Pillar ①: stable-ID grounding
- At `perceive()` time, **assign an id** to each interactive element — inject `data-aid="<n>"`
  (Agent-E `mmid` style, re-injected every perceive) OR carry the CDP `backend_node_id`
  (browser-use style).
- `observe` returns a list of `[<id>] <role>: <name>`; the tool schema for `click`/`fill`
  **takes an `id`** (accept the visible label too for back-compat, but prefer id).
- The action layer dereferences id → exact node (`querySelector("[data-aid='37']")` or
  `DOM.resolveNode`) — **no `ground()` name re-match at action time**. This deletes the
  ambiguity/silent-wrong-pick failure mode at its source.
- Stale id (page changed) → soft "re-perceive" observation, not a crash (browser-use
  `tools/service.py:711-714`).

### Pillar ③: forced reflection + objective change signal
- Replace the thin `{"changed": bool}` click/fill result with a **structured diff**: new
  elements that appeared (`*[`-style), DOM-mutated?, url changed? (browser-use `*[`
  `system_prompt.md:59`; Agent-E `MutationObserver`).
- Add a lightweight per-step **reflection contract** in `skill.py`: each step state
  "what the last action changed / did it work / next goal" before acting. This is a *general
  reasoning structure*, not a test-specific hint (so no leak).

## 3. Cost — the load-bearing risk, must be measured
Index-all could increase per-observe tokens on big real pages (the diagnostic pages are tiny).
The structural prune + cap is what keeps it bounded. **Acceptance gate (G-cost):** on live
dev-39, total Copilot calls and `Σ nano_aiu` must stay within the current engine's noise band
(the new principle: cost = perception-size × call-count × model-tier — index-all raises
perception-size per call but should cut call-count by killing blind spinning; net must not
regress). If it regresses, tighten the prune / cap before keeping.

## 4. Validation methodology (independent ground truth; anti-cheat)
- **The cheat dissolves by construction**, but still prove it: re-run the existing diagnostic
  with a **genericized prompt** (no `Go/Menu` examples) AND with the renamed/hidden labels
  changed to words never seen anywhere — if it still passes, it is the *mechanism*, not the hint.
- **Diagnostic before/after** (`passk_diag`) for pass^k + false-success + cost, dev + once-only
  sealed — same instrument as the patch round, so the rewrite is comparable to the patches.
- **Live dev-39 before/after** for external validity + G-cost (the patch round's live numbers
  are the baseline to beat / not-regress).
- **Compare three arms** apples-to-apples: (a) current main agentic, (b) the patch branch, (c)
  the pillar-rewrite branch — same eval/harness/verifier/model, only the engine differs.
- Deterministic verify gate stays the success oracle; never an LLM judge (carry #4a/#4b forward).

## 5. Sequencing (riskiest-isolated)
1. **②** index-all + prune (root fix; behind offline gate + G-cost). Measure cost first — this
   is the make-or-break.
2. **①** stable-ID grounding on the index-all output (tool-schema change → expect test churn in
   `test_agentic_executor` / `test_cdp_iframe`; update as the contract legitimately changes).
3. **③** structured change-signal + reflection contract.
4. Then the supporting mechanisms if budget allows: graduated loop / forced-done, wait
   primitives, selector cache (gap doc §"Supporting").

## 6. Guardrails (carry from the patch round)
- **Agentic-only**; never touch `executor.py` (legacy) or the frontend's plan-history UI.
- **Deterministic verify gate stays**; eval `harness.py` / `scoring.py` / `verify` / the live
  set are READ-ONLY; the diagnostic set is a probe, never an evolve target.
- **G-cost is a hard gate**; **G-abstain** non-regression (the loop/reflection changes are the
  most abstain-bleed-prone — guard like #1's rework).
- **Self-maintenance must not regress**: the 7-tier cascade currently handles selector drift;
  the id approach must keep (or beat) that — re-inject id every perceive so UI class/id churn
  still resolves.

## 7. Honest open questions
- **id stability** across re-renders: data-aid must be re-assigned each perceive (like Agent-E
  mmid) — confirm it survives SPA re-paints between observe and act.
- **cost on real pages** with index-all: unknown until measured (§3) — this gates the whole plan.
- **tool-schema change** (click-by-id) ripples into the SSE event args + the inspectable-failure
  view; verify the frontend still renders (the Event *types* are unchanged, only the arg shape).
- Whether the rewrite actually beats the cheaper patches on **live** — if the patches already
  capture most of the gain on real sites, the rewrite's extra cost may not pay off. The
  three-arm comparison (§4) decides this honestly.
