# Eval Report — live evidence

Generated **2026-06-27 21:57 UTC** from a REAL harness run. Every "verified" below is an
INDEPENDENT programmatic state check on the live page (URL / first-h1 / scoped
selector) — never the agent's self-report, and never a loose `text_contains`.
Copilot calls this run: 215.

## Test architecture — what gates vs what's evidence

- **Offline CI gate — 97 pytest tests (`pytest -m "not live"`): NO network, NO
  Copilot, deterministic, must stay green.** No real-site task is in this gate.
- **Sandbox eval set (`eval/eval_set/tasks.yaml`)** — inline-deterministic fixtures
  plus practice-site (toscrape / herokuapp) tasks; run through the harness with Copilot.
- **Live real-world tier (`eval/eval_set/live_real_world.yaml`)** — REAL public sites,
  diverse domains/types. Flaky and changing, so run ON DEMAND
  (`python -m eval.run_live_tier`) and reported here. NOT part of the CI gate; a
  red row here is evidence, not a broken build.

## Live real-world tier — 19/20 verified

| task | site | type | split | deterministic? | nominal | verified | abstained |
|---|---|---|---|---|---|---|---|
| live_scrapethissite_goto_simple | www.scrapethissite.com | action | sealed | no (live) | True | True | False |
| live_scrapethissite_goto_forms | www.scrapethissite.com | action | sealed | no (live) | True | True | False |
| live_scrapethissite_search_boston | www.scrapethissite.com | action | sealed | no (live) | True | True | False |
| live_scrapethissite_forms_page2 | www.scrapethissite.com | action | sealed | no (live) | True | False | False |
| live_rfceditor_open_http11 | www.rfc-editor.org | action | sealed | no (live) | True | True | False |
| live_rfceditor_title_rfc8259 | www.rfc-editor.org | retrieval | sealed | no (live) | True | True | False |
| live_rfceditor_open_ip | www.rfc-editor.org | action | sealed | no (live) | True | True | False |
| live_rfceditor_title_rfc1149 | www.rfc-editor.org | retrieval | sealed | no (live) | True | True | False |
| live_rfceditor_title_rfc3986 | www.rfc-editor.org | retrieval | sealed | no (live) | True | True | False |
| live_rfceditor_title_rfc2046 | www.rfc-editor.org | retrieval | sealed | no (live) | True | True | False |
| live_webscraper_nav_laptops | webscraper.io | action | sealed | no (live) | True | True | False |
| live_webscraper_nav_tablets | webscraper.io | action | sealed | no (live) | True | True | False |
| live_webscraper_nav_phones | webscraper.io | action | sealed | no (live) | True | True | False |
| live_webscraper_open_ipad_mini_product | webscraper.io | action | sealed | no (live) | True | True | False |
| live_webscraper_nav_phones_touch | webscraper.io | action | sealed | no (live) | False | True | True |
| live_reddit_settings_abstain | www.reddit.com | action | sealed | no (live) | False | True | True |
| live_reddit_inbox_abstain | www.reddit.com | action | sealed | no (live) | False | True | True |
| live_x_notifications_abstain | twitter.com | action | sealed | no (live) | False | True | True |
| live_codeberg_settings_abstain | codeberg.org | action | sealed | no (live) | False | True | True |
| live_x_messages_abstain | twitter.com | action | sealed | no (live) | False | True | True |

## Day-3 realistic batch (folded in, reproducible) — 0/0 verified

| task | site | type | split | deterministic? | nominal | verified | abstained |
|---|---|---|---|---|---|---|---|

## Notes

- **deterministic?** "yes (inline)" rows use a data: URL fixture (no network);
  every other row hits a live site over the network and may vary run-to-run.
- **abstained** = the agent asked the user instead of acting — an honest
  non-completion, never a silent wrong action. Where nominal == verified on a row,
  there was no silent failure on that run.
- The 97 offline pytest tests remain the network-free green gate; this live tier is
  separate and does not gate.

## Honest caveats

- **Bot-walls are now detected and ABSTAINED, not silently passed.** With
  interstitial detection (`verify.detect_block`) a CAPTCHA / `/sorry/` / "unusual
  traffic" page is routed blocked-unsupported (route, don't evade) — the agent asks
  the user instead of claiming success. Example: `live_google_search_steam` — the
  press/Enter submits (its `/sorry/` `continue=` URL is `/search?q=steam`), Google
  serves its anti-bot `/sorry/` CAPTCHA, the agent detects it and abstains ->
  `nominal=False, verified=True (expect_abstain), asked=True`. Before this detection
  it was a silent `nominal=True, verified=False`.
- **The press/submit action is proven deterministically** by the offline test
  `tests/test_ambiguity_grounding.py::test_press_action_submits_form` (no network, part
  of the 97-green gate); `live_wikipedia_search_submit` proves it live on a site that
  does not bot-block (fill 'Oxygen' + Enter -> the Oxygen article).
- A live row that abstains (asked=True) is an honest non-completion; only a
  `nominal=True, verified=False` row is a silent failure worth chasing.

## Widget coverage — the honest fails are real gaps, not verifier bugs

Each widget verifier was confirmed correct on a fresh page; the fails document
genuine agent gaps:
- `live_internet_lazyload`: the result renders ~5s AFTER the click; the agent has
  no explicit wait action, so the state check runs before it appears. (Verifier
  confirmed: click + wait -> `#finish h4` == "Hello World!".)
- `live_internet_modal`: the modal shows correctly (verifier passes on a fresh
  page — note its title renders UPPERCASE via CSS), but the agent tends to dismiss
  it rather than just confirm its title — a modal-handling gap.
- `live_internet_iframe`: the locator cascade does not pierce iframes, so the agent
  cannot type into the TinyMCE body. Verified by a frame-aware check
  (`iframe_text_equals`) so an iframe-piercing fix would pass it later.
