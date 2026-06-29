"""Token gate for the publicly-exposed agent endpoints.

The agent is reachable over a public URL (e.g. behind the Azure Container Apps
ingress); without a gate, anyone who learns the URL could drive the browser agent
and burn the operator's Copilot quota. Protected paths require a shared secret
from `AGENT_ACCESS_TOKEN`.

Fail-closed: if `AGENT_ACCESS_TOKEN` is unset, protected paths return 503 — the
operator must configure a token before exposing it publicly.

The token is accepted from the `agent_token` cookie or an `Authorization:
Bearer` header. The cookie path is what makes SSE (`EventSource`) and `<img>`
screenshot loads work, since neither can set request headers; the browser
attaches the cookie automatically. We deliberately do NOT accept a `?token=`
query param: URL-borne tokens leak through access logs, proxy logs, browser
history, and `Referer` headers. Keeping the token out of the URL also avoids
tripping `redact()`.
"""

from __future__ import annotations

import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

COOKIE_NAME = "agent_token"
_PROTECTED_PREFIXES = ("/agent", "/sse", "/screenshots")


def _configured() -> str | None:
    token = os.environ.get("AGENT_ACCESS_TOKEN")
    return token or None


def is_configured() -> bool:
    return _configured() is not None


def _bearer(header: str | None) -> str | None:
    if header and header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def valid(supplied: str | None) -> bool:
    configured = _configured()
    if not configured or not supplied:
        return False
    return secrets.compare_digest(supplied, configured)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in _PROTECTED_PREFIXES):
            if _configured() is None:
                return JSONResponse(
                    {"detail": "AGENT_ACCESS_TOKEN not configured"}, status_code=503
                )
            supplied = request.cookies.get(COOKIE_NAME) or _bearer(
                request.headers.get("authorization")
            )
            if not valid(supplied):
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)


def issue_cookie(response: Response, token: str, secure: bool) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=86400,
        path="/",
    )
