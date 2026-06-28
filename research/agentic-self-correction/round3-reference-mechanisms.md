# Round 3 — experimenting the reference-repo mechanisms (not assuming them)

Earlier rounds **reasoned** that the OSS "three pillars" (① stable-ID, ② index-all+prune,
③ change-signal) plus ④ graduated-loop were net-negative for us. This round **measures** them.
The author writes both the probes and the implementation, so an explicit anti-cheat gate binds
it ([ANTI-CHEAT-GATE.md](./ANTI-CHEAT-GATE.md)): G-FREEZE, G-LEAK, G-LIVE, G-INDEP, G-NULL.

## Instrument
`eval/eval_set/mechanisms.yaml` + `eval/passk_mech.py` (records pass^k + false_success + COST:
calls / input-tokens / nano_aiu per family). The first probe draft was **rejected by an
independent adversarial audit (G-INDEP)**: 5/10 probes duplicated `diagnostic.yaml`, Family B's
"cost" axis was unmeasurable at 40-element scale, one probe was rigged-to-pass, and Families B/D
were passable by the wide-observe PROMPT (which the author controls) rather than a code pillar.
The set was revised to keep only patch-unfakeable gaps.

## Evidence-based verdicts (baseline k=3)
| mechanism | verdict | evidence |
|---|---|---|
| **① stable-ID** | **REAL gap → fixed** | same-name multiplicity 0/3, agent wanders ~25 steps; see below |
| **② index-all + prune** | **G-NULL** | the agent routes around the wide-observe coverage limit (passes without it); cost noise at this scale |
| **③ change-signal** | dropped | covered by #4a discriminating-verify + diag_decoy |
| **④ graduated loop** | dropped | its only real case was the round-2 grounding bug, already fixed |

So of the four, **only ① is a genuine engine gap — and it does not occur in our nav/retrieval
live failures**. This confirms, with data, the earlier first-principles deferral of ②③④.

## ① implementation + result
The engine deduped perceive rows by `(role,name)` and `locate` stopped on ambiguity, so it could
neither see nor address one of several identically-named controls. Fix (`cdp.py` /
`agentic_executor.py` / `skill.py`):
- `perceive_indexed`: indexed observe — no dedup, injects a stable `data-aid` per match, returns
  the nearest container text as disambiguating `ctx`.
- `click`/`fill` take an optional `index` → `resolve_aid` dereferences `data-aid` (no name
  re-match, so it cannot pick the wrong same-named element). By-name acting, iframe fallback, and
  wide-observe are unchanged. Change-detection strips `data-aid` so injection never reads as a diff.

**mechanisms.yaml family A: 0/3 → 3/3 pass^k**, false_success 0, avg calls **21 → 6.7** (the
25-step wandering collapses). Gates: offline 227 green · G-LEAK clean (a leaked comment caught +
scrubbed) · G-INDEP APPROVE-WITH-NITS (both nits fixed) · **G-LIVE 6/6** (periodic_table, iframe,
oxygen, decoy, gov.uk, books — no regression).

## Honest scope
① is a **robustness gain with no live-headline payoff**: lists/tables/forms with repeated action
labels are common on app-style sites but absent from our wikipedia/docs/gov.uk live set. The
observe-output shape change (adds `i`/`near`, drops dedup in the listing) does reach live tasks,
but acting stays by-name there and success is gated by the independent `state_check`, so no
verified number can be inflated. The headline answer this round produces: **of the borrowed OSS
mechanisms, three don't apply to us and one (①) is real but off-distribution — experimented, not
assumed.**
