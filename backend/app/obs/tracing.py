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
    # Authorization / Cookie / Set-Cookie / Proxy-Authorization header lines.
    # Keep the header name; mask the value. Matches "Header: value" and "Header=value".
    (
        re.compile(
            r"(?im)^(\s*(?:authorization|proxy-authorization|cookie|set-cookie)\s*[:=]\s*).+$"
        ),
        r"\1" + _MASK,
    ),
    # Bearer tokens appearing inline (not necessarily on a header line).
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+/=]+"), "Bearer " + _MASK),
    # OpenAI-style secret keys: sk-, sk-proj-, sk-ant-, etc.
    (re.compile(r"\bsk-[A-Za-z0-9._\-]{8,}"), _MASK),
    # GitHub tokens (gho_, ghp_, ghu_, ghs_, ghr_) + Copilot token env style.
    (re.compile(r"\bgh[opusr]_[A-Za-z0-9]{16,}"), _MASK),
    # api_key=... / apikey=... / access_token=... / token=... query/form params.
    (
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|token)(=)[^\s&\"']+"),
        r"\1\2" + _MASK,
    ),
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


def redact(value: Any) -> Any:
    """Recursively mask secrets/PII in strings, dicts, and lists.

    Applied at every serialization boundary before data leaves the process.
    Dict keys whose name signals a secret have their entire value masked,
    independent of value-pattern matching, to catch opaque tokens.
    """
    if isinstance(value, str):
        return _redact_str(value)
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and _REDACT_KEYS.search(k):
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
