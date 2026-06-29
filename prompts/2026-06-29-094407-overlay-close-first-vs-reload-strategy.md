# Overlay Handling: Close-First Strategy vs Reload

- **Datetime:** 2026-06-29 09:44:07
- **Summary:** User rejected the proposed reload-on-blocked recovery and argued the agent should instead perceive the overlay/ad, close it, confirm the blocker is gone, then retry the click.

## Prompt

> wait i feel: 若 click 連續 3 次以上 TimeoutError,頁面很可能被插頁廣告/cookie/overlay 蓋住 <- this is ok, but the strategy is not ok, is it not possible for agent to view 插頁廣告/cookie/overlay? and then confirm if it can be close then close it first, then validate if it the blocker gone, and it can be clicked again. i feel this is the right strategy

## What I Did

- Treated this as a design-strategy challenge to verify with evidence, not to accept or defend on opinion (no-sycophancy + don't-guess).
- Checked the perception code: `cdp.perceive` DOES scan child frames, and Playwright can reach cross-origin iframes — so my earlier "close button is in a cross-origin iframe, therefore unperceivable" hypothesis was suspect. Tested it instead of trusting it.
- Wrote two probes under `research/finance-cases/` (`probe_vignette.py`, `probe_close.py`) that reproduce the companiesmarketcap Google Vignette interstitial and exercise the agent's real perceive/locate/click path against it.
- **Findings (live):**
  - The agent CAN perceive a close control — `perceive('close') → "Close Ad X"` (user's instinct was right; my unperceivable claim was wrong).
  - BUT `cdp.locate` returns `None` for that perceived element — a real perceive→locate cascade gap (sees it, can't resolve it to click).
  - Even a DIRECT Playwright force-click on "Close Ad X" did NOT dismiss the vignette (`#google_vignette` stayed, Apple still blocked) — the main-frame close is effectively a decoy; the real dismiss lives in a cross-origin `safeframe.googlesyndication.com` iframe.
  - `Escape` does not close it. `navigate`-reload is the only thing that reliably clears the one-shot vignette (matches the earlier captured live runs).
- **Conclusion / pushback:** close-first is correct for normal overlays (cookie banners, in-page modals), but fails on this stubborn ad-vignette. Proposed a LADDER prompt: (1) observe + click a close/dismiss control and re-check, then (2) fall back to reloading the URL if still blocked; never guess deep-link URLs. Surfaced this contradiction to the user before editing the shared system prompt rather than silently implementing close-only.
- **Deferred:** did NOT yet edit `skill.py` or run the A/B — asked the user to choose ladder vs close-only first, since it is a global system-prompt change requiring measurement (cmc-Apple action log + offline gate + a few live cases).
- Also noted the perceive/locate cascade gap as a separate, independently-fixable code bug.
