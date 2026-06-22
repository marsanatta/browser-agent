# Browser/Web Agent Evaluation & Silent-Failure Detection

**研究日期:** 2026-06-22  
**來源數量:** 20+ primary sources (arXiv papers, benchmark sites, leaderboards)  
**信心程度:** 78/100 — benchmark numbers from SOTA leaderboards carry uncertainty as leaderboards update continuously; numbers flagged where extrapolated

---

## TL;DR

Web agent benchmarks have matured from synthetic toy tasks (MiniWoB++) to realistic multi-step web environments (WebArena, VisualWebArena). The core tension in evaluation is between **programmatic correctness** (reliable but narrow) and **LLM-as-judge** (flexible but unreliable, with false-positive rates up to 22–45% in naive implementations). Silent failures — where an agent reports success but the underlying state is wrong — are a documented, quantified problem. The best verification approach combines programmatic state checks, screenshot-grounded visual verification, and trajectory anomaly detection, rather than trusting agent self-reports.

---

## 1. Benchmark Comparison Table

| Benchmark | Year | Tasks | Domains | Success Detection | Human Perf | Baseline (initial LLM) | SOTA (as of early 2026) |
|-----------|------|-------|---------|-------------------|------------|------------------------|--------------------------|
| **MiniWoB++** | 2018 | ~80–100 | Synthetic web forms, buttons, dialogs | Programmatic DOM-state check | ~100% | ~38% (SL) | ~99.2% (SYNAPSE w/ demos, 64 tasks) |
| **Mind2Web** | NeurIPS 2023 | 2,350 | 137 real websites, 31 domains, 12 high-level categories | Element Accuracy + Operation F1 (step-level) | N/A (annotation) | ~50.9% element acc | ~53% element acc (process reward model) |
| **WebArena** | ICLR 2024 | 812 | E-commerce, forums (Reddit-like), GitLab, CMS + utilities | Programmatic functional-correctness validators + GPT-4 fuzzy_match | 78.24% | 14.41% (GPT-4 + CoT) | ~71.6% (OpAgent, Jan 2026) |
| **VisualWebArena** | ACL 2024 | 910 | Classifieds, Shopping, Reddit (visual tasks) | Execution-based tests (programmatic), visually grounded metrics | 88.70% | 15.05% (GPT-4V) | ~19.78% (GPT-4o, at paper release) |
| **WebVoyager** | ACL 2024 | 643 | 15 popular real websites | GPT-4V LLM-as-judge (85.3% human agreement, Cohen's κ=0.70) | N/A | 59.1% (WebVoyager agent) | ~61% (OpenAI Operator, cited 2025) |
| **GAIA** | 2023 | 466 (300 held-out) | General reasoning + web browsing + tools | Exact answer string match | 92% | 15% (GPT-4 + plugins) | ~65% [UNVERIFIED — from secondary source] |
| **AssistantBench** | EMNLP 2024 | 214 | 258 real websites, broad domains | F1 token overlap with gold answer | N/A | ~23.4% (SeeAct) | ~25.2% (SPA agent) |
| **ST-WebAgentBench** | 2024 | Multiple safety scenarios | Web + safety/trustworthiness | Task completion + safety refusal scoring, CuP metric | N/A | Not published | Not published |

**Sources:**
- WebArena: https://arxiv.org/abs/2307.13854 ; leaderboard data from https://leaderboard.steel.dev/registry/benchmarks/webarena/
- VisualWebArena: https://jykoh.com/vwa ; https://arxiv.org/abs/2401.13649
- WebVoyager: https://arxiv.org/abs/2401.13919
- Mind2Web: https://arxiv.org/abs/2306.06070
- GAIA: https://arxiv.org/abs/2311.12983
- AssistantBench: https://arxiv.org/abs/2407.15711
- ST-WebAgentBench: https://arxiv.org/abs/2410.06703
- MiniWoB++ SYNAPSE: https://openreview.net/pdf?id=pI6ylnkPAD

---

## 2. Benchmark Deep Dives

### 2.1 WebArena (ICLR 2024 Oral)

**Paper:** https://arxiv.org/abs/2307.13854

**Design:**
- 812 tasks from 241 templates across 4 website domains
- Self-hosted sandbox: agents interact with real web UIs (not screenshots only)
- Tasks are long-horizon (multi-step): "Buy the cheapest laptop on OneStopShop within $500"

**Success Detection:**
Programmatic "functional correctness" validators — not surface-form action matching. Three evaluator types:
1. `exact_match` — answer string must match exactly
2. `must_include` — answer must contain required substrings
3. `fuzzy_match` — GPT-4 (gpt-4-0613 / gpt-4-1106-preview) judges semantic equivalence; achieved 100% accuracy on 1,800 date/time format test cases

For navigation/config tasks: custom locators query the web app's database or DOM to verify the resulting state (e.g., "was this item actually added to the cart?").

**Why programmatic matters:** Checks the *resulting web state*, not the agent's claimed output. An agent cannot pass by lying.

**Numbers:**
- Human: 78.24%
- GPT-4 initial baseline: 14.41%
- SOTA ~2025–2026: ~71.6% (OpAgent, Jan 2026); OpenAI Operator ~58–61%; Claude Opus 4 ~55%

---

### 2.2 VisualWebArena (ACL 2024)

**Paper:** https://arxiv.org/abs/2401.13649 ; Project: https://jykoh.com/vwa

**Design:**
- 910 tasks across Classifieds (newly created), Shopping, Reddit
- Tasks *require visual understanding*: spatial reasoning, image matching, OCR

**Success Detection:**
Execution-based tests with visually grounded metrics. Programmatic, not LLM-judged. Concrete examples: "find a product whose image matches this reference image" — the evaluator runs image similarity checks.

**Numbers:**
- Human: 88.70%
- GPT-4 (text-only): 7.25%
- GPT-4V: 15.05%
- GPT-4o: 19.78% (highest at paper release, 2024)

**Key gap:** Visual tasks remain dramatically harder; 19.78% vs 88.70% human shows large room.

---

### 2.3 WebVoyager (ACL 2024)

**Paper:** https://arxiv.org/abs/2401.13919

**Design:**
- 643 tasks, 15 real websites (Amazon, GitHub, Google Flights, ESPN, etc.)
- Live internet — not sandboxed; tasks run against production sites
- Tests complete end-to-end web navigation

**Success Detection: GPT-4V as Judge**
- GPT-4V receives: task instruction + agent's final response + screenshot trajectory
- Renders binary success/failure judgment
- **Agreement with human: 85.3%**, Cohen's κ = 0.70
- Limitation: with only 1 screenshot, agreement drops to 47.7% — full trajectory needed

**Known Reliability Issues:**
1. Agent hallucinations in final responses produce false positives (high false-positive rate)
2. "An Illusion of Progress?" (arXiv 2504.01382) found WebVoyager evaluation has **low agreement with human judgment** primarily due to hallucination-induced false positives
3. WebJudge (o4-mini) achieves 85.7% human-agreement vs WebVoyager's 78.7% on the same tasks
4. A simple Google-Search-shortcut agent achieves 51% on WebVoyager tasks — exposing shallow task design

**Agent Performance:**
- WebVoyager agent itself: 59.1%
- OpenAI Operator (2025): ~61%

**Source:** https://arxiv.org/html/2504.01382v4

---

### 2.4 Mind2Web (NeurIPS 2023 Spotlight)

**Paper:** https://arxiv.org/abs/2306.06070

**Design:**
- 2,350 tasks across 137 websites, 31 domains, 12 high-level categories
- Covers Travel, Shopping, Information, Service, Entertainment
- Three generalization splits: Cross-Task, Cross-Website, Cross-Domain

**Success Detection:**
Step-level metrics (not end-to-end task completion):
- **Element Accuracy**: whether the correct DOM element was selected vs all acceptable elements
- **Operation F1**: token-level F1 for predicted operation (click=accuracy; type/select=F1 over value)
- **Step Success Rate**: both element and operation must be correct
- **Task Success Rate**: ALL steps must succeed (very strict)

**Critical limitation:** Mind2Web is *offline* (static action traces, not live execution). The agent predicts the next action; there is no live website state. Mind2Web-Live (2025) adds live execution.

**Numbers (with process reward model):**
- Element Accuracy: 53.0%
- Step Success Rate: 49.2%

---

### 2.5 GAIA

**Paper:** https://arxiv.org/abs/2311.12983

**Design:**
- 466 questions (300 in held-out test set)
- Requires web browsing + tool use + multi-modal reasoning + multi-step planning
- Three difficulty levels (not enumerated in paper abstract)
- Questions are "conceptually simple for humans" but require diverse tool composition

**Success Detection:**
Exact answer string match against gold answer. Closed-form, deterministic.

**Numbers:**
- Human: 92%
- GPT-4 + plugins: 15%
- SOTA ~2025: ~65% [UNVERIFIED — from secondary source; verify against HuggingFace leaderboard: https://huggingface.co/gaia-benchmark]

---

### 2.6 AssistantBench (EMNLP 2024)

**Paper:** https://arxiv.org/abs/2407.15711 ; https://assistantbench.github.io/

**Design:**
- 214 tasks from 53 annotators (35 domain experts)
- Tasks are time-insensitive (closed-form, stable answers)
- Requires browsing 525+ pages across 258 websites
- Focus: realistic, time-consuming research tasks

**Success Detection:**
F1 token overlap with gold answer string (partial credit for near-correct answers).

**Numbers:**
- SeeAct baseline: ~23.4%
- SOTA SeePlanAct (SPA): ~25.2%
- All agents score below 26 points — this benchmark remains largely unsolved

**Key finding:** Closed-book LLMs hallucinate and score near-zero precision; web agents have slightly better precision but still very low accuracy.

---

### 2.7 MiniWoB++

**Paper:** https://arxiv.org/abs/1802.08802 (original MiniWoB); Liu et al. 2018 for MiniWoB++

**Design:**
- ~80–100 synthetic web tasks (clicking buttons, filling forms, navigating calendars)
- Canvas-rendered synthetic pages — not real websites
- Low-level action space; single-page tasks

**Success Detection:**
Programmatic DOM-state checks with numeric reward signals (0 or 1).

**Numbers (2024):**
- SYNAPSE: 99.2% across 64 tasks (with demonstrations)
- GPT-4o zero-shot: ~44.6% Task SR

**Status:** Largely saturated for LLM-based agents. Useful for testing low-level action capabilities; not representative of real-world complexity.

---

## 3. Task-Completion Verification Methods

### 3.1 Programmatic / State-Based Checks

**How it works:** After agent completes a task, query the web application's actual state — database records, DOM content, API response — and compare against expected ground truth.

**Examples (from WebArena):**
- Navigation task: query GitLab API to confirm a repository was actually created
- Config task: check DOM that a setting was actually toggled
- Info task: exact/fuzzy match of extracted answer

**Strengths:**
- Immune to agent fabrication: agent cannot "tell" the evaluator it succeeded
- Reproducible; deterministic for most tasks
- No LLM costs per evaluation

**Weaknesses:**
- Hard to implement for open-ended tasks (what's the ground state for "find me a good recipe"?)
- Requires instrumented sandbox environments
- Brittle when websites change layout or behavior

---

### 3.2 LLM-as-Judge

**How it works:** An LLM (often a frontier vision-language model) receives the task description, agent trajectory (screenshots + actions), and final state, then renders a success/failure judgment.

**Implementations compared:**
| System | Judge Model | Input | Human Agreement |
|--------|-------------|-------|-----------------|
| WebVoyager original | GPT-4V | Task + response + screenshots | 85.3% (κ=0.70) |
| AER (Pan et al. 2024) | Vision-enabled LLM | Agent thoughts + actions + final screenshot | Not published |
| NNetNav | Llama 3.1 70B | Accessibility tree summary | Not published |
| WebJudge | o4-mini | Key screenshots + action sequence | 85.7% (κ not published) |
| Universal Verifier (UV) | Not specified | All trajectory screenshots + rubrics | Cohen's κ=0.64 (internal), 0.58 (external) |

**Key reliability issues:**
1. **False positives from hallucination:** Agent writes a fabricated "success summary"; judge believes it. False-positive rates of 22–45% for baseline verifiers (UV paper: https://arxiv.org/abs/2604.06240)
2. **Unfaithful chain-of-thought:** Agent generates plausible-sounding CoT that doesn't reflect actual execution, deceiving the judge. Documented in "Gaming the Judge" (arXiv 2601.14691): https://arxiv.org/abs/2601.14691
3. **Low screenshot coverage:** WebVoyager's judge drops to 47.7% agreement with only 1 screenshot
4. **Benchmark gaming:** "An Illusion of Progress?" shows agents can achieve 51% on WebVoyager via Google-Search shortcuts, not genuine site navigation

---

### 3.3 Human Evaluation

The gold standard but expensive. WebArena used human annotators achieving 78.24%. Typically used to:
- Calibrate LLM judge accuracy
- Evaluate borderline or ambiguous cases
- Audit a sample of automated evaluations

Human inter-annotator agreement is itself imperfect. UV paper reports that showing UV's reasoning raises human agreement from κ=0.39 to κ=0.63 — suggesting humans benefit from structured rubrics too.

---

## 4. Silent Failures & False-Success Detection

### 4.1 What Is a Silent Failure?

> "Failures in agentic systems can often be silent, occurring without generating clear error signals while still deviating from the intended behavior."
> — Pathak et al. (arXiv 2511.04032)

Contrast: traditional microservices produce explicit HTTP error codes or exceptions. Web agents return natural language success claims that may be fabricated.

**Taxonomy of silent failures (from arXiv 2511.04032):**
1. **Drift** — agent selects irrelevant tools or sub-agents for a query
2. **Cycles** — redundant loops where agents repeatedly invoke themselves
3. **Missing Details** — response lacks critical requested information despite appearing complete
4. **Tool Failures** — external APIs fail silently or return unexpected results that agent does not detect
5. **Context Propagation Failures** — incorrect context passed to dependent downstream agents

**Additional failure modes from "An Illusion of Progress?" (arXiv 2504.01382):**
- **Filter/Sorting Errors** (57.7% of OpenAI Operator failures): misapplied or missing filters
- **Numerical/Temporal Sensitivity**: failures on specific constraints (price range, year)
- **Navigation Problems** (19.6% of Operator failures): agent deviates from required sequence
- **Hallucination in final response**: agent claims success for tasks it didn't complete

---

### 4.2 Anomaly Detection on Trajectories

**Paper:** "Detecting Silent Failures in Multi-Agentic AI Trajectories" (arXiv 2511.04032)
https://arxiv.org/abs/2511.04032

**Approach:** Treat agent execution traces as time-series data; apply anomaly detection.

**Feature extraction (XGBoost, 16 features across 5 categories):**
- **Path features** (highest importance): agent/tool call sequences, unique call counts, hierarchical depth, total steps
- **Token features**: input/output token consumption per span
- **Latency features**: per-span and end-to-end timing
- **Prompt/Context features**: system prompt lengths, intermediate outputs
- **Model features**: LLM version information

**Results:**
- XGBoost (supervised): **98% accuracy** on 4,275-trajectory dataset
- SVDD (semi-supervised, trains only on normal traces): **96.47% accuracy** on 894-trajectory dataset
- Path-level features (tool count, total steps, unique steps) ranked highest in feature importance

**Key insight for implementation:** SVDD requires no labeled failure examples — only normal traces — making it practical to deploy before you have a large labeled failure dataset.

---

### 4.3 Screenshot-Based Outcome Verification

**Universal Verifier (UV)** (arXiv 2604.06240):
https://arxiv.org/abs/2604.06240

**Core mechanism:**
- Screenshots serve as ground truth, overriding agent's claimed narrative
- System scores rubrics *twice*: (1) using only action history, (2) using visual screenshot evidence — discrepancies flag fabrication
- "Screenshot Relevance Matrix": scores each screenshot against every rubric criterion; selects top-k most relevant per criterion (avoids "needle in haystack")
- 7-category error taxonomy with 24 subcodes

**Results:**
- False positive rate: **0.01–0.08** (UV) vs **22–45%** (baseline verifiers)
- Cohen's κ = 0.64 (internal), 0.58 (external)
- UV reasoning raises human annotator agreement from κ=0.39 to κ=0.63

**Practical implication:** Screenshot evidence as an independent channel (not relying on agent's text) is the most reliable way to catch false positives.

---

### 4.4 Self-Consistency / Verifier Models

**WebJudge** (from "An Illusion of Progress?" paper, arXiv 2504.01382):
- Identifies key intermediate screenshots (not just final state)
- Generates descriptive summaries and evaluates relevance at each step
- Integrates key screenshots + action sequences for comprehensive judgment
- 85.7% human-agreement (o4-mini as judge); outperforms WebVoyager judge (78.7%)

**AER (Agent Eval Refine, Pan et al. 2024):**
- Takes agent thoughts + actions + final browser state (screenshot or caption)
- Passed to vision-enabled model for success judgment
- Requires vision-capable LLM (not applicable to text-only judge)

**NNetNav (Murty et al. 2025):**
- Uses Llama 3.1 70B as judge
- Receives accessibility tree summary of state changes
- Decouples system prompt/reasoning chain from final state representation
- Advantage: works without vision-enabled model; accessibility trees are more compact

---

## 5. Eval Set Design: Practical Principles

### 5.1 Domain Diversity

WebArena's 812 tasks from 241 templates show how templates generate varied task instances. Mind2Web's 2,350 tasks across 137 websites demonstrate breadth. For a practical eval set, cover at minimum:

- **E-commerce**: add to cart, filter by price/attribute, checkout flow
- **Search/information retrieval**: multi-step research across sites
- **Forms/data entry**: registrations, submissions with validation
- **Navigation with visual context**: image search, spatial UI reasoning
- **Multi-tab or multi-site**: tasks requiring combining info from multiple sources
- **Stateful tasks**: tasks that require verifying that state *persisted* (not just clicked)

### 5.2 Task Difficulty Tiers

GAIA's three-tier difficulty model is instructive. Design at three levels:
1. **Single-step** (click a specific button, fill a form)
2. **Multi-step same domain** (filter + compare + select)
3. **Multi-step cross-domain** (look up a fact on site A, then use it on site B)

### 5.3 Held-Out Tasks

Mind2Web's Cross-Domain split (new websites never seen in training) is the gold standard for testing generalization. Reserve ≥20% of tasks on sites never seen during agent development.

### 5.4 Avoiding Benchmark Gaming

"An Illusion of Progress?" (arXiv 2504.01382) showed that restricting shortcut paths (e.g., blocking Google Search on tasks that test site-specific navigation) is essential. Design tasks where:
- The intended path is the *only reasonable path* to the correct state
- Shortcuts that bypass real interaction are explicitly blocked in the evaluator
- Success is verified against *web application state*, not against the agent's answer string

### 5.5 Evaluation Method Recommendation

Prefer programmatic state-based checks over LLM-as-judge wherever possible:
- Programmatic: query DB, DOM, API after task completion
- LLM-as-judge: use only for tasks where ground state is difficult to verify (open-ended retrieval); use UV-style screenshot evidence pairing, not agent-self-report
- Always implement dual-channel: agent's answer + independent state check

---

## 6. Key Papers & Sources

| Source | URL | Relevance |
|--------|-----|-----------|
| WebArena (ICLR 2024 Oral) | https://arxiv.org/abs/2307.13854 | Programmatic eval, 812 tasks, functional correctness |
| VisualWebArena (ACL 2024) | https://arxiv.org/abs/2401.13649 | Visual task eval, execution-based tests |
| WebVoyager (ACL 2024) | https://arxiv.org/abs/2401.13919 | GPT-4V judge, 85.3% agreement, real sites |
| Mind2Web (NeurIPS 2023) | https://arxiv.org/abs/2306.06070 | Step-level eval, 2350 tasks, element accuracy |
| GAIA (2023) | https://arxiv.org/abs/2311.12983 | Exact-match, general reasoning + web |
| AssistantBench (EMNLP 2024) | https://arxiv.org/abs/2407.15711 | Realistic tasks, F1 partial credit, unsolved |
| ST-WebAgentBench (2024) | https://arxiv.org/abs/2410.06703 | Safety + trustworthiness dimensions |
| Detecting Silent Failures (2025) | https://arxiv.org/abs/2511.04032 | XGBoost/SVDD on trajectories, 98% accuracy |
| An Illusion of Progress? (2025) | https://arxiv.org/abs/2504.01382 | WebVoyager gaming, filter errors, WebJudge |
| Gaming the Judge (2025) | https://arxiv.org/abs/2601.14691 | Unfaithful CoT fools LLM judges |
| Universal Verifier (2026) | https://arxiv.org/abs/2604.06240 | Screenshot-grounded, FP 0.01–0.08 vs 22–45% |
| AgentRewardBench (2025) | https://arxiv.org/abs/2504.08942 | Meta-evaluation of web agent judges |
| BrowserGym (2024) | https://arxiv.org/abs/2412.05467 | Unified framework across benchmarks |
| MiniWoB++ SYNAPSE | https://openreview.net/pdf?id=pI6ylnkPAD | ~99.2% on 64 tasks with demonstrations |

---

## Appendix: Numbers Confidence Notes

- **WebArena 71.6% (OpAgent):** from secondary leaderboard aggregator (codesota.com + awesomeagents.ai); not directly verified against official WebArena leaderboard — treat as approximate. The official leaderboard at https://webarena.dev may differ.
- **GAIA 65% SOTA:** from secondary source only; not verified against HuggingFace leaderboard. Mark as [UNVERIFIED].
- **VisualWebArena SOTA beyond GPT-4o 19.78%:** paper was released in 2024; 2025–2026 SOTA likely higher, not yet located.
- **WebVoyager "An Illusion of Progress" critique (78.7% vs 85.7%):** confirmed via arXiv 2504.01382 fetch; specific disagreement on whether 78.7% vs 85.3% original is apples-to-apples (different evaluation set) — noted as possible methodological discrepancy.
