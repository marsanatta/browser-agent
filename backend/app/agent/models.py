"""LLM gateway over the GitHub Copilot SDK (Python).

Hard constraint: every LLM call routes through the Copilot SDK used as a model
gateway. We never call Anthropic/OpenAI directly. The Copilot CLI runs as a
local headless server (`copilot --headless --port N`); we connect with
`CopilotClient(connection=RuntimeConnection.for_uri("localhost:N"))`, then issue
a tightly-scoped per-call request with an explicit model.

Verified against the installed package (github-copilot-sdk 1.0.2, the latest
version with a Windows wheel; 1.0.3 ships macOS-only wheels) and
docs.github.com/en/copilot/.../copilot-sdk:
    from copilot import CopilotClient, RuntimeConnection
    from copilot.session import PermissionHandler
    client = CopilotClient(connection=RuntimeConnection.for_uri("localhost:PORT"))
    await client.start()
    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all, model="gpt-5")
    resp = await session.send_and_wait("...")   # SessionEvent | None;
                                                # resp.data.content holds text

The SDK is async-native. Connection is LAZY: nothing connects at import or app
startup, so the app boots and SSE works WITHOUT a live Copilot server/auth
(connect happens on first `complete()`/`judge()`).

setup: `pip install github-copilot-sdk==1.0.2`; run `copilot --headless --port
$COPILOT_PORT` with COPILOT_GITHUB_TOKEN exported. If the package/CLI is absent,
this gateway raises a clear error on first LLM use only — boot is unaffected.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.obs.tracing import redact

# Tiered routing: cheap triage -> workhorse -> escalation. The judge MUST be a
# different model FAMILY from the actor to avoid self-preference correlation.
# IDs verified against `client.list_models()` on Copilot CLI 1.0.63 (2026-06).
ACTOR_TRIAGE = "gpt-5-mini"
ACTOR_WORKHORSE = "gpt-5.4"
ACTOR_ESCALATION = "claude-opus-4.8"
JUDGE_MODEL = "claude-sonnet-4.5"


@dataclass(frozen=True)
class LLMResponse:
    model: str
    content: str
    output_tokens: int | None = None  # completion tokens (resp.data.output_tokens), nullable
    usage: dict | None = None  # full ledger from the assistant.usage event, when present


class MockGateway:
    """Test double with the LLMGateway surface (complete/judge), no Copilot auth.

    `responder` maps a prompt to the raw text the model would return, so a test
    can drive the L2 locator fallback (or any LLM seam) deterministically."""

    def __init__(self, responder) -> None:
        self._responder = responder
        self.calls: list[str] = []

    async def complete(self, prompt: str, model: str = ACTOR_WORKHORSE) -> LLMResponse:
        self.calls.append(prompt)
        content = self._responder(prompt)
        # Synthetic usage event so the per-task token ledger is offline-testable
        # (no Copilot, no network) — same shape the real assistant.usage event has.
        out = len(content.split())
        inp = len(prompt.split())
        usage = {
            "input_tokens": inp,
            "output_tokens": out,
            "reasoning_tokens": 0,
            "total_nano_aiu": (inp + out) * 1000,
        }
        return LLMResponse(model=model, content=content, output_tokens=out, usage=usage)

    async def judge(self, prompt: str) -> LLMResponse:
        return await self.complete(prompt, model=JUDGE_MODEL)

    async def close(self) -> None:
        return None


class LLMGateway:
    """Lazy-connecting wrapper around a shared Copilot headless server.

    One CLI server backs many sessions; we open a fresh session per call so the
    actor context stays clean (stateless sub-task executor) and per-call model
    selection works.
    """

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        # If COPILOT_HOST/PORT are configured, connect to a separately-run
        # headless server (the DESIGN.md deployment shape) via for_uri. Otherwise
        # use stdio against the SDK's bundled binary, which works out-of-box with
        # `gh` auth and needs no separate server.
        self._host = host or os.getenv("COPILOT_HOST")
        self._port = port or (int(os.getenv("COPILOT_PORT")) if os.getenv("COPILOT_PORT") else None)
        self._client = None

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from copilot import CopilotClient, RuntimeConnection
        except ImportError as exc:  # setup: package not installed
            raise RuntimeError(
                "github-copilot-sdk is not installed; run "
                "`pip install github-copilot-sdk==1.0.2`."
            ) from exc

        if self._host and self._port:
            conn = RuntimeConnection.for_uri(f"{self._host}:{self._port}")
            client = CopilotClient(connection=conn)
        else:
            # stdio against the bundled Copilot CLI. It authenticates from the
            # process env automatically — COPILOT_GITHUB_TOKEN / GH_TOKEN /
            # GITHUB_TOKEN (docs.github.com/.../authenticate-copilot-cli). Make the
            # dependency explicit so a missing token fails fast with guidance on
            # first LLM use, rather than as an opaque auth error.
            if not any(os.getenv(v) for v in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")):
                raise RuntimeError(
                    "No Copilot token in the environment. Set COPILOT_GITHUB_TOKEN in "
                    ".env to a fine-grained PAT owned by your personal account with the "
                    "'Copilot Requests' permission (classic PATs are not supported)."
                )
            client = CopilotClient()
        await client.start()
        self._client = client
        return client

    async def complete(self, prompt: str, model: str = ACTOR_WORKHORSE) -> LLMResponse:
        client = await self._ensure_client()
        from copilot.session import PermissionHandler

        session = await client.create_session(
            on_permission_request=PermissionHandler.approve_all, model=model
        )
        # Accumulate the real token ledger from the assistant.usage event (input +
        # output + reasoning + total_nano_aiu). Best-effort: if the SDK surface
        # differs, the resp.data.output_tokens read below still gives completion tokens.
        usage: dict = {}

        def _on_event(event: Any) -> None:
            # CopilotSession.on(handler) delivers EVERY SessionEvent. The usage event's
            # data is AssistantUsageData (it carries reasoning_tokens, unlike the
            # message data); accumulate its ledger across the call's events.
            data = getattr(event, "data", None)
            if data is not None and hasattr(data, "reasoning_tokens"):
                for k, v in _usage_from_event(event).items():
                    usage[k] = usage.get(k, 0) + v

        try:
            session.on(_on_event)
        except Exception:
            pass

        resp = await session.send_and_wait(prompt)
        return LLMResponse(
            model=model,
            content=_extract_text(resp),
            output_tokens=_extract_output_tokens(resp),
            usage=usage or None,
        )

    async def judge(self, prompt: str) -> LLMResponse:
        """Verification call routed to a different model FAMILY than the actor."""
        return await self.complete(prompt, model=JUDGE_MODEL)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.stop()
            self._client = None


def _extract_text(resp) -> str:
    """Pull text from a send_and_wait result.

    The published examples disagree slightly on the response shape
    (`resp.data.content` vs `resp.content`); read defensively and redact the
    content before it can reach a span/SSE/log.
    """
    data = getattr(resp, "data", None)
    src = data if data is not None else resp
    text = getattr(src, "content", None) or ""
    return redact(text)


def _extract_output_tokens(resp: Any) -> int | None:
    """The easy completion-token read: resp.data.output_tokens (nullable)."""
    data = getattr(resp, "data", None)
    src = data if data is not None else resp
    val = getattr(src, "output_tokens", None)
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


_USAGE_KEYS = ("input_tokens", "output_tokens", "reasoning_tokens", "total_nano_aiu")


def _usage_from_event(event: Any) -> dict:
    """Extract a token ledger from an assistant.usage SessionEvent. The real event's
    `data` is AssistantUsageData (input/output/reasoning_tokens directly, and
    `copilot_usage.total_nano_aiu` nested). Defensive: also accepts a synthetic
    object/dict (offline tests) on `event.data`, `event.usage`, or the event itself."""
    for src in (getattr(event, "data", None), getattr(event, "usage", None), event):
        if src is None:
            continue
        out: dict = {}
        for key in _USAGE_KEYS:
            val = src.get(key) if isinstance(src, dict) else getattr(src, key, None)
            if val is not None:
                try:
                    out[key] = int(val)
                except (TypeError, ValueError):
                    pass
        cu = src.get("copilot_usage") if isinstance(src, dict) else getattr(src, "copilot_usage", None)
        if cu is not None:
            nano = cu.get("total_nano_aiu") if isinstance(cu, dict) else getattr(cu, "total_nano_aiu", None)
            if nano is not None:
                try:
                    out["total_nano_aiu"] = int(nano)
                except (TypeError, ValueError):
                    pass
        if out:
            return out
    return {}
