# Merge Round-3 (A/B/C); Build Foundation Before Evaluating Models

- **Datetime:** 2026-06-27 07:52:09
- **Summary:** The eval set is too small for the planner-model bake-off to mean anything; merge the stable round-3 capability work (A/B/C) into main and keep the planner default as-is — get a solid foundation/infrastructure in place before doing any model evaluation.

## Prompt

> first the test set is too small, i don't think this mean anything actually, i want the 2, we have a good fundation and infrastructure first before we start to evaluate the model /save-prompt

## What I Did

- **Agreed and corrected my own overclaim.** I had inferred "opus planner is worse than gpt-5.4" from a full-tier 16-vs-14 and a 4-task bake-off — both single-run on a small, flaky eval set. The user is right: that sample can't support a model conclusion (it's exactly the "trust your own eval, with SE/CI and ≥3 runs" discipline the project mandates). So no model decision now.
- **Chose option 2: merged round-3 (A/B/C) into `main`** (fast-forward `06c6e7a` → `3200382`), keeping the opus planner default unchanged:
  - **A** peek-the-page replan (replaces the context-free no-op; wires the previously-inert replanner tier opus-4.8/xhigh).
  - **B** planner-sees-start-url (stops the planner navigating to a site's generic portal).
  - **C** relative-URL resolution (`act._resolve_url`; fixes a relative-URL regression B induced).
  - Reproducible wins: `wikipedia_search_submit` + `wikipedia_signin_synonym` F→T (3/3 each, and they pass under all three planner models). Offline gate 163, network-free. No A/B/C regression, no M3 rise from A/B/C.
- **Deferred to a later round (foundation first):** the planner-model choice (needs a bigger eval set + multi-run verified-rate w/ CI before deciding), and the **`internet_modal` silent failure** — the bake-off showed it is **silent across all three models** (gpt-5.4/sonnet-4.6/opus), so it's a structural modal-handling / verify-after-act gap, NOT model-specific; fix is predict-then-verify, a future piece.
- Ran the offline gate on main post-merge to confirm green, then a pre-push secret/PII scan before pushing. Honesty gates kept throughout (state_check frozen, wikipedia kept only on independent 3/3 verified-flips, pydocs NOT claimed fixed — flaky ~40%, gnu.org unreachable from this env documented as a hard gap).
