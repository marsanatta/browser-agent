# Live View v2 — Planner Output, Spinner, Retry/Replan Detail (via /code-planner + /eng-pipe)

- **Datetime:** 2026-06-26 16:28:48
- **Summary:** Reviewing the live agent-activity view on a REAL run surfaced three gaps: (1) the planning spinner doesn't actually animate, and there's no live/final planner OUTPUT shown; (2) the retry loop shows attempt/class/recovery but not WHAT was tried or its result; (3) a replan shows no output, so you can't tell what changed. Ground each in the codebase with /code-planner, then fix via /eng-pipe.

## Prompt

> 1. planner shows 規劃任務中… but the left circle is not animated at all, and I don't see the planners has like a live output or even final output, we should have it 2. I see the retry loop like 第 1 次嘗試 NOT_FOUND → REGROUND [×4] → REPLAN but i think we should enhance the information on what is trying (log or something) and what is the trying result. and for the replan it's the same, i don't see the replan output so i don't know what is changed from the replan /code-planner to see how to resolve each issue and /eng-pipe the fix /save-prompt

## Issues to resolve

1. **Spinner not animating** — `.live-spinner` keyframe either broken or killed by the global `prefers-reduced-motion` rule; verify and fix so it visibly spins.
2. **No planner output** — during the ~12s planning LLM call the user sees only "規劃任務中…" with no content. Want live streaming planner output and/or a clear final plan. Depends on whether the Copilot SDK `complete()` can stream assistant-text deltas (investigate `models.py`).
3. **Retry loop lacks detail** — recovery chain shows `attempt N / NOT_FOUND / → / REGROUND` but not what element/locator/action was tried nor the concrete result. Surface the "what was tried + result" (tool_call args/result, locator tier/strategy) per attempt.
4. **Replan shows no output** — executor replans (`planner.plan()` again, `subtasks = subtasks[:i] + new_subtasks`) but emits no event carrying the NEW plan, so the user can't see what changed. Emit the replanned plan and show the diff/new steps.

## Plan
- /code-planner to ground each issue (spinner CSS, SDK streaming feasibility, event vocabulary, executor replan path, StepDetail rendering).
- /eng-pipe the fix with eng-test + code-review; loop eng-debug on any eng-test failure.
- Continue in the existing `feat/live-view` worktree (unmerged feature). Not pushed.
