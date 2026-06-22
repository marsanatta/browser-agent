"""Per-step screenshot capture + local static serving.

DESIGN §8: the inspectable-failure view needs an annotated screenshot per step
(highlighted element). DESIGN explicitly prefers a SERVED URL over base64 on the
SSE hot path, so this writes PNG bytes to a git-ignored directory and the SSE
event carries only an opaque `/screenshots/<id>.png` reference plus the element's
bounding box (CSS pixels). Image bytes never touch the SSE `data:` field.

Captured page pixels can contain logged-in PII, so the directory is treated as a
secret and git-ignored (.gitignore: `screenshots/`).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from app.stream.events import HighlightBox, ScreenshotAnnotated

_STORE_DIR = Path(__file__).resolve().parents[2] / "screenshots"
ROUTE_PREFIX = "/screenshots"


def store_dir() -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORE_DIR


async def capture_step(
    page: Any, step_id: str, locator: Any = None, caption: str | None = None
) -> ScreenshotAnnotated | None:
    """Screenshot the current page and, when a locator is given, compute the
    acted-on element's bounding box for the highlight overlay. Returns None on
    any capture failure — observability must never break the agent loop."""
    try:
        png = await page.screenshot()
    except Exception:
        return None

    out_dir = store_dir()
    shot_id = uuid.uuid4().hex[:12]
    (out_dir / f"{shot_id}.png").write_bytes(png)
    ref = f"{ROUTE_PREFIX}/{shot_id}.png"

    box = await _highlight(locator)
    return ScreenshotAnnotated(
        step_id=step_id, screenshot_ref=ref, highlight=box, caption=caption
    )


async def _highlight(locator: Any) -> HighlightBox:
    if locator is None:
        return HighlightBox(0, 0, 0, 0)
    try:
        bb = await locator.bounding_box()
    except Exception:
        bb = None
    if not bb:
        return HighlightBox(0, 0, 0, 0)
    return HighlightBox(
        x=bb["x"], y=bb["y"], width=bb["width"], height=bb["height"]
    )
