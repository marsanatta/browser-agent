"""Phase B runner: score one split through the REAL agent, capture failures + M3 for RCA.

  GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.phase_b --split dev [--tag round0]

Writes research/phase_b_<split>_<tag>.json (per-case rows) and prints a failure-focused
summary (verified-rate, silent-failure count M3, per-failure purpose/outcome). The sealed
split is REFUSED here — it is scored once at the very end via run_live_tier --sealed only.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from app.agent.models import LLMGateway

from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH

ROOT = Path(__file__).resolve().parent.parent


async def run_split(split: str):
    tasks = [t for t in load_tasks(LIVE_PATH) if t.split == split]
    gw = _CountingGateway(LLMGateway())
    rows = []
    try:
        for t in tasks:
            site = urlparse(t.start_url).netloc
            try:
                r = await _run_once(t, gw, full=True)
                rows.append({
                    "id": t.id, "purpose": t.purpose, "site": site, "abstain": t.expect_abstain,
                    "nominal": r.nominal, "verified": r.verified, "asked": r.asked,
                    "blocked": r.blocked, "steps": r.steps, "error": r.error,
                    "silent": bool(r.nominal and not r.verified),
                })
            except Exception as exc:
                rows.append({"id": t.id, "purpose": t.purpose, "site": site,
                             "verified": False, "error": f"{type(exc).__name__}: {exc}", "crash": True})
    finally:
        await gw.close()
    return rows, gw.calls


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "holdout"])
    ap.add_argument("--tag", default="round0")
    args = ap.parse_args()
    if args.split == "sealed":
        raise SystemExit("sealed is scored once at the end via run_live_tier --sealed")

    rows, calls = await run_split(args.split)
    n = len(rows)
    verified = sum(1 for r in rows if r.get("verified"))
    silent = sum(1 for r in rows if r.get("silent"))
    print(f"\n=== {args.split} ({args.tag}): {verified}/{n} verified ({100*verified//n if n else 0}%) | "
          f"M3 silent={silent}/{n} | copilot_calls={calls} ===")
    print("--- FAILURES (verified=False) ---")
    for r in sorted([r for r in rows if not r.get("verified")], key=lambda r: r.get("purpose", "")):
        print(f"  [{r.get('purpose'):20s}] {r['id']:42s} nominal={r.get('nominal')} asked={r.get('asked')} "
              f"blocked={r.get('blocked')} silent={r.get('silent')} err={r.get('error')}")
    out = ROOT / "research" / f"phase_b_{args.split}_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
