# browser-agent

A browser agent that takes a plain-English task and runs it on a real website — then
measures, with an independent check, whether it actually succeeded or only *looked* like it did.

> **Three terms, defined once:**
> - **Browser agent** — a program that reads a natural-language task (for example "open the
>   Helium article on Wikipedia") and drives a real web browser to do it: click, type, scroll,
>   navigate.
> - **DOM / accessibility tree** — the structured data a web page exposes. The agent reads
>   these (not a raw screenshot) to find elements like buttons and links.
> - **Nominal vs verified** — *nominal* success means the agent ended the task claiming success.
>   *Verified* success means an independent check confirmed the goal on the final page. The gap
>   between them is the **silent-failure rate** — the most important reliability number here.

The agent does two hard things beyond clicking: it **self-corrects** (on failure it diagnoses
the cause from what the browser actually shows, then changes strategy) and it **self-maintains**
(when a selector breaks, it re-finds the element through a cascade of fallbacks). It is honest
about where it fails: walled sites (login / CAPTCHA / anti-bot) are reported as failures, never
evaded.

---

## Table of contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Run it](#run-it)
- [Live frontend](#live-frontend)
- [Key design decisions](#key-design-decisions)
- [Decisions that changed (and why)](#decisions-that-changed-and-why)
- [Works well (with examples)](#works-well-with-examples)
- [Known limitations (with examples)](#known-limitations-with-examples)
- [Repo layout](#repo-layout)
- [Where AI helped](#where-ai-helped)
- [Security](#security)

---

## What it does

You type a task in plain English. The agent runs it in a real browser and streams its progress
to a web page in real time. When a step fails, you can open an **inspectable-failure view** for
that step: the screenshot, the element it tried, the failure category, the retry chain, and an
honest final verdict (goal-verified / actions-completed / failed).

The default engine is **LLM-in-loop (also called agentic)**: one language-model session drives
the browser, deciding each step from what the page actually shows. This was not the first
design. The project started with a deterministic "plan-then-execute" engine and switched after a
controlled experiment — see [Decisions that changed](#decisions-that-changed-and-why).

---

## How it works

The default engine runs **one Copilot tool-calling session per task**. The language model (LLM)
decides each step by calling tools; deterministic code grounds the elements and decides success.

```
plain-English task
  → one tool-calling session, looping until "finish":
       observe → (read | click | fill | navigate) → verify → finish
```

- **observe(target)** — filtered perception. It lists only the interactive elements whose
  accessibility name relates to `target` (an ARIA role + name list). The agent never reads raw
  page HTML; that would blow up cost.
- **click / fill(target)** — a deterministic grounding cascade resolves the visible text or
  label to a real element: role + name → role → id → test-id → aria-label → href → text. The
  reply tells the model whether the page actually changed.
- **read(target)** — read text off the page (a price, a fact, body prose), for tasks that
  extract a value.
- **verify(goal)** — a deterministic check against the live page: `url_contains`,
  `text_visible`, or `selector_visible`. It reads the real DOM and URL. It does **not** trust the
  model's claim.
- **finish(success)** — ends the task. **`finish(success=true)` is rejected unless the
  deterministic `verify` just passed and the page is not blocked.** This is the trustable-success
  backstop: the model's word is never accepted as success.

This is *self-correction* and *self-maintenance* in one loop: the model sees the real page at
every step. If a click misses (the page did not change), it observes again and picks a better
target. If it hits a login or CAPTCHA wall, it gives up immediately and reports failure — it
never tries to log in or solve a CAPTCHA. The loop is bounded: at most 25 tool calls and 120
seconds per task.

A second engine — the original deterministic **plan-then-execute** ("script-orchestration") — is
still in the repo and can be selected with `AGENT_MODE=script-orchestration`, but it is no longer
the default. The reason is measured, below.

All LLM calls route through the **GitHub Copilot SDK used as a model gateway** (a hard constraint
of this assignment) — never a direct Anthropic or OpenAI call.

---

## Run it

**Prerequisites.** Docker, plus a GitHub Copilot login for live LLM calls. The deterministic
parts and the offline tests need no Copilot.

### Option A — Docker (what the frontend uses)

```bash
cp .env.example .env
# In .env, set two values:
#   GH_TOKEN            = output of `gh auth token` (reuses your Copilot login)
#   AGENT_ACCESS_TOKEN  = a long random secret that gates the public endpoints
#                         (python -c "import secrets; print(secrets.token_urlsafe(32))")

docker compose up --build          # starts the app on http://localhost:8123
```

### Option B — Local (Windows desktop, one command)

```powershell
# Build the backend virtual environment once (see backend/pyproject.toml for extras):
cd backend; python -m venv .venv; .venv\Scripts\pip install -e ".[dev]"; cd ..

# Build the frontend and serve the app on http://localhost:8123:
.\scripts\run-local.ps1
```

`run-local.ps1` builds `frontend/dist` and runs the backend (which serves the API, the SSE
stream, the built frontend, and screenshots from one origin). Set `AGENT_ACCESS_TOKEN` in the
git-ignored `backend/.env` to gate the public endpoints; share that token only with people who
should drive the agent.

### Option C — Tests

```powershell
cd backend
.venv\Scripts\python -m pytest -m "not live" -q   # offline unit tests, network-free, no Copilot
.venv\Scripts\python -m pytest -q                 # adds live Playwright tests over the real network
```

---

## Live frontend

The web page accepts a task, shows the live step timeline, and makes failures inspectable. It
is served by the backend on `http://localhost:8123`.

One detail a reviewer should know:

- **The stream uses POST, not the browser's `EventSource`.** Some edge proxies/CDNs buffer
  Server-Sent Events (SSE) sent over GET and release them only at the end. Sending the same
  stream over POST makes it arrive live. This is why progress updates appear step by step, not
  all at once at the end.

The public endpoints require the access token (sent as a cookie or an `Authorization: Bearer`
header — never in the URL). Only `/health` and the static frontend are open.

---

## Key design decisions

Each decision is backed by a reason or by measured evidence.

| Decision | Reason or evidence |
|----------|--------------------|
| **LLM-in-loop is the default engine** | A controlled A/B test on the 80-task eval set, with the model held identical, showed the agentic loop beats deterministic plan-then-execute by **+40 points verified and 18× fewer silent failures**, at slightly lower cost. See [Decisions that changed](#decisions-that-changed-and-why). |
| **Cost is perception size × call count × model tier — not whether the LLM is in the loop** | The agentic loop makes more calls per task (~10), but each call's perception is **filtered** to elements related to the target, so each call is small. Measured, it is **~16% cheaper** than plan-then-execute at the same model. Cost is measured, never inferred from loop shape. |
| **Hybrid perception, never raw HTML** | `observe` returns an ARIA role + name element list filtered to the target. Raw HTML would blow up token cost and add noise. |
| **Self-maintenance = a deterministic grounding cascade** | `click` / `fill` resolve the visible text to a real element through role + name → role → id → test-id → aria-label → href → text. When a click misses, the model observes again and picks a better target. |
| **Success is decided by a deterministic check, never self-report** | `finish(success=true)` is rejected unless an independent check (`url_contains` / `text_visible` / `selector_visible`) passed on the live page **and** the page is not blocked. The model's claim is recorded as *nominal*; the independent check is *verified*. |
| **The verify condition must be strict and specific** | A loose check that passes on the wrong page is the main cause of false success. The agent is told to verify the specific URL path **and** a goal-unique landmark, not generic page text. |
| **Anti-bot: route, don't evade** | On a login / CAPTCHA / anti-bot wall the agent gives up on the first sign and reports failure. It holds no credentials and solves no CAPTCHA. |

---

## Decisions that changed (and why)

Two decisions were tried, measured, and then changed — the design is evidence-driven, not a priori.
Full method, numbers, and caveats live in `ANALYSIS.md`; the high-level version:

1. **Default engine: script-orchestration → LLM-in-loop.** The agent first ran as deterministic
   plan-then-execute (the LLM plans once, Python runs the steps, the LLM stays out of the per-step
   loop). A controlled A/B on the 80-task eval set — model held identical — showed the LLM-in-loop
   engine wins by **+40 points verified, 18× fewer silent failures, and ~16% lower cost**. The old
   "plan-then-execute is ~5× cheaper" belief turned out to be ~90% the model choice, not the
   architecture. The default switched; the old engine stays as `AGENT_MODE=script-orchestration`.
   → [ANALYSIS §2.1 — the experiment](./ANALYSIS.md#21-the-experiment--and-why-we-migrated-from-script-orchestration).
2. **Two of three "silent failures" were eval-design flaws, not agent bugs.** Two cases had vague
   or knowledge-mixed instructions; rewritten as clean browser-navigation tasks, they verified
   correctly. The lesson: validate the test before blaming the system.
   → [ANALYSIS §4 — how correctness is verified](./ANALYSIS.md#4-how-correctness-is-verified-the-agent-cannot-grade-itself).

---

## Works well (with examples)

These are the **good cases in the live demo gallery** (`frontend/src/examples.js` — the picked
examples shown in the UI, the source of truth for this list). Each ships a discriminating success
**criterion**, so a finished run shows **verified ✓**, not just *nominal* (§4).

| Gallery case (live) | What it exercises | Verified by (criterion) |
|---|---|---|
| **docs.python.org** — Std Library → json module | two-hop documentation navigation | `url_contains library/json` |
| **Wikipedia** — pick 'Argon' from autocomplete | a real typeahead-widget interaction | `h1_equals "Argon"` |
| **GOV.UK** — Driving & transport → Driving licences | two-hop browse | `url_contains browse/driving/driving-licences` |
| **Amazon** — search "usb c cable" → open first result | clicks through the headless "Continue shopping" anti-bot interstitial, searches, opens the product | `url_contains /dp/` |
| **the-internet** — read the on-load modal's title | a modal that pops up on load | `selector_text_equals .modal-title h3` |
| **httpbin** — fill + submit a multi-field order form | text / tel / email / radio / checkboxes / textarea, each named from its wrapping `<label>` | `url_contains httpbin.org/post` |
| **stockanalysis.com** — Apple → Balance Sheet | multi-step financial drill-down | `url_contains financials/balance-sheet` |
| **stockanalysis.com** — compare NVDA vs JPM P/E, drill into the winner | cross-page reasoning: read each live P/E, judge which is higher, open the winner's Balance Sheet | `url_contains /nvda/financials/balance-sheet` |
| **screener.in** — search TCS → read ROCE | search + read a live company metric | `url_contains /company/TCS` |

**Rubric-targeted hard cases.** A focused set that probes the three things the test grades —
**silent-failure prevention**, **self-correction**, and **self-maintenance** — each with a
discriminating state check (never a loose URL match). Every assertion was confirmed *discriminating*
on the live page before encoding (`research/selector_probe*.py`); they run via the eval harness
(`eval/passk_live.py`, one subprocess per run) and the first three are in the live gallery.

| Hard case | Axis it probes | Why it's hard | Verified by |
|---|---|---|---|
| **todomvc** — add 3 items, complete the 2nd, filter to Active | **silent-failure** | the URL never changes — only the real DOM state separates success from failure, so a lazy `url_contains` would falsely pass. There is no Add button: items commit on **Enter**. | `selector_text_equals .todo-count "2 items left"` |
| **uitestingplayground/disabledinput** — enable, then type | **self-correction** | the field starts *disabled*; typing first silently fails — the agent must enable it and **wait for editability** before typing | `input_value_equals #inputField "hello world"` |
| **uitestingplayground/ajax** — click, wait for the result | **self-correction** | the result appears ~15 s later via AJAX — the agent must **state-wait**, not declare done early | `selector_text_equals #content "Data loaded with AJAX get request."` |
| **the-internet/dynamic_controls** — Remove, wait until gone | **self-correction** | the removal is **async** (~2 s); the agent must wait for the state change, not act on stale state | `selector_text_equals #message "It's gone!"` |
| **selectorshub** — type into the *First Crush* field | **self-maintenance** | the input lives inside a **shadow DOM** — plain locators miss it; the locator cascade must pierce the shadow root | `input_value_equals #inp_val "browser agent"` |
| **the-internet/add_remove_elements** — Add 3 elements | **self-maintenance** | the created *Delete* buttons have **no stable id/selector** — the agent must locate dynamically-generated, id-less elements | `element_count #elements .added-manually == 3` |

Two of these drove real engine fixes: a **`getByPlaceholder` locator tier** (the todomvc / shadow
inputs are named only by their placeholder) and **`fill` pressing Enter on a trailing newline** (so
Enter-to-submit inputs with no button — todomvc, search boxes — actually commit).

**Population evidence (not just hand-picked cases).** The live eval set has **80 tasks across 19
domains**, split by site into dev / holdout / sealed so "generalization" is real, not
memorization. Scored by the independent check, on the default agentic engine:

| Split | Tasks | Verified | Silent failures |
|-------|-------|----------|-----------------|
| dev | 39 | 0.923 | 0 |
| holdout | 21 | 0.810 | 0 |
| sealed (scored once) | 20 | 1.000 | 0 |
| **Total** | **80** | **0.913 (73/80)** | **0** |

Source: [`research/executor-ab-plan-mode-vs-llm-in-loop.md`](./research/executor-ab-plan-mode-vs-llm-in-loop.md)
(the agentic column), corrected for one case: that run reported `internet_modal` as a silent
failure, but it was a **verifier case-sensitivity bug** — the modal title renders UPPERCASE via CSS
while the assertion expected the mixed-case source text, so a correct read false-failed. With the
verifier fixed (case-insensitive text match), `internet_modal` verifies, so measured silent
failures drop from 1 to **0** and the dev/total rates rise by that one case. This is a single run;
live sites flake by a few tasks, so treat small per-split differences as noise. The sealed split is
scored only once, so its number cannot be over-fit.

---

## Known limitations (with examples)

These are the **limitation cases in the live demo gallery** (`frontend/src/examples.js`). They are
listed **on purpose**; every one is **detected and reported** (an honest abstain / give-up), never
silently wrong.

| Case | Real example (live gallery) | Status |
|------|--------------|--------|
| **Login wall** | `screener.in` — a public screen opens, but sorting it redirects to a sign-up / login page | Honest give-up: the agent hits the wall **mid-task** and abstains instead of faking the sort. |
| **CAPTCHA** | `google.com/recaptcha/api2/demo` — Submit is gated by a reCAPTCHA | Honest give-up. The agent will not solve or bypass a CAPTCHA. |
| **Anti-bot (DataDome)** | `g2.com` — HTTP 403; a DataDome challenge shell whose HTML loads `captcha-delivery.com` | Detects the wall and abstains honestly (no false success); never spoofs a fingerprint. |
| **Anti-bot (Cloudflare)** | `nowsecure.nl` — the modern "Just a moment…" managed challenge | Recognizes the block (body: "performing security verification") and abstains. Route, don't evade. |
| **iframe contents** | `the-internet.herokuapp.com/iframe` — typing inside a rich-text editor in an iframe | The grounding cannot act inside the iframe, so the agent **gives up honestly** (not silent). |

**Beyond the gallery cases**, two honest limitations apply across tasks: a **grounding miss on a
dense page** (e.g. Wikipedia periodic-table navigation) ends in honest non-completion once the step
budget runs out; and **failures are expensive** — the agentic loop retries to its 25-step budget
(~$0.08–0.10/task), so a failure costs more than `script-orchestration`'s early give-up.

**One honest gap in how walls are handled.** Anti-bot / CAPTCHA walls now get a distinct `BLOCKED`
classification (`detect_block`, naming the cause), but detection runs **after** acting, there is no
clean top-level "unsupported" run verdict, and a plain login wall still ends in a generic give-up. A
**pre-flight** detector (HTTP 403, a CAPTCHA iframe, a password field on a sign-in page) would give a
cleaner verdict. The probe script `backend/probe_unsupported.py` is the seed for it; wiring it
into the loop is future work.

### Unsupported — real probe evidence

These three walls were probed with the real browser (`backend/probe_unsupported.py`: headless
Chromium, `domcontentloaded`, 30 s timeout). Each row is the observed state, not a guess. The point
is that the agent **fails closed and reports failure** — it never tries to log in, solve a CAPTCHA,
or spoof a fingerprint.

| Wall type | Site | What the probe saw | Why it is unsupported |
|-----------|------|--------------------|-----------------------|
| CAPTCHA | `google.com/recaptcha/api2/demo` | HTTP 200, the form fields visible; the reCAPTCHA itself is a cross-origin challenge iframe the agent cannot act on | The agent can fill the form, but Submit is gated by a CAPTCHA it will not solve. |
| Anti-bot (DataDome) | `g2.com` | HTTP 403, empty body — a ~2.5 KB DataDome challenge shell whose HTML loads `captcha-delivery.com` | DataDome blocks the automated client at the edge (403) and serves a challenge shell. The agent abstains honestly — never a false success, never a fingerprint spoof. |
| Anti-bot (Cloudflare) | `nowsecure.nl` | HTTP 403, title "Just a moment…", body "Performing security verification … protect against malicious bots" | A managed JS challenge served inline; `detect_block` matches the body text and the agent abstains. |

Routed-away categories (never evaded): Cloudflare Turnstile / DataDome / PerimeterX, CAPTCHA
pages, login / MFA gates, and banking / SSO / healthcare sites.

---

## Repo layout

```
backend/app/agent/agentic_executor.py  the DEFAULT engine: one LLM-in-loop tool-calling session
backend/app/agent/agentic/             agentic support: cdp.py (perceive + grounding cascade), skill.py (prompt + budgets)
backend/app/agent/executor.py          the legacy plan-then-execute engine (AGENT_MODE=script-orchestration)
backend/app/agent/                     planner, locate (plan-mode cascade), perceive, act, classify, recover
backend/app/agent/verify.py            the deterministic success check (surfaced as the agentic `verify` tool)
backend/app/browser/                   swappable browser runtime (Playwright default; CDP escalation seam)
backend/app/obs/                       tracing + redact (secrets masked before any log / span / SSE / screenshot)
backend/app/stream/                    SSE event vocabulary (live timeline + annotated-screenshot events)
backend/app/main.py                    FastAPI server: /agent/run (POST stream), /auth, /health, static frontend
frontend/                              React + Vite: task input, live timeline, inspectable-failure view
eval/                                  live eval set (80 tasks, dev/holdout/sealed) + scoring harness + REPORT.md
docs/                                  design grounding research (browser-agent papers/theses)
prompts/                               dated, verbatim key prompts — the AI-collaboration trail
research/                              autoresearch findings, the executor A/B experiment, eval-report.md
ANALYSIS.md                            efficiency, cost, extensibility, correctness analysis
```

---

## Where AI helped

This repo was built AI-first. The prompt records in [`prompts/`](./prompts/) are the actual log,
not reconstructions. The main places AI helped:

1. **Grounding the design in research.** A self-scoring research loop read state-of-the-art
   browser-agent papers and built the `docs/` knowledge base **before any code**. Those grounded
   principles were encoded into `.claude/CLAUDE.md` so every later step inherited them — and were
   **corrected later** when first-party measurements disagreed (for example, the "keep the LLM out
   of the loop" cost belief).
2. **Hardening the design and building it.** A grill session plus a multi-agent review loop
   stress-tested the design, and the implementation was built through an engineering pipeline
   (ground → plan → code → review → test → debug) with a fresh-context reviewer at each step.
3. **An eval-driven improvement loop, with AI doing the loop and the review.** AI ran rounds of
   "expand the eval set → find a failure cluster → try a fix → check for regressions", and ran the
   controlled A/B that decided the engine. My role was to watch the key metrics and make the final
   keep / discard call. One important result was a **measured reversal**: the deterministic
   "LLM-out-of-the-loop" engine was replaced by the agentic loop only after the numbers showed it
   was both more reliable and not more expensive.

Every "passed" or "verified" claim was checked from the code — often by an independent AI
reviewer — before it was kept.

---

## Security

- **Redaction runs before any output.** Secrets (`sk-*`, Bearer tokens, `Authorization` /
  `Cookie` headers, API keys, GitHub tokens) and obvious PII (emails) are masked in
  `backend/app/obs/tracing.py::redact` before data reaches a log, a span, the SSE stream, or a
  stored screenshot. Captured cookies and page state are treated as secrets and are git-ignored.
  Never commit `.env`.
- **The public endpoints are gated by one shared secret** (`AGENT_ACCESS_TOKEN`). It is checked
  in constant time, **fails closed** (unset → 503, wrong → 401), and is exchanged once at
  `POST /auth` for an httponly cookie. The token is **never accepted in a `?token=` URL** —
  URL-borne tokens leak through logs, history, and `Referer`.
- **Threat model.** This is a **single-operator demo**. The gate stops a
  stranger who learns the URL from draining the operator's Copilot quota. It has no per-user
  identity or revocation by design — real user accounts are out of scope for this assignment.

Public or self-created material only. Set the access token in the git-ignored `.env`, share it
out-of-band, and never commit or print it.
