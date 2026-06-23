# Design-vs-Code Audit: Task Walkthrough, Scoring, Eval Set

- **Datetime:** 2026-06-23 07:12:42
- **Summary:** Trace one full task end-to-end, explain agent self-report vs independent scoring, describe the eval set/split/metrics, then run browser-agent-expert and honestly map where the code matches the design vs differs/skipped — tagging each claim traced-in-code or belief. No code changes.

## Prompt

> before we add more tasks i want to understand 2 things first, how the agent see a page
> and choose what to click, and how the harness decide a task is success. dont change code
> this turn.
>
> walk me through one full task from start to end, from the task text, how the plan is
> made, how it pick which element to act on, how it know the step worked. name the parts
> and how the data move between them. also how the harness score success, tell me clearly
> what the agent itself report vs what is checked independently against the real page
> state. and what tasks are in the eval set, the dev / held out split, and what
> reliability metric you report like pass^k, over how many tasks each.
>
> then run /browser-agent-expert and compare, where your code match the design and where
> it already different or skipped.
>
> same rule, your CLAUDE.md say engineering rigor, so mark each answer as traced in code
> or just belief not verified. honest map is better than a confident one. /save-prompt

## What I Did

- Read the actual code this turn (not sub-agent reports): planner.py, executor.py, verify.py, eval/harness.py, eval/scoring.py, eval/verify/state.py, eval/eval_set/tasks.yaml, eval/loader.py. Made no edits.
- Walkthrough (traced): task text → LLMPlanner (Copilot) → list[SubTask]; per step perceive→`_match`(name string→IndexedElement)→locate(10-tier)→precondition→predict Expectation→act→verify_after_act. Named every data hand-off.
- Key finding: element choice is open-loop NAME-MATCHING between the planner's guessed target and perceived element names (`_match`), NOT the LLM picking from the perceived list.
- Scoring (traced): `nominal` = agent's `all_ok` self-report, recorded only for the CuP gap; `verified` = `state_check` on the live final page (independent, used for TSR/TCR). Agent's word is discarded for grading.
- Eval set (traced): 12 tasks; 8 dev (the-internet + books) / 4 held-out (quotes, 33%); types action 7 / retrieval 4 / side_effect 1; difficulty single+multi_same_domain only (multi_cross_domain declared but 0 tasks). pass^3 computed only over side_effect → n=1 task. TCR/TSR/CuP over all 12; held-out TSR over 4.
- Ran /browser-agent-expert; compared design vs code. Matches: deterministic locate+verify, 10-tier cascade, nominal-vs-verified/CuP, budget-matched baseline, held-out. Diverges/skipped (traced): "dual-channel" is single-channel (no screenshot judge built), open-loop element naming, WRONG_PAGE detector absent, SEP not in live loop, vision/tiering/REAL/Inspect/SVDD are seams or unused.
- Tagged each claim [TRACED] vs [BELIEF] per the engineering-rigor rule; surfaced the honesty gaps (pass^3 n=1; dual-channel aspirational) rather than presenting a confident map.
