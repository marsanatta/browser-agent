# Grounding-bug fix: route element ambiguity to L2 / abstain (never silent pick)

- **Datetime:** 2026-06-23 (system clock 23:31:53)
- **Summary:** RCA of a grounding bug (agent picks the wrong element silently, or NOT_FOUNDs, on ambiguous targets) + the real fix, implemented via `/eng-pipe` with independent review and live A/B/C proofs. Confirmed bar: case B can only honestly ABSTAIN (perceive merges duplicates), not right-pick.

## Prompt (RCA + fix, as given)

> quick context from an RCA i ran, then the real fix for today. don't rewrite the planner, and don't write any analysis/limitations doc yet.
>
> RCA: agent fails "go google.com, type steam, click search button" with NOT_FOUND. perceive DOES see the button, but google renders TWO buttons with the same role+name; perceive merges them to one; locate needs count==1, role+name matches 2 -> miss, and the merged element has no id/href/class so every lower tier misses -> NOT_FOUND. A GROUNDING bug. Docs already prescribe the fix ("not-found -> re-ground/heal" = hand live candidates to the LLM), and `make_l2_fallback` EXISTS in locate.py, but prod main.py never passes a gateway so L2 is dead in prod.
>
> THREE ambiguity cases, different touches:
> - A. substring/different names ('log' -> 'Login Page'/'Login'/'Blog login'): `_match` returns candidates[0] (wrong), locate resolves it uniquely -> SILENT wrong click. _match bug.
> - B. same name, distinct href (two 'Read more'): merged to one, silent wrong pick.
> - C. same name, no attr (google): NOT_FOUND.
>
> Fix = route all ambiguity to ONE re-ground (L2): (1) wire L2 in prod (pass gateway into executor/locate in main.py); (2) `_match`: more than one candidate -> rank, real tie -> do NOT return candidates[0], signal ambiguous -> route to L2; (3) locate: role+name resolves to multiple -> filter visible+enabled+in-viewport, lone survivor wins, else route to L2; never silently fall through to candidates[0].
>
> Prove all three: (C) google resolves the right Search button or honestly abstains; (B) silent_wrong_pick_readmore through the real harness, right-pick or abstain, no silent CuP; (A) substring case no longer silently clicks wrong. 84 'not live' tests stay green. /save-prompt this RCA + the evidence. Do NOT write any ANALYSIS/DESIGN limitations section. Don't touch planner internals, don't grow the task set.

Follow-up: `commit if you haven't` (tree was clean — auth hardening already in b9473ce); `ok go with /eng-pipe until finish all` (after confirming the B-abstain bar).

## What I Did

- **Grounded in code first** (didn't trust the garbled RCA verbatim): traced `perceive._merge_co_labeled` (collapses same-(role,name) to one element, keeps FIRST node's attrs), `locate` (count==1 == resolve; `make_l2_fallback` present but `main.py` passes no gateway -> dead), `executor._match` (`candidates[0]` silent pick), and `eval.harness` (always real LLMPlanner -> B needs live Copilot). Surfaced the material constraint: because perceive merges, **case B can only honestly abstain**, not right-pick — confirmed with the user as the accepted bar.
- **Fix (3 source files):**
  - `backend/app/agent/locate.py` — extracted one shared `_cascade(page, build_el, cache, key, store_el)` + `_interactable(page, loc)`; tier-1 (role_name) count>1 narrows by visible+enabled+in-viewport, lone survivor wins, genuine ambiguity returns miss (no fall-through to attr tiers). `make_l2_fallback`'s post-pick resolution now reuses `_cascade`, so L2 cannot re-introduce the silent pick. Narrowed survivor not cached (position-dependent).
  - `backend/app/agent/executor.py` — `_match` returns `(target, ambiguous)`, never `candidates[0]`; the ambiguous branch in `_attempt` builds a pseudo-target (raw name, empty attrs) so the deterministic cascade misses and routes to L2 over the distinct candidates, or abstains (NOT_FOUND) with no gateway. Updated both call sites.
  - `backend/app/main.py` — hoisted one `LLMGateway`, passed to `Executor(..., gateway=gateway)` so L2 runs in prod.
- **Tests:** rewrote `backend/tests/test_self_healing.py`'s offline heal test to a UNIQUE-name role_name->id->css heal chain (the old two-same-name 'Go' fixture encoded the very silent pick the RCA fixes) and repurposed that fixture into a regression test asserting `locate` abstains; added `backend/tests/test_ambiguity_grounding.py` (`_match` unit for A, off-viewport narrowing for C, executor abstain-no-silent-nav integration for A).
- **Evidence (independent ground truth):**
  - Offline suite **90 passed** (`-m "not live"`) + **8 live passed** = **98 green**, no regression.
  - **B** through the REAL `eval.harness` with live Copilot (venv) on `silent_wrong_pick_readmore`: `nominal=False, verified=False, asked=True`, **SILENT_CuP=False** (was nominal=True/verified=False, CuP=1.0). 10 Copilot calls, 4 steps, click verdicts NO_CHANGE.
  - **C** real google.com run: typed 'steam' (`fill -> CHANGED`) then honestly abstained on the two ambiguous Search buttons (`click failed: NOT_FOUND`, `asked=True`, `nominal=False`) — no silent click. Deterministic off-viewport fixture narrows count 2->1.
  - **A** `_match('log')` -> `(None, [3 candidates])`; executor abstains with no silent navigation.
- **Independent fresh-context review:** PASS, no RED. Two YELLOW — dead `_match` ranking (removed: the post-filter candidate set is homogeneous so ranking never disambiguated; exact-beats-substring is already structural) and pre-existing L2 pseudo-cache non-round-trip (accepted: correctness-neutral, self-invalidating, out of scope, would break the `ghost` test). One GREEN nit (mixed-role pseudo prompt) left.
- **Semantic change flagged:** the agent no longer silently resolves ANY same-name-ambiguous element via a carried lower-tier attribute; self-healing of unique-named elements is unaffected.
- Did NOT touch the planner or perceive; did NOT grow the task set; did NOT write any ANALYSIS/DESIGN limitations doc. **Not committed, not pushed** (awaiting go-ahead).
