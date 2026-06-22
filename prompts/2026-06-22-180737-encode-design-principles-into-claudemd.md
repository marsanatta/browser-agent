# Encode Grounded Design/Impl/Verification Principles Into CLAUDE.md

- **Datetime:** 2026-06-22 18:07:37
- **Summary:** Use the browser-agent-expert skill to distill the grounded research into design, implementation, and verification engineering rules, added as a section in the project .claude/CLAUDE.md to enforce best-quality work on the assignment.

## Prompt

> now with /browser-agent-expert now with the principles for design,implementation,verification for .claude/CLAUDE.md making sure it is perform best quality for this assignment.md /save-prompt

## What I Did

- Invoked the `browser-agent-expert` skill and followed its query protocol: routed the cross-category request to the synthesis doc `docs/research/00-synthesis-and-design-implications.md` (the primary cross-category source) and read it as ground truth.
- Appended a new **"Browser-Agent Engineering Principles (grounded in docs/)"** section to `.claude/CLAUDE.md`, organized as Design / Implementation / Verification, each rule one line:
  - Design: LLM-out-of-hot-path, hybrid perception (never raw DOM), mandatory verify-after-act, classify-then-respond failure handling, semantic-first locator cascade, retry-only-on-new-observation + ask_user, hierarchical+stateless executor, anti-bot routing as the honest unsupported list, first-class observability.
  - Implementation: swappable browser runtime, tiered models + caching, SSE/AG-UI frontend + Skyvern-style inspectable-failure view, Langfuse+OTel, containerized headless Chromium, redact-at-serialization.
  - Verification: hard-verifiers-first, judge guardrails, nominal-vs-verified (CuP) + silent-failure stack, pass^k≥3, eval-set discipline (key-node scoring, REAL/Inspect AI, n≈1000), the budget-matched-baseline ablation rule, honest failure-mode surfacing.
- Kept it surgical (append only; existing sections untouched) and pointed back to `/browser-agent-expert` + the docs as the source of truth, with the verification-flag discipline preserved.
- Saved this prompt and committed.
