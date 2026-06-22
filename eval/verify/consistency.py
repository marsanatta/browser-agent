"""Consistency check: a Semantic-Entropy-style silent-failure signal.

eval/02 §B3/F4: rather than trust verbalized confidence (which is social
performance, not calibration — eval/02 §B2), run an extraction 2-3x and flag
DISAGREEMENT. High disagreement across independent samples is the practical,
ground-truth-free uncertainty signal for an extraction step. A unanimous answer
is the low-entropy (confident) case; a split is the high-entropy (flag) case.

This is the deployable, testable approximation. The full SEP from hidden states
(arXiv 2406.15927) needs logits the Copilot gateway does not expose, so the
sampling form is what we ship; the hidden-state probe is a SEAM (see seams.py).

`extract_fn` is any async callable returning a comparable value (e.g. the agent's
extracted field). Values are normalized (strip + casefold) before comparison so
trivial formatting differences do not count as disagreement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class ConsistencyResult:
    value: str | None         # the majority answer (None if all samples were empty)
    agreed: bool              # True iff every sample agrees (low entropy)
    agreement: float          # fraction of samples matching the majority, in [0, 1]
    samples: tuple[str, ...]  # the normalized samples, for inspection


def _norm(v: object) -> str:
    return str(v).strip().casefold() if v is not None else ""


async def consistency_check(
    extract_fn: Callable[[], Awaitable[object]], n: int = 3
) -> ConsistencyResult:
    """Run `extract_fn` n times; report the majority answer, whether all samples
    agreed, and the agreement fraction. n>=2; n=3 is the eval/02 §F4 default."""
    if n < 2:
        raise ValueError("consistency_check needs n >= 2 independent samples")
    samples = tuple([_norm(await extract_fn()) for _ in range(n)])
    counts = Counter(samples)
    value, top = counts.most_common(1)[0]
    agreement = top / n
    return ConsistencyResult(
        value=value or None,
        agreed=len(counts) == 1,
        agreement=agreement,
        samples=samples,
    )
