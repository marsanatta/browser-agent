# Live Agent Activity View — Real-Time Streaming UI (via /eng-pipe)

- **Datetime:** 2026-06-26 14:10:27
- **Summary:** Improve the frontend so that clicking Run/Execute shows a LIVE, near-real-time view of what the agent is doing step by step (with dynamic animation), instead of appearing to hang on "executing" and revealing everything only at the end. Model it on the live agent-activity feed in pj enso; first check how Enso implements it and evaluate feasibility for this project. Build in a dedicated worktree off latest main via /eng-pipe with eng-test + code-review gates, looping /eng-debug until all eng-test issues are fixed.

## Prompt

> in a new dedicated worktree (derived from latest main) work on improving the UI. now when click execute, it shows executing, but i want the feature live view, it should live shows what the agent is doing, not in the end to show all. it should have some dynamic animation. it must have the near real time refresh for the latest operation. I want the similar live agent acitivities like pj enso, you can check how it implement it. and evaluate the feasibility on this project. /eng-pipe must have eng-test and code-review if encounter issue in the eng-test do /eng-debug until fix all the issues /save-prompt

## What I Did

- **Worktree:** `git worktree add -b feat/live-view _wt/live-view` from latest `main` (`a6e7729`, which already includes the i18n work + a prior "surface SSE auth failures instead of freezing on 'executing'" fix).
- **Investigated** (grounding): (a) how pj enso streams + animates live agent activity, to copy the UX pattern; (b) the browser-agent's own streaming path end-to-end — backend `executor.run()` event yielding and frontend `EventSource`/reducer rendering — to find WHY it appears to batch to the end rather than update live, then evaluate feasibility.
- **Plan / feasibility:** [to be filled by the pipeline] — assess whether the gap is backend (events not yielded incrementally / buffering) or frontend (events arrive but no prominent live "current action" + animation), then design the live view accordingly (latest-operation focus, dynamic animation, near-real-time refresh).
- **/eng-pipe** with mandatory **eng-test** + **code-review**; on any eng-test failure, loop **/eng-debug** until all issues fixed. Review uses the `vici-browser-reviewer` discipline (this is VICI Task 1) — measure live behavior, not just the offline gate.
- **Discipline:** branch off latest main in an isolated worktree; not pushed (user reviews + pushes by hand); secrets/PII kept out of SSE/logs.
