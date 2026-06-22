# browser-agent

Natural-language browser-automation agent. See [`DESIGN.md`](./DESIGN.md) for the full
design and [`docs/`](./docs/INDEX.md) for the grounding research.

**Status: M3 eval layer + M4 frontend/public deploy** — on top of the M0–M2 core
(FastAPI + SSE, `BrowserProvider`, Copilot LLM gateway, redaction, the perceive ->
locate -> act -> verify loop with the bounded recovery ladder). M3 adds the self-built
eval set + scoring harness (key-node TCR/TSR, pass^k, nominal-vs-verified silent-failure
gap, budget-matched baseline) — see [Eval](#eval-m3). M4 adds a React frontend with a live
step timeline and an **inspectable-failure view** (per step: annotated screenshot,
chosen locator tier, `failure_category`, recovery/retry chain, nominal-vs-verified
verdict), per-step screenshot capture served out-of-band, and a desktop self-host +
Cloudflare quick-tunnel deploy. `/agent/run` streams real step events; `/sse/stream`
is the M0 placeholder. The deterministic core needs no LLM; the planner lazy-connects
to Copilot on first use.

**Supported / unsupported:** bot-wall-free public sites only. Login / MFA / CAPTCHA /
anti-bot walls are routed to an "unsupported" outcome, never evaded.

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
quick tunnel. Uptime depends on the desktop staying on during evaluation (DESIGN §9).

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
