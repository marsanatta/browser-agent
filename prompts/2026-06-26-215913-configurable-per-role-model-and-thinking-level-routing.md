# Configurable Per-Role Model + Thinking-Level Routing (UI + researched defaults)

- **Datetime:** 2026-06-26 21:59:13
- **Summary:** Make the LLM model — and then also the thinking level (reasoning effort) — a configurable per-role input on the frontend UI, with research-backed best defaults for each role (planner / execution / replanner), so cost-aware routing is in place before autoresearch round-3 starts.

## Prompt

> we should make it an input and configurable on UI update this first before your autoresearch, and i want the autoresearch to start with the right choice of the models as default values /research this and target on routing with the right model to save cost /save-prompt [nomd]

Embedded follow-up refinements (the user asked to fold these into this same record):

> your research should be focusing on state of art model evaluation, which is suitable for planning, which suitable reasoning, which suitable for execution, which suitable for calling tools

> embed this in the previous prompt for save-prompt too

> for the model research you should respect to the latest ones the rank you refer must include opus 4.8 or it's pointless

> and if judge is not needed now just remove it

> can you update the escalation to replanner? that's easier to understand

> there is another thing can adjust for each role which is the thinking level, also /research [nomd] on this options and select best suitable one for each roles as default value, same it should be input and configurable from frontend UI too

## What I Did

- **Researched cost + SOTA-capability routing** (researcher agent, primary-sourced, dated 2026-06-26):
  - Corrected a stale premise: GitHub Copilot moved to **usage-based (per-token AI-Credits) billing on 2026-06-01**; the premium-request multiplier model is now legacy. The optimal routing is nearly identical in both billing worlds.
  - Capability-per-role: planner (PlanBench-XL/Online-Mind2Web), execution (tool-calling τ²-bench / BFCL, GUI-grounding ScreenSpot-Pro), reasoning (FrontierMath/ARC-AGI). **Re-ran the planner ranking after the user demanded Opus 4.8 be included** — PlanBench-XL omitted it (flagged stale); on the Opus-4.8-inclusive web-planning bench (Online-Mind2Web 84%, primary Anthropic 2026-05-28) **Opus 4.8 wins**, so the planner default changed `gemini-3.1-pro` → `claude-opus-4.8` (gemini kept as a cost-down UI option).
- **Final per-role defaults:** planner = `claude-opus-4.8` / `high`; execution(L2) = `claude-haiku-4.5` / `low`; replanner = `claude-opus-4.8` / `xhigh`.
- **Removed the judge role entirely** (dead code — zero callers; hard-verifiers-only by design): deleted `JUDGE_MODEL`, both `judge()` methods, `judge_model`, the judge knob, query param, and a stray test stub.
- **Renamed escalation → replanner** across the model-role chain (constant / gateway attr / query param / UI label / tests), leaving the unrelated recovery-ladder "escalation" concept untouched.
- **Researched thinking level (reasoning effort)** and verified — from the installed `github-copilot-sdk` v1.0.2 **source** — that it is controllable: `create_session(reasoning_effort=...)` / `set_model(..., reasoning_effort=...)`, scale `low/medium/high/xhigh` (no minimal/off/max). Carried the honest flags: Copilot may silently clamp the level per model; on Haiku the param is a no-op (= the desired non-thinking hot path) — so `complete()` creates the session **defensively** (degrades to model default if the param is rejected, rather than failing a run).
- **Implementation (backend):** `models.py` — role-based `PLANNER/EXECUTION/REPLANNER_MODEL`, `MODEL_MENU` + `ROLE_DEFAULTS` + `resolve_model`; `THINKING_LEVELS` + `EFFORT_DEFAULTS` + `resolve_effort`; gateway carries per-role model + effort, `complete()` forwards `reasoning_effort`. `planner.py` carries `_model` + `_effort`. `main.py` — public `GET /models` (menu, defaults, thinking levels, thinking defaults) and `/agent/run` accepts validated `model_*` + `think_*` overrides (fail-safe to defaults).
- **Implementation (frontend):** `App.jsx` fetches `/models` and renders a collapsible **Models** panel — each role row has a **model select + thinking select**, pre-filled from the researched defaults and sent as query params on run; `i18n.js` en + zh-Hant labels (tech terms kept in English).
- **Verification:** added `test_model_routing.py` (defaults-in-menu/levels, resolve_model/resolve_effort fallback, gateway+planner+executor threading, public `/models`). Offline gate green throughout: **143 → 150 → 152 passed**, network-free, no regressions.
- **Honesty:** the model/level picks are research-recommended but **not independently verified by me** — exact SDK id strings, a couple benchmark cells, and the Copilot per-model effort-clamp behavior carry the researcher's flags. Did NOT start round-3; nothing pushed.
