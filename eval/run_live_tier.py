"""Run the live real-world eval tier on demand; write evidence to eval/REPORT.md.

NOT part of the offline CI gate: this hits REAL public sites (flaky, and they
change) and needs Copilot. The 93 offline pytest tests stay network-free and
remain the green gate. Run manually from the repo root:

    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.run_live_tier

It runs the real-world tier AND the day-3 realistic batch (folded in so that
proof is reproducible in-repo), each through the SAME harness path (_run_once,
independent state checks), then writes a dated raw table to eval/REPORT.md.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.agent.models import LLMGateway

from eval.harness import _CountingGateway, _run_once
from eval.loader import EvalTask, load_tasks

LIVE_PATH = Path(__file__).resolve().parent / "eval_set" / "live_real_world.yaml"
REPORT_PATH = Path(__file__).resolve().parent / "REPORT.md"

# Day-3 realistic batch (sandbox), folded in so its proof lives in the repo.
DAY3_BATCH = [
    "internet_form_auth_nav",
    "internet_login_page_reached",
    "books_open_light_in_attic",
    "books_open_travel_category",
    "books_price_visible",
    "quotes_open_einstein_author",
    "quotes_open_login",
    "synonym_label_signin_vs_login",
]


def _is_live(t: EvalTask) -> bool:
    return t.start_url.startswith("http")


def _site(t: EvalTask) -> str:
    return urlparse(t.start_url).netloc if _is_live(t) else "(inline data: URL)"


async def _run(tasks: list[EvalTask]):
    gw = _CountingGateway(LLMGateway())
    rows = []
    try:
        for t in tasks:
            try:
                rec = await _run_once(t, gw, full=True)
                rows.append((t, rec, None))
            except Exception as exc:  # a flaky live site must not abort the batch
                rows.append((t, None, f"{type(exc).__name__}: {exc}"))
    finally:
        await gw.close()
    return rows, gw.calls


def _table(rows) -> str:
    lines = [
        "| task | site | type | deterministic? | nominal | verified | abstained |",
        "|---|---|---|---|---|---|---|",
    ]
    for t, rec, err in rows:
        det = "no (live)" if _is_live(t) else "yes (inline)"
        if err:
            lines.append(f"| {t.id} | {_site(t)} | {t.task_type} | {det} | ERROR | ERROR | - |")
        else:
            lines.append(
                f"| {t.id} | {_site(t)} | {t.task_type} | {det} | "
                f"{rec.nominal} | {rec.verified} | {rec.asked} |"
            )
    return "\n".join(lines)


def _verified(rows) -> int:
    return sum(1 for _, rec, _ in rows if rec and rec.verified)


async def main() -> None:
    live = load_tasks(LIVE_PATH)
    by_id = {t.id: t for t in load_tasks()}
    day3 = [by_id[i] for i in DAY3_BATCH if i in by_id]

    live_rows, c1 = await _run(live)
    day3_rows, c2 = await _run(day3)

    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = f"""# Eval Report — live evidence

Generated **{when}** from a REAL harness run. Every "verified" below is an
INDEPENDENT programmatic state check on the live page (URL / first-h1 / scoped
selector) — never the agent's self-report, and never a loose `text_contains`.
Copilot calls this run: {c1 + c2}.

## Test architecture — what gates vs what's evidence

- **Offline CI gate — 93 pytest tests (`pytest -m "not live"`): NO network, NO
  Copilot, deterministic, must stay green.** No real-site task is in this gate.
- **Sandbox eval set (`eval/eval_set/tasks.yaml`)** — inline-deterministic fixtures
  plus practice-site (toscrape / herokuapp) tasks; run through the harness with Copilot.
- **Live real-world tier (`eval/eval_set/live_real_world.yaml`)** — REAL public sites,
  diverse domains/types. Flaky and changing, so run ON DEMAND
  (`python -m eval.run_live_tier`) and reported here. NOT part of the CI gate; a
  red row here is evidence, not a broken build.

## Live real-world tier — {_verified(live_rows)}/{len(live_rows)} verified

{_table(live_rows)}

## Day-3 realistic batch (folded in, reproducible) — {_verified(day3_rows)}/{len(day3_rows)} verified

{_table(day3_rows)}

## Notes

- **deterministic?** "yes (inline)" rows use a data: URL fixture (no network);
  every other row hits a live site over the network and may vary run-to-run.
- **abstained** = the agent asked the user instead of acting — an honest
  non-completion, never a silent wrong action. Where nominal == verified on a row,
  there was no silent failure on that run.
- The 93 offline pytest tests remain the network-free green gate; this live tier is
  separate and does not gate.

## Honest caveats

- **Real sites bot-wall and change.** A live `verified=False` can be an anti-bot
  interstitial (route-to-unsupported per the project's "route, don't evade" policy),
  not an agent regression. Inspect the final URL to distinguish — a `/sorry/`,
  consent, or CAPTCHA page is a bot-wall. Example observed here:
  `live_google_search_steam` lands on Google's `/sorry/` CAPTCHA: the press/Enter DID
  submit (its `continue=` URL is `/search?q=steam`), but Google blocks headless
  automation, so it never reaches results -> `nominal=True, verified=False`. The
  independent check caught that silently-claimed success — exactly its job.
- **The press/submit action is proven deterministically** by the offline test
  `tests/test_ambiguity_grounding.py::test_press_action_submits_form` (no network, part
  of the 93-green gate); the Google row shows the submit firing on a real site, then a
  bot-wall — not a press failure.
- A live row that abstains (asked=True) is an honest non-completion; only a
  `nominal=True, verified=False` row is a silent failure worth chasing.
"""
    REPORT_PATH.write_text(body, encoding="utf-8")
    print(f"REPORT written: {REPORT_PATH}")
    print(
        f"live tier: {_verified(live_rows)}/{len(live_rows)} verified | "
        f"day-3 batch: {_verified(day3_rows)}/{len(day3_rows)} verified"
    )


if __name__ == "__main__":
    asyncio.run(main())
