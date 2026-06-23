# Phase 0: expect_abstain + per-step verdict — built and proven

- **Datetime:** 2026-06-23 08:48:45
- **Summary:** Build the minimum harness capability (expect_abstain outcome scoring + per-step verdict capture) + one ambiguous task, then prove with real runs that CuP moves off zero and a correct abstention scores as success — before pointing autoresearch at the repo.

## Prompt

> let's converge ... build your phase 0, the expect_abstain outcome and the per step verdict
> capture, plus the one ambiguous-same-name task. then prove it for real, show me CuP actually
> moves off zero ... and show me a correct refusal on an impossible task now scores as success
> ... one straight answer, is the harness now able to score silent wrong picks and correct
> abstentions honestly ... or is there one concrete blocker left ... name the exact missing
> piece /save-prompt

## What I Did (built + proved, real runs)

- Built: events.step_finished gains a `verdict` (CHANGED/NO_CHANGE) per step; executor emits it; harness captures step_verdicts + tracks ASK_USER. loader gains `expect_abstain` (assert optional when set). harness scores abstain tasks by outcome: verified = asked AND not nominal. Added 2 tasks (ambiguous identical-label; impossible->abstain). Fixed the loader test for the new schema. 83 offline tests pass.
- Real harness run on the 2 tasks: CuP silent-failure gap = 0.500 (off zero) — but from the IMPOSSIBLE task hallucinating success (nominal=True, verified=False), not from the ambiguous one. The ambiguous task's agent ASKED instead of mis-picking.
- Deterministic MockPlanner proofs: (B) forced refusal -> asked=True, nominal=False -> expect_abstain verified=True (correct refusal scored as SUCCESS) PROVEN. (A) forced click on identical-label "(about)" -> click failed NOT_FOUND, nominal=False — NOT a silent pick.
- HONEST CORRECTION to last turn: my claim that an ambiguous-same-name task yields a silent wrong-pick CuP is empirically WRONG. locate()'s count==1 makes an ambiguous NAME fail LOUDLY (NOT_FOUND); it never becomes a silent claim-of-success. A true silent wrong-pick needs a shared name with a uniquely-resolvable WRONG element (shared label + distinct id/href). Relabeled the task comments to match reality.
- Straight answer: abstention scoring = ready+proven; silent-failure/CuP scoring = ready+proven off-zero; the missing piece is a TASK that actually elicits a silent wrong-pick (and, for the moving-DOM false positive, a step-level verdict ASSERTION primitive — verdicts are captured but not yet scoreable).
