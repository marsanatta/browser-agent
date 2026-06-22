# SOTA in LLM-Driven Browser / Web Automation Agents (2024–2026)

> Architecture survey to ground the design of a new generalized natural-language browser automation agent.

**研究日期 (Research date):** 2026-06-22
**來源數量 (Sources):** ~40 primary sources — GitHub source code, arXiv papers, official docs, system cards, vendor blogs
**信心程度 (Confidence):** HIGH for systems verified against source code / arXiv primary text; MEDIUM for vendor-self-reported benchmarks; flagged inline where unverified or refuted.

---

## TL;DR

- The field splits along **three perception philosophies**: vision-maximalist (screenshot + Set-of-Marks), text/DOM-maximalist (pruned HTML or accessibility tree), and split-brain / hybrid (vision to plan, structure to ground). There is no consensus winner — each trades universality against cost and fragility.
- **The "DOM vs accessibility-tree" framing repeated in blog comparisons is frequently wrong.** Source-code verification shows browser-use, Stagehand, and Agent-E all *fuse* the DOM and the Chromium accessibility tree. Read the code, not the marketing.
- **Most production OSS agents use a flat ReAct or tool-calling loop with no built-in verification step.** Anthropic's own docs admit the model "assumes outcomes of its actions without explicitly checking their results." Self-correction is the clearest 2025–2026 research frontier and the clearest gap in shipped systems.
- **No system ships real long-term / episodic memory** — all rely on the in-context window plus, at most, a free-text scratchpad or client-side file I/O (Anthropic's memory tool).
- **Benchmark numbers are largely incomparable and partly illusory.** Different eval sets, vendor self-reports, LLM-as-judge confounds, and documented benchmark-exploitation mean cross-system success-rate tables should be treated with heavy caution. Several public 2026 "leaderboards" contain **fabricated** model entries — excluded here.

---

## 1. Comparison Table

Perception: **SoM** = Set-of-Marks (numbered overlays on screenshot); **AX** = accessibility tree; **DOM** = HTML DOM; **px** = raw screenshot pixels.

| System | Perception | Action space | Planning / control loop | Memory | Paper? | Primary source |
|---|---|---|---|---|---|---|
| **browser-use** | Hybrid DOM+AX → indexed element list; screenshot optional (`use_vision`) | 24 actions incl. click(idx/xy), input, scroll, extract, `evaluate` (JS), tabs, files, done | ReAct + optional hierarchical planner (`PlanItem` list, replan-on-stall) | In-context: free-text scratchpad + structured history + compaction every ~25 steps | No (software artifact) | [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use) |
| **Stagehand** (Browserbase) | Hybrid DOM+AX "snapshot" (`dom` mode); `hybrid`/`cua` add vision | 11-action enum (click/fill/type/press/scroll/hover/drag…); composable primitives `act`/`extract`/`observe`/`agent` | Tool-calling loop (not ReAct); `observe→cache→replay` for zero-token replay; `maxSteps` 20 | Accumulating `ModelMessage[]`; cache layer (not memory); cross-exec continuation experimental | No | [github.com/browserbase/stagehand](https://github.com/browserbase/stagehand) |
| **Skyvern** | Vision-heavy hybrid (screenshot + custom DOM tree) | click/type/scroll/select/upload etc. via DOM+vision | Hierarchical **Planner-Actor-Validator** (Validator alone +17pp in ablation) | In-context | No | [github.com/Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) |
| **Agent-E** (Emergence) | **AX tree** text (`mmid` inject → `accessibility.snapshot` → reconcile to DOM) | 10 minimal skills; scroll via `PageDown`; no drag/hover/upload | Hierarchical plan-then-act; **stateless navigator** (fresh chat per subtask) | In-context | **Yes — [arXiv:2407.13032](https://arxiv.org/abs/2407.13032)** | [github.com/EmergenceAI/Agent-E](https://github.com/EmergenceAI/Agent-E) |
| **LaVague** | HTML-RAG (retrieve relevant DOM chunks) | Compiles to Selenium/Playwright via Action Engine | World Model picks engine → Action Engine; single-step lookahead | Append-only `ShortTermMemory` | No | [github.com/lavague-ai/LaVague](https://github.com/lavague-ai/LaVague) |
| **WebVoyager** | **SoM** annotated screenshot (numbered boxes via JS); no HTML to model | 7 actions: Click[N], Type, Scroll, Wait, GoBack, Google, Answer | Flat ReAct loop; 15-step budget | Text history full; last 3 screenshots only | **Yes — [arXiv:2401.13919](https://arxiv.org/abs/2401.13919)** (ACL 2024) | [github.com/MinorJerry/WebVoyager](https://github.com/MinorJerry/WebVoyager) |
| **SeeAct** (OSU) | Screenshot **only** to generate action; HTML enters at grounding stage | (element, operation, value): CLICK / TYPE / SELECT | **Generate-then-ground** (2 GPT-4V calls/step); not ReAct | NL `Previous Actions:` list only | **Yes — [arXiv:2401.01614](https://arxiv.org/abs/2401.01614)** (ICML 2024) | [github.com/OSU-NLP-Group/SeeAct](https://github.com/OSU-NLP-Group/SeeAct) |
| **AutoWebGLM** (THU/Zhipu) | **Pruned HTML** (custom HTML Pruner) + OCR for canvas/images | 10 function-call actions (click/hover/select/type/scroll/go/jump_to/switch_tab/user_input/finish) | Flat sequential policy; multi-step baked into weights via 3-stage training | In-context `#Previous commands` list | **Yes — [arXiv:2404.03648](https://arxiv.org/abs/2404.03648)** (KDD 2024) | [github.com/THUDM/AutoWebGLM](https://github.com/THUDM/AutoWebGLM) |
| **Anthropic Computer Use** | **Screenshot-only** (px); no DOM/AX | Versioned: screenshot/mouse/click/type/key + scroll/drag/zoom; companion bash + text_editor + memory tools | Single model, reactive client-side loop; **no built-in reflection** | `messages[]` (stateless API) + optional client-side `memory_20250818` file tool | No (docs/blog) | [computer use docs](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool) |
| **OpenAI CUA / Operator** | **Screenshot-only** (px) via `computer_screenshot` | Batched `actions[]`: click/double_click/drag/move/scroll/keypress/type/wait/screenshot | Single end-to-end model (vision+RL); hidden CoT; separate safety monitor model | Chained via `previous_response_id` (latest screenshot only, **not accumulated**; 8K ctx) | No (system card) | [Operator System Card](https://cdn.openai.com/operator_system_card.pdf) |
| **MultiOn** | **DOM + ARIA** hybrid (structure-based); element IDs | CLICK[ID], GOTO, TYPE, SUBMIT, CLEAR, SCROLL, ASK USER HELP | Research: MCTS + critic + DPO (Agent Q). Production: status machine | `session_id` plan/progress; 10-min idle TTL | **Yes (method) — [arXiv:2408.07199](https://arxiv.org/abs/2408.07199)** | [docs.multion.ai](https://docs.multion.ai/learn/sessions) |
| **UI-TARS** (ByteDance) | **Screenshot-only** native VLM (no AX tree); Qwen2-VL backbone | Native GUI action vocabulary (click/type/scroll/drag…) end-to-end | End-to-end model; UI-TARS-2 adds multi-turn PPO | Reflection-tuning (DPO); data flywheel | **Yes — [arXiv:2501.12326](https://arxiv.org/abs/2501.12326)** | [arxiv.org/abs/2501.12326](https://arxiv.org/abs/2501.12326) |
| **OmniParser** (Microsoft) | Screenshot → **SoM** (interactable-detection + icon captioning); *perception module, not an agent* | n/a (feeds any LLM) | n/a | n/a | **Yes — [arXiv:2408.00203](https://arxiv.org/abs/2408.00203)** | [microsoft.github.io/OmniParser](https://microsoft.github.io/OmniParser/) |

---

## 2. The Three Perception Philosophies

The cleanest organizing axis for the whole field.

### Vision-maximalist (screenshot + Set-of-Marks)
The LLM sees an annotated screenshot and refers to elements by numeric label, never by selector. **WebVoyager**, **OmniParser**, **UI-TARS**, and **Anthropic/OpenAI computer use** sit here (the last two without SoM — raw pixel coordinates).

- WebVoyager uses GPT-4V-ACT (JS tool) to enumerate interactive elements and overlay numbered boxes on a 1024×768 screenshot (~765 tokens/image), with per-box auxiliary text (type, inner text, `aria-label`). It explicitly rejects DOM/AX input as "overly verbose." [arXiv:2401.13919]
- The **+19pp lift** from text-only (40.1%) to multimodal (59.1%) on WebVoyager's own benchmark confirms SoM-style grounding is load-bearing. [arXiv:2401.13919, Table 1]
- 2025–2026 the vision camp won the foundation-model race: **UI-TARS** (native VLM, no AX tree) hit OSWorld 42.5% / WebVoyager 84.8% / ScreenSpot-Pro 61.6%; UI-TARS-2 (multi-turn PPO) reached OSWorld 47.5% / Online-Mind2Web 88.2%. [arXiv:2501.12326, arXiv:2509.02544]

### Text / DOM-maximalist (pruned HTML or AX tree)
The LLM sees a serialized structure and acts on element IDs.

- **AutoWebGLM** feeds a custom-pruned HTML tree (keeps operable elements + bounded context, OCR for canvas) to a fine-tuned 6B model. [arXiv:2404.03648]
- **Agent-E** is marketed as "flexible DOM distillation" but the source code (`ae/utils/get_detailed_accessibility_tree.py`) shows it is mechanically an **AX-tree extraction**: inject `mmid` → `page.accessibility.snapshot(interesting_only=True)` → reconcile AX nodes to DOM → denoise. A clean case of marketing-vs-source-reality. [arXiv:2407.13032 + source]
- **MultiOn** uses DOM+ARIA and `CLICK [ID]` actions — cheaper and precise on the web, brittle to structural change.

### Split-brain / hybrid
- **SeeAct** generates an action in natural language from a screenshot *only*, then grounds it to an HTML element in a separate stage. Its central finding: **grounding, not planning, is the bottleneck** (Oracle 65.7% vs realistic Choice 40.6% on Mind2Web Cross-Task — a ~25pp gap). [arXiv:2401.01614]
- **browser-use** and **Stagehand** both fuse DOM + AX into an indexed element representation; browser-use rebuilds the full tree every step (~5–15k tokens/step), Stagehand perceives on demand and caches.

### The Set-of-Marks reconciliation (genuinely informative)
WebVoyager finds SoM gives +19pp; SeeAct finds SoM-style annotation is its **worst** grounding strategy (13.0% Cross-Task, severe hallucination). Reconciliation: WebVoyager annotates only precisely-enumerated interactive elements (clean, non-occluding boxes); SeeAct overlaid boxes+labels on top-50 ranked candidates on dense pages, causing occlusion and label mismatch. **Lesson: SoM works when annotations are sparse and precise; it fails when dense and occluding.** A separate study ([arXiv:2409.01927](https://arxiv.org/abs/2409.01927)) found DOM-based grounding (~90.4%) beats CV/SoM grounding (~78.4%) for web.

---

## 3. Action Space Patterns

- **Coordinate-based** (Anthropic, OpenAI, UI-TARS): universal across any GUI, zero integration, but layout-fragile and structurally prone to silent failure — no DOM ground truth to verify against.
- **Element-ID / index-based** (browser-use, MultiOn, AutoWebGLM, SeeAct, Agent-E): precise and cheap on the web, web-only, brittle to structural change.
- **Escape hatches matter**: browser-use exposes `evaluate` (arbitrary JS) and file I/O; this expands capability but is a security surface (two published security papers analyze browser-use specifically: [arXiv:2506.07153](https://arxiv.org/abs/2506.07153), [arXiv:2505.13076](https://arxiv.org/abs/2505.13076)).
- **Batched actions** (OpenAI returns multiple actions/turn; browser-use up to 5/step) cut LLM round-trips — a direct cost/latency lever.
- **Human-in-the-loop primitive**: AutoWebGLM (`user_input`), MultiOn (`ASK USER HELP`), Agent-E all expose an explicit "ask the human" action — a cheap robustness affordance.

---

## 4. Planning & Control Loops

| Pattern | Systems | Notes |
|---|---|---|
| Flat ReAct | WebVoyager, browser-use (base) | Think → Act → Observe; simplest; dominant in OSS |
| Tool-calling loop | Stagehand, Anthropic, OpenAI | One LLM call/step picks a tool; no explicit reasoning trace required |
| Generate-then-ground | SeeAct | Plan in NL, ground separately — isolates the grounding bottleneck |
| Hierarchical (planner/executor) | browser-use (planner on), Skyvern (Planner-Actor-Validator), Agent-E | Decompose then execute; Skyvern's Validator alone = +17pp |
| Tree search | MultiOn/Agent Q (MCTS), WebOperator, Plan-MCTS | Research-grade; expensive; strong on long-horizon |
| End-to-end trained | UI-TARS, AutoWebGLM | Multi-step competence baked into weights via SFT→RL |

**The single most build-relevant fact:** none of the shipped commercial loops (Anthropic, OpenAI) includes a built-in verification/reflection step. Anthropic docs explicitly warn the model "assumes outcomes of its actions without explicitly checking their results." Skyvern's separate **Validator** stage and browser-use's optional **judge** are the OSS counterexamples — and Skyvern's ablation shows the validator is worth +17pp.

### 2025–2026 self-correction research (the frontier)
- **"Don't Act Blindly"** ([arXiv:2604.05477](https://arxiv.org/abs/2604.05477)): after each action, capture the resulting screen, compare actual vs predicted effect; block progression on discrepancy.
- **World-Model-Augmented + Action Correction (WAC)** ([arXiv:2602.15384](https://arxiv.org/abs/2602.15384)): an LLM world model simulates each candidate action before execution; a judge scores {0, 0.5, 1}; a correction loop runs if all candidates fall below threshold.
- **Step-level process reward models** (GUI-Critic-R1, GUI-Shepherd, AgentPRM/NeurIPS 2025): intermediate per-action rewards replacing binary outcome-only signals.
- **Reflection-Based Memory** ([arXiv:2506.02158](https://arxiv.org/abs/2506.02158)): store failed trajectories (actions + DOM + reasoning), retrieve by similarity to avoid repeats — no retraining.

---

## 5. Memory

**Universal finding: no system ships real long-term/episodic memory.** All rely on the in-context window.

- **browser-use**: free-text `AgentBrain.memory` scratchpad + structured `AgentHistoryList` + compaction (every ~25 steps or ~40k chars; keep first + last 6, summarize older). No vector/RAG. Token counting not implemented (uses char count).
- **Stagehand**: accumulating `ModelMessage[]`; cache layer is performance/self-healing (SHA256 of method+URL+DOM hash, 48h TTL), not memory.
- **Anthropic**: stateless API (`messages[]` resent each turn); only first-party cross-session affordance is the optional **client-side** `memory_20250818` file tool — Claude issues file ops against a `/memories` directory your app hosts; Anthropic stores nothing.
- **OpenAI CUA**: 8K context forces a no-accumulation loop — newest screenshot + chained `previous_response_id` only. No cross-session memory.
- **MultiOn**: `session_id` holds plan/progress, 10-min idle TTL. The "learning" the CEO describes is **training-time** (LoRA/DPO), not runtime per-user memory.
- **WebVoyager**: keeps full text history but only the last 3 screenshots (cost-driven eviction at ~765 tokens/image).

---

## 6. Benchmarks (treat as incomparable)

> Critical caveat: these systems were **not co-evaluated on a shared protocol**. WebVoyager (live, LLM-judged) ≠ Mind2Web (offline step-matching) ≠ WebArena (self-hosted functional). Do not rank by raw numbers.

| Benchmark | Notable result | Source |
|---|---|---|
| WebVoyager dataset (643 tasks, live) | WebVoyager multimodal 59.1%; auto-eval κ=0.70 vs human | [arXiv:2401.13919] |
| Mind2Web (offline step SR) | SeeAct Choice 40.6% / Oracle 65.7% (Cross-Task); AutoWebGLM avg 59.5% (fine-tuned) | [arXiv:2401.01614], [arXiv:2404.03648] |
| WebArena (812 tasks) | GPT-4 Turbo 14.9% (2023) → WebRL 49.1% → OpAgent 71.6% (2026) | [arXiv:2411.02337], [arXiv:2602.13559] |
| OSWorld (computer use) | UI-TARS-1.5 42.5%, UI-TARS-2 47.5% | [arXiv:2501.12326], [arXiv:2509.02544] |
| ScreenSpot-Pro (grounding) | UI-TARS-1.5 61.6%; OmniParser V2+GPT-4o 39.6%; bare GPT-4o 0.8% | [arXiv:2504.07981] |
| AssistantBench (Princeton HAL) | Best ~38.8% (Browser-Use + o3); **cost anti-correlated with score** | [hal.cs.princeton.edu/assistantbench](https://hal.cs.princeton.edu/assistantbench) |

### "An Illusion of Progress?" — the most decision-relevant paper
[arXiv:2504.01382](https://arxiv.org/abs/2504.01382) (Xue et al., Apr 2025) human-evaluated 6 frontier agents on its new Online-Mind2Web: Operator 61.3% (best), Claude Computer Use 3.7 56.3%, SeeAct early-2024 baseline 30.7%, Browser Use / Agent-E / Claude 3.5 ~28–30%. **Core claim: most 2025 agents barely beat a 2024 baseline — benchmark progress is partly illusory.** A Berkeley RDI study separately found WebArena exploitable (high scores without genuinely solving tasks).

---

## 7. Data-Hygiene Warning (verified during research)

Several public 2026 "leaderboards" — **llm-stats.com, benchlm.ai, awesomeagents.ai, codesota.com** — contain **fabricated entries** (nonexistent models like "Claude Opus 4.8", "Claude Mythos 5", "GPT-5.2" with invented ScreenSpot-Pro scores of 87–95%). Two independent research agents caught this. **Trust only arXiv papers, official benchmark sites, and the Princeton HAL leaderboard.** Vendor self-reports (Notte 86.2% WebVoyager, browser-use 89.1%, Skyvern 85.85%, Magnitude ~94%) are LLM-as-judge confounded and not independently reproduced — GitHub issue #2808 documents a failed browser-use reproduction.

---

## 8. Design Takeaways for a Robust Generalized Agent

1. **Hybrid perception with cascading fallback** beats committing to one channel. DOM/AX is cheap and precise but web-only and structurally brittle; pixels are universal but expensive and layout-fragile. SoM works only when annotations are sparse and precise. No shipped system offers documented runtime cascade — this is a real gap to fill.
2. **An explicit verification step is the highest-ROI robustness lever.** Skyvern's Validator = +17pp; the entire 2025–2026 self-correction literature (effect-verification, world-model simulation, step-level PRMs) converges on this. None of the big commercial loops does it for you.
3. **Silent failure is structural in pixel-only, verification-free designs** — there is nothing to cross-check a screenshot against. A robust agent must add a verify-after-act step that compares observed vs predicted effect.
4. **Cost/latency is dominated by the LLM loop, not the browser.** OSWorld-Human ([arXiv:2506.16042](https://arxiv.org/abs/2506.16042)): planning/reflection/judging calls = 75–94% of latency; agents take 2.7–4.3× more steps than humans. Levers: observe-once→cache→replay (Stagehand), batched actions, prune-to-last-N-screenshots, on-demand perception.
5. **Memory is an open problem, not a solved one.** Reflection-based memory (store + retrieve failed trajectories) is the most promising lightweight pattern and needs no retraining — worth building given nobody ships it.
6. **Hierarchical decomposition pays off on long-horizon tasks** (Skyvern Planner-Actor-Validator, Agent-E's stateless navigator). A stateless sub-task executor with fresh context avoids context pollution.
7. **Ship an explicit human-in-the-loop action** (`ask_user`) — cheap, and the precedent is universal (MultiOn, Agent-E, AutoWebGLM).
8. **Evaluate with independent ground truth, not self-consistency or vendor LLM-judges.** Benchmark inflation, fabricated leaderboards, and the "Illusion of Progress" finding all argue that honest, reproducible eval is itself a differentiator.

---

## Sources

**OSS frameworks (source-verified):**
- browser-use — [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use) · [docs.browser-use.com](https://docs.browser-use.com)
- Stagehand — [github.com/browserbase/stagehand](https://github.com/browserbase/stagehand) · [docs.stagehand.dev](https://docs.stagehand.dev) · [browserbase.com/blog/stagehand-v3](https://www.browserbase.com/blog/stagehand-v3)
- Skyvern — [github.com/Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern)
- Agent-E — [github.com/EmergenceAI/Agent-E](https://github.com/EmergenceAI/Agent-E) · [arXiv:2407.13032](https://arxiv.org/abs/2407.13032)
- LaVague — [github.com/lavague-ai/LaVague](https://github.com/lavague-ai/LaVague)

**Research agents (arXiv primary):**
- WebVoyager — [arXiv:2401.13919](https://arxiv.org/abs/2401.13919) (ACL 2024) · [code](https://github.com/MinorJerry/WebVoyager)
- SeeAct — [arXiv:2401.01614](https://arxiv.org/abs/2401.01614) (ICML 2024) · [code](https://github.com/OSU-NLP-Group/SeeAct) · [project](https://osu-nlp-group.github.io/SeeAct/)
- AutoWebGLM — [arXiv:2404.03648](https://arxiv.org/abs/2404.03648) (KDD 2024) · [code](https://github.com/THUDM/AutoWebGLM)
- UI-TARS — [arXiv:2501.12326](https://arxiv.org/abs/2501.12326) · UI-TARS-2 [arXiv:2509.02544](https://arxiv.org/abs/2509.02544)
- OmniParser — [arXiv:2408.00203](https://arxiv.org/abs/2408.00203) · [microsoft.github.io/OmniParser](https://microsoft.github.io/OmniParser/)
- Agent Q (MultiOn) — [arXiv:2408.07199](https://arxiv.org/abs/2408.07199)

**Commercial / computer-use (primary docs):**
- Anthropic — [computer use docs](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool) · [memory tool docs](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/memory-tool) · [research blog](https://www.anthropic.com/research/developing-computer-use) · [reference impl](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)
- OpenAI — [Operator System Card](https://cdn.openai.com/operator_system_card.pdf) · [computer-use API docs](https://developers.openai.com/api/docs/guides/tools-computer-use)
- MultiOn — [docs.multion.ai](https://docs.multion.ai/learn/sessions)

**Benchmarks, surveys & analysis:**
- An Illusion of Progress? — [arXiv:2504.01382](https://arxiv.org/abs/2504.01382)
- Grounding-vs-Planning bottleneck — [arXiv:2409.01927](https://arxiv.org/abs/2409.01927)
- WebRL — [arXiv:2411.02337](https://arxiv.org/abs/2411.02337) (ICLR 2025)
- ScreenSpot-Pro — [arXiv:2504.07981](https://arxiv.org/abs/2504.07981)
- OSWorld — [arXiv:2404.07972](https://arxiv.org/abs/2404.07972) · OSWorld-Human — [arXiv:2506.16042](https://arxiv.org/abs/2506.16042)
- WebArena — [arXiv:2307.13854](https://arxiv.org/abs/2307.13854) · Mind2Web — [arXiv:2306.06070](https://arxiv.org/abs/2306.06070)
- AssistantBench (HAL leaderboard) — [hal.cs.princeton.edu/assistantbench](https://hal.cs.princeton.edu/assistantbench)
- Surveys: WebAgents [arXiv:2503.23350](https://arxiv.org/abs/2503.23350) (KDD 2025) · OS Agents [arXiv:2508.04482](https://arxiv.org/abs/2508.04482) (ACL 2025) · GUI Agents [arXiv:2412.13501](https://arxiv.org/abs/2412.13501) · Trustworthy GUI [arXiv:2503.23434](https://arxiv.org/abs/2503.23434)
- Security: Mind the Web [arXiv:2506.07153](https://arxiv.org/abs/2506.07153) · Hidden Dangers [arXiv:2505.13076](https://arxiv.org/abs/2505.13076)

**Excluded (fabricated / unverified):** llm-stats.com, benchlm.ai, awesomeagents.ai, codesota.com leaderboards — contain invented 2026 model entries.

---

## Confidence & Gaps

**Confidence:** HIGH on architecture/perception/action-space/loop/memory for all source-verified systems (browser-use, Stagehand, Agent-E, Anthropic, OpenAI, WebVoyager, SeeAct, AutoWebGLM). MEDIUM on benchmark numbers (vendor self-reports, incompatible protocols). Some 2026 arXiv IDs (e.g. 2602.x, 2604.x) are from the 2025–2026 research-agent sweep and individually unverified for exact dates.

**Top gaps:**
1. **No rigorous cross-framework benchmark** under a shared protocol — all comparisons stitch incompatible eval sets.
2. **Production internals of commercial systems** (OpenAI/Anthropic training, MultiOn production model) are closed; any "planner-executor/reflection-module" description of their internals is third-party inference.
3. **Self-healing locator robustness has no published drift benchmark** — the 2025–2026 self-correction work is promising but its real-world durability under live DOM churn is largely unmeasured.
