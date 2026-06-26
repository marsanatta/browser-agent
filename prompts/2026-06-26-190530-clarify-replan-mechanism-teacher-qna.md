# Clarify The Current Replan Mechanism (teacher-agent qna)

- **Datetime:** 2026-06-26 19:05:31
- **Summary:** Use the teacher-agent skill in qna mode to clearly explain how the replan mechanism is currently designed (and why it is a context-free no-op), grounded in the real code.

## Prompt

> and can you clarifiy what is the replan mechanism design currently using /teacher-agent [qna] ? /save-prompt

## What I Did

- Ran **teacher-agent in qna mode** (announced it; did NOT read/create/write `teacher/student-model.json` — qna is ephemeral by contract).
- Treated it as a single-concept explanation (skipped curriculum/student-agent phases) and delivered the **5-layer format** (L1 plain sentence → L2 analogy + checkpoint → L3 real code → L4 text flow-diagram + checkpoint → L5 the core "why it's a no-op" with a claim-vs-reality table), in 繁體中文 with English technical terms.
- Grounded every layer in the **actual code**: the `run()` loop replan block (`recovery(REPLAN)` + main's `phase`/`plan_ready`, `new_subtasks = await self._planner.plan(task)` with only the task string, `subtasks = subtasks[:i] + new_subtasks` splice), and `planner.py`'s `plan(task: str)` building `_PLAN_PROMPT` from `__TASK__` alone (single-shot, no history).
- Gave a **concrete trace** (gnu.org "Licenses" click): first plan → NOT_FOUND → REGROUND exhausts → `plan(task)` re-called with the identical string → same plan → spliced (`[navigate] + [navigate, click]`) → re-navigate + same fail → `ask_user`. Core insight: replan feeds the planner zero new information, so it returns the same plan — the `recovery(REPLAN)` event implies adaptation that never happens.
- Noted the contrast that today's bug-fix #4 fixed the **local** "retry only on a new observation" guard (REGROUND fingerprint) but the **global** replan is still open-loop — which is exactly what the proposed Round-3 close-the-loop replan would address.
- No code changed; explanation only. Used the teacher-agent (qna) and save-prompt skills.
