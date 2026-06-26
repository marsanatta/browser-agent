# Surface The Real Token Ledger In The Web Frontend (via /eng-pipe)

- **Datetime:** 2026-06-25 11:56:25
- **Summary:** While the day-5 measurement instrumentation's live run was finishing, check whether the new token tracking shows in the web UI; it didn't, so design it (frontend skills) and add it via /eng-pipe. Measurement-only, observe-only.

## Prompt

> while waiting will those token track show in UI frontend? if not, search frontend skills we have design it, and /eng-pipe to add them /save-prompt

## What I Did

- **Answered:** No — the token ledger lived in the gateway/harness/`AUDIT.md` path, but the live SSE stream (`/agent/run`) carried no token field and the React UI never rendered one. `_CountingGateway.tokens` was harness-only; `main.py` used a bare `LLMGateway` with no running total.
- **Committed the in-flight audit instrumentation first** (`998dc9a`) so the frontend work would be a clean separate commit — the live re-run had just confirmed the FULL token ledger (`out/in/reasoning/nano_aiu` all non-zero, e.g. out=728 in=12485 reason=680 nano_aiu=1.56e9) and `attribution_coverage = 1.000`.
- **Ran /eng-pipe** (grill skipped — pre-aligned; ground light — known files; fresh-context review; offline+build test):
  - Backend: `LLMGateway` accumulates a per-gateway `.tokens` ledger in `complete()` (same accrual rule as `_CountingGateway`: prefer the `assistant.usage` event, else `output_tokens`). A fresh gateway per `/agent/run` → real per-run total. `events.run_finished` gained a `tokens` field; `Executor.run()` includes `getattr(self._gateway, "tokens", {}) or {}` (empty for the gateway-less baseline).
  - Frontend (React 18 + Vite, used `/vercel-react-best-practices` + `/vercel-web-design-guidelines` conventions): the `RUN_FINISHED` reducer stores `tokens`; a `TokenPanel` cost strip in `RunVerdict` renders out/in/reasoning tokens + AIU (`total_nano_aiu/1e9`), formats k-magnitudes, and shows "tokens: n/a" for older/baseline runs. `styles.css` matches the existing dark visual language.
  - Tests: +3 offline (gateway accrual; RUN_FINISHED carries tokens via a fake gateway; empty-without-gateway). Offline gate **110 green + network-free**; frontend **builds clean**.
  - Independent fresh-context review: **PASS, no RED**; one YELLOW (a cosmetic `_fmt` 9999→"10.0k" seam) fixed (round-first).
- **Discipline:** planner.py untouched · no verifier loosened · observe-only (no agent-loop behavior change) · tokens shown for cost transparency, never minimized.
- Committed as `81cf9f0`, separate from the audit commit `998dc9a`. **Not pushed** (user reviews + pushes by hand).
