# Project Claude Code Rules — browser-agent

## Think Before Coding

- **State assumptions explicitly.** If multiple interpretations exist, present them — don't pick silently. If something is unclear, stop and ask.
- **Surface tradeoffs.** Don't hide cost/benefit. If a simpler approach exists, say so. Push back when warranted.
- **No sycophancy.** Agreeing when wrong wastes time. If you think a premise is mistaken, say so with reasoning.
- **Don't manage confusion by guessing.** Say "I haven't verified" rather than "should work".

## Plan Before Non-Trivial Code

- **For any task touching > 1 file or > ~30 lines:** state a brief plan first (steps + how each step is verified), wait for approval, then code.
- **For trivial changes** (typo, one-liner, obvious bug fix): just do it.

## Simplicity First

- **Minimum code that solves the problem.** No speculative features, no configurability that wasn't asked for, no error handling for impossible scenarios, no abstractions for single-use code.
- **Three similar lines beat a premature abstraction.**
- **If you wrote 200 lines and it could be 50, rewrite before showing it.**

## Code Comments

- **Default: write no comments.** Code should self-explain through naming. If you feel the urge to comment, first try renaming or extracting a function.
- **When you do comment, explain WHY, never WHAT.** "Increment counter" is noise; "1-indexed because the upstream protocol requires it" is signal.
- **Legitimate reasons to comment:**
  - Non-obvious workaround — link the cause (bug ID, spec, browser quirk, library version)
  - Hidden invariant, precondition, or ordering requirement not visible from the signature
  - Warning: race condition, thread safety, side effect, performance pitfall
  - Reference to external spec / RFC / paper the code implements
  - Genuinely complex algorithm that resists further simplification
- **Never write task-anchored comments.** No "added for the X flow", "as requested", "fixes issue #123", "TODO from this chat", "AI-generated". Those belong in commit messages / PR descriptions.
- **Audience is an engineer reading this in 12 months**, not the reviewer of today's diff.

## Surgical Changes

- **Don't make unnecessary changes.** Do not touch formatting, comments, imports, or code unrelated to the mission. Every changed line should trace directly to what was asked.
- **Don't refactor things that aren't broken.** Match existing style unless the style itself is the bug.
- **Clean up only your own mess.** Remove imports/variables that your changes orphaned. Don't delete pre-existing dead code unless asked.

## Engineering Rigor (CRITICAL — applies to ALL work)

- **NEVER use self-consistency as validation.** Always use independent ground truth. If validation uses the same formula as production code, it will pass even when both are wrong.
- **NEVER claim "no bug" or "passes" without tracing the actual code with concrete examples.** Specific inputs, specific values, step by step. Not abstract reasoning, not "should work."
- **Before saying "I'm sure":** read the code, trace the execution, construct a failing scenario. If you haven't done this, say "I haven't verified."
- **Evidence-based debugging:** execution tracing, divergence detection. Never guess from stale memory.

## Secrets, Tokens & Credentials

- **Never commit secrets.** No API keys, tokens, passwords, connection strings, cookies, session data, or `.env` files in the repo or in git history.
- **Read config from the environment.** Use `process.env` / environment variables (or a git-ignored `.env` loaded at runtime). Provide a `.env.example` with placeholder values only.
- **Never print secrets** in logs, error messages, screenshots, traces, or the web frontend. Redact tokens and credentials before they reach any output or stored artifact.
- **No personal data in the repo.** No real emails, usernames, machine paths, internal hostnames, or org-internal identifiers in code, comments, prompts, or docs. Use placeholders.
- **Browser automation captures sensitive state.** Treat captured cookies, auth headers, local storage, and page content (which may contain logged-in PII) as secrets — keep them out of committed logs, fixtures, and eval artifacts.
- **If a secret is exposed,** stop, rotate it, and scrub it from history — don't just delete the latest copy.

## Commit Messages

- **NEVER** include `Co-Authored-By` lines or any AI attribution in git commit messages.

## Browser-Agent Engineering Principles (grounded in `docs/`)

These distill `docs/research/00-synthesis-and-design-implications.md`. **Before designing, implementing, or verifying any agent component, consult `/browser-agent-expert`** for the grounded decision + its source + verification flag. The docs and that skill are the source of truth — when a principle changes, update them, not just this list. A `vendor-unverified` number is not a fact; carry the flag through.

### Design

- **Keep the LLM out of the hot path.** Deterministic / cached / rule-based execution first; invoke the LLM only on failure. This is the cost lever *and* the reliability lever at once.
- **Hybrid perception.** Fused DOM + accessibility-tree indexed element list as primary; screenshot + Set-of-Marks only when DOM grounding is ambiguous, and only with sparse, precise boxes. **Never feed raw DOM** (token blowup).
- **Verify-after-act is mandatory.** Predict expected effect → act → diff actual vs predicted (DOM / URL / network) → re-ground on NO_CHANGE. Ground every correction signal in observable browser state, **never** in the LLM's self-assessment.
- **Self-correction = classify-then-respond, not generic retry.** not-found → re-ground/heal; not-interactable → wait/scroll/dismiss overlay; wrong-page → replan; stale/timing → state-wait then retry the *same* action.
- **Self-maintenance = semantic-first locator cascade.** `getByRole`+name → `getByLabel` → `getByText`+role → `getByTestId` → heuristic fingerprint → LLM re-rank of ≤5 → vision. Two-layer cache so a hit costs 0 LLM tokens. Avoid CSS/XPath as primary.
- **Retry only on a new observation.** Escalate retry → local strategy-switch → global replan on exhaustion; **confirm before any side-effecting (write/submit) retry**; expose an explicit `ask_user` escape hatch.
- **Hierarchical plan + stateless sub-task executor** (fresh context per sub-task to avoid pollution).
- **Anti-bot: route, don't evade.** Send Cloudflare-Turnstile / DataDome / login-walled sites to a "needs-auth / unsupported" outcome. That list *is* the honest unsupported-sites disclosure ASSIGNMENT.md requires.
- **Observability is first-class.** Every step logs prompt, model version, chosen locator + cascade level, screenshot, predicted-vs-actual diff, and failure class.

### Implementation

- **Swappable browser-runtime interface.** Self-host Playwright/Chromium as default; Steel.dev / Browserbase as escalation. Stateless ephemeral browser per task; recycle to bound memory creep.
- **Tiered models.** Haiku/o4-mini triage → Sonnet workhorse → Opus/o3 strictly gated on repeated failure. Prompt caching + Batch API on by default. Raw frontier-per-step is a cost trap.
- **Frontend = SSE progress streaming** (`sse-starlette`/FastAPI) with the AG-UI event vocabulary; a Skyvern-style **inspectable-failure view** (annotated screenshot · element tree · prompt+raw response · locator+cascade level · `failure_category` · retry chain · HAR).
- **Observability backend = Langfuse + OpenTelemetry GenAI spans** (each Playwright action wrapped as a tool span). The trajectory store feeds frontend replay and the anomaly trip-wire.
- **Deploy headless Chromium in a real container** (`mcr.microsoft.com/playwright` base, `--disable-dev-shm-usage`, non-root, `tini`).
- **Redact secrets at serialization, not post-hoc** — see *Secrets, Tokens & Credentials* above. No raw cookie/auth/`sk-*` ever reaches a span, SSE `data:`, or replay file.

### Verification

- **Independent ground truth, hard verifiers first.** Deterministic post-state checks (DOM / URL / API / extracted field) before any LLM judge; not needing a judge removes its worst failure modes. (Extends *Engineering Rigor*: never self-consistency.)
- **If an LLM judge is unavoidable:** different model family from the agent, explicit **"Unknown" escape hatch**, one dimension per call. Panels don't fix correlated error — spend extra judges on independent axes.
- **Measure silent failure explicitly.** Report **nominal vs verified completion** (CuP-style); the delta is the headline reliability number. **Never** accept verbalized confidence as a success signal. Stack: Semantic-Entropy probe on extraction + consistency sampling + independent post-action state check + trajectory anomaly trip-wire.
- **Report pass^k (k≥3), not pass@1** for any side-effecting task (booking/order/submit) — one wrong run in k is product-fatal.
- **Eval-set discipline.** Domain × task-type × difficulty tiers; ≥20% held-out unseen sites; block shortcut paths; **WebCanvas key-node (TCR/TSR) scoring over binary**; REAL + Inspect AI as harness; target n≈1,000 and report SE/CI. Build eval-first from 20–50 *real* failure cases with two-reviewer pass/fail agreement.
- **Ablation rule (non-negotiable):** any "X improves performance" claim must report total token usage **and** a budget-matched vanilla-actor baseline.
- **Surface failure modes honestly** — concrete unsupported-site examples; intent drift is an open problem we *mitigate* (goal-level verify) but do not claim to solve.
