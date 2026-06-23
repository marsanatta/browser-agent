# Eval Growth Strategy: Can the Harness Even See the Blind Spots?

- **Datetime:** 2026-06-23 08:09:27
- **Summary:** Before scaling the eval set, decide whether the current harness can turn the known blind spots (_match silent pick, verify-after-act false positive, abstain) into honest red results — and from that, the correct order of harness-primitive vs red-task vs fix vs scale.

## Prompt

> i want to grow the task set but i'm worried if i add like 40 more tasks right now they'll
> mostly be the same kind, clean label sites ... and the eval will just go more green while
> these blind spots stay invisible ... is there even one task i could add that would actually
> catch the _match silent pick or the verify after act false positive, or would every new task
> just pass over them the same way. and then ... what has to exist first so that growing the
> set actually reveals these instead of hiding them. do we fix _match and the step check first
> and then add tasks, or do we add the failing tasks first ... and let those red tests drive
> the fix. i don't want a bigger eval that's just a bigger green wall /save-prompt

## What I Did (analysis, no code change)

Catchability with the harness exactly as-is (reasoned from traced code):
- _match silent wrong-pick: YES — two same-accessible-name elements, first=wrong, assert correct destination. Wrong pick lands on a wrong observable final page → verified=False, and shows as CuP silent failure (nominal True / verified False). Final state_check is sufficient.
- pass^k: YES (data only) — add 3-4 side_effect tasks; pass_hat_k already runs over all side_effect tasks.
- synonym/label≠accessible-name: YES — same shape as the books FAIL (NOT_FOUND → verified False).
- verify-after-act false positive (moving DOM): NO, not cleanly — harness scores final state, not the per-step verdict; can only catch indirectly via an outcome-flipping no-op-needs-recovery task, and even then reports "task failed" not "step-check fooled." Needs a step-level verdict check.
- abstain/stop-and-ask: NO — no abstain primitive; state_check can't express "correctly refused." Unscoreable today.

Principle: a task belongs in the set only if the harness can score it honestly today; otherwise the harness primitive is the prerequisite, not the code fix or the bulk tasks.

Recommended order:
- Phase 0 (tiny harness): add expect_abstain outcome + per-step verdict capture (the unlock for the two unscoreable cases).
- Phase 1 (~5 adversarial RED tasks, data): ambiguous-same-name, synonym/truncated-label, moving-DOM-needs-recovery, impossible→abstain, +3 side_effect. Most red today; CuP leaves 0; pass^k means something.
- Phase 2 (fixes driven by red): _match ambiguity rank/flag instead of candidates[0]; click step-check asserts target-specific effect instead of page-wide DOM diff.
- Phase 3 (scale breadth) across unused axes (cross-domain, more side-effect), not clean-label clones.

Nuance vs the user's "add failing tasks first": two of the five (abstain, step false-positive) can't be honestly red until the harness can score them, so a sliver of harness work precedes even the red tasks. Tags: catchability = reasoned-from-traced-code; phase plan = judgment.
