# browser-agent

Natural-language browser-automation agent. See [`DESIGN.md`](./DESIGN.md) for the full
design and [`docs/`](./docs/INDEX.md) for the grounding research.

**Status: M0 scaffold** — FastAPI + SSE skeleton, `BrowserProvider` interface, Copilot
SDK LLM gateway (lazy-connect), redaction + observability seam, React/Vite frontend. The
agent loop itself is M1. The app starts and SSE streams **without** a live Copilot
connection.

**Supported / unsupported:** bot-wall-free public sites only. Login / MFA / CAPTCHA /
anti-bot walls are routed to an "unsupported" outcome, never evaded.

## Prerequisites (Windows desktop self-host)

- **Python 3.11–3.12** (`github-copilot-sdk` requires >= 3.11; the Windows wheel is
  pinned to 1.0.2 — 1.0.3 ships macOS-only wheels).
- **Node 18+** for the frontend.
- **GitHub Copilot CLI** for live LLM calls (not required for M0 boot/tests):
  `copilot --headless --port 4321`. The backend connects to this as a model gateway and
  connects **lazily** on first LLM use, so M0 runs without it.

## Backend

```powershell
cd backend
uv venv --python 3.11           # or: python -m venv .venv
uv pip install -e ".[dev]"      # or: .venv\Scripts\pip install -e ".[dev]"
copy .env.example .env          # placeholders; edit if running live Copilot
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
```

- Health: `http://localhost:8000/health`
- SSE stream: `http://localhost:8000/sse/stream?task=demo` (placeholder step events).

Run tests:

```powershell
cd backend
.venv\Scripts\python -m pytest -q
```

For live browser runs later (M1+), install the Chromium binary once:
`.venv\Scripts\python -m playwright install chromium`.

## Frontend

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173, subscribes to the backend SSE endpoint
```

Point the frontend at a non-default backend with `VITE_BACKEND_URL`. Production build:
`npm run build`.

## Live LLM (Copilot SDK gateway)

All LLM calls route through the GitHub Copilot SDK used as a model gateway — never a
direct Anthropic/OpenAI call. Start the headless CLI server and export its token (the
token is read by the **CLI server**, not committed):

```powershell
$env:COPILOT_GITHUB_TOKEN = "gho_your_token"
copilot --headless --port 4321
```

The backend reads `COPILOT_HOST` / `COPILOT_PORT` from `.env` and connects on first LLM
call.

## Security

Redaction runs **before** any data reaches a span, an SSE `data:` field, a log, or a
stored trace (`backend/app/obs/tracing.py::redact`). Secrets (`sk-*`, Bearer tokens,
`Authorization`/`Cookie` headers, `api_key=`, GitHub tokens) and obvious PII (emails) are
masked. Captured cookies / auth / page state are treated as secrets and are git-ignored.
Never commit `.env`.
