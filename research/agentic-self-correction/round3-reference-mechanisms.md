# Round 3 — Do the reference-repo mechanisms help OUR agent? (experimented, not assumed)

**Question.** Five OSS browser agents (browser-use, Agent-E, stagehand, agent-browser,
browser-use/benchmark) converge on four mechanisms our engine lacks or only weakly has:
① stable-ID grounding, ② index-all + structural prune, ③ objective change-signal /
reflection, ④ graduated loop / forced-done. Earlier rounds **reasoned** (first-principles)
that ②③④ were net-negative for us and deferred them. This round replaces the reasoning with
**measurement**: build a controlled instrument, run a baseline, and keep a mechanism only on
evidence.

**Why this round needed an explicit anti-cheat gate.** The same agent authored both the eval
probes and the implementation meant to pass them — the conflict that already produced two real
leaks (#3a named the diagnostic's renamed/hidden labels; #4a named two live tasks' exact
`url_contains` answer-keys). So the round is bound by [ANTI-CHEAT-GATE.md](./ANTI-CHEAT-GATE.md):

| gate | rule |
|---|---|
| **G-FREEZE** | probes committed before any mechanism code (git proves order); probe is a measure, never an evolve target |
| **G-LEAK** | zero probe vocabulary (markers/labels) in any code/prompt diff — mechanical grep |
| **G-LIVE** | the pre-existing READ-ONLY `live_real_world.yaml` (not authored here) is the real arbiter |
| **G-INDEP** | a fresh-context subagent adversarially reviews the probes AND the diff before keep |
| **G-NULL** | honest null results; objective cost reported regardless of the prior prediction |

## Method
- **Instrument:** `eval/eval_set/mechanisms.yaml` (deterministic inline_html probes, each setting
  a unique marker only on the CORRECT action) + `eval/passk_mech.py` (records pass^k +
  false_success + COST — calls / input-tokens / nano_aiu — per family, since cost is the central
  ②①③ question). Run by its own runner, never `eval.harness`, so it never enters the headline.
- **G-INDEP on the probes first.** The first 10-probe draft was **rejected**: 5/10 duplicated
  `diagnostic.yaml`, Family B's "cost" axis was unmeasurable at 40-element scale, one probe was
  rigged-to-pass (`_same_destination` already solved it), and Families B/D were passable by the
  wide-observe PROMPT (author-controlled) rather than a code pillar. Revised to 6 probes keeping
  only patch-unfakeable gaps.

## Results — baseline (k=3)
| family (mechanism) | baseline pass^k | reading |
|---|---|---|
| **A — same-name multiplicity (①)** | **0/3** + control 1/1 | REAL gap: agent wanders ~25 steps (5× the control's cost), can't disambiguate |
| **B — large-DOM coverage (②)** | 2/2 | G-NULL: agent routes around the wide-observe limit (passes without ②); cost is noise at this scale |

Mechanisms **③** (change-signal) and **④** (graduated loop) were dropped without a probe: ③ is
already covered by #4a discriminating-verify + `diag_decoy`; ④'s only real case was the round-2
grounding bug, already fixed. **Of the four borrowed mechanisms, only ① is a genuine engine gap.**

## ① — implementation and outcome
**Root cause (traced, not guessed).** `perceive` deduped rows by `(role,name)` and `locate`
returned None on ambiguity, so the engine could neither SEE nor address "the 2nd of three
identical links." Confirmed deterministically: three `<a>Edit</a>` collapsed to one perceivable
row; `click("Edit")` → ambiguous → None.

**Change** (`cdp.py`, `agentic_executor.py`, `skill.py`):
- `perceive_indexed` — the observe path now indexes every match (no dedup), injects a stable
  `data-aid`, and returns the nearest container text as disambiguating `ctx`.
- `click`/`fill` accept an optional `index`; `resolve_aid` dereferences `data-aid` — **no name
  re-match, so it cannot pick the wrong same-named element.**
- By-name acting, the iframe fallback (`perceive_indexed` → `perceive` on empty main frame), and
  the wide-observe path are unchanged. `snapshot` strips `data-aid` so the injected attributes
  never register as a DOM change.

**Outcome.** mechanisms.yaml family A **0/3 → 3/3 pass^k**, false_success 0, avg calls **21 → 6.7**
(the wandering collapses). Gates: offline **227 green** · **G-LEAK** clean (a leaked code comment
caught + scrubbed) · **G-INDEP** APPROVE-WITH-NITS (both nits fixed: change-detection ignores
`data-aid`; injected/shown index caps aligned) · **G-LIVE 6/6** (periodic_table, iframe, oxygen,
decoy, gov.uk, books — no regression).

## Honest scope and limitations
- **① is robustness-only — no live-headline payoff.** Lists/tables/forms with repeated action
  labels are common on app-style sites but **absent from our wikipedia/docs/gov.uk live set**, so
  ① fixes a pattern our current eval does not contain. This is stated, not hidden.
- The observe-output shape change (adds `i`/`near`, drops dedup in the listing) **does reach live
  tasks**, but acting stays by-name there and success is gated by the independent `state_check`, so
  no verified number can be inflated. G-LIVE 6/6 confirms no behavioural regression.
- The synthetic probes can only motivate; the live set is the arbiter (G-LIVE). A mechanism that
  won on the probes but not live would have been discarded — that is why ② was called G-NULL
  despite a clean probe, and why ① was only kept after G-LIVE held.

## Conclusion
The headline this round produces is not a score bump but a **measured** answer to "are the borrowed
OSS improvements worth adopting for us": **three of four do not apply, and the one that does (①) is
real but off-distribution for our eval.** Experimented, not assumed — and produced under an
anti-cheat gate strong enough that the author could not have delivered a pillar by tuning the
prompt or the probe.
