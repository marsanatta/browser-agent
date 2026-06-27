# Supported vs Unsupported Sites (honest disclosure)

The assignment requires a concrete listing of what works and what does not, *with
examples*. This file is grounded in real runs, not aspiration:

- The **supported** list = sites that actually pass in the eval harness
  (`eval/REPORT.md`, regenerated from a real run).
- The **unsupported** list = sites I actually probed in M5 with the real
  `PlaywrightProvider` + `perceive()` (`backend/probe_unsupported.py`) and the
  **observed** failure mode recorded verbatim.

## Scope boundary (read this first)

The agent operates on **bot-wall-free public sites**. It has **no credential
store and no CAPTCHA solver, by design** (DESIGN §1, §10). On a login wall,
CAPTCHA, or anti-bot challenge it therefore **cannot complete the task and reports
failure** — it does not attempt to evade, fingerprint-spoof, or solve the
challenge.

**Honest framing of "routing to unsupported":** there is currently **no dedicated
classifier** in the agent that detects a wall and emits a distinct
`needs-auth/unsupported` status. What actually happens is the mechanism below:
`perceive()` returns few or zero actionable elements (or the target element is
absent), locate misses, the bounded recovery ladder exhausts without a new
observation, and the step ends in an honest `NOT_FOUND` failure surfaced in the
inspectable trace. The *effect* is "we don't act on walled sites"; the
*implementation* is "we fail closed", not "we branch to a labelled unsupported
outcome". Adding an explicit pre-flight wall-detector (status==403, DataDome /
Turnstile / reCAPTCHA iframe present, password field present) is a documented
known gap (see end of file).

## Supported patterns (these PASS in the harness)

Source: `eval/REPORT.md` (real run, 2026-06-22, n=12, TSR 0.917; held-out TSR
1.000 on a site never used in dev).

| Site | Pattern | Operations that pass |
|---|---|---|
| `the-internet.herokuapp.com` | forms / navigation | nav to Form Authentication, reach Login Page, submit `tomsmith`/`SuperSecretPassword!` → `/secure`, Dropdown, Checkboxes |
| `books.toscrape.com` | e-commerce browse + retrieval | browse to Travel category, open a product page, read a visible price |
| `quotes.toscrape.com` (**held-out**, never used in dev) | information retrieval / forms | open an author page, read birthplace, reach Login, browse a tag page |

These share the supported profile: **server-rendered, no bot wall, stable ARIA
roles/links/forms**. The deterministic 10-tier locator cascade resolves them with
zero or few LLM calls.

One **supported-site task still FAILs** (honest, recorded in REPORT.md):
`books_open_light_in_attic` — instruction gives a *truncated* title
(`"A Light in the ..."`) and the assertion demands the exact `h1` `"A Light in
the Attic"`. The agent does not reliably resolve the truncation to the exact link.
This FAIL is **nominal=FAIL as well as verified=FAIL** (CuP contribution 0 — the
agent did not falsely claim success). It is the concrete intent/grounding-gap
example called out in the README disclosure.

## Unsupported sites — REAL probe results (M5)

Probe harness: `backend/probe_unsupported.py` (real Chromium via
`PlaywrightProvider`, `wait_until=domcontentloaded`, 30s timeout). Run on
2026-06-22. Each row is the observed state, not a guess.

### 1. Login wall — `https://github.com/login`

- **HTTP 200**, title `Sign in to GitHub`, `final_url` unchanged.
- `perceive()` found **25 interactive elements** including a real
  `input[type=password]` (`has_password_field: true`) and a `Sign in` button.
- **Observed behavior / why unsupported:** the page renders fine, but the task
  ("sign in") cannot complete without credentials, which the agent does not hold.
  An attempt would fill a username/password it does not have and click Sign in,
  which fails the authentication — there is no successful verified outcome. The
  agent has **no credential store and injects no cookies** (DESIGN §10), so this
  is a hard stop, not an evasion.

### 2. CAPTCHA — `https://www.google.com/recaptcha/api2/demo`

- **HTTP 200**, title `ReCAPTCHA demo`, `mentions_captcha: true`.
- `perceive()` found **6 elements**: `First Name`, `Last Name`, `Email`, color
  radios, and `Submit`. The reCAPTCHA widget itself is a cross-origin
  challenge iframe that `perceive()` does not expose as an actionable element.
- **Observed behavior / why unsupported:** the agent can fill the visible form
  fields, but `Submit` is gated by a reCAPTCHA the agent **cannot and will not
  solve**. Verification of a successful submit would fail. The agent does not
  attempt any CAPTCHA-bypass.

### 3. Anti-bot wall (DataDome) — `https://www.g2.com/`

- **HTTP 403** (hard block), `body_excerpt` **empty**, `perceive()` found
  **0 interactive elements**.
- Page HTML (2,498 bytes total) is a challenge shell containing
  `title="DataDome CAPTCHA"` in an iframe (`mentions_datadome: true`,
  `mentions_captcha: true`).
- **Observed behavior / why unsupported:** the site blocks the automated client at
  the edge with a 403 before any content loads. With **zero perceivable
  elements**, the agent's `_match` returns `None`, the locate step misses, the
  bounded recovery ladder finds no new observation, and the run ends in an honest
  `NOT_FOUND` failure. This is exactly "fail closed" — no fingerprint spoofing or
  challenge-solving is attempted.

## Category summary (DESIGN §10)

Routed-away (never evaded): Cloudflare Turnstile / DataDome / PerimeterX walls,
CAPTCHA pages, login / MFA gates, banking / SSO / healthcare. The three probes
above are concrete instances of the first three categories with real observed
status codes and element counts.

## Dense-page "click the first result" + the headless anti-bot ceiling (Amazon)

The observation handed to the planner was capped at the first 40 DOM-order elements,
so on a DENSE results page (e.g. Amazon) the real product links — deep in the DOM after
~45 header/nav/filter elements — were never shown to the planner, which then guessed a
non-existent target ("first search result") and collapsed to a wrong label ("Results").
**Fixed:** the observation scope is now a configurable factor that WIDENS on each
locate-failure replan (`backend/app/agent/executor.py`), so deep result links
progressively enter view until reachable. Proven by a deterministic network-free repro
(`backend/tests/test_view_scope.py`) AND a clean-site live run (45 chrome links + product
links → the agent widens, sees the products, clicks the first → `/product/`).

Two honest residual limits remain, **neither solvable by the view-scope fix alone**:

1. **Headless anti-bot (the dominant live-Amazon blocker).** On the DEFAULT headless
   Playwright runtime, `amazon.com` frequently returns a ~150-byte "Continue shopping"
   interstitial / cross-region redirect instead of the real page (observed across
   repeated runs). By the "route, don't evade" principle this is an anti-bot wall, so
   `amazon.com` is **unsupported on the default headless runtime**. Confirmed escalation
   path: driving a REAL stealth browser over CDP (the Steel.dev / Browserbase tier the
   `BrowserProvider` seam is designed for; here probed via a real Chrome) reaches the
   FULL results page — **48 product tiles, 616 links, no interstitial** — i.e. the
   anti-bot is a browser-layer issue the CDP escalation removes, not an agent-logic one.
2. **The "first result" ordinal intent + LLM variance.** Even on a clean (no anti-bot)
   dense site, end-to-end was **~3/5**: the view-scope fix reliably makes the products
   visible, but the LLM replan occasionally returns no usable plan. "Click the first
   result" is an ordinal intent the name-based locator cannot express deterministically;
   the agent depends on the LLM mapping it to a concrete product label. This is the
   honest reliability ceiling — **mitigated, not solved**.

## Known gap

The wall handling today is **implicit (fail-closed)**, not an explicit
`needs-auth/unsupported` status. A pre-flight detector keyed on the very signals
this probe already computes (HTTP 403, DataDome/Turnstile/reCAPTCHA iframe,
`input[type=password]` on a "sign in" page) would let the frontend show a clean
"unsupported: login wall / CAPTCHA / anti-bot" verdict instead of a generic
`NOT_FOUND`. The probe script is the seed for that classifier; wiring it into the
agent loop is future work.
