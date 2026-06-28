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
- [How quality is checked](#how-quality-is-checked)
- [Cost, scalability, correctness](#cost-scalability-correctness)
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

### Option A — Docker + public tunnel (what the frontend uses)

```bash
cp .env.example .env
# In .env, set two values:
#   GH_TOKEN            = output of `gh auth token` (reuses your Copilot login)
#   AGENT_ACCESS_TOKEN  = a long random secret that gates the public endpoints
#                         (python -c "import secrets; print(secrets.token_urlsafe(32))")

docker compose up --build          # starts the app on port 8123 + a Cloudflare tunnel
docker compose logs cloudflared    # prints the public https://<...>.trycloudflare.com URL
```

The default tunnel is a Cloudflare **quick tunnel**: no Cloudflare account, no token. It prints
a temporary `*.trycloudflare.com` URL. To use a **stable named tunnel** instead, set
`CLOUDFLARE_TUNNEL_TOKEN` in `.env` and swap the `cloudflared` command in `docker-compose.yml`
(see the comments there).

### Option B — Local (Windows desktop, one command)

```powershell
# Build the backend virtual environment once (see backend/pyproject.toml for extras):
cd backend; python -m venv .venv; .venv\Scripts\pip install -e ".[dev]"; cd ..

# Build the frontend, serve the app on http://localhost:8123, and start a quick tunnel:
.\scripts\run-local.ps1 -Tunnel
```

`run-local.ps1` builds `frontend/dist`, runs the backend (which serves the API, the SSE stream,
the built frontend, and screenshots from one origin), and — with `-Tunnel` — auto-generates an
`AGENT_ACCESS_TOKEN`, saves it to the git-ignored `backend/.env`, and prints it. Share that
token only with people who should drive the agent.

### Option C — Tests

```powershell
cd backend
.venv\Scripts\python -m pytest -m "not live" -q   # offline unit tests, network-free, no Copilot
.venv\Scripts\python -m pytest -q                 # adds live Playwright tests over the real network
```

---

## Live frontend

The web page accepts a task, shows the live step timeline, and makes failures inspectable. It
is served by the backend behind a Cloudflare tunnel.

Two facts a reviewer should know:

- **The quick-tunnel URL is temporary.** It changes every time the tunnel restarts and dies
  when the process stops, so the URL ships with the submission, not hardcoded here. The desktop
  must stay awake for the whole evaluation window.
- **The stream uses POST, not the browser's `EventSource`.** Cloudflare quick tunnels buffer
  Server-Sent Events (SSE) sent over GET and release them only at the end (cloudflared issue
  #1449). Sending the same stream over POST makes it arrive live. This is why progress updates
  appear step by step, not all at once at the end.

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
| **All LLM calls via the Copilot SDK gateway** | A hard assignment constraint. The agentic loop runs one cheap model (`claude-haiku-4.5`) per session. |

---

## Decisions that changed (and why)

Two decisions were tried, measured, and then changed. Both are kept here because they show the
design is evidence-driven.

### 1. Script-orchestration → LLM-in-loop (the main one)

The agent was first built as **deterministic plan-then-execute** ("script-orchestration"): the
LLM writes a plan once, then Python runs the steps; the LLM stays out of the per-step loop. The
guiding belief was "keep the LLM out of the hot path to save cost."

That design has a structural weakness. It commits to a plan made **before** seeing the page, so
it cannot react to what it actually lands on — and it often **claims success on a page it never
checked** (a silent failure). We built the alternative (LLM-in-loop) and ran a controlled A/B
test on the 80-task eval set, holding the model identical (both `claude-haiku-4.5`):

| Engine (same model) | Verified | Silent failures (CuP) | Cost |
|---------------------|----------|-----------------------|------|
| Plan-then-execute (script-orchestration) | 0.500 (40/80) | 18 | $3.85 |
| **LLM-in-loop (agentic)** | **0.900 (72/80)** | **1** | **$3.24** |

The agentic loop wins by **+40 points verified, 18× fewer silent failures, and ~16% lower cost**.
Plan-then-execute loses even when given an expensive `opus` planner (0.762 verified, at ~2.9× the
cost). An earlier belief that plan-then-execute was "~5× cheaper" turned out to be **~90% the
model choice, not the architecture**. So we switched the default to LLM-in-loop; the old engine
stays as `AGENT_MODE=script-orchestration`. Full method, per-split numbers, and caveats are in
[`research/executor-ab-plan-mode-vs-llm-in-loop.md`](./research/executor-ab-plan-mode-vs-llm-in-loop.md).

### 2. Two of three "silent failures" were eval-design flaws, not agent bugs

When we re-checked a silent-failure cluster, two test cases had vague or knowledge-mixed
instructions. We rewrote them as clean browser-navigation tasks, and they then verified
correctly. The lesson: validate the test before blaming the system.

---

## Works well (with examples)

These patterns are reliable. Each row names a real site and operation, drawn from the live eval
set (`eval/eval_set/live_real_world.yaml`).

| Site | Operation that works | Why it works |
|------|----------------------|--------------|
| `the-internet.herokuapp.com` | Dynamic Loading: click Start and wait for the hidden text to load; Status Codes: click the link for HTTP 200 and confirm the page | Server-rendered, stable ARIA roles and links. |
| `en.wikipedia.org` | Open a named article (Helium, Oxygen); type in the search box and press Enter; pick an autocomplete suggestion (Argon); click the Sign In link | Clear link/role names; the largest slice of the eval set (19 cases). |
| `books.toscrape.com` | Open a book category from the sidebar; open a product page and report its price or stock count | Static e-commerce; deterministic text extraction. |
| `docs.python.org`, `developer.mozilla.org`, `arxiv.org`, `www.gov.uk`, `stackoverflow.com`, `news.ycombinator.com`, `www.gnu.org` | Open a named navigation page (Help, Blog, Questions, Licenses, "new", a standard-library module page) | Server-rendered public docs with stable navigation links. |

**Population evidence (not just hand-picked cases).** The live eval set has **80 tasks across 19
domains**, split by site into dev / holdout / sealed so "generalization" is real, not
memorization. Scored by the independent check, on the default agentic engine:

| Split | Tasks | Verified | Silent failures |
|-------|-------|----------|-----------------|
| dev | 39 | 0.897 | 1 |
| holdout | 21 | 0.810 | 0 |
| sealed (scored once) | 20 | 1.000 | 0 |
| **Total** | **80** | **0.900 (72/80)** | **1** |

Source: [`research/executor-ab-plan-mode-vs-llm-in-loop.md`](./research/executor-ab-plan-mode-vs-llm-in-loop.md)
(the agentic column). This is a single run; live sites flake by a few tasks, so treat
small per-split differences as noise. The sealed split is scored only once, so its number cannot
be over-fit.

---

## Known limitations (with examples)

These cases are hard, unstable, or unsupported. They are listed **on purpose**. With one named
exception, every one is **detected and reported**, not silently wrong.

| Case | Real example | Status |
|------|--------------|--------|
| **Login wall** | `github.com/login` — page loads, but the task needs credentials the agent does not hold | Honest give-up. The agent sees the login form and reports failure on the first sign. |
| **CAPTCHA** | `google.com/recaptcha/api2/demo` — Submit is gated by a reCAPTCHA | Honest give-up. The agent will not solve or bypass a CAPTCHA. |
| **Anti-bot wall** | `g2.com` — HTTP 403 with zero perceivable elements (a DataDome challenge shell) | Fails closed. No fingerprint spoofing is attempted. |
| **Headless anti-bot** | `amazon.com` on the default headless browser often returns a tiny "Continue shopping" interstitial instead of the real page | **Unsupported on the default runtime.** Driving a real browser over CDP (Chrome DevTools Protocol, the designed escalation tier) reaches the full page — it is a browser-layer block, not an agent-logic one. |
| **Wrong-page silent failure** | `the-internet.herokuapp.com/entry_ad` (read a modal title) — the agent claims success but the independent check disagrees | **The one measured silent failure (1 of 80).** A no-oracle ceiling that both engines share. |
| **iframe contents** | `the-internet.herokuapp.com/iframe` — typing inside a rich-text editor in an iframe | The grounding cannot act inside the iframe, so the agent **gives up honestly** (not silent). |
| **Grounding miss on a dense page** | `en.wikipedia.org` periodic-table navigation; some `stackoverflow.com` navigation | Honest non-completion: the agent cannot locate the target, burns its step budget, and gives up. |
| **Failures are expensive** | any task where the target cannot be found | The agentic loop retries up to its 25-step budget (~$0.08–0.10/task), so a failure costs more than plan-then-execute's early give-up. |

**One honest gap in how walls are handled.** The agent gives up on a wall, but it does **not** yet
emit a distinct "unsupported: login / CAPTCHA / anti-bot" label — it ends in a generic give-up. A
pre-flight detector (HTTP 403, a CAPTCHA iframe, a password field on a sign-in page) would give a
cleaner verdict. The probe script `backend/probe_unsupported.py` is the seed for it; wiring it
into the loop is future work.

### Unsupported — real probe evidence

These three walls were probed with the real browser (`backend/probe_unsupported.py`: headless
Chromium, `domcontentloaded`, 30 s timeout). Each row is the observed state, not a guess. The point
is that the agent **fails closed and reports failure** — it never tries to log in, solve a CAPTCHA,
or spoof a fingerprint.

| Wall type | Site | What the probe saw | Why it is unsupported |
|-----------|------|--------------------|-----------------------|
| Login | `github.com/login` | HTTP 200, title "Sign in to GitHub", a real `input[type=password]` among 25 elements | The page loads, but the task needs credentials the agent does not hold (no credential store, no cookie injection). |
| CAPTCHA | `google.com/recaptcha/api2/demo` | HTTP 200, the form fields visible; the reCAPTCHA itself is a cross-origin challenge iframe the agent cannot act on | The agent can fill the form, but Submit is gated by a CAPTCHA it will not solve. |
| Anti-bot (DataDome) | `g2.com` | HTTP 403, empty body, **0 perceivable elements** (a ~2.5 KB DataDome challenge shell) | The site blocks the automated client at the edge before any content loads; with zero elements there is nothing to act on. |

Routed-away categories (never evaded): Cloudflare Turnstile / DataDome / PerimeterX, CAPTCHA
pages, login / MFA gates, and banking / SSO / healthcare sites.

---

## How quality is checked

The differentiator is that success is graded by an **independent check**, never the agent's own
claim.

- **Independent ground truth.** The eval harness grades each run by re-deriving success from the
  actual DOM / URL the agent left, using a check that is **separate code** from the in-loop
  `verify` tool the agent calls. The verifier never grades itself with its own formula.
- **The headline metric is the silent-failure gap** (nominal vs verified), not raw accuracy. The
  system is allowed to be wrong only when it says so. On the default engine the gap is **1 in 80**.
- **Two-pass eval admission.** Every task passed (1) a real-browser probe confirming the check
  holds at the solution page and the path is wall-free, and (2) an independent reviewer
  confirming the check is true *only if* the task is actually done. Weak checks were dropped.
- **In production, verification is opt-in and labeled honestly.** When you supply a success
  criterion, "verified ✓" means that independent check really passed on the final page. Without
  one, the run is shown as **"actions completed — not goal-verified"**, deliberately distinct from
  a verified pass. We do not sell "verified" as a blanket guarantee.

---

## Cost, scalability, correctness

See [`ANALYSIS.md`](./ANALYSIS.md) for the full discussion; the architecture numbers are in
[`research/executor-ab-plan-mode-vs-llm-in-loop.md`](./research/executor-ab-plan-mode-vs-llm-in-loop.md).

- **Runtime.** Per-task time is dominated by the Copilot round-trips, not the browser. The
  agentic loop makes about **10 tool-calling round-trips per task**, bounded by 25 steps and 120
  seconds. The browser actions themselves run in milliseconds.
- **Cost.** The Copilot subscription is **flat-rate, not per-token**, so the real limit is
  **requests per task** (~10), bounded by the Copilot quota and rate limit — not a dollar bill.
  For comparison only, the per-task cost modeled from Copilot's own token ledger is about
  **$0.04 on `claude-haiku-4.5`**, ~16% lower than plan-then-execute at the same model. Dollar
  figures from earlier research are different-model estimates and are **not** quoted as facts.
- **Scalability.** The browser is **stateless and ephemeral per task** (~300–500 MB each,
  recycled on close), so no state leaks between tasks and you scale by running more workers. The
  binding ceiling is the Copilot rate limit, not browser RAM. A queue + autoscale shape is
  designed-for but **not built** — an honest limitation. Deployment today is a single desktop.
- **Correctness.** Graded by the independent check, reported as nominal vs verified. See
  [How quality is checked](#how-quality-is-checked).

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
- **Threat model.** This is a **single-operator demo** on a temporary tunnel. The gate stops a
  stranger who learns the URL from draining the operator's Copilot quota. It has no per-user
  identity or revocation by design — real user accounts are out of scope for this assignment.

Public or self-created material only. Set the access token in the git-ignored `.env`, share it
out-of-band, and never commit or print it.
