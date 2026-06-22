# 07 — Memory/Skill Libraries, Deliberate Search, and Milestone-Based Evaluation

**研究日期:** 2026-06-22
**來源數量:** 13 primary sources (6 arXiv papers + 7 secondary)
**信心程度:** 78/100
**Scope:** Techniques NOT yet covered by the existing design — specifically excludes Reflexion, AgentOccam, and basic ReAct.

---

## TL;DR

Six techniques were investigated across three families. The most actionable conclusion is **counterintuitive**: a 2026 budget-constrained study (arXiv 2606.15017) shows that AWM-style workflow memory *loses* to a vanilla actor given the same token budget on WebArena — the memory module's gains vanish when you control for total inference cost. That does not kill the memory-library idea entirely, but it means the case for it must be made against a budget-matched baseline, not naive comparisons. Tree search (LATS) is definitively too expensive for a reliability-and-cost-optimized browser agent: ~17× more tokens than a linear actor, with the best-case web score improvement not justifying that multiple. Milestone-based eval (WebCanvas key-nodes) and deterministic replicas (REAL) are both immediately adoptable for our evaluation harness.

---

## Research Plan & Subquestions

1. Voyager: What is the exact skill library mechanism, and does it transfer beyond its Minecraft home?
2. AWM: How does workflow induction work, and do its gains survive a token-budget-matched comparison?
3. LATS: What is the real token cost of MCTS-based search, and is it ever justified for web tasks?
4. Auto-Eval (arXiv 2404.06474): Can an LLM evaluator replace oracle reward for Reflexion-style loops?
5. WebCanvas / Mind2Web-Live: What is "key-node" scoring, and how does it improve over binary success?
6. REAL: How are deterministic website replicas built, and what do they miss?

---

## Section 1 — Reusable Memory and Skill Libraries

### 1.1 Voyager (arXiv 2305.16291)

**Paper:** Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models," May 2023.
**URL:** https://arxiv.org/abs/2305.16291

#### Mechanism

Voyager has three interlocking components:

1. **Automatic curriculum** — GPT-4 proposes progressively harder tasks based on current inventory and world state, maximising exploration coverage.
2. **Skill library** — Successful programs are stored as JavaScript functions, indexed in a vector database using OpenAI `text-embedding-ada-002` embeddings keyed on the natural-language description of the skill. At inference time, the top-5 relevant skills are retrieved by cosine similarity and injected into the GPT-4 prompt.
3. **Iterative prompting loop** — Up to 4 refinement rounds per task; each round feeds back (a) environment state, (b) execution errors, and (c) self-verification from a *separate* GPT-4 critic call that judges whether the task succeeded and proposes corrections if not.

Skill composition is implicit: retrieved skills are concatenated into the prompt, and GPT-4 writes new code that calls them. There is no explicit composition graph.

#### Measured Results (Minecraft)

| Metric | Voyager | Best prior (Reflexion) |
|--------|---------|------------------------|
| Unique items collected | 3.3× more | baseline |
| Stone tools milestone speed | 15.3× faster | baseline |
| Distance traversed | 2.3× more | baseline |
| Items w/o skill library | 7% of full | — |
| Items w/o self-verification | 27% of full | — |

**GPT-4 vs GPT-3.5 within Voyager:** GPT-4 yields 5.7× more unique items.

Ablations show: curriculum > self-verification > skill library in early stages; the library matters most after 80+ tasks where the benefit of reuse compounds.

#### Cost / Latency

- Every task runs at minimum 2 GPT-4 calls (generator + verifier) and up to 4 rounds × 2 calls = 8 GPT-4 calls per task.
- Paper does not model dollar cost. At 2023 pricing, GPT-4 was 15× costlier than GPT-3.5-turbo; unmodelled.
- Embedding retrieval is cheap (ada-002), negligible relative to GPT-4 calls.

#### Limits / Transferability to Web Agents

- Environment is Minecraft via the Mineflayer JavaScript API. The API is stable and error-catchable, with instant reset and no side effects outside the game.
- Zero-shot generalisation tested only across Minecraft world seeds, not across environments.
- Skills written for one Mineflayer API version do not transfer to a different environment.
- Web browser DOM changes constantly: accessibility-tree node IDs are unstable across page loads, making code-based skills brittle. A skill that clicks `button[data-testid="submit-order"]` breaks when the attribute changes.
- **No published result on web navigation benchmarks.** All numbers are Minecraft-specific.

---

### 1.2 Agent Workflow Memory — AWM (arXiv 2409.07429)

**Paper:** Wang et al., "Agent Workflow Memory," September 2024.
**URL:** https://arxiv.org/abs/2409.07429

#### Mechanism

AWM induces *workflows* — reusable sub-routines — from past trajectories via an LLM prompt that extracts common patterns and abstracts example-specific values (e.g., "dry cat food" → `{product-name}`).

**Workflow data structure:** `(d_j, P_j^d)` where:
- `d_j` = natural-language goal description ("search for a product on Amazon")
- `P_j^d` = series of steps, each containing: environment state in NL, agent reasoning, executable action

Retrieval is implicit: all induced workflows are appended to the agent's memory context `M + W → M_w`. The LLM selects relevant ones during generation; there is no explicit vector-retrieval ranking.

**Two modes:**
- **Offline:** Workflows induced once from training data before inference. Fixed context for all test tasks.
- **Online:** After each test task, if the evaluator judges success (`L_eval(e^t) = 1`), the trajectory becomes a new workflow and joins memory. Iterative accumulation.

#### Measured Results (Headline Numbers)

| Benchmark | AWM | Baseline | Relative Gain |
|-----------|-----|----------|---------------|
| WebArena | 35.5% | 23.5% (BrowserGym) | +51.1% relative |
| WebArena | 35.5% | 33.0% (SteP, human-engineered) | +7.6% |
| Mind2Web cross-task (step SR) | 45.1% | 36.2% (MindAct) | +24.6% relative |
| Mind2Web cross-website | 33.9% | 25.0% | +8.9pp absolute |
| Mind2Web cross-domain | 35.5% | 18.6% | +16.9pp absolute |

#### Budget-Matched Reality Check (arXiv 2606.15017)

A June 2026 study ("Are Online Skill and Memory Modules Always Worth Their Tokens?", https://arxiv.org/html/2606.15017) ran AWM, ASI, and ReasoningBank against **Vanilla-IB** — a vanilla actor with an equivalent total token budget (15-step horizon instead of 10) — on WebArena and WorkArena-L1.

**Key result (Gemini 3 Flash):**

| Method | Success Rate | Total Tokens |
|--------|-------------|-------------|
| Vanilla-IB | 50.74% | 71.9K avg |
| AWM | 44.98% | 102.0K avg |
| ASI | 47.86% | 107.1K avg |
| ReasoningBank | 45.54% | 86.4K avg |

Vanilla-IB **outperforms AWM by 5.76pp** while using **29% fewer tokens**. The pattern held across GPT-5.4-mini and Qwen 3.6-27B.

Root causes identified:
- **Double cost:** The module costs tokens *plus* the injected workflows inflate every subsequent actor prompt.
- **Contamination:** Failed trajectories sometimes get inducted as workflows, injecting bad strategies.
- **Fragility:** Workflows with specific UI selectors break on changed page elements.
- **Model dependency:** Weaker models produce noisier workflow induction output.

#### Limitations

- No cost analysis in the original paper; headline numbers compare against weaker baselines.
- Offline + online workflows "are not fully compatible" — combining them degrades performance.
- Workflow execution fails when popup menus or dynamic elements break expected navigation paths.
- No explicit retrieval ranking; on large workflow libraries the entire library is in context, growing unboundedly.

---

### 1.3 Autonomous Evaluation and Refinement (arXiv 2404.06474)

**Paper:** Pan et al., "Autonomous Evaluation and Refinement of Digital Agents," April 2024. Published at COLM 2024.
**URL:** https://arxiv.org/abs/2404.06474

#### Mechanism

The paper trains/prompts an automatic evaluator to replace the oracle reward signal in Reflexion-style inference-time refinement loops.

**Two evaluator architectures:**

1. **Caption-then-reason (modular):** A fine-tuned VLM (QWen-VL, trained on 1,263 screenshot-description pairs from WebScreenshot, Mind2Web, Android-in-the-Wild, and in-house iOS captures) captions final screenshots; then a language model (GPT-4 or Mixtral) reasons about success using the caption + action history + task instruction.
2. **End-to-end VLM:** GPT-4V directly ingests screenshots + instructions with chain-of-thought reasoning.

**Reflexion integration:** The evaluator produces a binary success/failure judgment. On failure, the agent generates a verbal self-critique and retries; tested for up to 3 rounds.

**Filtered behavior cloning variant:** The evaluator scores each step of a CogAgent trajectory; only high-reward steps are kept; the filtered dataset is used to fine-tune the policy.

#### Measured Results

| Evaluator | WebArena agreement w/ oracle | Android agreement |
|-----------|------------------------------|-------------------|
| GPT-4V (end-to-end) | 80.6% | 90.6% |
| Captioner + GPT-4 | 82.1% | 89.8% |
| Captioner + Mixtral | 74.4% | 92.9% |

**Reflexion gain on WebArena (GPT-4 agent baseline 14.4%):**
- Captioner + Mixtral reward: +16% relative
- GPT-4V-based reward: **+29% relative** (approximately 14.4% → ~18.6%)

**Filtered BC on iOS device control (52 test tasks):**
- Baseline CogAgent: 8/52 = 15.4%
- Self-training (unfiltered): 11/52
- Filtered BC (evaluator-filtered): 14/52 = **75% relative improvement over baseline**

#### Error Analysis

On 50 evaluations per model:
- Type 1 (perception failure): 10% modular, 5% GPT-4V
- Type 2 (reasoning error): 50% GPT-4-based, 70% Mixtral
- Type 3 (task ambiguity): 30% GPT-4-based, 10% Mixtral-Captioner

**Failure modes:** missing subtle UI details, miscounting items on cluttered interfaces, overlooking error messages indicating task failure.

---

## Section 2 — Deliberate Search / Look-Ahead

### 2.1 LATS — Language Agent Tree Search (arXiv 2310.04406)

**Paper:** Zhou et al., "Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models," October 2023. ICML 2024.
**URL:** https://arxiv.org/abs/2310.04406

#### Mechanism

LATS adapts Monte Carlo Tree Search to LLM agents. Each MCTS node stores:
- `x`: original task input
- `a₁...ᵢ`: action sequence up to this node
- `o₁...ᵢ`: observation sequence (environment feedback)
- `N(s)`: visit count, `V(s)`: value estimate (for UCT selection)

**Value function:**
```
V(s) = λ · LM(s) + (1-λ) · SC(s)
```
- `LM(s)`: LLM prompted to score state correctness numerically
- `SC(s)`: self-consistency score — how often the same action recurs at this state
- `λ = 0.5` for reasoning tasks, `λ = 0.8` for acting tasks

**Reflection:** Failed trajectories trigger a verbal reflection (error analysis + proposed alternatives). Both failed trajectories and reflections are stored in external memory and injected into subsequent iterations.

**Operations:** selection → expansion → evaluation → simulation → backpropagation → reflection, repeated until success or budget exhaustion.

#### Measured Results

| Task | LATS | ReAct | Reflexion |
|------|------|-------|-----------|
| HotPotQA EM | 0.71 | 0.35 | — |
| WebShop avg score | 75.9 | 54.2 | — |
| WebShop success rate | 38.0% | 19.8% | — |
| HumanEval (GPT-4) | 92.7% pass@1 | — | 88.0% |
| Game of 24 | 0.44 | — | — |

LATS more than doubles ReAct on WebShop (38.0% vs 19.8%) and nearly doubles HotPotQA EM.

#### Token Cost Reality

| Method | Avg tokens / question (HotPotQA, n=50) |
|--------|----------------------------------------|
| LATS | 173,290 – 185,392 |
| RAP | 176,500 |
| ToT | 210,215 |
| MASTER (MCTS variant) | ~10,937 |

LATS uses ~17× more tokens per query than a lean non-tree method. On WebShop (GPT-3.5-turbo at ~$0.002/1K tokens, 2023 pricing), a 185K-token session costs roughly $0.37 per task — vs <$0.02 for a linear ReAct pass. At 2026 pricing with distilled models the absolute cost drops, but the 17× multiplier is structural, not model-dependent.

**The paper's own note:** "Higher computational cost relative to simpler prompting methods. Requires the environment to support reverting to earlier states."

**Web-specific constraint:** LATS requires reverting the browser state to a prior node after a failed branch. Web browsers are not transaction-safe: clicking "submit" or navigating away cannot be undone without full page reload/session replay. This makes MCTS branching technically complex in real web contexts.

#### Limitations

- Requires state-reversible environment; web browsers are not by default.
- Self-reflection quality degrades in complex environments (WebShop reflections become generic).
- May exhaust the full search budget on hard tasks without finding a solution.
- Value function calibration (λ hyperparameter) must be tuned per domain.

---

## Section 3 — Milestone-Based and Deterministic Evaluation

### 3.1 WebCanvas / Mind2Web-Live (arXiv 2406.12373)

**Paper:** Pan et al., "WebCanvas: Benchmarking Web Agents in Online Environments," June 2024.
**URL:** https://arxiv.org/abs/2406.12373
**GitHub:** https://github.com/iMeanAI/WebCanvas

#### Mechanism

WebCanvas introduces **key-node evaluation** — an intermediate-state scoring approach for live web tasks.

**Key node definition:** Essential actions or states that must be achieved to successfully complete a task. Nodes are annotated during dataset construction as the minimal set of observable checkpoints that unambiguously indicate progress (e.g., "search results page loaded with keyword X visible," "item added to cart confirmed").

**Scoring metrics:**

- **Task Completion Rate (TCR):** Fraction of key nodes the agent hits across all tasks. Partial credit — hitting 3/5 key nodes scores 60% for that task. Aggregate = mean across tasks.
- **Task Success Rate (TSR):** Binary — did the agent hit ALL key nodes for a task? Aggregate = fraction of tasks fully completed.

TCR is more informative than TSR for diagnosing failure modes (the agent got halfway but not further) and for comparing agents that both fail end-to-end.

**Dynamic website handling:** The annotation pipeline uses automated monitoring + human verification to flag when website changes break a key node's validity. Broken tasks are repaired or retired from the benchmark.

**Mind2Web-Live dataset:** 542 tasks with 2,439 intermediate evaluation states, sampled and refreshed from the original (static) Mind2Web dataset.

#### Measured Results

| Agent | TSR | TCR |
|-------|-----|-----|
| Best performing (GPT-4-based) | 23.1% | 48.8% |

No per-agent breakdown is available in sources accessed; only the top-line figure is reported. The gap between TSR (23.1%) and TCR (48.8%) reveals agents make substantial progress on tasks they ultimately fail — binary metrics would score all these as 0.

#### Annotation Cost

Not quantified in accessible sources. The paper claims "lightweight and generalizable annotation tools," but the annotation involves iterative peer review among annotators. [UNVERIFIED: per-task annotation effort]

---

### 3.2 REAL — Deterministic Website Replicas (arXiv 2504.11543)

**Paper:** Garg, VanWeelden et al., "REAL: Benchmarking Autonomous Agents on Deterministic Simulations of Real Websites," April 2025.
**URL:** https://arxiv.org/abs/2504.11543
**Website:** https://realevals.xyz
**SDK:** https://github.com/agi-inc/agisdk

#### Mechanism

REAL builds **high-fidelity, deterministic replicas** of real websites — clones that preserve the UX structure and workflow of the originals but run in a controlled sandbox.

**12 website replicas** (note: paper abstract says 11; live site lists 12):

| Clone Name | Real-World Original |
|------------|---------------------|
| Omnizon | Amazon |
| Staynb | Airbnb |
| DashDish | DoorDash |
| GoCalendar | Google Calendar |
| GoMail | Gmail |
| OpenDining | OpenTable |
| NetworkIn | LinkedIn |
| Udriver | Uber |
| Fly Unified | United Airlines |
| TopWork | Upwork |
| Zilloft | Zillow |
| Marrisuite | Marriott |

**Determinism achieved via:** locked data, fixed timestamps, fixed UX elements, configurable via URL parameters. Pre-authenticated sessions ("already logged in and ready"), cross-tab session persistence.

**Evaluation method (two reward functions):**
1. **Action tasks** — programmatic state diff: compare browser local storage initial vs. final state against expected key-value mutations. `r_A = 1` on exact match, 0 otherwise.
2. **Retrieval tasks** — rubric-guided LLM judge assesses whether the agent's answer matches ground truth.

**112 tasks** spanning easy/medium/hard difficulty, covering both action and retrieval types.

#### Measured Results

| Model | REAL Score |
|-------|------------|
| Claude-3.7-Sonnet-Thinking | 41.1% (best) |
| Gemini-2.5-Pro-Experimental | 38.4% |
| o3 | 34.8% |
| Stagehand + GPT-4o | lower (exact not found in sources) |
| Browser-Use + GPT-4o | lower (exact not found in sources) |

#### What Real Behaviors Are NOT Captured

Based on the paper's design:
- **Real-time data** — live pricing, availability, search results that change minute-to-minute are replaced by static fixtures.
- **CAPTCHA, bot detection, rate limiting** — replicas do not simulate these (by design, for reproducibility).
- **Third-party auth flows** (OAuth, SSO) — pre-authenticated sessions bypass these.
- **Layout changes and A/B tests** — replicas are frozen; real sites constantly A/B test UI.
- **Network latency variance** — local replicas do not simulate slow networks or partial page loads.

#### Comparison to WebArena

WebArena uses self-hosted open-source apps (GitLab, Reddit clones, OpenStreetMap). REAL targets mainstream commercial website patterns (e-commerce checkout, calendar booking, travel search). The failure modes are different: WebArena tests workflow automation of developer tools; REAL tests consumer-web task patterns that represent the majority of real agent use cases.

---

## Section 4 — Synthesis and Adopt/Skip Decisions

### The Core Trade-Off

The critical variable across all techniques is **cost vs. marginal gain against a budget-matched baseline**. The 2026 budget study (arXiv 2606.15017) is the most important recent finding: it shows that frontier models in 2026 may already internalize the reasoning that memory scaffolds externalize, eliminating marginal value while adding structural overhead.

### Decision Matrix

| Technique | Adopt? | Reasoning |
|-----------|--------|-----------|
| Voyager skill library (code-based) | Skip — wrong substrate | Skills are JS functions for a stable API (Mineflayer). Web DOM is unstable; code-based skills break on selector changes. No web benchmark evidence. |
| AWM workflow memory (NL workflows) | Conditional — only offline, with budget-matched baseline required | Headline numbers (+51% on WebArena) are against weak baselines. A 2026 budget study shows vanilla actor beats AWM by 5.76pp using 29% fewer tokens. If we pursue this, use offline induction only; always compare against a token-budget-matched baseline. |
| Auto-evaluator as Reflexion reward (2404.06474) | Adopt for eval harness only | 74–92% agreement with oracle is good enough for training-data filtering, not for production reward. Captioner + GPT-4 is the cheapest high-accuracy variant. Use it to filter good trajectories for fine-tuning data, not to gate live-task retries. |
| LATS tree search | Skip — too expensive, wrong env model | ~17× token multiplier over linear actor. Requires browser state reversion (browsers are not transaction-safe). Web score improvement (WebShop +16pp) does not justify ~17× cost. |
| WebCanvas key-node scoring | Adopt immediately for evaluation | TCR (partial credit) reveals far more signal than binary TSR. The 48.8% TCR vs 23.1% TSR gap shows agents make substantial progress on tasks they ultimately fail — binary metrics hide this. Use key-node scoring for our eval set from day 1. |
| REAL deterministic replicas | Adopt as primary eval environment | Solves the reproducibility and safety problems with live-web eval. 12 realistic consumer-web clone sites. Pre-built SDK (agisdk). Claude-3.7 achieves 41.1% — meaningful headroom to improve. Use as the primary offline eval harness. |

---

## Section 5 — Data and Comparisons

### Memory/Skill Library Cost-Benefit Summary

| Method | Reported gain | Against what baseline | Budget-matched outcome |
|--------|-------------|----------------------|------------------------|
| Voyager skill library | 3.3× items | ReAct/AutoGPT | N/A (Minecraft only) |
| AWM (offline) | +51.1% WebArena | Nominal baseline | Loses to Vanilla-IB (-5.76pp, +29% tokens) |
| AWM (online) | +24.6% Mind2Web | MindAct | Budget-matched not tested |

### Tree Search Cost Summary

| Method | Tokens / task | vs. Linear actor |
|--------|-------------|-----------------|
| Linear ReAct | ~10–11K | 1× |
| LATS | ~173–185K | ~17× |
| ToT | ~210K | ~19× |

### Evaluator Accuracy

| Evaluator | WebArena agreement | Cost |
|-----------|--------------------|------|
| GPT-4V end-to-end | 80.6% | High |
| Captioner + GPT-4 | 82.1% | Medium |
| Captioner + Mixtral | 74.4% | Low |

### Live Evaluation Benchmarks Comparison

| Benchmark | Tasks | Scoring | Reproducibility | Best agent |
|-----------|-------|---------|----------------|------------|
| WebArena | 812 | Binary | Self-hosted OSS apps | ~35% |
| Mind2Web (static) | 2,000+ | Step match | Static HTML snapshots | ~45% step SR |
| Mind2Web-Live (WebCanvas) | 542 | Key-node (TCR + TSR) | Live web (volatile) | 23.1% TSR / 48.8% TCR |
| REAL | 112 | State-diff + LLM judge | Deterministic clones | 41.1% (Claude-3.7) |

---

## Section 6 — Risks and Caveats

1. **Budget-matched finding is very recent (June 2026)** — arXiv 2606.15017. It was tested with Gemini 3 Flash, GPT-5.4-mini, and Qwen 3.6-27B. Results may differ for other models or task distributions.

2. **AWM offline mode was not the primary focus of the budget study** — the study ran AWM in what appears to be online mode. Offline-only AWM (inducing from a training corpus of high-quality trajectories) may still show positive ROI.

3. **LATS on web navigation is extrapolated** — the paper's web result is on WebShop (a simulated shopping env), not live browser tasks. The state-reversion constraint may be solvable via browser session snapshots, but this adds infrastructure cost not accounted for.

4. **REAL replica count discrepancy** — the arXiv abstract says 11 websites; realevals.xyz lists 12. The live site is more recent and likely correct. [UNVERIFIED: paper v2 exact count]

5. **WebCanvas key-node annotation cost** — per-task annotation cost is not quantified. For our custom eval set, manual annotation of key nodes adds setup overhead.

6. **Auto-evaluator agreement (74–92%) is not calibrated for hard tasks** — the evaluator fails most on task ambiguities (30% of GPT-4-based errors) and reasoning errors (50% of GPT-4 errors). It should not be used as a live production pass/fail gate.

---

## Sources

1. arXiv 2305.16291 — Voyager: https://arxiv.org/abs/2305.16291
2. arXiv 2409.07429 — Agent Workflow Memory: https://arxiv.org/abs/2409.07429
3. arXiv 2310.04406 — LATS: https://arxiv.org/abs/2310.04406
4. arXiv 2404.06474 — Autonomous Evaluation and Refinement: https://arxiv.org/abs/2404.06474
5. arXiv 2406.12373 — WebCanvas: https://arxiv.org/abs/2406.12373
6. arXiv 2504.11543 — REAL: https://arxiv.org/abs/2504.11543
7. arXiv 2606.15017 — Budget-constrained skill/memory study: https://arxiv.org/html/2606.15017
8. REAL website (replica list, leaderboard): https://realevals.xyz
9. AGI Inc. blog — REAL Bench introduction: https://www.theagi.company/blog/introducing-real-bench
10. AWM HTML paper: https://arxiv.org/html/2409.07429v1
11. LATS HTML paper v3: https://arxiv.org/html/2310.04406v3
12. Voyager GitHub: https://github.com/minedojo/voyager
13. Beancount.io Voyager research log: https://beancount.io/bean-labs/research-logs/2026/05/08/voyager-open-ended-embodied-agent-lifelong-learning
