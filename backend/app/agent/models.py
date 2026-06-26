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
(connect happens on first `complete()`).

setup: `pip install github-copilot-sdk==1.0.2`; run `copilot --headless --port
$COPILOT_PORT` with COPILOT_GITHUB_TOKEN exported. If the package/CLI is absent,
this gateway raises a clear error on first LLM use only — boot is unaffected.
"""

from __future__ import annotations

import os
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from app.obs.tracing import redact

# Per-role model defaults. Routing principle (docs/architecture/02, docs/00):
# keep the cheapest *adequate* model on the hot path (execution / L2 re-rank), pay
# for a strong PLANNER (a bad plan multiplies downstream retries, each a billed
# call), and reserve the expensive frontier model for the rare deep REPLANNER
# (the peek-the-page replan).
#
# Picks from research/2026-06-26 (cost + SOTA capability per role; both the legacy
# premium-request-multiplier and the 2026-06 usage-based token billing favour the
# same models). The exact SDK id strings follow the menu's naming convention and
# are NOT re-confirmed against client.list_models() — MODEL_MENU is the single
# source of truth; correct an id here if the live Copilot menu differs.
PLANNER_MODEL = "claude-opus-4.8"      # top web-agent planner (Online-Mind2Web/OSWorld)
EXECUTION_MODEL = "claude-haiku-4.5"   # hot-path tool-calling / L2, cheap+adequate
REPLANNER_MODEL = "claude-opus-4.8"    # rare deep replan that drives the browser

# Curated, selectable ids for the per-role UI picker and override validation (the
# subset we route among, not the whole vendor menu). Used as the FALLBACK when the
# live Copilot list (`available_models`) can't be queried — no token / offline / $0
# path. Every ROLE_DEFAULTS value must appear here so the picker shows the default.
MODEL_MENU = (
    "gemini-3.1-pro",
    "claude-sonnet-4.6",
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "gpt-5-mini",
    "gemini-3-flash",
    "claude-opus-4.8",
    "gpt-5.5",
    "gpt-5.4",
)

ROLE_DEFAULTS = {
    "plan": PLANNER_MODEL,
    "exec": EXECUTION_MODEL,
    "replanner": REPLANNER_MODEL,
}


def resolve_model(value: str | None, role: str, menu: Collection[str] = MODEL_MENU) -> str:
    """Model id for a role: an explicit override iff it is in `menu` (the live
    Copilot list when available, else MODEL_MENU), else the role default. Fail-safe
    — an unknown or empty override never breaks a run; it silently falls back to the
    researched default rather than passing an unroutable id to Copilot."""
    if value and value in menu:
        return value
    return ROLE_DEFAULTS[role]


# Thinking level (reasoning effort) per role. The Copilot SDK exposes a 4-level
# scale — no "minimal"/"off"/"max" — via create_session(reasoning_effort=...) and
# set_model(..., reasoning_effort=...) (verified against github-copilot-sdk source).
# Planner spends (once/task, high leverage); the hot path stays cheap (on a
# manual-thinking model like Haiku the knob is a no-op = non-thinking, which is what
# we want); the rare replanner thinks hardest. NOTE: Copilot may clamp the requested
# level per model — treat it as a hint and assert via the reasoning_tokens meter.
THINKING_LEVELS = ("low", "medium", "high", "xhigh")
PLANNER_EFFORT = "high"
EXECUTION_EFFORT = "low"
REPLANNER_EFFORT = "xhigh"

EFFORT_DEFAULTS = {
    "plan": PLANNER_EFFORT,
    "exec": EXECUTION_EFFORT,
    "replanner": REPLANNER_EFFORT,
}


def resolve_effort(value: str | None, role: str) -> str:
    """Thinking level for a role: an explicit override iff it is a valid Copilot
    level, else the role default. Fail-safe, like resolve_model."""
    if value and value in THINKING_LEVELS:
        return value
    return EFFORT_DEFAULTS[role]


@dataclass(frozen=True)
class LLMResponse:
    model: str
    content: str
    output_tokens: int | None = None  # completion tokens (resp.data.output_tokens), nullable
    usage: dict | None = None  # full ledger from the assistant.usage event, when present


class MockGateway:
    """Test double with the LLMGateway surface (complete/list_models), no Copilot
    auth.

    `responder` maps a prompt to the raw text the model would return, so a test
    can drive the L2 locator fallback (or any LLM seam) deterministically."""

    def __init__(self, responder) -> None:
        self._responder = responder
        self.calls: list[str] = []

    async def list_models(self) -> list[str]:
        return list(MODEL_MENU)

    async def complete(
        self, prompt: str, model: str = EXECUTION_MODEL, reasoning_effort: str | None = None
    ) -> LLMResponse:
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

    async def close(self) -> None:
        return None


class LLMGateway:
    """Lazy-connecting wrapper around a shared Copilot headless server.

    One CLI server backs many sessions; we open a fresh session per call so the
    actor context stays clean (stateless sub-task executor) and per-call model
    selection works.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        *,
        workhorse_model: str = EXECUTION_MODEL,
        replanner_model: str = REPLANNER_MODEL,
        workhorse_effort: str = EXECUTION_EFFORT,
        replanner_effort: str = REPLANNER_EFFORT,
    ) -> None:
        # If COPILOT_HOST/PORT are configured, connect to a separately-run
        # headless server (the DESIGN.md deployment shape) via for_uri. Otherwise
        # use stdio against the SDK's bundled binary, which works out-of-box with
        # `gh` auth and needs no separate server.
        self._host = host or os.getenv("COPILOT_HOST")
        self._port = port or (int(os.getenv("COPILOT_PORT")) if os.getenv("COPILOT_PORT") else None)
        self._client = None
        # Per-role model + thinking-level routing: `complete()` with no explicit
        # model/effort uses the hot-path workhorse; replanner_* is reserved for the
        # rare deep replan. All overridable per /agent/run.
        self.workhorse_model = workhorse_model
        self.replanner_model = replanner_model
        self.workhorse_effort = workhorse_effort
        self.replanner_effort = replanner_effort
        # Running per-gateway token ledger (a fresh gateway is created per /agent/run,
        # so this is the real per-run total surfaced to the frontend).
        self.tokens = {k: 0 for k in _USAGE_KEYS}

    def _accrue(self, resp: Any) -> None:
        usage = getattr(resp, "usage", None)
        if usage:
            for key in self.tokens:
                if usage.get(key):
                    self.tokens[key] += usage[key]
        elif getattr(resp, "output_tokens", None):
            self.tokens["output_tokens"] += resp.output_tokens

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

    async def complete(
        self, prompt: str, model: str | None = None, reasoning_effort: str | None = None
    ) -> LLMResponse:
        model = model or self.workhorse_model
        effort = reasoning_effort or self.workhorse_effort
        client = await self._ensure_client()
        from copilot.session import PermissionHandler

        base = dict(on_permission_request=PermissionHandler.approve_all, model=model)
        try:
            session = (
                await client.create_session(reasoning_effort=effort, **base)
                if effort
                else await client.create_session(**base)
            )
        except Exception:
            # Copilot rejects reasoning_effort for models that don't expose it (e.g.
            # Haiku 4.5 is manual-thinking-only); degrade to the model's default effort
            # rather than fail the run. A real auth/connection error re-raises on retry.
            session = await client.create_session(**base)
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
        result = LLMResponse(
            model=model,
            content=_extract_text(resp),
            output_tokens=_extract_output_tokens(resp),
            usage=usage or None,
        )
        self._accrue(result)
        return result

    async def list_models(self) -> list[str]:
        """Live Copilot model ids — the dropdown's source of truth. Raises if no
        token / SDK is available; `available_models` catches that and falls back to
        MODEL_MENU."""
        client = await self._ensure_client()
        models = await client.list_models()
        return [m.id for m in models]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.stop()
            self._client = None


async def available_models(gateway: LLMGateway) -> list[str]:
    """The active model dropdown: the live Copilot list when a token is configured,
    else the static MODEL_MENU fallback (offline / $0 path). Never raises."""
    try:
        ids = await gateway.list_models()
    except Exception:
        return list(MODEL_MENU)
    return ids or list(MODEL_MENU)


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
