"""pass^k runner for the hard-case probe set (live sites). External k-loop over the
SAME harness._run_once — harness.py / scoring untouched. Reports, per task: how many
of k runs verified (independent state check), nominal-vs-verified delta (silent
failure), and avg Copilot calls.

    GH_TOKEN=$(gh auth token) PYTHONPATH=backend python -m eval.passk_live --k 3
"""
from __future__ import annotations

import argparse
import asyncio

from app.agent.models import LLMGateway

from eval.harness import _CountingGateway, _run_once
from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH

NEW_IDS = [
    "live_checkboxes_both_checked",
    "live_todomvc_add_complete_filter",
    "live_uitap_disabled_input_enable",
    "live_uitap_ajax_wait",
    "live_internet_dynamic_controls_remove",
    "live_selectorshub_shadow_input",
    "live_internet_add_remove_elements",
    "live_internet_tables_sort_lastname",
    "live_internet_shifting_menu_gallery",
]


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--only", default=None, help="comma-sep subset of ids")
    args = ap.parse_args()

    by_id = {t.id: t for t in load_tasks(str(LIVE_PATH))}
    ids = args.only.split(",") if args.only else NEW_IDS
    tasks = [by_id[i] for i in ids if i in by_id]
    missing = [i for i in ids if i not in by_id]
    if missing:
        print(f"WARN missing ids: {missing}")

    gw = _CountingGateway(LLMGateway())
    rows = []
    try:
        for t in tasks:
            runs = []
            for _ in range(args.k):
                try:
                    runs.append(await _run_once(t, gw, full=True))
                except Exception as exc:
                    print(f"  {t.id}: run error {type(exc).__name__}: {exc}")
            nver = sum(1 for r in runs if r.verified)
            nnom = sum(1 for r in runs if r.nominal)
            false_succ = sum(1 for r in runs if r.nominal and not r.verified)
            calls = sum(r.copilot_calls for r in runs) / max(len(runs), 1)
            rows.append((t, len(runs), nver, nnom, false_succ, calls))
            print(f"  {t.id}: verified {nver}/{len(runs)} | nominal {nnom}/{len(runs)} | "
                  f"silent-fail {false_succ} | avg_calls {calls:.1f}  [{t.purpose}]")
    finally:
        await gw.close()

    print("\n=== pass^k summary (k={}) ===".format(args.k))
    print("| task | purpose | verified^k | nominal | silent-fail | avg calls |")
    print("|---|---|---|---|---|---|")
    passk = 0
    for t, n, nver, nnom, fs, calls in rows:
        ok = "PASS^k" if nver == n and n > 0 else f"{nver}/{n}"
        if nver == n and n > 0:
            passk += 1
        print(f"| {t.id} | {t.purpose} | {ok} | {nnom}/{n} | {fs} | {calls:.1f} |")
    total_fs = sum(r[4] for r in rows)
    print(f"\npass^{args.k}: {passk}/{len(rows)} tasks | total silent-failures: {total_fs} | "
          f"Copilot calls: {gw.calls}")


if __name__ == "__main__":
    asyncio.run(main())
