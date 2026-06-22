# Round 1 Synthesis — Grounded Design for the Browser Agent

研究日期: 2026-06-22
Inputs: [01-sota-browser-agents.md](architecture/01-sota-browser-agents.md), [02-self-correction-and-healing.md](architecture/02-self-correction-and-healing.md), [03-evaluation-and-failure-detection.md](evaluation/03-evaluation-and-failure-detection.md)

Three independent research lines (SOTA survey, self-correction/healing, evaluation/silent-failure) **converge on one architecture**. That convergence — not any single source — is the load-bearing finding. This file distills it into concrete design decisions and maps each to the assignment's grading axes.

---

## The convergent architecture (what every source points to)

1. **Keep the LLM out of the hot path.** Deterministic / cached / rule-based execution first; invoke the LLM only on failure. (Stagehand replay, Healwright cache, AgentOccam, zero-cost a11y healing.) This is simultaneously the cost lever and the reliability lever.
2. **Align the observation before acting.** Merge co-labeled elements, render tables/lists as Markdown, replay only pivotal history. AgentOccam got WebArena 16.5%→43.1% from this *alone, with no extra LLM calls* — the cheapest robustness win available.
3. **Hybrid perception, cascading fallback.** DOM + accessibility tree fused into an indexed element list (browser-use, Stagehand, Agent-E all do this despite differing marketing). Screenshot + Set-of-Marks only when DOM grounding is ambiguous, and only with **sparse, precise** boxes (dense/occluding SoM *hurts* — SeeAct 13%). No shipped system offers a documented runtime cascade — a real gap to fill.
4. **Ground the correction signal in observable browser state, never in the LLM's self-assessment.** DOM diff, URL change, network completion, a11y preconditions are independent signals; verbal self-critique (Reflexion-style) is not and does not reliably fix errors.
5. **Verify-after-act is the highest-ROI robustness lever — and almost nobody ships it.** Predict expected effect → act → diff actual vs predicted → re-ground on NO_CHANGE. Skyvern's Validator stage alone = +17pp; Multimodal Auto-Validation 76.2%→81.24% on WebVoyager.
6. **Classify the failure, then respond per-class** (not generic retry): not-found → re-ground/heal; not-interactable (`is_visible/is_enabled` false) → wait/scroll/dismiss overlay; wrong-page (URL check fails) → replan; stale/timing → state-based wait then retry the *same* action.
7. **Semantic-first locator cascade** for self-maintenance: `getByRole`+accessible-name → `getByLabel` → `getByText`+role → `getByTestId` → heuristic fingerprint (LCS + weighted attributes, Healenium-style) → LLM re-rank of a ≤5 shortlist (VON Similo + GPT-4 pattern) → vision fallback. ARIA role+name is the most stable because it is a user-facing contract, not an implementation detail. Avoid CSS/XPath as primary; Playwright `:near()` is deprecated.
8. **Retry only on a new observation; escalate** retry → local strategy-switch → global replan on exhaustion; **confirm before side-effecting (write/submit) retries.**
9. **Measure silent failure explicitly: nominal vs verified completion.** The delta is the headline reliability number (ST-WebAgentBench CuP: avg verified < 2/3 of nominal across 3 SOTA agents → >1/3 of "completed" tasks are silent failures). Overconfidence is large and real: 22% actual success reported as 77% (55pp gap); *pre-execution* adversarial "argue why this fails" calibrates better than post-hoc review.

---

## Proposed agent architecture (grounded, layered)

```
Task (natural language)
        │
   ┌────▼─────┐   Planner (hierarchical): decompose → sub-tasks
   │  PLAN    │   replan trigger = sub-goal fails after N execution attempts
   └────┬─────┘
        │  per sub-task → stateless executor (fresh context, no pollution)
   ┌────▼──────────────────────────────────────────────┐
   │  PERCEIVE  fused DOM+AX → indexed elements         │  observation
   │            + Markdown tables; screenshot/SoM on    │  alignment
   │            demand; cache, don't rebuild every step │  (cheap win)
   ├───────────────────────────────────────────────────┤
   │  LOCATE    semantic cascade → cache hit = 0 LLM    │  self-
   │            tokens; LLM heal only on miss, re-cache │  maintenance
   ├───────────────────────────────────────────────────┤
   │  PREDICT   expected effect (URL/DOM/network)       │
   │  ACT       (batched where safe; confirm writes)    │  self-
   │  VERIFY    diff actual vs predicted                │  correction
   │  CLASSIFY  not-found / not-interactable / wrong-   │
   │            page / stale → per-class recovery       │
   └────┬──────────────────────────────────────────────┘
        │  on exhaustion: local switch → replan → ask_user
   ┌────▼─────┐   Task-level verification (dual-channel):
   │  VERIFY  │   (a) programmatic state assertion where possible
   │  TASK    │   (b) screenshot-grounded judge, scored twice
   └────┬─────┘       (history-only vs +screenshots; gap = fabrication)
        │           Report: nominal vs verified completion + trace
   ┌────▼─────┐   Reflection memory: store failed trajectories,
   │  MEMORY  │   retrieve by similarity to avoid repeats (no retrain)
   └──────────┘
```

**Observability is first-class** (feeds the frontend's failure-inspection requirement): every step logs prompt, model version, chosen locator + cascade level, screenshot, predicted-vs-actual diff, and failure class. A trajectory anomaly trip-wire (SVDD trained on normal traces; needs no labeled failures) flags drift/cycles post-hoc.

---

## Mapping to the assignment's grading axes

| Grading axis (ASSIGNMENT.md) | Grounded mechanism | Source |
|---|---|---|
| **Self-correction (not just try/except)** | Verify-after-act (predict→diff→re-ground) + per-class failure handling + retry-vs-replan escalation | Skyvern Validator +17pp; AgentOccam; UFO2; Multimodal Auto-Validation |
| **Self-maintenance (selector adaptation)** | Semantic locator cascade + fingerprint heal + LLM re-rank + two-layer cache | Playwright/Testing-Library; Healenium; Erratum; VON Similo; Stagehand |
| **Eval-set depth** | Domain × task-type × difficulty tiers; ≥20% held-out unseen sites; block shortcut paths | WebArena; Mind2Web splits; GAIA tiers; Illusion-of-Progress |
| **Silent-failure prevention** | Nominal-vs-verified (CuP); dual-channel verification; pre-exec adversarial check; trajectory anomaly | ST-WebAgentBench; Universal Verifier; Overconfidence paper; IBM 2511.04032 |
| **Cost/latency/scalability analysis** | LLM-out-of-hot-path; cache/replay (0-token hits); batched actions; prune-to-last-N screenshots; tiered models | OSWorld-Human (LLM = 75–94% of latency); Stagehand replay; zero-cost a11y healing |
| **Correctness verification** | Independent ground truth (programmatic state), never self-consistency | WebArena functional validators |

---

## Honest gaps (do NOT block design — recorded for transparency)

- **Intent drift is an open research problem.** A healed locator can click the *wrong* element for the original task with CI green. No framework detects it; only a goal-level verifier (our verify-after-act + CuP check) mitigates. We cannot claim to solve it.
- **Vendor self-healing numbers are unverified** (Functionize 99.97%, Magnitude 94%, MCP heal ~65%) — directional only, no independent benchmark.
- **Commercial internals are closed** (OpenAI/Anthropic training + reward). Any internal description is third-party inference.
- **Some 2025–2026 arXiv IDs are single-source**; load-bearing ones were re-fetched and verified, but specific numbers from single-source recovery papers should not be cited externally without re-check.

---

## Round 2 — Build / Deploy Stack (gap now filled)

Inputs: [04-browser-infra-and-models.md](infrastructure/04-browser-infra-and-models.md), [05-frontend-and-deployment.md](infrastructure/05-frontend-and-deployment.md). Both self-scored 82/100 with unverified items flagged.

**Browser substrate & cost**
- Self-hosted Playwright/Chromium behind a **swappable interface**, with Steel.dev (Apache-2.0, self-host *or* cloud) as the escalation path; reserve Browserbase for the minority needing managed stealth. Self-host vs hosted break-even ≈ 5K–10K tasks/mo.
- **Don't beat anti-bot by evasion.** Route Cloudflare Turnstile / DataDome / PerimeterX-gated sites to a **"needs human auth / unsupported"** outcome. This *is* the honest "what's unsupported" list the assignment asks for.
- **Cost is the LLM loop, not the browser (>10:1).** A 5-min task ≈ $0.008 browser vs $0.04–$5.81 LLM. Tiered models: Haiku/o4-mini triage → Sonnet workhorse → Opus/o3 strictly gated (HAL: o4-mini ≈ $0.043/task Pareto-optimal; **raw Opus ≈ $3.65/task is a cost trap**). Prompt caching (~90% off cached input) + Batch API (50% off) on by default.
- **Never feed raw DOM** (can exceed 1M tokens/page) — a11y-tree-primary bounds per-step token cost, reinforcing the perception decision above.
- Scaling: stateless ephemeral-browser-per-task workers (~300–500 MB each), queue-driven, recycle browsers to bound memory creep.

**Frontend & observability** (serves the "inspectable failure" requirement)
- **Transport: SSE** (`sse-starlette` on FastAPI) for step push; upgrade to WebSocket only if human-in-the-loop pause/resume is added.
- **Event vocabulary: AG-UI protocol** (standard `STEP_STARTED` / `TOOL_CALL_*` / `INTERRUPT`) rather than a bespoke schema.
- **Inspectable failure view** (Skyvern-style), per step: annotated screenshot (element highlighted) · element tree · LLM prompt + raw response + parsed action · chosen locator + cascade level · `failure_category` · retry chain · HAR/trace.
- **Observability: Langfuse self-hosted** (inline screenshot spans via `LangfuseMedia`, agent-graph view) fed by **OTel GenAI spans** — each Playwright action wrapped as a tool span. This is the trajectory store the frontend replays and the anomaly trip-wire consumes.
- **Deploy:** headless Chromium needs a real container — `mcr.microsoft.com/playwright` base, `--disable-dev-shm-usage`, non-root, `tini`; Fly.io `performance-2x` (4 GB) or equivalent. Static React frontend on Vercel/Cloudflare Pages. (Zeabur+Chromium specifics UNVERIFIED — test before committing.)
- **Security (matches `.claude/CLAUDE.md`): redact at serialization**, not post-hoc — strip `sk-*`/Bearer/`api_key=`/`Authorization`/`Cookie` before any byte reaches a span, SSE `data:`, or replay file; screenshots behind signed URLs, not base64 in the stream; `recordHar({ omitContent: true })`.

**New unverified items (flagged, non-blocking):** Fly.io SSE idle-timeout behavior; Zeabur Chromium support; at-scale hosted browser-hour cost (arithmetic discrepancy between sources); 2026 model $/task needs in-house measurement on our own task distribution; AG-UI has no standard screenshot event type.

---

## Round 3 — Eval Methodology & Memory/Search Adopt-Skip (rigor layer)

Inputs: [06-eval-methodology.md](evaluation/06-eval-methodology.md), [07-memory-search-and-milestone-eval.md](architecture/07-memory-search-and-milestone-eval.md). Self-scored 82 / 78.

**Eval methodology — how to verify correctness without trustworthy ground truth** (the assignment's hardest axis)
- **Hard verifiers first, LLM judges last.** Use deterministic post-state checks (DOM/URL/API/extracted field) wherever inspectable; reserve LLM judges for text-only quality. Not needing a judge eliminates the worst judge failure modes outright.
- **If a judge is unavoidable:** different model family from the agent (GPT-4 shows significant self-preference bias), explicit **"Unknown" escape hatch**, one dimension per call, recalibrate monthly vs human labels.
- **Panels don't fix correlated error** — 9 judges ≈ 2 independent votes; best single judge ≈ full panel. Spend extra judges on *independent axes*, not redundant votes.
- **Report pass^k (k≥3), not pass@1.** One wrong execution in k tries is product-fatal for bookings/orders/form submits. pass^k is the production-readiness signal.
- **Silent-failure layer = three stacked signals:** Semantic Entropy Probes on extraction steps + repeat-and-compare consistency sampling + independent post-action state verification. **Never** accept verbalized confidence as the success signal (LLMs are systematically overconfident).
- **Statistical rigor:** target n≈1,000 eval items, report SE/CI (clustered SE when tasks share a site); measure **calibration and discrimination separately**.
- **Harness: Inspect AI**, each run in a clean isolated sandbox (shared state → correlated failures indistinguishable from real ones).
- **Eval-driven development:** start from 20–50 *real* failure cases with two-reviewer agreement on pass/fail; saturation means the set needs harder tasks.

**Memory / search / milestone — opinionated adopt-skip**
- **SKIP Voyager code-skill libraries** — wrong substrate (DOM selectors are unstable; code skills break silently); no web benchmark evidence.
- **SKIP LATS / MCTS tree search** — ~17× token multiplier and needs transaction-safe state reversion browsers don't provide. **Linear retry-with-reflection** gives +29% on WebArena at ~3× cost — strictly better for a cost-bounded web agent.
- **ADOPT (cautiously) AWM offline workflow induction** — induct reusable workflows *offline from a curated good-trajectory corpus only*, never online (failed trajectories poison the library).
- **ADOPT auto-evaluator (2404.06474) as a training-data filter, not a live pass/fail gate** (too noisy: ~30% error on ambiguous tasks).
- **ADOPT WebCanvas key-node (TCR/TSR) scoring for our eval set** — binary success hides real partial progress (23.1% TSR vs 48.8% TCR gap); key-node scoring localizes where a task stalls.
- **ADOPT REAL (2504.11543) as the primary offline eval harness** — 12 deterministic clones of mainstream sites, state-diff evaluation (no judge noise), reproducible and safe vs live-web.
- **Non-negotiable ablation rule:** always report total token usage **and** a budget-matched vanilla-actor baseline. Any "memory/skill improves performance" claim is incomplete without it (a budget-matched vanilla actor beat AWM by 5.76pp using 29% fewer tokens — arXiv 2606.15017).

**New flagged gaps (non-blocking):** offline-AWM vs budget-matched baseline untested; per-task key-node annotation cost unquantified; LATS at low branching with Playwright `storageState` unresearched; pass^k exact formula and abstention coverage/accuracy numbers abstract-only.

---

## Final convergence verdict

**Design-readiness: ~92/100. Research loop converged across 3 rounds (8 docs) — sufficient to design a high-quality agent that targets every grading axis. Not claiming 100, and it is not reachable** (closed commercial internals, intent-drift is an open research problem, and several $/task and abstention figures require in-house measurement — none of which block design).

All six grading axes now have grounded, sourced, implementable mechanisms (table above) **plus** a grounded build/deploy/frontend/security stack **and** a rigorous eval methodology (hard-verifier-first, pass^k, SEP+consistency+state-verify, Inspect AI + REAL harness, budget-matched baselines). The remaining unknowns are either fundamentally unanswerable from public sources or are measurements we can only take by building. Continuing to research would be loop-for-its-own-sake. **Recommendation: stop research, move to an architecture/implementation plan.**
