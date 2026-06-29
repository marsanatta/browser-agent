"""pass^k runner for the hard-case probe set — PROCESS-ISOLATED.

Each run executes in its OWN subprocess (`python -m eval.run_one --only <id>`), exactly like
production (`/agent/run` = one task per request) and `run_one.py`. This is deliberate: running
many agentic sessions in ONE process/event-loop intermittently drops the Copilot session
("JSON-RPC -32603 ... Session not found") — the SDK's cross-thread tool-bridge + client +
Playwright recycled in one loop. One run per process eliminates it (verified: own-process runs
pass clean where the in-process batch fails). harness.py / the engine are UNTOUCHED.

    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.passk_live --k 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys

NEW_IDS = [
    "live_todomvc_add_complete_filter",
    "live_uitap_disabled_input_enable",
    "live_uitap_ajax_wait",
    "live_internet_dynamic_controls_remove",
    "live_internet_add_remove_elements",
]


def _reap_stray_copilot() -> None:
    """Best-effort: kill any lingering copilot CLI between runs so an orphan can't collide with
    the next run's fresh session. Eval-only."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "copilot.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "copilot/bin/copilot"], capture_output=True)
    except Exception:
        pass


async def _run_one_subprocess(case_id: str) -> dict:
    """Run ONE case in a fresh subprocess (env/cwd inherited). Returns the parsed RESULT dict."""
    _reap_stray_copilot()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "eval.run_one", "--only", case_id,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    rec: dict | None = None
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("RESULT "):
            try:
                rec = json.loads(line[len("RESULT "):])
            except Exception:
                rec = None
    return rec or {"id": case_id, "error": "no RESULT line", "nominal": None, "verified": False}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--only", default=None, help="comma-sep subset of ids")
    args = ap.parse_args()

    ids = args.only.split(",") if args.only else NEW_IDS
    rows = []
    for cid in ids:
        runs = []
        for _ in range(args.k):
            rec = await _run_one_subprocess(cid)
            runs.append(rec)
            v = "Y" if rec.get("verified") else ("ERR" if rec.get("error") else "N")
            print(f"  {cid} run: verified={v} nominal={rec.get('nominal')} "
                  f"calls={rec.get('calls')} err={rec.get('error')}", flush=True)
        nver = sum(1 for r in runs if r.get("verified"))
        nnom = sum(1 for r in runs if r.get("nominal"))
        fs = sum(1 for r in runs if r.get("nominal") and not r.get("verified"))
        calls = sum((r.get("calls") or 0) for r in runs) / max(len(runs), 1)
        purpose = next((r.get("purpose") for r in runs if r.get("purpose")), "")
        rows.append((cid, len(runs), nver, nnom, fs, calls, purpose))
        print(f"{cid}: verified {nver}/{len(runs)} | nominal {nnom}/{len(runs)} | "
              f"silent-fail {fs} | avg_calls {calls:.1f}  [{purpose}]", flush=True)

    print(f"\n=== pass^k summary (k={args.k}) ===")
    print("| task | purpose | verified^k | nominal | silent-fail | avg calls |")
    print("|---|---|---|---|---|---|")
    passk = 0
    for cid, n, nver, nnom, fs, calls, purpose in rows:
        ok = "PASS^k" if (nver == n and n > 0) else f"{nver}/{n}"
        if nver == n and n > 0:
            passk += 1
        print(f"| {cid} | {purpose} | {ok} | {nnom}/{n} | {fs} | {calls:.1f} |")
    print(f"\npass^{args.k}: {passk}/{len(rows)} tasks | "
          f"total silent-failures: {sum(r[4] for r in rows)}")


if __name__ == "__main__":
    asyncio.run(main())
