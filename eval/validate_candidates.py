"""A4 pass-1 validator: prove a candidate task's ground truth BEFORE it enters the set.

Independent of the agent — for each candidate it drives Playwright directly to the
declared `solution_url` and confirms the `assert` HOLDS there and the path is bot-wall-free
(eval-expansion plan, Phase A4). This guards against the worst failure mode: a wrong
assert that would manufacture a fake "agent failure". An `expect_abstain` candidate is
inverted: it is valid only if a real bot-wall is actually hit.

Candidates JSON = a list of objects:
  {id, start_url, solution_url, assert, expect_abstain?}
`solution_url` is the page where a correct completion lands (assert is checked there).

Run (no Copilot, just a real browser):
  PYTHONPATH=backend python -m eval.validate_candidates path/to/candidates.json
Writes eval/_candidate_validation.json and prints a PASS/FAIL + reason per candidate.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.agent.verify import detect_block
from app.browser.provider import PlaywrightProvider

from eval.verify import state_check

_NAV_TIMEOUT_MS = 25000


async def _goto(page: Any, url: str) -> str | None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


async def _check_one(page: Any, c: dict) -> tuple[str, str, str]:
    cid = c["id"]
    err = await _goto(page, c["start_url"])
    if err:
        return cid, "FAIL", f"start_url unreachable: {err}"
    entry_block = await detect_block(page)

    if c.get("expect_abstain"):
        # An abstain case is valid ONLY if the task is genuinely uncompletable by an
        # unauthenticated agent: a real bot-wall (reason "blocked") OR an auth wall that
        # gates the resource (reason "impossible"). A site that just loads and lets you
        # act is NOT a legitimate abstain.
        if entry_block:
            return cid, "PASS", f"abstain confirmed: bot-wall at entry ({entry_block})"
        # Navigate the gated resource (the thing the task needs), if distinct.
        gated = c.get("solution_url")
        if gated and gated != c["start_url"]:
            await _goto(page, gated)
        if (b := await detect_block(page)):
            return cid, "PASS", f"abstain confirmed: bot-wall ({b})"
        final = (getattr(page, "url", "") or "").lower()
        if any(k in final for k in ("login", "signin", "sign-in", "sign_in", "oauth", "/account/")):
            return cid, "PASS", f"abstain confirmed: auth wall (redirected to {final[:70]})"
        try:
            body = (await page.inner_text("body"))[:6000].lower()
        except Exception:
            body = ""
        if any(p in body for p in (
            "sign in to", "log in to", "please log in", "you must be logged in",
            "sign in required", "log in or sign up", "you need to be logged in",
        )):
            return cid, "PASS", "abstain confirmed: login required (page prompts sign-in)"
        return cid, "FAIL", f"no bot-wall/auth-wall at {final[:70] or c['start_url']} -> not a real abstain"

    sol = c.get("solution_url") or c["start_url"]
    err = await _goto(page, sol)
    if err:
        return cid, "FAIL", f"solution_url unreachable: {err}"
    if (b := await detect_block(page)):
        return cid, "FAIL", f"solution_url is bot-walled ({b}) -> should be expect_abstain"
    if not await state_check(page, c["assert"]):
        return cid, "FAIL", "assert does NOT hold at solution_url (bad ground truth)"
    return cid, "PASS", "assert holds at solution_url; path bot-wall-free"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", help="path to candidates JSON")
    args = ap.parse_args()
    cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))

    prov = PlaywrightProvider(headless=True)
    await prov.launch()
    results: list[tuple[str, str, str]] = []
    try:
        for c in cands:
            page = await prov.new_page()
            try:
                r = await _check_one(page, c)
            except Exception as exc:
                r = (c["id"], "FAIL", f"probe crashed: {type(exc).__name__}: {exc}")
            finally:
                try:
                    await page.close()
                except Exception:
                    pass
            results.append(r)
            print(f"{r[1]:5s} {r[0]}: {r[2]}")
    finally:
        await prov.close()

    npass = sum(1 for _, v, _ in results if v == "PASS")
    print(f"\n{npass}/{len(results)} candidates PASS ground-truth validation")
    out = [{"id": i, "verdict": v, "reason": r} for i, v, r in results]
    Path("eval/_candidate_validation.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
