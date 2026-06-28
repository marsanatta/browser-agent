# Reference-agent mechanisms vs our engine — gap analysis + next-gen design

Grounded in a first-hand read of the 5 cited OSS browser agents (not the plan's summary):
browser-use, Agent-E, stagehand, agent-browser, browser-use/benchmark. file:line cited.

## The core realization

Our agentic self-correction (#3a wide-observe-on-miss, #1 stagnation nudge, #2
ambiguous-vs-absent) is a set of **reactive patches on a self-inflicted blindness**: we
**filter perception by the target name** (`agentic/cdp.py` `_SCAN_JS`), so when a control is
renamed/hidden the agent goes blind, and we patch the blindness after the fact. The
reference agents **don't have the blindness** — they solve it structurally. Three pillars
make their next-step thinking accurate + effective; we have only weak versions of all three.

## Pillar ① — stable-ID grounding (accuracy; kills silent wrong-pick)

The LLM picks an **opaque ID assigned at perceive-time**, which dereferences to the *exact*
node — there is **no name re-match at action time** (which is exactly where our ambiguity /
miss happens).

- **browser-use** — serializer prints `[backendNodeId]<tag …>` (`dom/serializer/serializer.py:1007`);
  "model outputs backend_node_id" → `_selector_map[backend_node_id]=node` (`:712-713`); action
  does `selector_map[id]` → `DOM.resolveNode(nodeId)` (`actor/element.py:86`, `actor/page.py:474`).
- **Agent-E** — injects `mmid` on every element; LLM emits `[mmid='114']` → `querySelector`
  (`core/skills/click_using_selector.py:17,175`).
- **stagehand** — `encodedId` → `combinedXpathMap[id]` → xpath (`lib/v3/handlers/observeHandler.ts:153-157`).

**Ours:** the LLM emits a *name*; `cdp.ground()` re-runs the 7-tier cascade to re-find it at
action time → ambiguous (two matches) or absent (renamed) → the miss we patch.

## Pillar ② — index-ALL interactive, made cheap by structural pruning (no blindness)

They **never name-filter** the index; the whole interactive set is always visible, so the LLM
re-picks a different element on failure. Cost is controlled by **deterministic structural
pruning**, not by hiding non-matching names.

- **browser-use** — index by ~12 behavior signals, not name (`dom/clickable_elements.py`);
  bbox-containment suppression (`serializer.py:45-57`), paint-order occlusion removal
  (`dom/serializer/paint_order.py`), attr allow-list (`views.py:18-62`).
- **Agent-E** — full accessibility tree, only role-level `only_input_fields` knob
  (`utils/get_detailed_accessibility_tree.py:56`); cost via tree prune/dedup/`<select>` flatten.

**Ours:** `_SCAN_JS` filters by name (cheap but blind). We have **no structural-pruning layer**
— which is *why* we filtered by name in the first place. This is the root cause.

## Pillar ③ — forced per-step reflection + objective change signal (effective; honest loop)

Every step the LLM must assess the last result before acting, and it sees an **objective**
signal of what its action changed (not its own assumption).

- **browser-use** — the step schema forces `Evaluation of Previous Step → Memory → Next Goal →
  Action` (`agent/system_prompts/system_prompt.md:33-36`); `*[` marks elements that newly
  appeared since the last step (`:59`) so the agent sees what its action did.
- **Agent-E** — in-page `MutationObserver` (`utils/dom_mutation_observer.py`, wired
  `core/playwright_manager.py:251`): after click/type, DOM-changed → "may need further
  interaction"; no change → the action did nothing.

**Ours:** free-form function-calling with no forced reflection structure; feedback is a thin
`{"changed": bool}`.

## Supporting mechanisms (nice-to-have once the pillars exist)

- **Graduated loop detection** — escalating nudges at 5/8/12 repeats then a **forced-done
  schema swap** (browser-use `views.py:157-248`, `service.py:1560-1582`). Ours (#1) is a flat
  "3× → one nudge".
- **Stale-ID = soft recoverable**, not a halt (browser-use `tools/service.py:711-714`).
- **Verify: outcome vs process split** + "reaching the page ≠ success unless the deliverable
  is present" (stagehand `rubricVerifier.ts`, `fusedOutcome.ts:62-90`); **discriminating
  verify** (agent-browser `SKILL.md:169-173`) — we have this as #4a; **LLM-judge telemetry-only,
  never gates** (browser-use `judge.py`, `service.py:1623-1625`).
- **wait primitives** `wait --url/--text/--fn` for state-based waits vs blind retry
  (agent-browser `actions.rs:4161-4304`). We have none.
- **act-layer selector cache** (`sha256(instruction+url+varkeys)`) → re-runs cost ~0 LLM
  (stagehand `ActCache.ts:151-199`). We deliberately don't cache (UI-drift immunity) → no
  re-run saving.

## Gap table

| mechanism | reference | ours |
|---|---|---|
| ① stable-ID grounding | ✅ | ❌ name re-match |
| ② index-all + structural prune | ✅ | ❌ name-filter |
| ③ forced reflection + change signal | ✅ | 🔸 weak (`changed:bool`) |
| graduated loop / forced-done | ✅ | 🔸 flat #1 |
| discriminating verify | ✅ | ✅ #4a |
| wait primitives | ✅ | ❌ |
| selector cache | ✅ (stagehand) | ❌ (by choice) |

## Recommended next-generation design

The substantive direction is **not more patches** but adopting the three pillars:

1. **Index-all + structural prune** (replace `_SCAN_JS` name-filter with index-all-interactive
   + bbox/occlusion/attr pruning). Eliminates the blindness at the source → renamed/hidden/
   synonym stop being special cases → and the prompt-example leak (the `Go/Menu` hint in #3a)
   becomes unnecessary, dissolving the teaching-to-the-test concern entirely.
2. **Stable-ID grounding** (assign an id at perceive-time; LLM picks the id; action dereferences
   it). Removes the action-time re-match → kills silent wrong-pick and ambiguity.
3. **Forced reflection + objective change signal** (a per-step "evaluate last result" structure
   + a DOM-mutation/new-element signal instead of `changed:bool`).

This is a **perception/grounding-layer rewrite** (cdp.py + the tool loop), bigger than the
current patches, but it is the design the 5 OSS agents converge on and the honest answer to
"is the improvement real or prompt-overfit".

## Honest status

- The current patches (#3a/#2/#1/#4a) are a cheaper *interim* that lifted the controlled probe
  0.875→1.0 with cost down, but with a prompt-example leak (`Go/Menu`) that only the live run
  or a genericized re-run can clear.
- Live before/after (the external-validity answer) is in progress at the time of writing.
- The pillars above are the recommended *next* autoresearch target, scoped as a design change,
  not a patch.
