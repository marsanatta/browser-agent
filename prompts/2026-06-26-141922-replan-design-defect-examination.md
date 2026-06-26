# Examine Replan: Is It A No-Op / Design Defect?

- **Datetime:** 2026-06-26 14:19:22
- **Summary:** Examine the replan code with an eng-debug + first-principles design mindset to explain what is actually being replanned, what its effect is, and whether there's a design issue.

## Prompt

> and for the replan i don't see the exact difference of what is being replan and the effect. is there some issue for the replan? examine the code and use /eng-debug and first principle design mindset to answer /save-prompt

## What I Did

- **Read the actual replan machinery** (`executor.py:128-140`, `planner.py:33` Planner protocol + `66-69` LLMPlanner.plan + `46-58` _PLAN_PROMPT, `classify.py:86` WRONG_PAGE→REPLAN) rather than reasoning from the name.
- **Confirmed the defect with evidence:** replan calls `self._planner.plan(task)` with **only the original task string**; `Planner.plan(task: str)` has no parameter for failure/observation/history, and the prompt is built from `__TASK__` alone (single-shot, no conversation history). So the LLM receives a **byte-identical prompt** → returns the same plan → it's spliced `subtasks[:i] + new_subtasks` (a from-scratch whole-task plan pasted into mid-run state) → fails identically → ask_user. Hence the user's observation "no difference" is correct: replan feeds the planner zero new information.
- **Named four issues, first-principles:** (1) violates the project's own "retry only on a NEW observation" rule (executor docstring line 8); (2) the planner is structurally blind — there is no `replan(task, history, failure, observation)` signature; (3) the splice is incoherent (fresh full-plan into the middle of an in-progress page state, usually re-navigating); (4) REPLAN is mis-triggered — `classify` maps `WRONG_PAGE→REPLAN` but `WRONG_PAGE` is never emitted (ANALYSIS §4 known gap), so the real trigger is "any locally-exhausted step" (NOT_FOUND/NO_CHANGE) where re-planning the whole task can't help.
- **Drew the key contrast:** the **local** recovery ladder (REGROUND / wait-scroll-dismiss / state-wait / settle in `recover.py`) IS observation-justified and works; it is specifically the **global replan** that is open-loop and inert. So step-level self-correction is real; the task-level "replan" is theater.
- **Gave the first-principles fix:** replan must be a function of the failure — feed it the failed step + failure class + `perceive()`'s current indexed elements, ask for a DIFFERENT element/strategy (e.g. press-Enter instead of clicking an autocomplete-covered button) or an honest "impossible," and re-plan only the **suffix** from the current state. This requires the planner to see the page = closing the planner's loop (the B2 open-loop ceiling).
- **Verdict:** a genuine design defect and a concrete manifestation of the planner-open-loop ceiling — a strong round-3 candidate, deeper than the press-Enter quick win and touching the (currently frozen) planner. **Examined code only; wrote no code, changed nothing.**
