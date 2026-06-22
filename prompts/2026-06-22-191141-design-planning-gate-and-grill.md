# Design Planning: Grounded, Gate-Reviewed, Grilled

- **Datetime:** 2026-06-22 19:11:41
- **Summary:** Produce the implementation design for the browser agent, grounded via /browser-agent-expert, pass an agent-teams review gate (loop until pass), and resolve open decisions via /grill-me + /research before finalizing.

## Prompt

> start the design planning for this mission. read the assignment.md and use /browser-agent-expert as the knowledge source for the design and plan mainly in chinese. before you present your design to me, should fisrt pass the plan review for /agent-teams (each use brwoser-agent-expert too) refine your design, this is a loop refine design until pass the gate /save-prompt

## What I Did

- Drafted `DESIGN.md` grounded in `docs/` (via `/browser-agent-expert`), citing source docs per decision.
- Ran a 3-reviewer grounding gate (architecture / evaluation / infra+compliance), each reviewer using `/browser-agent-expert`. Round 1: B PASS, A & C FAIL.
- Incorporated all critical fixes: A1 observe-first (AgentOccam) as distinct prevention layer; A2 zero-cost deterministic 10-tier locator cascade before LLM; A3 AWM budget-matched counter-example; C1 concrete `UNSUPPORTED_SITES.md`; C2 prompts/ clarification; C3 cost-caveat prominence; C4 intent-drift disclosure; C5 redact-before-span; C6 custom `screenshot_annotated` event.
- Re-ran the gate on the refined plan (A & C lenses) → both flipped to PASS (Gate Round 2 fully passed).
- Plan mode forced; wrote the final plan to the plan file. Used `/grill-me` to resolve open decisions and `/research` where I was uncertain:
  - Strategy: vertical slice → deepen (aim A).
  - Deploy: desktop self-host (Windows-native) + Cloudflare Tunnel (no container/Fly.io/Zeabur).
  - LLM (hard constraint): **GitHub Copilot SDK (Python, headless local server)** used as a model gateway; tiered per-session model + different-family judge. Cost model becomes flat-rate Copilot quota, not per-token.
  - Backend = Python; docs language = English; seed sites = the-internet / automationexercise / books.toscrape / Wikipedia (separate from REAL eval).
- Ported the approved plan into a full English `DESIGN.md`.
