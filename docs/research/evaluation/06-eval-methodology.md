# Eval Methodology: Verifying Agent Correctness Without Trustworthy Ground Truth

**研究日期:** 2026-06-22  
**來源數量:** 16 primary sources (1 transcript + 15 papers/docs)  
**信心程度:** 82/100 — high on LLM-judge failure modes and statistical rigor; moderate on tau-bench pass^k formula (abstract-only access); HAL scaffold-variance % not quantified in public abstract

---

## TL;DR

Evaluating a browser agent without trustworthy ground truth requires layering: (1) hard verifiers where possible, (2) LLM judges only where unavoidable — but with known biases mitigated, (3) pass^k over pass@k to expose reliability not just peak capability, (4) error bars with ≥1000 samples to distinguish real improvements from noise, (5) calibrated abstention so the agent reports "uncertain" instead of silently fabricating success. The single most dangerous failure mode is the correlated-judge trap: nine LLM judges provide ~2 independent votes — panels do not fix systematic errors.

---

## Part A: LLM-as-Judge — Reliability and Failure Modes

### A1. When LLM judges fail: the core failure taxonomy

**Self-preference bias.** LLMs assign systematically higher scores to outputs whose text patterns are familiar to them — not just outputs they generated. GPT-4 shows a "significant degree of self-preference bias"; the highest positive scoring delta for each model occurs when it judges itself [arXiv 2410.21819]. The mechanism: low perplexity correlates with higher evaluation scores, regardless of correctness. Implication: never use the same model family as both agent and judge.

**Judge accuracy on hard items.** JudgeBench (arXiv 2410.12784) found that many strong judge models including GPT-4o perform "just slightly better than random guessing" on challenging items spanning knowledge, reasoning, mathematics, and coding. This is not a niche finding — it applies to exactly the tasks a browser agent tackles (multi-step factual lookups, computation, code execution results).

**Correlated panel errors: the "Nine Judges" result.** Adding more LLM judges does not compensate for correlated errors. Across 9 frontier models from 7 families, the effective independent votes were ~2, not 9; panel accuracy falls "8–22 percentage points short of what independent voting would achieve"; the best single judge matches or outperforms the full panel; established aggregation methods close at most 11% of this gap even with access to correct answers [arXiv 2605.29800]. **This directly refutes the intuition that a panel of diverse judges is robust.**

**PoLL counter-evidence (partial).** A Panel of LLM evaluators (Cohere Command-R 35B + GPT-3.5 + Claude Haiku) achieved Pearson correlation 0.917 with Chatbot Arena human rankings vs GPT-4's 0.817, at 7–8× lower cost [arXiv 2404.18796]. However, the PoLL result was on preference/ranking tasks; JudgeBench and the "Nine Judges" result cover factual correctness tasks. **These findings are not contradictory: panels help with preference diversity but not with factual error correlation.** For browser-agent eval, factual correctness dominates.

**Unfaithful chain-of-thought.** Judges produce CoT explanations that do not reliably predict their final scores. The JudgeBench paper frames this as a core reliability issue [arXiv 2410.12784]. Implication: do not trust that a judge's stated reasoning reflects its actual scoring logic.

### A2. What the Anthropic "Demystifying Evals" guidance says

From the primary source (https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):

- **Grade outcomes, not steps.** Frontier models find valid solutions evaluators did not anticipate; rigid step-checking penalizes legitimate creativity.
- **Three grader types:** code-based (fast, objective, for binary outcomes), model-based (flexible, for open-ended tasks), human (gold-standard calibration). Use the cheapest that is sufficient.
- **LLM judges need frequent calibration against expert human judgment.** "Model grading often takes careful iteration to validate accuracy."
- **Give judges escape hatches** — explicit permission to return "Unknown" reduces hallucination from forced choices.
- **Isolate grading dimensions** — one judge per dimension rather than a single composite judge.
- **Anti-pattern: bypassable evals.** Graders that can be gamed reward clever cheating, not correct task completion.
- **Anti-pattern: class imbalance.** Test only when behavior should occur → agent learns to overtrigger. Build balanced positive/negative sets.

### A3. Agent-as-a-Judge: step-level evaluation

Standard LLM judges assess only final output. For multi-step browser tasks, intermediate steps matter: wrong clicks, hallucinated form fields, incorrect data extraction mid-session. Agent-as-a-Judge (arXiv 2410.10934) uses an agentic system to evaluate another, providing intermediate feedback throughout. On the DevAI benchmark (55 realistic AI dev tasks, 365 hierarchical requirements), Agent-as-a-Judge "dramatically outperforms LLM-as-a-Judge and is as reliable as human evaluation." [UNVERIFIED: specific correlation numbers not available from abstract.]

**For our system:** Agent-as-a-Judge is most applicable for evaluating complex multi-step web tasks where intermediate state matters — e.g., "did the agent correctly identify the form before submitting?"

---

## Part B: Abstention and Calibration

### B1. The overconfidence problem

Agents are systematically overconfident. Arvind Narayanan's team (HF workshop transcript) found: not-calibrated agents "tend to be overconfident rather than underconfident"; when asked how likely they succeeded, overconfident agents return 1.0 while actually succeeding ~50% of the time. This is the **silent failure problem** for browser agents: the agent reports success confidently, but the task was not completed correctly.

Calibration has been improving at leading labs (reducing sycophancy pressure), but **discrimination** — the ability to separate successes from failures — has been getting worse [transcript, Narayanan]. Good calibration without discrimination means the agent says ~50% on everything, which is useless for selective human review.

**For our system:** We need both calibration (stated confidence matches actual rate) and discrimination (confident on successes, uncertain on failures). These require separate measurement.

### B2. Verbalized confidence: what the research shows

LLMs systematically overstate confidence when asked to verbalize it, "potentially imitating human patterns" [arXiv 2306.13063]. White-box methods achieve AUROC ~0.605 for failure prediction; black-box strategies (sampling + consistency checking) reach 0.522–0.605. None consistently outperform on challenging tasks. **Verbalized "I'm 90% confident" is not calibrated confidence; it is social performance.**

Practical implication: eliciting "Are you confident?" produces unreliable signals. More robust: consistency across multiple independent completions of the same task.

### B3. Semantic entropy probes: internal uncertainty without external ground truth

Semantic Entropy Probes (SEPs) approximate semantic entropy from hidden states of a single generation, bypassing the need for multiple external samples [arXiv 2406.15927]. Key properties:
- Work from internal model representations — no external ground truth required
- Reduce overhead of uncertainty quantification "to almost zero"
- "Retain high performance for hallucination detection" [UNVERIFIED: specific AUROC numbers not in abstract]
- Practical for real-time agent deployment

**For our system:** SEPs are deployable as a zero-cost uncertainty layer in the agent's extraction steps. Flag high-entropy outputs for human review instead of passing them downstream.

### B4. Abstention survey (arXiv 2407.18418)

The survey frames abstention as addressing three axes: query (is this answerable?), model (do I have the knowledge?), and human values (should I answer?). For browser agents, the first two apply: the agent should abstain (or escalate) when the task is ambiguous or when it lacks evidence to verify an extraction. The survey confirms abstention "mitigates hallucinations and enhances safety." [UNVERIFIED: specific abstention methods and coverage-accuracy tradeoff numbers not available from abstract.]

**For our system:** Build explicit abstention into the agent's success-check layer. "Cannot verify" is a valid output that routes to human review rather than generating a confident false positive.

---

## Part C: Statistical Rigor — pass^k, Error Bars, Sample Size

### C1. pass@k vs. pass^k — why both are needed

From Anthropic's demystifying-evals doc and the tau-bench paper:

**pass@k** = probability of ≥1 success in k trials. As k grows, this approaches 100% — it measures maximum capability.

**pass^k** = probability all k trials succeed. As k grows, this falls — it measures consistency/reliability.

At k=1, both equal the per-trial success rate. By k=10 they tell opposite stories about the same agent. For customer-facing browser automation (orders, bookings, form submissions), one wrong execution in k tries is unacceptable — **pass^k is the product-relevant metric.**

tau-bench (arXiv 2406.12045) reports: GPT-4o achieves pass^1 <50% and **pass^8 <25% in the retail domain**. This means that even the best available model at time of publication, asked to execute a retail task 8 times, consistently completes it correctly in all 8 runs less than 25% of the time.

tau²-bench (arXiv 2506.07982) extends this to dual-control environments where both agent and simulated user manipulate shared state (a Dec-POMDP model of telecom support). Agents show "significant performance drops" when shifting from single-control to dual-control scenarios, exposing hidden failures invisible in standard benchmarks.

### C2. Error bars: the Miller framework

From arXiv 2411.00640:

**Bernoulli standard error** (independent binary items): `SE = √(s̄(1−s̄)/n)`. This is the minimum baseline.

**Clustered standard error**: when eval items share context (e.g., multiple questions about one webpage), clustered errors can be "over 3× larger than naive standard errors." The Llama 3 technical report made this error — applying Bernoulli formula to F1 scores, yielding systematically wrong confidence intervals.

**Paired comparison**: when comparing two agent versions on the same items, compute differences at item level to exploit correlation: `SE_{A−B} = √(SE²_A + SE²_B − 2·SE_A·SE_B·Corr(s_A, s_B))`.

**Minimum sample size:** to detect a 3% absolute accuracy difference with 80% power and 5% significance: **n ≈ 969 independent items**. Practical rule: "new evals should contain at least 1,000 questions."

**Resampling:** going from k=1 to k=2 samples per item reduces variance by 1/3; k=4 reduces by 1/2.

### C3. HAL standardized harness (arXiv 2510.11977)

"Holistic Agent Leaderboard" provides a standardized harness that runs parallel evaluations across hundreds of VMs, reducing evaluation time from weeks to hours. Key findings:
- 21,730 agent rollouts across 9 models × 9 benchmarks in coding, web navigation, science, customer service; ~$40,000 total cost
- **Higher reasoning effort reduces accuracy in the majority of runs** — counterintuitive finding that exposes assumption failures in ad-hoc evaluation
- Caught undocumented behaviors: agents searching benchmark source datasets rather than solving tasks (a form of eval gaming)
- Recommendation: evaluate at harness level, not just model level — same model on different harnesses produces meaningfully different scores [also confirmed by Bespoke Labs in transcript]

**Scaffold-dependence is real.** The transcript speaker (Mahesh, Bespoke Labs) explicitly states: "the same model on different harnesses has different metrics" — pointing to TerminalBench dashboard as evidence. HAL quantifies this but the specific variance percentage is not available from the abstract.

---

## Part D: Practical Harness Choices

### D1. Inspect AI (https://inspect.aisi.org.uk)

AISI's (UK AI Safety Institute) open evaluation framework:
- **Composable building blocks:** datasets, agents, tools, scorers — all separately configurable
- **Agent loop:** `generate_loop` runs model in tool-use loop until it stops calling tools
- **Multi-agent support:** `handoff()` forwards full conversation history between agents; `as_tool()` provides string-in/string-out interface for simpler delegation
- **Sandboxing:** Docker, Kubernetes, or Modal containers for safe agent execution
- **Scorers:** includes `model_graded_qa()` for LLM-as-judge; custom scorers composable
- **Standard error computation** built into result logging (confirmed in transcript: Nathan from HF notes Inspect computes SE automatically)
- **Adopted by Hugging Face** for community evals (HLE benchmark uses Inspect + O3-mini as judge)
- **Strong endorsement in transcript:** Nathan (Open LLM Leaderboard maintainer) recommends using established frameworks like Inspect rather than custom frameworks — reduces maintenance burden and enables cross-benchmark comparison

**For our system:** Inspect is the recommended harness foundation. It handles sandboxing, multi-agent coordination, LLM-as-judge integration, and statistical reporting in one composable framework.

### D2. The eval-driven development workflow (Anthropic)

From the demystifying-evals doc:
1. Start with 20–50 tasks from real failures (not synthetic scenarios)
2. Two independent domain experts must agree on pass/fail for each task
3. Create reference solutions proving tasks are solvable
4. Automated evals → production monitoring → A/B testing → transcript review (layered; no single layer catches everything)
5. **"Read the transcripts"** — non-negotiable; automated graders miss subtle issues

**Anti-patterns that surfaced in both the doc and the transcript:**
- 0% pass@100 usually means broken task spec, not an incompetent model
- Shared state between runs (leftover files, cached data) causes correlated failures
- If asked for three things but graded on two, agents learn to ignore the third (reward hacking)
- Eval saturation: when agents reach ~100%, migrate to regression suite and develop harder tasks

---

## Part E: Transcript Practitioner Guidance (HF Agentic Evaluations Workshop)

### E1. Reliability ≠ Capability (Arvind Narayanan, Princeton)

The central thesis of the workshop: AI agents have been improving rapidly on capability benchmarks, but reliability has improved only gradually. Narayanan's team measured 4 reliability dimensions:

1. **Consistency**: outcome consistency (same pass/fail across repeated runs?) + trajectory consistency (same action sequence?)
2. **Robustness**: fault robustness (API timeouts, injected failures) + prompt robustness (semantics-preserving rephrasing)
3. **Calibration + Discrimination**: stated confidence calibrated to actual success rate; agent can distinguish its successes from failures
4. **Failure severity**: minor (formatting error) vs. major (data deletion, wrong transaction)

Key finding: over 18 months when accuracy improved dramatically, composite reliability improved only gradually. The accuracy–reliability relationship is roughly linear but with a much lower slope.

**For our system:** Report all four reliability dimensions alongside accuracy. A 70% accurate browser agent that is highly inconsistent is not deployable; a 60% accurate agent that fails gracefully and knows when to escalate may be more useful.

### E2. Calibration failure modes observed in Gaia traces

Narayanan's team found two specific calibration failure patterns:
- **Process noise confusion:** when tool calls fail mid-run, models incorrectly reduce their confidence even when the final answer is still correct. Process messiness is uncorrelated with answer correctness.
- **Ambiguous task confusion:** many real-world tasks are genuinely ambiguous; agents that handle them poorly reveal real-world deployment gaps, even if this "under-elicits" lab capability.

### E3. Evaluation requires environments (Gaia2/ARE + Bespoke Labs)

Key practitioner consensus from the workshop:
- **Hard verifiers over LLM rubrics whenever possible.** Gaia2 moved away from LLM rubric judging toward event-level deterministic verification: expected action sequence annotated per scenario → compared to actual action sequence with correct parameters checked via equality or simple algorithmic code. Soft verifiers (LLM) used only for text content (e.g., email body check).
- **Sandbox isolation is non-negotiable.** Enables reproducibility, allows destructive action testing, prevents cross-run contamination, makes eval cheap.
- **Environment noise injection for robustness.** Gaia2 injects: tool failures, API signature variations (to detect overfitting to specific signatures), irrelevant external events. Prevents agents from overfitting evaluation patterns.
- **Grade all task components.** If task specifies three things and only two are graded, the agent learns to neglect the third (Bespoke Labs speaker, Mahesh).
- **Agent should not have access to the grader or solution.** Prevents reward hacking; Harbor framework enforces this natively.
- **Inference providers distort model evaluation.** Use local inference or controlled environments; inference providers may alter prompting in ways that confound model vs. provider evaluation (Nathan, HF).

### E4. Reporting requirements (Balaji, HF eval policy)

- Report seeds, prompt perturbations, pass@k, harness version, model version, quantization
- Session-level logging for reproducibility and accountability: same aggregate score can hide completely different session behaviors
- Error bars/standard error are currently absent from most eval reports — this is a known gap
- Two agents with identical accuracy scores can differ in steps taken, cost, errors, time — report all

---

## Part F: What We Should Adopt for Our Browser-Agent Eval

### F1. Grading hierarchy (prefer cheaper/more reliable)

| Priority | Grader Type | Use When | Example |
|---|---|---|---|
| 1 (default) | Hard deterministic verifier | State change is inspectable | DOM state, URL, API call params, extracted field value |
| 2 | Code-based test | Output is parseable | JSON structure, numeric value, regex match |
| 3 | LLM judge (isolated, calibrated) | Text content, open-ended quality | Email body correctness, summary coverage |
| 4 | Human review | Calibration, disputed cases | Weekly transcript sample |

LLM judge must: be a different model family from the agent under test; have an explicit "Unknown" escape hatch; grade one dimension at a time; be validated monthly against human labels.

### F2. Reliability metrics to report

For each task set, report:
- **pass^k (k=3 minimum)**: consistency metric; our primary production readiness signal
- **pass@1**: per-trial accuracy; comparable to existing benchmarks  
- **Outcome consistency**: what fraction of tasks have the same pass/fail on every run?
- **Calibration + discrimination**: agent-stated confidence vs. actual success rate (AUROC)
- **Cost and step count per task**: efficiency alongside correctness
- **Failure severity distribution**: minor vs. major failures (data loss, wrong submission)

### F3. Statistical requirements

- Minimum 1,000 eval items for a primary benchmark [Miller, arXiv 2411.00640]
- Always report standard error: `SE = √(s̄(1−s̄)/n)` for independent items; use clustered SE when items share page context
- For model comparison, use paired analysis (same URLs/tasks across versions)
- A 3% improvement is only meaningful with n ≥ 969 independent items at 80% power

### F4. Silent failure layer

The explicit goal of the silent-failure layer is to catch cases where the agent outputs confident success but the task was actually not completed correctly. Three complementary mechanisms:

1. **Semantic Entropy Probes** on extraction steps [arXiv 2406.15927]: internal uncertainty signal, near-zero overhead, no ground truth required. Flag high-entropy extractions for review.
2. **Consistency sampling**: run the same extraction 2–3 times; inconsistent outputs trigger escalation.
3. **State verification**: after the agent reports completion, independently verify the post-action state (DOM, API response, screenshot delta) against expected outcome using a hard verifier. This is the Gaia2 "hard verifier" approach.

Never accept verbalized confidence as the sole success signal [arXiv 2306.13063].

### F5. Harness and infrastructure

- Use **Inspect AI** as the eval harness (sandboxing, LLM-as-judge integration, SE computation, multi-agent support)
- Run each task in a clean sandbox; no shared state between runs
- Inject API failures and prompt variations to measure robustness alongside accuracy
- Do not use the same inference provider as production for eval (provider-specific effects confound model evaluation)
- Document: model version, quantization, harness version, scaffold, temperature, judge model, eval date

---

## Sources

| # | Source | URL | Access |
|---|---|---|---|
| 1 | HF Agentic Evaluations Workshop transcript | Local: `job/homeworks/design/yt-agentic-evals-transcript.txt` | Full read |
| 2 | Anthropic "Demystifying evals for AI agents" | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | Full fetch |
| 3 | Inspect AI documentation | https://inspect.aisi.org.uk | Partial fetch |
| 4 | HAL: Holistic Agent Leaderboard (arXiv 2510.11977) | https://arxiv.org/abs/2510.11977 | Abstract + summary |
| 5 | tau-bench / pass^k (arXiv 2406.12045) | https://arxiv.org/abs/2406.12045 | Abstract; HTML 404 |
| 6 | tau²-bench dual-control (arXiv 2506.07982) | https://arxiv.org/abs/2506.07982 | Abstract |
| 7 | Agent-as-a-Judge (arXiv 2410.10934) | https://arxiv.org/abs/2410.10934 | Abstract |
| 8 | JudgeBench — judge meta-eval (arXiv 2410.12784) | https://arxiv.org/abs/2410.12784 | Abstract |
| 9 | PoLL Panel of LLM judges (arXiv 2404.18796) | https://arxiv.org/abs/2404.18796 | Full HTML |
| 10 | Nine Judges, Two Effective Votes (arXiv 2605.29800) | https://arxiv.org/abs/2605.29800 | Abstract |
| 11 | Self-preference bias (arXiv 2410.21819) | https://arxiv.org/abs/2410.21819 | Abstract |
| 12 | Abstention survey "Know Your Limits" (arXiv 2407.18418) | https://arxiv.org/abs/2407.18418 | Abstract only |
| 13 | Stated-confidence calibration (arXiv 2306.13063) | https://arxiv.org/abs/2306.13063 | Abstract |
| 14 | Semantic entropy probes (arXiv 2406.15927) | https://arxiv.org/abs/2406.15927 | Abstract |
| 15 | Adding Error Bars to Evals (arXiv 2411.00640) | https://arxiv.org/abs/2411.00640 | Full HTML |

---

## Unverified / Flagged Items

- **HAL scaffold-variance percentage**: abstract does not quantify what % of score variance comes from scaffold vs. model. Full paper not fetched (HTML returned 404; PDF not tried).
- **tau-bench pass^k formula**: mathematical definition confirmed described but not quoted verbatim (HTML returned 404; abstract only).
- **Agent-as-a-Judge specific correlation numbers**: abstract states "dramatically outperforms" without a numeric figure.
- **Abstention coverage-accuracy tradeoff numbers** (arXiv 2407.18418): abstract-only access; specific metrics not confirmed.
- **SEP AUROC numbers** (arXiv 2406.15927): abstract says "retain high performance" — specific number not quoted.
- **arXiv 2506.07982** (tau²-bench): June 2026 paper — accessible and consistent with description, but cited numbers are abstract-level only.
