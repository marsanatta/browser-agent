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

from app.obs.tracing import redact

# Tiered routing: cheap triage -> workhorse -> escalation. The judge MUST be a
# different model FAMILY from the actor to avoid self-preference correlation.
ACTOR_TRIAGE = "gpt-4.1"
ACTOR_WORKHORSE = "gpt-5"
ACTOR_ESCALATION = "gpt-5"
JUDGE_MODEL = "claude-sonnet-4.5"


@dataclass(frozen=True)
class LLMResponse:
    model: str
    content: str


class LLMGateway:
    """Lazy-connecting wrapper around a shared Copilot headless server.

    One CLI server backs many sessions; we open a fresh session per call so the
    actor context stays clean (stateless sub-task executor) and per-call model
    selection works.
    """

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self._host = host or os.getenv("COPILOT_HOST", "localhost")
        self._port = port or int(os.getenv("COPILOT_PORT", "4321"))
        self._client = None

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from copilot import CopilotClient, RuntimeConnection
        except ImportError as exc:  # setup: package not installed
            raise RuntimeError(
                "github-copilot-sdk is not installed; run "
                "`pip install github-copilot-sdk==1.0.2` and start "
                "`copilot --headless --port <PORT>`."
            ) from exc

        uri = f"{self._host}:{self._port}"
        client = CopilotClient(connection=RuntimeConnection.for_uri(uri))
        await client.start()
        self._client = client
        return client

    async def complete(self, prompt: str, model: str = ACTOR_WORKHORSE) -> LLMResponse:
        client = await self._ensure_client()
        from copilot.session import PermissionHandler

        session = await client.create_session(
            on_permission_request=PermissionHandler.approve_all, model=model
        )
        resp = await session.send_and_wait(prompt)
        return LLMResponse(model=model, content=_extract_text(resp))

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
