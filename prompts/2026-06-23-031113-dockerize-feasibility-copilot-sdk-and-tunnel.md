# Dockerization Feasibility: Copilot SDK + Cloudflare Tunnel

- **Datetime:** 2026-06-23 (system clock returned 03:11:13)
- **Summary:** Investigate feasibility of dockerizing the app such that it (1) still uses the GitHub Copilot SDK via a token in .env and (2) still exposes the Cloudflare tunnel with the token gate, publicly. Grounded via /code-planner (codebase) + /research (external).

## Prompt

> investigate the feasibility of dockerize this app and it should fullfil two 1. it can still
> use the github copilot sdk using the token or something set in .env 2. it can expose the
> cloudfront tunnel with basic auth still and expose to the public. do /research and
> /code-planner as grounding for this /save-prompt

## What I Did

- /code-planner grounding: read models.py, security.py, provider.py, run-local.ps1, .env.example, README. Found the only real Docker blocker is the Copilot SDK (per-OS wheels, interactive gh auth on the stdio path); token gate + Playwright + tunnel are easy.
- /research findings ([nomd], not saved as research doc):
  - Copilot SDK: ships manylinux wheels (glibc Linux OK; Alpine/musl NOT, issue #591). Non-interactive auth via COPILOT_GITHUB_TOKEN (or GH_TOKEN/GITHUB_TOKEN) - CLI uses it automatically, bypasses libsecret/keychain. Token = fine-grained PAT, user-owned, with 'Copilot Requests' permission (classic PAT unsupported). Caveat: the Windows pin 1.0.2 / macOS 1.0.3 are not the Linux wheel - Dockerfile must install a manylinux version (verify at build).
  - cloudflared: runs headless in Docker (cloudflare/cloudflared). Token-based NAMED tunnel recommended for containers (cloudflared tunnel run --token). Caveat: quick tunnels officially do NOT support SSE (our core transport) + 200-concurrent cap -> use a named token tunnel (free CF account) for a real deploy. App-level AGENT_ACCESS_TOKEN gate is OS-agnostic, unchanged.
- Verdict: BOTH FEASIBLE. Plan: base mcr.microsoft.com/playwright/python:vX-jammy (glibc), pip install backend + manylinux github-copilot-sdk, uvicorn serves API+SSE+dist+screenshots, docker-compose adds cloudflared (named token tunnel). Repo changes: Dockerfile + compose + entrypoint; platform-conditional SDK pin; rewrite run-local.ps1. models.py/security.py/provider.py unchanged (already env-driven).
- Did NOT build it (feasibility investigation only); did NOT commit.
