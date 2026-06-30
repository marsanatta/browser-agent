"""Parallel, process-isolated eval runner — runs many cases concurrently.

Each (task, repetition) is one `eval.run_one` SUBPROCESS (process isolation is what keeps
the Copilot session from dropping; running many agentic sessions in one process is the
failure mode). Concurrency is bounded by an asyncio.Semaphore over those subprocesses, NOT
multiprocessing: the CPU work lives inside each child process, so the parent only needs to
launch N children at once and collect — an I/O-bound orchestration that asyncio fits.

Tuned default jobs=8: enso's historically-validated Copilot batch concurrency is 6 (it ramps
to 8-10); locally N=6 and N=12 process-isolated runs were both clean (no 429 / -32603 /
session-drop), well under the ~100-concurrency 429 threshold (copilot-sdk issue #299).

  GH_TOKEN=$(gh auth token) PYTHONPATH=backend python research/run_eval_parallel.py \
      --file eval/eval_set/live_real_world.yaml --jobs 8 --k 1

k=1  -> population: per-split TSR (verified) + silent-failure (CuP) + SE.
k>1  -> robustness: per-task pass^k (all k must verify) + false-success + bootstrap-CI.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.loader import load_tasks
from eval.run_live_tier import LIVE_PATH


def _reap_once() -> None:
    """Kill stray copilot/headless browsers ONCE before launching. NOT per-task: a per-task
    reap would kill the copilot of sibling subprocesses still running concurrently."""
    procs = (["copilot.exe", "chrome.exe", "headless_shell.exe"] if sys.platform == "win32"
             else ["copilot"])
    for p in procs:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", p], capture_output=True)
        except Exception:
            pass


async def _run_unit(file: str, case_id: str, rep: int, sem: asyncio.Semaphore) -> dict:
    async with sem:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "eval.run_one", "--file", file, "--only", case_id,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
    rec = {"id": case_id, "rep": rep, "error": "no RESULT line",
           "nominal": None, "verified": False, "asked": False, "blocked": False}
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("RESULT "):
            try:
                rec = {**json.loads(line[len("RESULT "):]), "rep": rep}
            except Exception:
                pass
    return rec


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion. Unlike a bootstrap of the mean,
    this does NOT collapse to a point when k==n (all successes) — at the boundary a bootstrap
    reports a misleading [1,1], hiding the real small-n uncertainty. Closed-form, resume-safe."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, center - half), min(1.0, center + half))


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(LIVE_PATH))
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--k", type=int, default=1, help="repetitions per task (pass^k when >1)")
    ap.add_argument("--ids", default="", help="comma-separated task ids (default: all)")
    ap.add_argument("--out", default=os.path.join("research", "parallel_results.jsonl"))
    args = ap.parse_args()

    tasks = load_tasks(args.file)
    if args.ids:
        keep = set(args.ids.split(","))
        tasks = [t for t in tasks if t.id in keep]

    done: dict[tuple[str, int], dict] = {}
    if os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            try:
                d = json.loads(line)
                done[(d["id"], d.get("rep", 0))] = d
            except Exception:
                pass

    units = [(t.id, rep) for t in tasks for rep in range(args.k) if (t.id, rep) not in done]
    print(f"tasks={len(tasks)} k={args.k} units={len(units)} cached={len(done)} "
          f"jobs={args.jobs} model=default(opus-4.8)", flush=True)

    _reap_once()
    sem = asyncio.Semaphore(args.jobs)
    f = open(args.out, "a", encoding="utf-8")
    lock = asyncio.Lock()
    completed = 0

    async def worker(cid: str, rep: int) -> None:
        nonlocal completed
        r = await _run_unit(args.file, cid, rep, sem)
        async with lock:
            f.write(json.dumps(r) + "\n"); f.flush()
            completed += 1
            print(f"[{completed}/{len(units)}] {cid} rep={rep} "
                  f"verified={r.get('verified')} nominal={r.get('nominal')} err={r.get('error')}",
                  flush=True)

    await asyncio.gather(*(worker(cid, rep) for cid, rep in units))
    f.close()

    by_id: dict[str, list[dict]] = defaultdict(list)
    for (cid, _rep), d in done.items():
        by_id[cid].append(d)
    for line in open(args.out, encoding="utf-8"):
        try:
            d = json.loads(line)
            if (d["id"], d.get("rep", 0)) in {(c, r) for c, r in units}:
                by_id[d["id"]].append(d)
        except Exception:
            pass

    split_of = {t.id: t.split for t in tasks}
    if args.k == 1:
        per = defaultdict(list)
        for cid, runs in by_id.items():
            per[split_of[cid]].append(runs[0])
        print("\n| Split | Tasks | Verified | SE | Silent failures |", flush=True)
        print("|---|---|---|---|---|", flush=True)
        tv = tn = tsf = 0
        for split in ("dev", "holdout", "sealed"):
            rs = per.get(split, [])
            if not rs:
                continue
            n = len(rs)
            v = sum(1 for r in rs if r.get("verified"))
            sf = sum(1 for r in rs if r.get("nominal") and not r.get("verified"))
            se = math.sqrt((v / n) * (1 - v / n) / n) if n else 0.0
            tv += v; tn += n; tsf += sf
            print(f"| {split} | {n} | {v/n:.3f} ({v}/{n}) | ±{se:.3f} | {sf} |", flush=True)
        se = math.sqrt((tv / tn) * (1 - tv / tn) / tn) if tn else 0.0
        print(f"| **Total** | **{tn}** | **{tv/tn:.3f} ({tv}/{tn})** | **±{se:.3f}** | **{tsf}** |", flush=True)
        print(f"\nMETRICS-DONE verified={tv}/{tn} silent_failures={tsf}", flush=True)
    else:
        passk_vals, fs_tasks, fs_runs, tot_runs = [], 0, 0, 0
        print(f"\n=== pass^k (k={args.k}) per task ===", flush=True)
        for cid in sorted(by_id):
            runs = by_id[cid]
            allv = all(r.get("verified") for r in runs)
            anyfs = any(r.get("nominal") and not r.get("verified") for r in runs)
            passk_vals.append(1.0 if allv else 0.0)
            fs_tasks += anyfs
            fs_runs += sum(1 for r in runs if r.get("nominal") and not r.get("verified"))
            tot_runs += len(runs)
            print(f"  {cid}: verified={sum(1 for r in runs if r.get('verified'))}/{len(runs)} "
                  f"passk={allv} false_success={anyfs}", flush=True)
        n = len(passk_vals)
        kpass = sum(int(v) for v in passk_vals)
        mean = kpass / n if n else 0.0
        lo, hi = _wilson_ci(kpass, n)
        print(f"\npass^k = {mean:.3f} ({kpass}/{n})  95% CI (Wilson) [{lo:.3f}, {hi:.3f}]", flush=True)
        print(f"false-success tasks = {fs_tasks}/{n}  runs = {fs_runs}/{tot_runs}", flush=True)
        print(f"\nPASSK-DONE passk={mean:.3f} false_success_tasks={fs_tasks}/{n}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
