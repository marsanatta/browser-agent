# Curated Reference List — Task 1 Browser Agent (+ shared eval methodology)

Annotated against the grounding research already in [research/](research/). Each entry is marked:
- **[covered]** — already researched & source-verified in our docs; pointer given. Not re-researched.
- **[NEW]** — not yet covered; queued for / captured in a dedicated research round.

URL note: a few IDs in the source list were truncated; reconstructed arXiv IDs are marked `(reconstructed)` and should be confirmed before external citation.

---

## Libraries

| Resource | Status | Where |
|---|---|---|
| browser-use — MIT NL→browser agent. https://github.com/browser-use/browser-use | **[covered]** | [01](research/01-sota-browser-agents.md) (source-verified: hybrid DOM+AX, 24 actions, ReAct+planner) |
| Playwright — driver, robust locators + auto-wait. https://playwright.dev | **[covered]** | [02](research/02-self-correction-and-healing.md) (semantic locator priority ladder) |
| OmniParser — vision UI parsing. https://github.com/microsoft/OmniParser | **[covered]** | [01](research/01-sota-browser-agents.md), [02](research/02-self-correction-and-healing.md) (SoM, ScreenSpot jump) |
| Healenium — self-healing locators. https://github.com/healenium/healenium | **[covered]** | [02](research/02-self-correction-and-healing.md) (LCS + weighted-attribute fingerprint, score-cap 0.5) |

## Benchmarks / eval

| Resource | Status | Where |
|---|---|---|
| WebArena — functional state-based oracles. https://arxiv.org/abs/2307.13854 | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) (3 evaluator types, 78.24% human) |
| WebVoyager — live-web, VLM judge. https://arxiv.org/abs/2401.13919 | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) (GPT-4V judge 85.3%, κ=0.70; 1-shot drops to 47.7%) |
| Online-Mind2Web / "Illusion of Progress" — silent failure / WebJudge. https://arxiv.org/abs/2504.01382 | **[covered]** | [01](research/01-sota-browser-agents.md), [03](research/03-evaluation-and-failure-detection.md) (51% shortcut agent; WebJudge 85.7%) |
| WebCanvas / Mind2Web-Live — key-node (milestone) scoring. https://arxiv.org/abs/2406.12373 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |
| Mind2Web — cross-task/website/domain OOD splits. https://arxiv.org/abs/2306.06070 | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) (three generalization splits, step-level metrics) |
| GAIA — general assistant tasks. https://arxiv.org/abs/2311.12983 (reconstructed) | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) (exact-match, 3 tiers, 92% human) |
| AssistantBench — abstention-aware scoring. https://arxiv.org/abs/2407.15711 | **[covered]** | [01](research/01-sota-browser-agents.md), [03](research/03-evaluation-and-failure-detection.md) (~25% SOTA, F1 partial credit) |
| ST-WebAgentBench — safety / Completion-under-Policy. https://arxiv.org/abs/2410.06703 | **[covered]** | [02](research/02-self-correction-and-healing.md), [03](research/03-evaluation-and-failure-detection.md) (CuP: verified < 2/3 nominal) |
| REAL — deterministic site replicas. https://arxiv.org/abs/2504.11543 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |
| BrowserGym / AgentLab — eval harness. https://arxiv.org/abs/2412.05467 | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) (unified harness, source table) |

## Architecture / self-correction

| Resource | Status | Where |
|---|---|---|
| AgentOccam — observation/action-space alignment. https://arxiv.org/abs/2410.13825 | **[covered]** | [02](research/02-self-correction-and-healing.md) (WebArena 16.5%→43.1%, no extra LLM calls) |
| ReAct — reason+act loop. https://arxiv.org/abs/2210.03629 | **[covered]** | [01](research/01-sota-browser-agents.md) (dominant OSS control loop) |
| Reflexion — verbal self-correction memory. https://arxiv.org/abs/2303.11366 | **[covered]** | [02](research/02-self-correction-and-healing.md) (+ intrinsic-correction caveat) |
| Voyager — reusable skill library. https://arxiv.org/abs/2305.16291 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |
| Agent Workflow Memory — reusable workflow memory. https://arxiv.org/abs/2409.07429 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |
| LATS — language-agent tree search. https://arxiv.org/abs/2310.04406 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |
| Set-of-Marks — visual grounding prompting. https://arxiv.org/abs/2310.11441 | **[covered]** | [01](research/01-sota-browser-agents.md), [02](research/02-self-correction-and-healing.md) (works sparse, hurts dense) |
| Agent-as-a-Judge — trajectory-level judging. https://arxiv.org/abs/2410.10934 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Autonomous Evaluation & Refinement — auto-eval + reflexion reward. https://arxiv.org/abs/2404.06474 | **[NEW]** | → [07](research/07-memory-search-and-milestone-eval.md) |

## Eval methodology (both tasks)

| Resource | Status | Where |
|---|---|---|
| HF "Agentic Evaluations Workshop" (video transcript, local) | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Anthropic "Demystifying evals for AI agents". https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Inspect AI — eval framework. https://inspect.aisi.org.uk | **[NEW]** | → [06](research/06-eval-methodology.md) |
| tau-bench — simulated-user tool tasks (origin of pass^k). https://arxiv.org/abs/2406.12045 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| tau²-bench — dual-control simulated-user tasks. https://arxiv.org/abs/2506.07982 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| HAL — standardized harness + cost. https://arxiv.org/abs/2510.11977 (reconstructed) | **[NEW]** (leaderboard cost data used in [04](research/04-browser-infra-and-models.md)) | → [06](research/06-eval-methodology.md) |
| Judge-correctness meta-eval. https://arxiv.org/abs/2410.12784 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| PoLL (Panel of LLM judges) — jury voting. https://arxiv.org/abs/2404.18796 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| "Nine Judges, Two Votes" — panels don't fix correlated error. https://arxiv.org/abs/2605.29800 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Self-preference bias — judges favor own outputs. https://arxiv.org/abs/2410.21819 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| "Gaming the Judge" — unfaithful CoT fools judges. https://arxiv.org/abs/2601.14691 | **[covered]** | [03](research/03-evaluation-and-failure-detection.md) |
| "Know Your Limits" (abstention survey). https://arxiv.org/abs/2407.18418 (reconstructed) | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Stated-confidence calibration. https://arxiv.org/abs/2306.13063 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| Semantic-entropy probes — hallucination detection. https://arxiv.org/abs/2406.15927 | **[NEW]** | → [06](research/06-eval-methodology.md) |
| "Adding Error Bars to Evals" (Miller) — statistical rigor. https://arxiv.org/abs/2411.00640 | **[NEW]** | → [06](research/06-eval-methodology.md) |

---

## Summary

- **17 [covered]** — already source-verified across docs 01–05; skipped to save cost.
- **18 [NEW]** — split into two focused rounds:
  - **[06] Eval methodology & judge reliability** (the assignment's "verify correctness without ground truth" axis): judge meta-eval, panels & their correlated-error limits, self-preference bias, abstention/calibration, semantic entropy, statistical error bars, pass^k reliability, Inspect AI / HAL harnesses, Anthropic eval guidance + the workshop transcript.
  - **[07] Agent memory/skills, search, milestone eval**: Voyager, Agent Workflow Memory, LATS, Autonomous Eval & Refinement, plus milestone/deterministic web benchmarks (WebCanvas/Mind2Web-Live key-node, REAL).
