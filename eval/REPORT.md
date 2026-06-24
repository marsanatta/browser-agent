# Eval Report — live evidence

Generated **2026-06-24 13:30 UTC** from a REAL harness run. Every "verified" below is an
INDEPENDENT programmatic state check on the live page (URL / first-h1 / scoped
selector) — never the agent's self-report, and never a loose `text_contains`.
Copilot calls this run: 23.

## Test architecture — what gates vs what's evidence

- **Offline CI gate — 93 pytest tests (`pytest -m "not live"`): NO network, NO
  Copilot, deterministic, must stay green.** No real-site task is in this gate.
- **Sandbox eval set (`eval/eval_set/tasks.yaml`)** — inline-deterministic fixtures
  plus practice-site (toscrape / herokuapp) tasks; run through the harness with Copilot.
- **Live real-world tier (`eval/eval_set/live_real_world.yaml`)** — REAL public sites,
  diverse domains/types. Flaky and changing, so run ON DEMAND
  (`python -m eval.run_live_tier`) and reported here. NOT part of the CI gate; a
  red row here is evidence, not a broken build.

## Live real-world tier — 3/4 verified

| task | site | type | deterministic? | nominal | verified | abstained |
|---|---|---|---|---|---|---|
| live_wikipedia_helium_retrieval | en.wikipedia.org | retrieval | no (live) | True | True | False |
| live_pydocs_json_nav | docs.python.org | action | no (live) | True | True | False |
| live_google_search_steam | www.google.com | action | no (live) | True | False | False |
| live_wikipedia_signin_synonym | en.wikipedia.org | action | no (live) | True | True | False |

## Day-3 realistic batch (folded in, reproducible) — 8/8 verified

| task | site | type | deterministic? | nominal | verified | abstained |
|---|---|---|---|---|---|---|
| internet_form_auth_nav | the-internet.herokuapp.com | action | no (live) | True | True | False |
| internet_login_page_reached | the-internet.herokuapp.com | action | no (live) | True | True | False |
| books_open_light_in_attic | books.toscrape.com | retrieval | no (live) | True | True | False |
| books_open_travel_category | books.toscrape.com | action | no (live) | True | True | False |
| books_price_visible | books.toscrape.com | retrieval | no (live) | True | True | False |
| quotes_open_einstein_author | quotes.toscrape.com | retrieval | no (live) | True | True | False |
| quotes_open_login | quotes.toscrape.com | action | no (live) | True | True | False |
| synonym_label_signin_vs_login | (inline data: URL) | action | yes (inline) | True | True | False |

## Notes

- **deterministic?** "yes (inline)" rows use a data: URL fixture (no network);
  every other row hits a live site over the network and may vary run-to-run.
- **abstained** = the agent asked the user instead of acting — an honest
  non-completion, never a silent wrong action. Where nominal == verified on a row,
  there was no silent failure on that run.
- The 93 offline pytest tests remain the network-free green gate; this live tier is
  separate and does not gate.

## Honest caveats

- **Real sites bot-wall and change.** A live `verified=False` can be an anti-bot
  interstitial (route-to-unsupported per the project's "route, don't evade" policy),
  not an agent regression. Inspect the final URL to distinguish — a `/sorry/`,
  consent, or CAPTCHA page is a bot-wall. Observed this run:
  `live_google_search_steam` landed on Google's `/sorry/` CAPTCHA: the press/Enter DID
  submit (its `continue=` URL is `/search?q=steam`), but Google blocks headless
  automation, so it never reached results -> `nominal=True, verified=False`. The
  independent check caught that silently-claimed success — exactly its job, and the
  only silent failure in this run.
- **The press/submit action is proven deterministically** by the offline test
  `tests/test_ambiguity_grounding.py::test_press_action_submits_form` (no network, part
  of the 93-green gate); the Google row shows the submit firing on a real site, then a
  bot-wall — not a press failure.
- A live row that abstains (asked=True) is an honest non-completion; only a
  `nominal=True, verified=False` row is a silent failure worth chasing.
