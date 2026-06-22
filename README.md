# browser-agent

Natural-language browser-automation agent. See [`DESIGN.md`](./DESIGN.md) for the full
design, [`ANALYSIS.md`](./ANALYSIS.md) for runtime/cost/scalability/correctness analysis,
[`UNSUPPORTED_SITES.md`](./UNSUPPORTED_SITES.md) for the real supported/unsupported probe,
and [`docs/`](./docs/INDEX.md) for the grounding research.

**Status: M0–M5 complete.** Core (M0–M2): FastAPI + SSE, `BrowserProvider`, Copilot LLM
gateway, redaction, the perceive -> locate -> act -> verify loop with the bounded recovery
ladder. Eval (M3): self-built eval set + scoring harness (key-node TCR/TSR, pass^k,
nominal-vs-verified silent-failure gap, budget-matched baseline) — see [Eval](#eval-m3).
Frontend/deploy (M4): React frontend with a live step timeline and an
**inspectable-failure view** (per step: annotated screenshot, chosen locator tier,
`failure_category`, recovery/retry chain, nominal-vs-verified verdict), per-step screenshot
capture served out-of-band, and a desktop self-host + Cloudflare quick-tunnel deploy. Docs
+ honest disclosures (M5): this README, `ANALYSIS.md`, `UNSUPPORTED_SITES.md`. `/agent/run`
streams real step events; `/sse/stream` is the M0 placeholder. The deterministic core needs
no LLM; the planner lazy-connects to Copilot on first use.

## Architecture (one paragraph)

NL task -> **planner** (decompose into sub-tasks) -> per sub-task a deterministic
**perceive -> locate -> act -> verify -> classify -> recover** loop, with **self-maintenance**
(a 10-tier deterministic locator cascade -> fingerprint heal -> LLM re-rank -> vision, behind
a 2-layer cache so a hit costs zero tokens) and **self-correction** (predict the expected
effect, diff actual vs predicted after acting, classify the failure from *observable browser
state* — never the LLM's opinion — then re-ground / wait-scroll-dismiss / state-wait /
replan). All LLM calls route through the **GitHub Copilot SDK used as a model gateway** (hard
constraint), kept out of the hot path. The **frontend** subscribes over **SSE** and renders a
live timeline plus an inspectable per-step failure trace. An **eval harness** grades every run
by independent programmatic assertions on the live page (not the agent's self-report). Full
rationale with source citations in [`DESIGN.md`](./DESIGN.md).

## Supported / unsupported (honest disclosure)

Scope: **bot-wall-free public sites only.** Login / MFA / CAPTCHA / anti-bot walls are out of
scope; the agent holds no credentials and solves no CAPTCHAs, so on those sites it **fails
closed and reports failure — it never evades**. The full list with **real probe evidence**
(HTTP status, element counts, observed failure mode for github.com/login, a reCAPTCHA demo,
and a DataDome-walled site) and the passing supported patterns is in
[`UNSUPPORTED_SITES.md`](./UNSUPPORTED_SITES.md).

## Honest disclosure: intent drift & silent failure

**Intent drift is an open problem we mitigate but cannot eliminate.** A self-healed locator
can click a *plausible-but-wrong* element while a naive check stays green — nominal success,
verified failure. We mitigate with **verify-after-act** (predict -> diff -> re-ground) and by
making **nominal-vs-verified completion (CuP) the headline eval metric** (DESIGN §5, §6); we do
**not** claim to eliminate false success. The eval harness grades success by independent
programmatic assertions on the live page, never the agent's self-report, precisely so silent
failures are measurable rather than hidden.

**Concrete honest example (a real FAIL in `eval/REPORT.md`):** `books_open_light_in_attic`
gives a *truncated* title (`"A Light in the ..."`) and asserts the exact `h1`
`"A Light in the Attic"`; the agent does not reliably resolve the truncation, so the task is
`verified=FAIL`. Critically it is **also `nominal=FAIL`** — the agent did not falsely claim
success — so CuP stays 0.000 on this run (11/12 verified, TSR 0.917 ± 0.080). This is the
behaviour we want: a real miss surfaced honestly, not a silent pass.

## Where AI helped

This repo was built AI-first; the prompt records in [`prompts/`](./prompts/) are the actual
log. AI was used to:
- **Ground the design in research** — a self-scoring research loop built the `docs/`
  knowledge base from SOTA browser-agent papers/theses before any code
  (`prompts/2026-06-22-170558-grounding-research-loop.md`).
- **Make that knowledge navigable + gated** — a `browser-agent-expert` retrieval skill over
  `docs/`, validated with an agent-teams routing gate
  (`prompts/2026-06-22-180206-...index-skill-gate.md`).
- **Encode the grounded principles into `.claude/CLAUDE.md`** so every later step inherited
  them (`prompts/2026-06-22-180737-...encode-design-principles...md`).
- **Gate-review and grill the design** — `/grill-me` + an agent-teams review loop hardened
  `DESIGN.md` before implementation (`prompts/2026-06-22-191141-design-planning-gate-and-grill.md`).
- **Build it with the eng-pipe pipeline** (ground -> plan -> code -> review -> test -> debug)
  (`prompts/2026-06-22-191141-implement-plan-eng-pipe.md`).

## Prompt records

Key prompts that drove development live in [`prompts/`](./prompts/) (the assignment asks for
these; they are the real records, not reconstructions).

## Prerequisites (Windows desktop self-host)

- **Python 3.11–3.12** (`github-copilot-sdk` requires >= 3.11; the Windows wheel is
  pinned to 1.0.2 — 1.0.3 ships macOS-only wheels).
- **Node 18+** for the frontend.
- **Chromium** for Playwright: `.venv\Scripts\python -m playwright install chromium`.
- **GitHub Copilot** for live LLM calls (not required for the deterministic core or its
  tests). By default the gateway talks to the SDK's bundled binary over stdio and uses
  your `gh` / `copilot login` auth — no separate server needed. To target a separately-run
  headless server instead, set `COPILOT_HOST` + `COPILOT_PORT` in `.env`.

## Backend

```powershell
cd backend
uv venv --python 3.11           # or: python -m venv .venv
uv pip install -e ".[dev]"      # or: .venv\Scripts\pip install -e ".[dev]"
copy .env.example .env          # placeholders; edit if running live Copilot
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
```

- Health: `http://localhost:8000/health`
- M0 placeholder stream: `http://localhost:8000/sse/stream?task=demo`.
- **M1 agent loop**: `http://localhost:8000/agent/run?task=<NL task>` — plans with the
  Copilot LLM, then runs perceive/locate/act/verify and streams real step events.

Run tests (includes live seed-site integration tests over the real network):

```powershell
cd backend
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m pytest -m "not live" -q   # offline subset only
```

## Eval (M3)

A self-built eval set (`eval/eval_set/tasks.yaml`, ~12 NL tasks across
domain/type/difficulty, with **≥20% held-out on quotes.toscrape.com**, a site never
used in dev) plus a scoring harness that runs each task through the real agent and
grades success by **independent programmatic assertions on the live page** — never the
agent's self-report. Metrics: **key-node TCR/TSR**, **pass^k (k=3)** for side-effecting
tasks, and the headline **nominal-vs-verified (CuP) silent-failure gap**, each with a
**budget-matched vanilla baseline** column (the non-negotiable ablation rule). The
verification layer (`eval/verify/`) is REAL — programmatic state check + a
Semantic-Entropy-style consistency check; SVDD / Inspect AI / full REAL are marked
seams (`eval/verify/seams.py`). Scoring math is unit-tested offline (no Copilot).

```powershell
# Full run (a few dozen Copilot calls); regenerates eval/REPORT.md.
.\scripts\run-eval.ps1
.\scripts\run-eval.ps1 -Limit 3        # smoke run on the first 3 tasks
```

`eval/REPORT.md` is generated from an actual run (metric table, per-task pass/fail,
approximate Copilot call count, honest caveats). Scoring/verify/loader unit tests:

```powershell
cd backend
.venv\Scripts\python -m pytest tests/test_eval_scoring.py tests/test_eval_verify.py tests/test_eval_loader.py -q
```

## Frontend

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173, subscribes to the backend SSE endpoint
```

During development the frontend runs on Vite (`:5173`) and calls the backend via
`VITE_BACKEND_URL` (default `http://localhost:8000`). For the public deploy the built
`dist/` is served by the backend itself from the same origin (see below), so screenshots
and the SSE stream share one host and no CORS/tunnel cross-origin config is needed.

## Public deploy (desktop self-host + Cloudflare quick tunnel)

The backend serves the built frontend at `/` and per-step screenshots at `/screenshots/*`,
so one origin serves the whole app. A Cloudflare **quick tunnel** then exposes it on a
temporary `*.trycloudflare.com` URL — no Cloudflare account or DNS setup required.

```powershell
# 1. Build the frontend (output: frontend/dist, served by the backend)
cd frontend; npm install; npm run build

# 2. Run the backend (serves API + SSE + dist + screenshots)
cd ..\backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8123

# 3. Expose it publicly (separate terminal). cloudflared needs no login for a quick tunnel.
#    Install if missing: winget install --id Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8123
#   -> prints https://<random>.trycloudflare.com  (the public URL)
```

`scripts/run-local.ps1` runs steps 1–2 in one command; pass `-Tunnel` to also start the
quick tunnel and print the public URL.

> **The quick-tunnel URL is ephemeral / single-use.** It exists only while the
> `cloudflared` process runs: it **dies when the process stops and rotates to a new random
> URL on every restart** — there is no stable named hostname. So the URL shared for
> evaluation is valid only for that session, and **the desktop must stay awake** (no sleep /
> hibernate) with both `uvicorn` and `cloudflared` running for the whole evaluation window
> (DESIGN §9). If the box sleeps or either process exits, the public URL goes dead.

> **Protect the tunnel with an access token.** Before exposing the tunnel, the operator MUST
> set `AGENT_ACCESS_TOKEN` to a long random secret (kept out of git — put it in the
> git-ignored `.env`, never commit it) and share that token with evaluators out-of-band. The
> agent / SSE / screenshot endpoints require it (sent as `Authorization: Bearer <token>`, or
> `?token=<token>` for the SSE stream where headers are awkward); only `/health` stays open.
> The frontend prompts for the token and stores it in `localStorage`. **Exposing the tunnel
> WITHOUT a token is unsafe** — the URL is world-reachable, so an open agent endpoint invites
> quota abuse and arbitrary automation against your desktop browser.

When the frontend is served by the backend, leave `VITE_BACKEND_URL` unset before
building so it defaults to same-origin (`""`).

## Live LLM (Copilot SDK gateway)

All LLM calls route through the GitHub Copilot SDK used as a model gateway — never a
direct Anthropic/OpenAI call. By default the gateway connects over **stdio** to the SDK's
bundled binary and uses your existing GitHub auth:

```powershell
gh auth login        # or: copilot login
```

The gateway connects **lazily** on the first LLM call. To target a separately-run headless
server instead, set `COPILOT_HOST` + `COPILOT_PORT` in `.env`. Model IDs
(`backend/app/agent/models.py`) are verified against `client.list_models()`; the judge uses
a different model family from the actor.

## Security

Redaction runs **before** any data reaches a span, an SSE `data:` field, a log, or a
stored trace (`backend/app/obs/tracing.py::redact`). Secrets (`sk-*`, Bearer tokens,
`Authorization`/`Cookie` headers, `api_key=`, GitHub tokens) and obvious PII (emails) are
masked. Captured cookies / auth / page state are treated as secrets and are git-ignored.
Never commit `.env`.

**Public-tunnel access control.** The public endpoints are gated by `AGENT_ACCESS_TOKEN`
(see the deploy section): the agent/SSE/screenshot routes require the token via
`Authorization: Bearer <token>` or `?token=<token>`; `/health` is open. The token is a
secret — set it in the git-ignored `.env`, share it with evaluators out-of-band, and never
commit it or print it in logs/screenshots.
