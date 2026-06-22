# Browser Infrastructure & Model Selection for a Public LLM Browser-Automation Agent

**研究日期 (Research date):** 2026-06-22
**來源數量 (Sources):** ~35 primary/secondary URLs (vendor pricing pages, HAL/AssistantBench leaderboard, arXiv, security blogs)
**信心程度 (Confidence):** Medium-High. Vendor pricing fetched live (June 2026) and is authoritative-for-now. Model-cost data has **two conflicting primary sources** (flagged below). Self-hosted resource footprint is synthesized from production blogs, not a controlled benchmark.

> Scope note: this fills the **runtime/deploy substrate** gap. The agent's reliability architecture (perception, self-healing locators, eval, calibration) is assumed already grounded elsewhere. This document is about *where the browser runs*, *what breaks in the real world*, *which model drives the loop*, and *how it scales*.

---

## TL;DR

1. **Browser runtime:** Build on **self-hosted Playwright/Chromium** as the default substrate, but design the browser layer behind an interface so a hosted platform (**Steel.dev** self-host first, **Browserbase** for managed stealth) can be swapped in for anti-bot-heavy tasks. Self-host wins below ~5K tasks/mo on raw cost; hosted wins when *stealth patch-cycle maintenance* and *CAPTCHA* would otherwise be your job.
2. **Anti-bot reality:** No stealth tool reliably beats **Cloudflare Turnstile, DataDome intent-detection, or PerimeterX** by evasion. The 2026 frontier is *recognition* (Cloudflare Web Bot Auth / Signed Agents), not evasion. Plan for a meaningful fraction of the open web to be **effectively unreachable** without credentials or partner whitelisting.
3. **Auth = security liability:** Cookie/session injection is operationally standard but hands the agent an **unscoped, full-session credential** with no audit trail, vulnerable to prompt-injection exfiltration. Banking / corporate SSO / healthcare are **off-limits** for autonomous operation. Treat all captured session state as secrets.
4. **Model selection:** The two best public datasets **disagree**. On **AssistantBench (HAL, primary-verified)**, OpenAI reasoning models dominate cost-efficiency (**o4-mini Low ≈ $0.043/task, o3 Medium ≈ $0.071/task**) and Claude is poor value. On **Browser-Use's own vendor benchmark**, Claude leads on accuracy but at high cost. Both agree: **frontier models cost $0.20–$6/task; a tiered/cascade strategy is the only path to <$0.10/task.**
5. **Scaling:** One ephemeral browser per task, stateless workers, queue-driven (BullMQ/Redis or Temporal for durability), ~**300–500 MB RAM per active headless Chromium**, ~2–4 instances/GB, ~1 vCPU per 2–3 instances. **LLM cost dominates browser cost by >10:1** — optimize the model loop, not the browser fleet.

---

## Research Plan (subquestions)

1. What are the hosted browser-platform options, their features, and current pricing? (Browserbase, Steel, Hyperbrowser, Browserless)
2. When does self-hosting Playwright/Chromium beat a hosted platform?
3. What anti-bot / CAPTCHA / login realities break real-world automation, and which task types are unsupported without credentials?
4. How do agents handle auth, and what is the security implication of capturing cookies/session state?
5. Which LLMs drive browser agents in 2025-2026, and what is the cost/latency/capability tradeoff?
6. What do tiered/escalation routing strategies save, and what are real $/task figures?
7. How does this scale — concurrency, statelessness, queueing, resource footprint, cost-per-task at scale?

---

## 1. Browser Runtime Options

### 1.1 Hosted platform comparison (pricing fetched live, June 2026)

| Platform | License / self-host | Entry paid | Mid tier | Stealth | CAPTCHA | Proxy | Session persistence |
|---|---|---|---|---|---|---|---|
| **Browserbase** | Closed SaaS | $20/mo Developer (25 concurrent, 100 hr) | $99/mo Startup (100 concurrent, 500 hr) | Basic (UA spoof) → **Advanced custom Chromium on Scale only** | Included (basic; solves simple visual) | 1 GB ($12/GB) → 5 GB ($10/GB) | Yes; 7-day (Dev) / 30-day (paid) storage |
| **Steel.dev** | **Apache-2.0, fully self-hostable** | $29/mo Starter (10 concurrent, 290 hr, 7.2K CAPTCHA) | $99/mo Developer (20 concurrent, 1,238 hr, 28K CAPTCHA) | Built-in | Bundled in credits (~$3–4/1K solves) | $5–10/GB | Up to 24h sessions |
| **Hyperbrowser** | Closed SaaS | Pure PAYG (1 credit = $0.001) | — | "Ultra stealth" (WebGL/Canvas/Audio/UA spoof) | Included (rate unspecified) | $10/GB | Yes |
| **Browserless** | **OSS Docker (non-commercial free; enterprise license for prod self-host)** | $25/mo Prototyping (15 concurrent, 20K units) | $140/mo Starter (40 concurrent, 180K units) | Limited vs Browserbase | 10 units/solve (~$0.007–0.01) | Residential 6 units/MB; datacenter 2 units/MB | Up to 60-min sessions |

**Unit definitions (critical for cost math):**
- Browserbase / Steel: billed **per browser-hour** (per-minute granularity, first minute rounded up). Steel overage $0.05–0.10/hr; Browserbase $0.10–0.12/hr.
- Browserless: **1 unit = 30 seconds of browser time**; overage ~$0.0015–0.0020/unit ≈ ~$0.18–0.24/browser-hour. Most expensive per-hour but flexible.
- Hyperbrowser AI-agent step: **$0.02/step** (20 credits); browser session **$0.10/hr**.

**Pricing sources (fetched June 2026):**
- [browserbase.com/pricing](https://www.browserbase.com/pricing) · [docs.browserbase.com/guides/concurrency-rate-limits](https://docs.browserbase.com/guides/concurrency-rate-limits)
- [docs.steel.dev/overview/pricinglimits](https://docs.steel.dev/overview/pricinglimits) · [steel.dev/pricing](https://steel.dev/pricing)
- [hyperbrowser.ai/docs/reference/pricing](https://hyperbrowser.ai/docs/reference/pricing)
- [browserless.io/pricing](https://www.browserless.io/pricing)

> ⚠️ **Stale-pricing risk:** A Nov 2025 third-party (Skyvern) comparison listed different Browserbase tier names (Starter $39 / Professional $99) and a Hyperbrowser "$30/mo / 30K credits / 25 concurrent" subscription that the **current** pricing pages do **not** show. Treat the live-fetched June-2026 numbers above as authoritative and re-verify before committing budget. Hyperbrowser's subscription-tier claim is **[UNVERIFIED]** — only PAYG rates were confirmed on the live page.

### 1.2 Self-hosted Playwright/Chromium

- **What you build yourself:** stealth/fingerprint patching, CAPTCHA integration (e.g. CapSolver/2Captcha), proxy rotation, session storage, crash recovery, autoscaling.
- **Resource footprint** (synthesized from production blogs — *not* a controlled benchmark, flag as directional):
  - Bare launch (no page): ~150 MB RSS. Single active page: ~250 MB. Production planning rule: **300–500 MB/concurrent session**.
  - Memory grows ~1.5 GB over 8h without restart (no reclaim) → **recycle browsers periodically**. Pathological pages (8K screenshots, heavy video) can hit 2 GB.
  - CPU: 10–50% of one core when active. Allocate **1 core per 2–3 instances** (1:1 for JS-heavy sites).
  - **Docker gotcha:** default `/dev/shm` is 64 MB; Chromium needs more or it crashes silently. Set `--shm-size=2g` or `--ipc=host`, and `--disable-dev-shm-usage`.
- Sources: [rendershot.io/blog/headless-chromium-fleet-memory](https://rendershot.io/blog/headless-chromium-fleet-memory), [datawookie.dev playwright footprint](https://datawookie.dev/blog/2025-06-06-playwright-browser-footprint/), [bug0.com/knowledge-base/playwright-docker](https://bug0.com/knowledge-base/playwright-docker), [github.com/microsoft/playwright#38489](https://github.com/microsoft/playwright/issues/38489)

### 1.3 When self-hosting wins vs hosted

| Criterion | Self-hosted Playwright/K8s | Hosted (Browserbase/Steel cloud) |
|---|---|---|
| Stealth/fingerprint maintenance | **You** chase the patch cycle | Vendor-managed |
| CAPTCHA solving | DIY integration | Built-in |
| Proxy rotation | DIY | Included (metered) |
| Session persistence | Full control | Plan-gated (15 min – 24h) |
| Concurrency ceiling | Unlimited (your $$) | Hard plan cap |
| Cold-start latency | ~1–3s | ~1–3s (warm pool) |
| Ops burden | High | Low |
| **Break-even** | **>~10K tasks/mo** | **<~5K tasks/mo** |

**Steel.dev is the strategic middle:** Apache-2.0 means you can self-host the *exact same* browser sandbox you'd otherwise rent, then lift-and-shift to their cloud under load spikes. Steel/Browserless are infra-only (no agent loop) and slot *under* a framework like Stagehand or browser-use, replacing Browserbase cloud. ([steel-dev/steel-browser](https://github.com/steel-dev/steel-browser))

---

## 2. Anti-Bot / CAPTCHA / Login Reality

### 2.1 What detects bots (defense-in-depth, hardest layers first)

| Layer | Signal | Patchable by JS stealth? |
|---|---|---|
| **Network / TLS** | JA3/JA4 TLS-handshake fingerprint; HTTP/2 SETTINGS/PRIORITY frames; IP reputation | **No** — evaluated server-side before any JS runs |
| **Automation protocol** | CDP/Playwright driver fingerprint (the *mechanism* of driving the browser) | **No** — only by removing the Playwright shim (see nodriver) |
| **JS / DOM** | `navigator.webdriver`, missing plugins, UA-vs-Client-Hints mismatch, WebGL `SwiftShader`, canvas anomalies, missing `chrome.*` objects | Partially |
| **Behavioral** | Mouse trajectory, scroll/click timing, navigation-sequence stats (DataDome added *intent* detection in 2025) | Hard to fake convincingly |

Sources: [Cloudflare bot-detection-engines](https://developers.cloudflare.com/bots/concepts/bot-detection-engines/), [browserless.io TLS fingerprinting](https://www.browserless.io/blog/tls-fingerprinting-explanation-detection-and-bypassing-it-in-playwright-and-puppeteer), [scrapfly.io playwright stealth](https://scrapfly.io/blog/posts/playwright-stealth-bypass-bot-detection)

### 2.2 Stealth tooling landscape (2026 anti-detect benchmark, 31 targets)

| Tool | Base | Result | Note |
|---|---|---|---|
| **nodriver** | Chrome raw CDP (no Playwright shim) | **28/31 pass, 0 blocked** | Benchmark winner — eliminates automation-protocol fingerprint; but loses Playwright's rich API |
| CloakBrowser | Chromium fork (49 C++ mods) | 26/31 | Engine-level |
| Patchright | Chromium/Playwright | 25/31 | CDP-leak patches |
| Camoufox | Firefox fork | 25/31 | Engine-level spoof; had a 2025 maintenance gap |
| Vanilla Playwright | Chromium | 24/31 (baseline) | MS-maintained |
| **rebrowser-playwright** | Chromium/Playwright | 24/31 | **DEAD — unmaintained since Sept 2024; do not use** |
| playwright-stealth (Node) | Chromium/Playwright | fails PerimeterX/DataDome | **Unmaintained since 2023** |

Key takeaway: **the winning technique is removing the automation protocol, not better JS evasion.** ([ianlpaterson.com anti-detect benchmark](https://ianlpaterson.com/blog/anti-detect-browser-benchmark-patchright-nodriver-curl-cffi/))

**Browserbase's differentiator:** rather than evade, it joins **Cloudflare's Web Bot Auth / Signed Agents** program so sessions are *recognized as legitimate* (Scale plan only). ([docs.browserbase.com/features/stealth-mode](https://docs.browserbase.com/features/stealth-mode)) This is the only durable path against Turnstile.

### 2.3 CAPTCHA solve reality

| Type | Automated solve | Note |
|---|---|---|
| reCAPTCHA v2 image | ~95%+ | Well solved (CapSolver, 2Captcha) |
| hCaptcha image | ~90%+ | AI solvers + human fallback |
| FunCaptcha / Arkose | Moderate | Varies |
| **reCAPTCHA v3 (score)** | **Effectively unsolvable via API** | Score depends on behavioral reputation — cold sessions score low regardless of solver |
| **Cloudflare Turnstile** | **Partial/unreliable** | Behavioral; needs valid TLS + warmed session or partner whitelist |
| Cloudflare JS challenge (PoW) | Hard | Needs valid TLS fingerprint + JS execution; can't be API-solved |

Solver pricing snapshot (2025-2026, exact figures **[UNVERIFIED]**): 2Captcha ~$0.85–1.00/1K reCAPTCHA v2; CapSolver AI-first; AntiCaptcha human-worker. ([2captcha.com](https://2captcha.com/), [capsolver.com](https://www.capsolver.com/))

### 2.4 Task types effectively unsupported without credentials

- **Definitively blocked without pre-injected auth:** banking/financial (MFA + session-bound tokens), corporate SSO (SAML/OIDC/Kerberos ambient auth), government identity portals, healthcare portals (device-fingerprinted).
- **Partially blocked:** e-commerce checkout (login wall), social posting/DM (login required; viewing often open), SaaS dashboards (auth-gated data).

### 2.5 How agents handle auth — and the security implication

**Mechanisms:** (1) cookie injection (`document.cookie` / CDP `Network.setCookies`); (2) persistent context via Playwright `storageState` (cookies + localStorage) — the standard; (3) credential replay (breaks on MFA/SSO/passkeys); (4) emerging **OAuth delegated-scope** flows (the *correct* future approach — [workos.com logging-ai-agents-into-web-apps](https://workos.com/blog/logging-ai-agents-into-web-apps)).

**Security implications (CRITICAL — this is the deployment risk):**
- **Unscoped full-session access:** cookie auth gives the agent the entire user session, no permission scoping, no audit trail separating agent vs user actions. ([lyrie.ai agentic-browser-gap](https://lyrie.ai/research/research/2026-04-27-agentic-browser-gap))
- **Pass-the-cookie bypasses MFA** entirely; stolen session tokens stay valid for months. **94 billion browser cookies were exfiltrated by infostealers in 2025**; "Cookie-Bite" (Apr 2025) stole Entra ID session cookies bypassing MFA. ([gbhackers pass-the-cookie](https://gbhackers.com/new-pass-the-cookie-attacks-bypass-mfa/), [brandefense.io])
- **Prompt injection → exfiltration:** a malicious page can instruct the LLM to forward cookies or take destructive actions within the user's auth context. OpenAI/CISA call prompt injection "a frontier, unsolved problem." ([wiz.io agentic-browser-security-2025](https://www.wiz.io/blog/agentic-browser-security-2025-year-end-review), [arXiv:2505.13076](https://arxiv.org/pdf/2505.13076))
- **CDP leaks** raw headers including `Authorization: Bearer` to any process with CDP access.

**Operational mitigations:** ephemeral isolated browser profile **per task/per user** (no cookie cross-contamination); never persist cookies unencrypted; prefer OAuth delegated tokens over full session cookies; log agent actions separately at the app layer; never log page content/screenshots/localStorage/auth headers. (Consistent with this repo's CLAUDE.md secrets rules.)

---

## 3. Model Selection for the Agent Loop

### 3.1 Two conflicting primary datasets — present both, don't blend

**Dataset A — AssistantBench via HAL (Princeton, primary-verified, fetched [hal.cs.princeton.edu/assistantbench](https://hal.cs.princeton.edu/assistantbench)).** 214 hard open-web info-seeking tasks, browser-use framework. Human ≈ 90%; benchmark is deliberately hard so absolute accuracy is low.

| Model | Accuracy | $/task | Verdict |
|---|---|---|---|
| **o3 Medium** (Apr 2025) | **38.81%** | ~$0.071 | Accuracy leader, cheap |
| GPT-5 Medium (Aug 2025) | 35.23% | ~$0.195 | — |
| **o4-mini Low** (Apr 2025) | 28.05% | **~$0.043** | **Pareto-optimal value** |
| GPT-4.1 (Apr 2025) | 17.39% | ~$0.066 | — |
| Claude 3.7 Sonnet (Feb 2025) | 16.69% | ~$0.262 | Mediocre value |
| **Claude Opus 4.1 High** (Aug 2025) | 13.75% | **~$3.65** | **Worst value** |
| Claude Sonnet 4.5 High (Sep 2025) | 11.80% | ~$0.464 | — |
| Gemini 2.0 Flash (Feb 2025) | 2.62% | ~$0.010 | Cheap but weak |

**Dataset B — Browser-Use's own benchmark (vendor, [browser-use.com/posts/ai-browser-agent-benchmark](https://browser-use.com/posts/ai-browser-agent-benchmark)).** 100 curated hard tasks, binary LLM judge, June 2026. Vendor-run — treat with caution.

| Model | Success | Cost/100 tasks | Notes |
|---|---|---|---|
| Claude Fable 5 | 80% | ~$580 (~$5.81/task) | Highest accuracy, most expensive |
| Browser-Use Cloud (bu-ultra) | 78% | ~plan cost | Best production value (their product) |
| Claude Opus 4.6 | 62% | — | Best standalone frontier |
| Gemini 3.1 Pro | 59.3% | — | — |
| Claude Sonnet 4.6 | 59% | — | Best-value Anthropic |
| GPT-5 | 52.4% | — | Slowest |

> ⚠️ **Why they disagree:** different task sets, different harness versions, different judges, and a ~1-year model-generation gap (A uses early-2025 models; B uses mid-2026 Fable 5 / Opus 4.6 / Sonnet 4.6). **Do not average them.** The robust cross-dataset conclusions: (a) frontier models land at **$0.20–$6/task**; (b) **OpenAI reasoning models (o3/o4-mini) were the cost-efficiency leaders on the neutral benchmark**; (c) raw Claude Opus is a cost trap for high-volume loops; (d) the agent *framework* matters as much as the model (WebVoyager end-to-end systems hit 89–98% vs raw-model WebArena ~60–69%).

### 3.2 Perception representation drives token cost

- **Raw DOM/HTML:** can exceed 1M tokens/page (Agent-E paper cites YouTube home ~800K tokens) → tens of $/task. Avoid feeding raw DOM.
- **Accessibility tree (a11y):** best token compression with semantic structure preserved; de-facto standard for text-based agents (browser-use, Stagehand, Agent-E all build on AX-tree-derived element lists).
- **Screenshot/vision:** universal but token-heavy and slower; struggles with inter-step state changes.
- **Production pattern:** hybrid — a11y/DOM primary + vision fallback for non-standard layouts (~95% coverage). Independent reports claim DOM-driven stacks beat pure-vision by 12–17 reliability points (e.g. Playwright+Claude ~92% vs Computer Use ~78%) — **[UNVERIFIED editorial estimate](https://www.digitalapplied.com/blog/browser-automation-ai-agents-playwright-stagehand-2026)**.
- Sources: [arXiv:2506.10953](https://arxiv.org/pdf/2506.10953), Agent-E [arXiv:2407.13032](https://arxiv.org/abs/2407.13032)

### 3.3 Tiered / escalation routing (the path to <$0.10/task)

```
Tier 0: Deterministic code (free)        — known patterns, cached selectors, API fast-path, validations
Tier 1: Haiku / Flash (~$0.0001/call)    — triage, simple page parsing, routing decisions
Tier 2: Sonnet / o4-mini (~$0.006/call)  — multi-step navigation, form filling (the workhorse)
Tier 3: Opus / o3 / Fable (~$0.06+/call) — escalate ONLY on repeated failure / ambiguity
```

Published routing results (general LLM, **not browser-specific** — directional):
- RouteLLM (ICLR 2025): 85% cost reduction at 95% of GPT-4 quality by routing 86% of queries to a cheap model.
- Cascade: 97% of GPT-4 accuracy at 24% of cost.
- 70/20/10 tier distribution: 60–80% average cost reduction.
- Sources: [requesty.ai routing](https://www.requesty.ai/blog/ai-agent-cost-optimization-how-to-cut-llm-spend-by-80-percent-with-routing), [tianpan.co llm-routing-production](https://tianpan.co/blog/2025-10-19-llm-routing-production), [freecodecamp tiered-model-routing](https://www.freecodecamp.org/news/how-to-build-a-cost-efficient-ai-agent-with-tiered-model-routing/)

> ⚠️ **Cascade failure mode:** if the escalation rate creeps toward 100%, you pay for *both* the cheap attempt **and** the frontier attempt — savings vanish and cost can exceed frontier-only. Optimize for **token yield** (successful-task tokens), not per-call price. Monitor escalation rate as a first-class metric.

### 3.4 Production $/task ranges (editorial, treat as order-of-magnitude)

| Stack | Est. $/task | Reliability | Source class |
|---|---|---|---|
| Playwright + Claude (self-hosted) | $0.02–0.10 | ~92% | editorial estimate |
| Stagehand | $0.05–0.15 | ~89% | editorial estimate |
| Browserbase (managed) | $0.10–0.40 | ~90% | editorial estimate |
| Anthropic Computer Use | $0.20–0.40 | ~78% | editorial estimate |
| OpenAI CUA | $0.20–0.50 | ~75% | editorial estimate |

Source: [digitalapplied.com](https://www.digitalapplied.com/blog/browser-automation-ai-agents-playwright-stagehand-2026) — **editorial, not controlled benchmarks**. The HAL AssistantBench numbers in §3.1 are the only *benchmarked* $/task figures here.

### 3.5 Reference token pricing (June 2026, for sizing)

| Model | Input $/M | Output $/M |
|---|---|---|
| Claude Opus 4.8 | $15 | $75 |
| Claude Sonnet 4.6 | $3 | $15 |
| Claude Haiku 4.5 | $1 | $5 |
| GPT-5 | ~$2.50 | ~$15 |
| o3 Medium | ~$10 | ~$40 |
| o4-mini | ~$1.10 | ~$4.40 |
| Gemini 2.0 Flash | ~$0.10 | ~$0.40 |
| DeepSeek V3.2 | ~$0.14 | ~$0.28 |

> Note: verify current Anthropic pricing against [platform.claude.com/docs pricing](https://platform.claude.com/docs/en/about-claude/pricing) before committing — model lineup and prices shift. **Prompt caching** (up to 90% off cached input) and **Batch API** (50% off) materially change the math for repeated system prompts in an agent loop and should be on by default.

---

## 4. Scaling

### 4.1 Concurrency & architecture

- **One ephemeral browser per task** is the safe multi-tenant default (full isolation, no cookie bleed). Hosted platforms default to this.
- **Browser pool (warm)** reduces ~1–3s cold start but risks state bleed — reset/discard `BrowserContext` between tasks. Each Playwright `BrowserContext` is isolated (cookies/storage); multiple contexts per browser binary are cheaper than multiple binaries. Libraries: [apify/browser-pool](https://github.com/apify/browser-pool), [playwright-page-pool](https://pypi.org/project/playwright-page-pool/).
- **Persistent (stateful) session** only when a single multi-turn task needs auth continuity — and then treat the stored `storageState` as a live credential (§2.5).

### 4.2 Statelessness & queueing

- **Stateless workers:** task state in external DB/queue, browser ephemeral per task, worker pods disposable. Enables HPA/KEDA autoscale on **queue depth**.
- **Queue/orchestration:**
  - **BullMQ + Redis** (Node-native): retries, DLQ, priority, concurrency workers. Raise `lockDuration` above the default 30s or long browser tasks get stall-detected. ([docs.bullmq.io](https://docs.bullmq.io/guide/going-to-production))
  - **Temporal** (durable workflow): preferred for long-running, retry-on-crash, multi-step agent runs; integrates with OpenAI Agents SDK (2025). ([intuitionlabs.ai temporal](https://intuitionlabs.ai/articles/agentic-ai-temporal-orchestration)) — *aligns with the existing Temporal-based platform in this org's other projects.*
  - **K8s:** KEDA `ScaledObject` on queue depth; [aerokube Moon](https://aerokube.com/moon/latest/) for pod-per-session Playwright/Puppeteer/Selenium.

### 4.3 Resource footprint & cost at scale

- ~**300–500 MB RAM** per active headless Chromium → **2–4 instances/GB** (favor 2 for stability). ~**1 vCPU per 2–3 instances**.
- Recycle browsers to bound the ~1.5 GB/8h memory creep.

**Self-hosted cost model (AWS t3.large, 2 vCPU / 8 GB ≈ $0.0832/hr on-demand, ~4 concurrent browsers):**
- 100 tasks/day (avg 5 min): ~8.3 browser-hr → **~$0.69/day compute** + LLM.
- 10,000 tasks/day: ~833 browser-hr → ~35 nodes → **~$70/day compute** + LLM + SRE overhead.

**Hosted cost model (Browserbase Startup $99/mo, 500 hr included):**
- 500 hr = 6,000 tasks/mo at 5 min/task covered by base plan.
- 10,000 tasks/day = 300,000 tasks/mo ≈ 25,000 browser-hr → overage at $0.10/hr ≈ **~$2,500+/mo browser cost alone** (note: original sub-agent figure of $25K assumed 5-min tasks summed differently; recompute against live overage before quoting — **[VERIFY]**).

**Decision:** hosted wins **<~5K tasks/mo**; self-host wins **>~10K tasks/mo**.

> **The dominant cost is the LLM, not the browser.** At Browserbase Startup overage, a 5-min task ≈ **$0.0083 browser** vs **$0.04–$5.81 LLM**. Browser infra is rounding error at scale; spend optimization effort on the model loop (tiering, caching, a11y-tree token reduction).

---

## 5. Risks & Contradictions

- **Pricing is volatile.** All vendor numbers fetched June 2026; a Nov 2025 comparison already diverged. Re-verify before budgeting. Hyperbrowser subscription tiers **[UNVERIFIED]**.
- **Model-cost data conflicts** (HAL vs Browser-Use vendor benchmark, §3.1). Different task sets/harnesses/model generations. Don't blend; prefer the neutral HAL data for cost-efficiency decisions, but note its models are ~1 year old.
- **$/task production ranges (§3.4) are editorial**, not benchmarked. Only HAL AssistantBench gives benchmarked $/task.
- **Routing savings (60–85%) are general-LLM studies**, not browser-agent-specific controlled experiments.
- **Anti-bot is a moving target.** "Recognition" (Web Bot Auth) is the durable strategy but limits you to participating sites/vendors. A non-trivial fraction of the open web will remain unreachable.
- **Self-hosted resource footprint** synthesized from production blogs, not a controlled benchmark — validate on your own pages.

---

## 6. Conclusions & Recommendations for OUR Build

1. **Substrate:** self-hosted **Playwright/Chromium behind a swappable browser interface**; keep **Steel.dev (Apache-2.0)** as the drop-in escalation path because it self-hosts *and* has a cloud, and **Browserbase** for the minority of tasks needing managed Advanced stealth / Web Bot Auth recognition.
2. **Don't fight anti-bot by evasion.** Accept that Turnstile/DataDome/PerimeterX-gated and credentialed sites are out-of-scope for autonomous operation; route those to "needs human auth" rather than burning budget on unreliable stealth. If stealth is required, prefer the *recognition* path over the evasion arms race.
3. **Model loop:** **Sonnet-class workhorse (Tier 2) with o4-mini / Haiku triage (Tier 1) and an Opus/o3 escalation tier (Tier 3)**; gate Tier 3 strictly and **monitor escalation rate** to avoid the cascade cost trap. Turn on prompt caching + batch where applicable.
4. **Perception:** a11y-tree-primary with vision fallback — never feed raw DOM (token blowup). This also bounds per-step cost, which dominates total cost.
5. **Scale:** stateless ephemeral-browser-per-task workers, queue-driven (Temporal for durability given org alignment), KEDA autoscale on queue depth, recycle browsers to bound memory creep.
6. **Security is the deployment gate, not an afterthought:** ephemeral isolated profile per task, OAuth-delegated scopes over raw cookie injection where possible, treat all captured session state as secrets, log agent actions separately, and assume prompt injection — sanitize/contain page-derived instructions.
7. **Cost focus:** optimize the **LLM loop, not the browser fleet** (>10:1 cost ratio). Token reduction + tiering beats any browser-infra saving.
8. **Verify before quoting numbers:** re-fetch vendor pricing and recompute the at-scale browser-hour math; the only benchmarked $/task source is HAL AssistantBench.

---

## Sources

**Browser platforms (pricing fetched June 2026):**
- https://www.browserbase.com/pricing · https://docs.browserbase.com/guides/concurrency-rate-limits · https://docs.browserbase.com/features/stealth-mode
- https://docs.steel.dev/overview/pricinglimits · https://steel.dev/pricing · https://github.com/steel-dev/steel-browser
- https://hyperbrowser.ai/docs/reference/pricing
- https://www.browserless.io/pricing · https://github.com/browserless/browserless

**Self-hosted footprint:**
- https://rendershot.io/blog/headless-chromium-fleet-memory
- https://datawookie.dev/blog/2025-06-06-playwright-browser-footprint/
- https://bug0.com/knowledge-base/playwright-docker
- https://github.com/microsoft/playwright/issues/38489

**Anti-bot / CAPTCHA / stealth:**
- https://developers.cloudflare.com/bots/concepts/bot-detection-engines/
- https://www.browserless.io/blog/tls-fingerprinting-explanation-detection-and-bypassing-it-in-playwright-and-puppeteer
- https://scrapfly.io/blog/posts/playwright-stealth-bypass-bot-detection
- https://ianlpaterson.com/blog/anti-detect-browser-benchmark-patchright-nodriver-curl-cffi/
- https://2captcha.com/ · https://www.capsolver.com/ · https://anti-captcha.com/

**Auth & security:**
- https://workos.com/blog/logging-ai-agents-into-web-apps
- https://lyrie.ai/research/research/2026-04-27-agentic-browser-gap
- https://gbhackers.com/new-pass-the-cookie-attacks-bypass-mfa/
- https://www.wiz.io/blog/agentic-browser-security-2025-year-end-review
- https://arxiv.org/pdf/2505.13076

**Models / cost:**
- https://hal.cs.princeton.edu/assistantbench
- https://browser-use.com/posts/ai-browser-agent-benchmark
- https://arxiv.org/pdf/2506.10953 · https://arxiv.org/abs/2407.13032
- https://www.requesty.ai/blog/ai-agent-cost-optimization-how-to-cut-llm-spend-by-80-percent-with-routing
- https://tianpan.co/blog/2025-10-19-llm-routing-production
- https://www.freecodecamp.org/news/how-to-build-a-cost-efficient-ai-agent-with-tiered-model-routing/
- https://www.digitalapplied.com/blog/browser-automation-ai-agents-playwright-stagehand-2026
- https://platform.claude.com/docs/en/about-claude/pricing

**Scaling / orchestration:**
- https://github.com/apify/browser-pool · https://pypi.org/project/playwright-page-pool/
- https://docs.bullmq.io/guide/going-to-production
- https://intuitionlabs.ai/articles/agentic-ai-temporal-orchestration
- https://aerokube.com/moon/latest/

**Framework integration:**
- https://www.browserbase.com/blog/stagehand-v3 · https://docs.stagehand.dev/v3/basics/agent
- https://www.pkgpulse.com/guides/browserbase-vs-hyperbrowser-vs-steel-cloud-browsers-ai-2026
- https://www.firecrawl.dev/blog/best-browser-agents
