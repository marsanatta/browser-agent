# Self-Correction & Selector Self-Healing in Web/Browser Automation Agents

研究日期: 2026-06-22
來源數量: ~40 primary sources across 5 parallel research angles (arXiv papers, official docs, GitHub, engineering blogs)
信心程度: High for named papers and official docs (verified author/number-by-number); Medium for vendor self-reported metrics and single-source 2025-2026 mechanisms; future-dated arXiv IDs flagged inline

---

## TL;DR

Two reliability mechanisms, two distinct literatures that converge on the same architecture:

1. **Self-correction** (diagnose-and-replan) — the agent literature (Reflexion, Self-Refine, ReAct re-planning, Agent-E, AgentOccam) has matured into a layered model: *observe state change after every action → classify the failure → decide retry-vs-replan → verify before acting*. The dominant bottleneck is **low-level grounding**, not high-level planning. The hardest and least-measured problem is **silent failure** — the agent believes it succeeded but did not (22% actual vs 77% predicted success = a **55pp overconfidence gap**, arXiv:2602.06948).

2. **Self-maintenance** (selector self-healing) — the test-automation literature (Healenium, Erratum, Functionize, Stagehand, Healwright) converges on a **4-layer cascade**: deterministic priority chain (ARIA role/name → testid → text → CSS/XPath) → weighted attribute fingerprint matching → LLM re-ranking of a shortlist → vision fallback for canvas. The most stable locator across every source is **ARIA role + accessible name**, because it is a user-facing contract maintained for screen readers, not a DOM implementation detail.

The central warning from the most honest engineering post-mortems: self-healing has a **silent-drift failure mode** — the agent adapts to a UI change and now automates a *different flow* than intended, with CI green and no alarm raised. No current framework detects intent drift.

---

## PART 1 — SELF-CORRECTION (diagnose, then try a different strategy)

### 1.1 Foundational error-recovery loops

**Reflexion** — verbal self-critique stored in episodic memory.
[arXiv:2303.11366](https://arxiv.org/abs/2303.11366) (Shinn et al., NeurIPS 2023). After a failed episode the agent writes a verbal critique of the full trajectory, stores it in a memory buffer, and reads its own prior reflections before the next trial — a "semantic gradient" with no weight updates. This is the direct ancestor of browser-agent self-correction. Note the limitation (see §1.6): *intrinsic* self-correction without an independent ground-truth signal does not reliably improve reasoning errors, because the same model that erred also judges it.

**Self-Refine** — intra-task generate → critique → refine.
[arXiv:2303.17651](https://arxiv.org/abs/2303.17651) · [GitHub](https://github.com/madaan/self-refine) (Madaan et al., NeurIPS 2023). One LLM serves as generator, critic, and refiner in a tight loop *within a single task* (vs Reflexion's cross-episode memory). A browser agent applies this as: attempt action → evaluate outcome → reformulate the action description → re-execute, bounded by an iteration cap.

**ReAct re-planning, hierarchical.**
[arXiv:2603.14248](https://arxiv.org/abs/2603.14248) — "Why Do LLM-based Web Agents Fail? A Hierarchical Planning Perspective" (George Mason, 2026; title/authors verified, specific percentages UNVERIFIED). Decomposes agent behavior into high-level planning / low-level execution / replanning, and finds **low-level execution (grounding) is the dominant bottleneck**, not reasoning. Replanning is triggered only after a sub-goal fails multiple low-level execution attempts — this is the academic statement of the retry-vs-replan boundary.

### 1.2 Failure-cause classification

There is a gap between practitioner taxonomies and academic taxonomies — use both.

**Practitioner (Selenium/Playwright) error classes** — the concrete signals an agent can branch on:
- `NoSuchElementException` / "element not found" → selector resolution failure → trigger re-grounding/healing.
- "element not interactable" / `is_enabled()`/`is_visible()` false → element exists but is occluded/disabled/off-screen → wait, scroll, or dismiss an overlay (NOT re-ground).
- "wrong page" → page loaded successfully but is not the expected one → URL/state check failure → replan, not retry.
- timing / stale element → race with async render → state-based wait, then retry the *same* action.

**Academic taxonomies:**
- **AgentErrorTaxonomy** + **AgentErrorBench** + **AgentDebug** — [arXiv:2509.25370](https://arxiv.org/abs/2509.25370) "Where LLM Agents Fail and How They Can Learn From Failures." Five categories (memory / reflection / planning / action / system); names **cascading failure** as the primary mode; AgentDebug reports +24% all-correct and up to 26% relative task-success improvement. Best general-purpose taxonomy.
- **Agent-E change-observation** — [arXiv:2407.13032](https://arxiv.org/abs/2407.13032) (Abuelsaad/Vempaty et al., Emergence AI — NOT "Shrivastava"). Every action returns a *verbal state-change summary*. If a click produces **no meaningful DOM change**, the agent infers the action had no effect or hit the wrong element — classifying no-op vs wrong-element without explicit exception handling. WebVoyager 73.1% (vs prior text-only SOTA 52.6%). Flexible DOM distillation (three representations) resolves "element not found" by switching DOM-view granularity.

### 1.3 Retry-vs-replan decision

The principle from every source: **never retry blindly — every retry must be justified by a NEW observation.**

- **Local-first, escalate-on-exhaustion.** Try intra-context strategy switches (e.g., search-by-text instead of search-by-class; API → CLI → GUI) before escalating to a global replan. Browser-mappable from the cross-device H-RePlan structure: a failure event carries failed sub-task ID, categorized failure type, a log of local attempts with observations, and explicit escalation reasoning; only when same-context paths are exhausted does the orchestrator replan.
- **Idempotent retries only** ([Antigravity Lab](https://antigravitylab.net/en/articles/agents/antigravity-browser-agent-flaky-dom-timing)): exponential backoff (1s → 3s → 10s) with **human notification before retrying any side-effecting operation**. Distinguish read actions (safe to auto-retry) from write/submit actions (require confirmation).
- **Replan on page-discovery, not just failure** — when a newly loaded page reveals a previously-unknown filter/shortcut, replan the remaining decomposition rather than retry the original plan. This is the "wrong page" / "page changed under me" class.

### 1.4 Grounding / verification before acting

The highest-ROI prevention lever is **observation alignment** — clean the observation *before* the LLM acts, so it never needs to recover.

**AgentOccam** — [arXiv:2410.13825](https://arxiv.org/abs/2410.13825) (AWS). Three purely-mechanical fixes, **no extra LLM calls**: (1) merge co-labeled interactive elements, render tables/lists as Markdown; (2) selective history replay — keep only pivotal nodes + ancestors/siblings; (3) plan-based memory filtering. Adds explicit `branch`/`prune` actions for lightweight in-task reroute. **WebArena 43.1%** zero-shot (vs SteP 33.3%, AWM 35.5%, baseline 16.5%) — i.e. just aligning the observation beats most fancier agents. This is the cheapest, most robust thing to implement.

**Precondition validation before execution** — UFO2 [arXiv:2504.14603](https://arxiv.org/html/2504.14603v1) (Microsoft). Before each action, consult the accessibility API to verify `is_enabled()` / `is_visible()`. On failure, halt and return partial results to trigger replanning — preventing cascading errors. Three-class error taxonomy with class-specific recovery: plan errors → knowledge integration; execution errors → API fallbacks; control-detection failures → hybrid vision/UIA detection.

**Verify-before-act via world model** — predict the hypothetical next page state, score it ("will fail / partial / succeed"), and only execute above a confidence threshold; otherwise regenerate an alternative action. (World-model-augmented action-correction line, 2026; single-source, verify before relying.)

**Predict-effect → diff → re-ground** (the best validated mid-task self-correction pattern): after acting, compare the actual screen/DOM against the predicted effect. On NO_CHANGE, diagnose and re-ground. Closest *verified* browser-agent prior art: **Multimodal Auto-Validation for Self-Refinement** [arXiv:2410.00689](https://arxiv.org/abs/2410.00689) (built on Agent-E) — text+vision validator → critical feedback → retry, **WebVoyager 76.2% → 81.24%**. Single-source 2025-2026 variants worth tracking (verify IDs before citing): comparative re-selection among ≤5 candidates ([arXiv:2509.14382], reports 20.3% of failures are duplicate-element), SSIM/no-change detection for failed actions.

### 1.5 Silent-failure detection (the under-measured frontier)

This is the axis most relevant to a grading rubric that penalizes over-reporting.

- **The benchmarks don't test it.** WebArena ([2307.13854](https://arxiv.org/abs/2307.13854)), Mind2Web ([2306.06070](https://arxiv.org/abs/2306.06070)), WebVoyager ([2401.13919](https://arxiv.org/abs/2401.13919)), VisualWebArena ([2401.13649](https://arxiv.org/abs/2401.13649)) all measure **final-state success only**. None test mid-task recovery, wrong-track self-detection, or distinguish "task failed" from "agent didn't know it failed." WebArena's own analysis names "failure recovery" as the capability gap but does not measure it.
- **Overconfidence is large and measurable.** [arXiv:2602.06948](https://arxiv.org/abs/2602.06948) — agents succeeding 22% of the time predict 77% success (**55pp gap**). Counterintuitively, *pre-execution* assessment discriminates better than post-execution review, and an adversarial "find the bug" framing gives the best calibration. Design hint: ask the agent to argue why it *failed* before it self-reports success.
- **Named detection method.** [arXiv:2511.04032](https://arxiv.org/abs/2511.04032) "Detecting Silent Failures in Multi-Agentic AI Trajectories" (IBM, Pathak et al., Nov 2025; verified). Anomaly detection over trajectories targeting drift / cycles / missing-details (none raise an error). Supervised up to 98%, semi-supervised SVDD 96%. Post-hoc audit, not real-time.
- **Transplantable metric: Completion Under Policy (CuP).** [arXiv:2410.06703](https://arxiv.org/abs/2410.06703) ST-WebAgentBench (IBM, Levy et al.; verified). CuP "credits only completions that respect all applicable policies." Across three SOTA agents, **average CuP < 2/3 of nominal completion** → more than a third of "completed" tasks are silent violations. For an eval harness: report nominal completion AND verified completion; the delta is your silent-failure rate.

### 1.6 The intrinsic-correction caveat (load-bearing)

Self-correction reliability depends on whether the error signal is **independent** of the model that produced the error. Intrinsic verbal self-critique (Reflexion-style) does NOT reliably fix reasoning errors. Execution-grounded signals (DOM diff, URL change, network-request completion, accessibility-precondition checks) are independent and far more reliable. **Conclusion: ground the correction signal in observable browser state, not in the LLM's own self-assessment.**

---

## PART 2 — SELF-MAINTENANCE (detect UI change, adapt the locator)

### 2.1 Robust locator strategies (prevention first)

Every credible primary source converges on the same priority order. Source of truth: [Playwright Locators docs](https://playwright.dev/docs/locators) and [Testing Library — About Queries](https://testing-library.com/docs/queries/about/).

Playwright's documented priority (verbatim ordering):
1. `getByRole()` — "the closest way to how users and assistive technology perceive the page"
2. `getByText()`
3. `getByLabel()` — "use when locating form fields"
4. `getByPlaceholder()`
5. `getByAltText()`
6. `getByTitle()`
7. `getByTestId()`

CSS/XPath are explicitly discouraged: *"XPath and CSS selectors can be tied to the DOM structure or implementation. These selectors can break when the DOM structure changes."* `getByRole` "follow[s] W3C specifications for ARIA role, ARIA attributes and accessible name" ([accname computation spec](https://www.w3.org/TR/accname-1.1/)).

**Why ARIA role + accessible name is the most stable:** roles and accessible names are a **user-facing contract** (screen readers depend on them; developers rarely break them silently), while CSS classes and DOM positions are implementation details that churn on every refactor. Canonical example ([Argos CI](https://argos-ci.com/blog/playwright-locators)): brittle `div > button:nth-child(2)` vs resilient `getByRole("button", { name: "Sign in" })`.

**Testing Library philosophy:** tests should "resemble how users interact with your code." `getByTestId` is a last-resort escape hatch — "the user cannot see (or hear) these." When `getByRole` fails and you reach for `getByTestId`, that often signals an accessibility gap, not a testing limitation.

**Relative/chained locators** — the durable pattern is scoping a semantic locator inside a stable container: `page.locator('app-form').getByRole('button', { name: 'Submit' })`, or `filter({ has, hasText })` to disambiguate. **Important:** Playwright's layout pseudo-classes (`:near()`, etc.) are explicitly marked **deprecated** in [Other Locators](https://playwright.dev/docs/other-locators) — do not use for new code.

**Text locators are middle-tier:** more stable than CSS (text is user-visible, product-owned) but volatile under i18n / A/B copy edits / responsive truncation. Best combined with role so both must change to break the locator. Use standalone `getByText` only for non-interactive nodes (div/span/p) that lack a role.

**ARIA snapshots** — [Playwright aria-snapshots](https://playwright.dev/docs/aria-snapshots) serialize the accessibility tree as YAML (`- role "name" [attr=value]`) for semantic-level regression; breaks only when semantic structure changes, not on style/nesting changes.

**Locator-strategy stability ladder:**

| Strategy | Stability | A11y-aligned | When to use |
|---|---|---|---|
| `getByRole` + accessible name | Highest | Direct (W3C ARIA) | Interactive elements with roles |
| `getByLabel` | High | High | Form inputs |
| `getByText` + role | High | Medium | Stable labeled text |
| `getByTestId` | Med-High | None (invisible) | No semantic fallback (icon-only buttons, dynamic content) |
| `getByText` standalone | Medium | Low | Non-interactive text nodes |
| `getByPlaceholder` | Medium | Low | Inputs lacking labels |
| CSS | Low | None | Last resort |
| XPath | Lowest | None | Avoid |
| `:near()` / layout | Deprecated | None | Do not use |

### 2.2 Self-healing locator tools — how they actually work

**Healenium** (open-source Selenium proxy) — [GitHub](https://github.com/healenium/healenium-web) · [docs](https://healenium.io/docs/how_healenium_works). Wraps `WebDriver` with a `SelfHealingDriver`. On `NoSuchElementException` it intercepts, fetches the current DOM, and scores every element against a stored fingerprint using **LCS (Longest Common Subsequence)** over the DOM path plus weighted multi-attribute similarity (attribute similarity, element stability/position, locator specificity, neighbor context). The best score above the `score-cap` threshold (default 0.5) becomes the healed locator; it is used for the run and written back to a PostgreSQL history for future heals. (Exact weight coefficients reported in secondary sources, not independently verified against source.)

**Erratum** — [arXiv:2106.04916](https://arxiv.org/abs/2106.04916) (Brisset, Rouvoy, Seinturier, Pawlak; verified). The canonical academic DOM-diff repair: **tree-matching between old and new DOM snapshots** narrows the search space, then repairs the broken locator by finding the structurally equivalent node. **67% accuracy improvement over WATER** (prior SOTA). Distinction vs Healenium: Erratum needs *both* snapshots (tree alignment); Healenium needs only a stored fingerprint vs the current DOM (simpler to deploy).

**Functionize** — [self-healing page](https://www.functionize.com/automated-testing/self-healing-test-automation). Captures a "rich fingerprint" at record time (id, label, visible text, class, position, context); on failure an ML engine recalibrates against the live DOM using a **DOM-attributes + visual-cues hybrid**, with computer vision covering canvas-rendered UIs where DOM fingerprinting fails. Vendor self-reported 99.97% element accuracy / 80% flakiness reduction (UNVERIFIED — no independent benchmark).

**Mabl / Testim (Tricentis)** — element fingerprints with multi-attribute scoring; distinguishing claim is **cross-customer aggregate model training** (learning which attribute combinations are most stable across the app population). No peer-reviewed architecture published; mechanism is from marketing docs (UNVERIFIED at the algorithmic level).

**Microsoft Power Automate self-healing agent** (GA March 2026) — [release notes](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave2/power-automate/self-healing-agent-uiweb-automation-desktop-flows). Enterprise pattern: **opt-in per-action**. When a UI action fails to find its configured element, an AI agent proposes a replacement element — human-opt-in rather than autonomous, an explicit acknowledgment of silent-drift risk.

### 2.3 ML / embedding-based element re-identification

**VON Similo + GPT-4** — [arXiv:2310.02046](https://arxiv.org/abs/2310.02046) (Leotta et al.). LLM as a **re-ranking filter, not a primary scanner**: the cheap attribute-similarity method (VON Similo) produces a ranked shortlist of candidates, then GPT-4 re-ranks using contextual reasoning. Failed localizations dropped from 70 → 39 (~44%) on an 804-pair, 48-app benchmark. This is the cost-efficient pattern — heuristic shortlist first, LLM only on the ambiguous tail.

(EmbedRank-LM, an NL-driven embedding-similarity element-ID approach claimed for late 2025, could not be read — ResearchGate 403, abstract-only. UNVERIFIED.)

### 2.4 Zero-cost accessibility-tree healing (no LLM)

[arXiv:2603.20358](https://arxiv.org/abs/2603.20358) "Beyond LLM-based test automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction" (Renjith Nelson Joseph, March 2026; verified). Proposes a **10-tier priority-ranked hierarchy** extracted deterministically from the accessibility tree with no LLM calls: ARIA role+name → role only → data-testid → id → aria-label (exact) → aria-label (contains) → href fragment → CSS class (exact) → CSS class (contains) → visible text. On failure a `SmartFind` module invalidates only the broken entry and re-extracts that single element (not the whole page). Reported: 100% pass (31/31 on automationexercise.com), sub-1s re-discovery, **$0.00/run** vs a Browser-Use + Claude baseline of ~$0.30/run (~$1,350/month at scale). Caveat: single-site benchmark, controlled suite — promising, not broadly validated. [GitHub](https://github.com/Renjithnj/zero-cost-self-healing-qa).

### 2.5 How LLM-native browser agents re-locate when the DOM changes

The frameworks converge on a **3-level hierarchy** and differ mainly in where they draw the layer boundary and how aggressively they cache.

**Stagehand (Browserbase)** — [v3 blog](https://www.browserbase.com/blog/stagehand-v3) · [GitHub](https://github.com/browserbase/stagehand). The most explicitly documented hierarchy:
- L1 deterministic: every `act()` runs cached Playwright first — *"Replay will default to Playwright first to avoid unnecessary LLM calls. If the Playwright action fails, Stagehand AI will take over and self-heal."*
- L2 re-ground via **accessibility tree** (filters DOM noise) using semantic role/label, not CSS.
- L3 full-agent reassessment — review what happened and re-plan toward the goal in current context.
- Caching: discovered elements/actions cached for reuse with no extra LLM cost; invalidated on page-change detection. **Intent preservation**: `act("click the submit button")` encodes intent, surviving redesigns.

**browser-use** (Python) — LLM-centric, less caching. On not-found the LLM "rethinks the selector strategy" (e.g., search by text instead of class) and can replan multiple times; re-queries the LLM with current page state on each failure (more adaptive, higher cost). Practitioner rule: "never retry blindly — every retry must be justified by a NEW UI observation." Known failure: LLM API errors can hang rather than fail-fast ([issue #1497](https://github.com/browser-use/browser-use/issues/1497)); use exponential backoff with fail-fast.

**Playwright + LLM healing (Healwright pattern)** — [writeup](https://medium.com/@Amr.sa/healwright-let-your-playwright-tests-heal-their-own-selectors-on-the-fly-d0178568f9bc). On selector throw: pause → send a **compact DOM candidate (minimal JSON, not raw HTML)** + human-language element description to the LLM acting as "locator expert" → re-inject the new locator into the failed step (no test restart) → cache the validated locator in two layers (in-memory + persistent) so the LLM is only re-invoked on cache miss. Reported MCP-pattern healing success ~65%; ~35% need human intervention; fails on iframe/shadow-DOM/WebSocket state.

**Vision-first prevention** — Magnitude and OmniParser-style systems output **x/y pixel coordinates** rather than DOM selectors, so a moved button is re-located visually by design (prevention, not reactive healing). OmniParser v2 ([Microsoft Research](https://www.microsoft.com/en-us/research/articles/omniparser-v2-turning-any-llm-into-a-computer-use-agent/)) = YOLO-v8 detector + fine-tuned Florence-2; OmniParser+GPT-4o reaches 39.6% on ScreenSpot-Pro vs GPT-4o bare 0.8%. Trade-off: vision tokens are expensive and grounding still has a real gap (SeeAct [arXiv:2401.01614](https://arxiv.org/html/2401.01614v1) documents a persistent 20-25% gap vs oracle grounding, with hallucinated boxes and duplicate-element confusion and **no automated recovery**).

**Set-of-Marks grounding is single-shot.** VisualWebArena ([arXiv:2401.13649](https://arxiv.org/abs/2401.13649)) labels interactables with boxed integer IDs; a wrong pick triggers **nothing built-in** — "failure to do visual grounding is a common failure mode." Recovery is a separate, newer line layered on top (predict-effect → diff → re-ground). SoM *helps* when box geometry is exact (VWA's JS-injected boxes) and *hurts* when boxes are dense/occluding (SeeAct on Mind2Web); discriminator is box quality (OmniParser jumps 16.2% → 73.0% ScreenSpot with UI-aware detection, [arXiv:2408.00203](https://arxiv.org/abs/2408.00203)).

### 2.6 The silent-drift failure mode (read before shipping any healer)

[Bug0 (2026)](https://bug0.com/blog/ai-testing-browser-agent-tools-wont-fix-qa-2026): *"Healed tests can silently drift from original intent. The agent adapted to a UI change, but it's now testing a different flow than what you designed."* CI is green, the automation validates wrong behavior; LLM-generated test validity drops ~25% on complex scenarios. Plus non-determinism flakiness (same UI, different runs) and structural blind spots (MFA, iframes, shadow DOM, WebSocket, overlapping modals) that locator healing cannot fix.

[Antigravity Lab](https://antigravitylab.net/en/articles/agents/antigravity-browser-agent-flaky-dom-timing) prescriptions: semantic anchoring with **explicit negative constraints** ("what NOT to click"); **state-based waiting** ("wait until URL is /dashboard AND element X visible AND spinner gone") over fixed timeouts; idempotent-only retries; full observability (snapshot the prompt, model version, screenshot, and failure classification on every run).

**The unresolved frontier:** no framework detects *intent drift* — a healed locator that successfully clicks the *wrong* element for the original task. Detecting that requires a goal-level verifier (predicted-effect diff, CuP-style policy check), not a better locator.

---

## Cross-Cutting Synthesis: the architecture both literatures point to

1. **Keep the LLM out of the hot path.** Deterministic/cached/rule-based execution first; invoke the LLM only on failure. (Stagehand, Healwright, AgentOccam, arXiv:2603.20358.)
2. **Align/clean the observation before acting** — biggest cheap robustness win (AgentOccam: +27pp on WebArena from observation alignment alone).
3. **Classify the failure before responding** — not-found → re-ground; not-interactable → wait/scroll/dismiss; wrong-page → replan; stale/timing → state-wait then retry same action.
4. **Locator cascade, semantic-first**: ARIA role+name → testid → text → (heuristic fingerprint) → (LLM re-rank shortlist) → (vision).
5. **Ground the correction signal in observable browser state**, never in the LLM's self-assessment (DOM diff, URL change, network completion, a11y preconditions).
6. **Retry only on a new observation; confirm before side-effecting retries**; escalate retry → local strategy switch → global replan only on exhaustion.
7. **Measure silent failure explicitly** — report nominal vs verified completion (CuP-style); the gap is the headline reliability number.

---

## Risks, Contradictions & Gaps

- **getByTestId ranking disagreement.** Playwright/Testing Library rank testid *last* (invisible to users); some practitioner guides (BrowserStack) rank data-testid #2 (immune to copy/i18n). Both true from different axes; treat testid as a deliberate escape hatch.
- **Neither WebRL nor Agent Q uses classical reward shaping** (outcome-curriculum and MCTS-critique-DPO respectively) — relevant only if RL training is in scope; not needed for an inference-time harness.
- **Vendor metrics unverified** (Functionize 99.97%, Magnitude WebVoyager 94%, MCP healing 65%) — vendor/blog self-reported, no independent benchmark.
- **Future-dated arXiv IDs verified where load-bearing** (2603.20358, 2511.04032, 2410.06703, 2106.04916, 2602.06948 all fetched and confirmed). Single-source 2025-2026 recovery-mechanism papers (2604.05477, 2505.20660, 2506.08012, 2602.13559, 2509.14382) are RECENT/single-source — verify before citing in deliverables.
- **Refuted, do NOT cite:** Agent-E does not introduce a "self-aware vs oblivious failure" taxonomy (search-layer fabrication). Use ST-WebAgentBench's CuP for a real verified-vs-nominal metric. Agent-E author is Emergence AI team, not "Shrivastava." STeP = "Stacked LLM Policies," not "Scaffolded Training."
- **Gaps:** no quantitative real-world ARIA-vs-CSS locator failure-rate study found; no framework detects intent drift; EmbedRank-LM unreadable (ResearchGate 403).

---

## Primary Sources

Self-correction: [Reflexion 2303.11366](https://arxiv.org/abs/2303.11366) · [Self-Refine 2303.17651](https://arxiv.org/abs/2303.17651) · [Agent-E 2407.13032](https://arxiv.org/abs/2407.13032) · [AgentOccam 2410.13825](https://arxiv.org/abs/2410.13825) · [Hierarchical Planning 2603.14248](https://arxiv.org/abs/2603.14248) · [AgentErrorTaxonomy 2509.25370](https://arxiv.org/abs/2509.25370) · [UFO2 2504.14603](https://arxiv.org/html/2504.14603v1) · [Multimodal Auto-Validation 2410.00689](https://arxiv.org/abs/2410.00689)

Silent failure / calibration: [Silent-Failure Detection 2511.04032](https://arxiv.org/abs/2511.04032) · [Agentic Overconfidence 2602.06948](https://arxiv.org/abs/2602.06948) · [ST-WebAgentBench / CuP 2410.06703](https://arxiv.org/abs/2410.06703)

Benchmarks: [WebArena 2307.13854](https://arxiv.org/abs/2307.13854) · [Mind2Web 2306.06070](https://arxiv.org/abs/2306.06070) · [WebVoyager 2401.13919](https://arxiv.org/abs/2401.13919) · [VisualWebArena 2401.13649](https://arxiv.org/abs/2401.13649) · [SeeAct 2401.01614](https://arxiv.org/html/2401.01614v1) · [OmniParser 2408.00203](https://arxiv.org/abs/2408.00203)

Locators / healing: [Playwright Locators](https://playwright.dev/docs/locators) · [Playwright Other Locators](https://playwright.dev/docs/other-locators) · [Playwright ARIA Snapshots](https://playwright.dev/docs/aria-snapshots) · [Testing Library Queries](https://testing-library.com/docs/queries/about/) · [Healenium](https://github.com/healenium/healenium-web) · [Healenium docs](https://healenium.io/docs/how_healenium_works) · [Erratum 2106.04916](https://arxiv.org/abs/2106.04916) · [VON Similo + GPT-4 2310.02046](https://arxiv.org/abs/2310.02046) · [Zero-Cost a11y Healing 2603.20358](https://arxiv.org/abs/2603.20358) · [Functionize](https://www.functionize.com/automated-testing/self-healing-test-automation) · [MS Power Automate Self-Healing](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave2/power-automate/self-healing-agent-uiweb-automation-desktop-flows)

LLM-native frameworks: [Stagehand v3](https://www.browserbase.com/blog/stagehand-v3) · [Stagehand GitHub](https://github.com/browserbase/stagehand) · [Healwright pattern](https://medium.com/@Amr.sa/healwright-let-your-playwright-tests-heal-their-own-selectors-on-the-fly-d0178568f9bc) · [OmniParser v2](https://www.microsoft.com/en-us/research/articles/omniparser-v2-turning-any-llm-into-a-computer-use-agent/) · [Bug0 post-mortem](https://bug0.com/blog/ai-testing-browser-agent-tools-wont-fix-qa-2026) · [Antigravity Lab DOM drift](https://antigravitylab.net/en/articles/agents/antigravity-browser-agent-flaky-dom-timing)
