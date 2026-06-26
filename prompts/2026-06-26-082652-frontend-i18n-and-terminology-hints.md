# Frontend i18n (EN + zh-Hant) + Newcomer Terminology Hints (via /research + /eng-pipe)

- **Datetime:** 2026-06-26 08:26:52
- **Summary:** Add internationalization to the React/Vite frontend supporting English and Traditional Chinese, and make the jargon-heavy UI legible to someone who has never seen the app. Research the simplest-correct i18n approach first ([nomd], inline), then build it via /eng-pipe in a dedicated git worktree, using the frontend skill set.

## Prompt

> i want frontend to have i18n and support english and traditional chinese /research [nomd] the latest correct way (but not overcomplicated to implement this) /eng-pipe this in a dedicated worktree. and i want the UI to have more hint and terminology explain your audience is the person that don't understand the app. search for the frontend skill set and use them to design and implement.

## What I Did

- **Grounded first:** read the frontend — React 18 + Vite, **plain JSX** (no TS), 2 component files (`App.jsx`, `StepDetail.jsx`), ~50 hardcoded English strings, dense with domain jargon (locator tier, recovery chain, nominal vs verified, silent failure, AIU, failure category). That jargon density is exactly why the "explain to a newcomer" ask matters.
- **Ran /research `[nomd]`** (inline, no file): compared react-i18next vs react-intl/FormatJS vs a minimal custom Context hook for this scale. Grounded recommendation = **minimal Context** on pure simplicity/bundle (0 KB vs ~22 KB), but surfaced the tradeoff honestly. Sources: rafaelcamargo (minimal i18n for small apps), intlpull 2026 comparison, auto18n 2026, Wavelop hooks-only.
- **User decision overrode the minimal recommendation:** chose **react-i18next** explicitly *because it is the de-facto standard* — accepted the heavier bundle for the standard, future-proof path. Locked in.
- **Clarified the two genuine forks via AskUserQuestion** (no silent picks):
  - **Hint style** → hover/tap `ⓘ` tooltips (accessible: keyboard + aria, tap on mobile), explanations translated in both languages.
  - **Hint scope** → **jargon + basic flow** (explain Task / Start URL / Run / supported-sites disclosure AND the technical terms), audience = total newcomer.
- **Set up a dedicated worktree:** `git worktree add -b feat/frontend-i18n C:/Users/weishuhung/workspace/repos/_wt/i18n` (matches the repo's existing `_wt/` worktree convention). All build work happens there; `main` stays untouched.
- **Launched /eng-pipe** in that worktree (grill skipped — pre-aligned via the questions above; grounding done; proceeding to plan → code → fresh-context review → build/test). Frontend skills to apply during code + review: `/vercel-react-best-practices` and `/vercel-web-design-guidelines`.
- **Discipline:** decisions stated explicitly, tradeoff surfaced (did not silently substitute minimal Context after the user picked react-i18next), worktree isolation, not pushed (user reviews + pushes by hand).
