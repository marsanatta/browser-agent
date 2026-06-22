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
