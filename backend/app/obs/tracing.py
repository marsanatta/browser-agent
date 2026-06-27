"""Redaction + observability wiring.

Redaction is the security gate: secrets/PII MUST be masked here BEFORE any data
reaches an OTel span, an SSE `data:` field, a log line, or a stored trace.
Langfuse and OTel have no built-in redaction, so `redact()` is applied at the
serialization boundary, never post-hoc.
"""

from __future__ import annotations

import os
import re
from typing import Any

_MASK = "[REDACTED]"

_REDACTORS: tuple[tuple[re.Pattern[str], str], ...] = (
    # PEM private-key blocks (multiline). Strip the whole block.
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        _MASK,
    ),
    # Authorization / Cookie / Set-Cookie / Proxy-Authorization header lines.
    # Keep the header name; mask the value. Matches "Header: value" and "Header=value".
    (
        re.compile(
            r"(?im)^(\s*(?:authorization|proxy-authorization|cookie|set-cookie)\s*[:=]\s*).+$"
        ),
        r"\1" + _MASK,
    ),
    # Secret-named params as JSON-quoted values: "api_key":"...". Mask the value,
    # keep the quotes so JSON stays well-formed.
    (
        re.compile(
            r'(?i)(["\']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|'
            r'password|passwd|credential|token|jwt)["\']?\s*:\s*)"[^"]*"'
        ),
        r'\1"' + _MASK + '"',
    ),
    # Secret-named params as key=value query/form pairs.
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|"
            r"password|token|jwt)(=)[^\s&\"']+"
        ),
        r"\1\2" + _MASK,
    ),
    # Bearer tokens appearing inline (not necessarily on a header line).
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+/=]+"), "Bearer " + _MASK),
    # Value-shape patterns — masked regardless of surrounding key.
    # JWT (header.payload.signature).
    (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), _MASK),
    # AWS access key id.
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), _MASK),
    # Slack tokens.
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]+"), _MASK),
    # Google API key.
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), _MASK),
    # OpenAI-style secret keys: sk-, sk-proj-, sk-ant-, etc.
    (re.compile(r"\bsk-[A-Za-z0-9._\-]{8,}"), _MASK),
    # GitHub tokens: classic (ghp_/gho_/ghu_/ghs_/ghr_) and fine-grained (github_pat_).
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), _MASK),
    (re.compile(r"\bgh[opusr]_[A-Za-z0-9]{16,}"), _MASK),
    # Email addresses (PII).
    (
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        _MASK,
    ),
)

_REDACT_KEYS = re.compile(
    r"(?i)(authorization|cookie|set-cookie|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|token|secret|password|passwd|credential|session)"
)

# These ledger keys collide with the "token" secret heuristic but hold integer
# usage counts, never secrets. Exempt them so the per-run token meter survives
# serialization — without this the whole `tokens` dict (and its *_tokens members)
# masks to "[REDACTED]" and the UI shows no usage.
_USAGE_LEDGER_KEYS = frozenset(
    {"tokens", "output_tokens", "input_tokens", "reasoning_tokens"}
)


def redact(value: Any) -> Any:
    """Recursively mask secrets/PII in strings, dicts, and lists.

    Applied at every serialization boundary before data leaves the process.
    Dict keys whose name signals a secret have their entire value masked,
    independent of value-pattern matching, to catch opaque tokens.
    """
    if isinstance(value, str):
        return _redact_str(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return _redact_str(bytes(value).decode("utf-8", errors="replace"))
        except Exception:
            return _MASK
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for k, v in value.items():
            if (
                isinstance(k, str)
                and _REDACT_KEYS.search(k)
                and k.lower() not in _USAGE_LEDGER_KEYS
            ):
                out[k] = _MASK
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, (list, tuple)):
        return type(value)(redact(v) for v in value)
    return value


def _redact_str(text: str) -> str:
    for pattern, repl in _REDACTORS:
        text = pattern.sub(repl, text)
    return text


_initialized = False


def init_observability() -> None:
    """Lazy, side-effect-light OTel/Langfuse wiring skeleton.

    Real exporters are configured from env (OTEL_EXPORTER_OTLP_ENDPOINT,
    LANGFUSE_*). M0 only proves the seam exists; no exporter is required to
    boot. Redaction must run before any span/media is emitted here.
    """
    global _initialized
    if _initialized:
        return
    # setup: wire OpenTelemetry TracerProvider + Langfuse client from env here.
    # Both must serialize span attributes through `redact()` before export.
    _ = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    _ = os.getenv("LANGFUSE_HOST")
    _initialized = True
