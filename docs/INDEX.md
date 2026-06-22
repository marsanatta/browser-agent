# docs/ — Index (browser-agent-expert knowledge base)

**L0 abstract.** Grounding research for the Task 1 generalized browser-automation agent: how to build it (architecture), how to prove it works (evaluation), and how to run/ship it (infrastructure). 8 research docs, source-cited, with unverified claims flagged. This file is the **L1 routing layer** — the `browser-agent-expert` skill reads it to route a question to the right L2 document.

```
docs/
├── INDEX.md            ← L1 routing (this file)
└── research/
    ├── 00-synthesis-and-design-implications.md   ← L1 synthesis · START HERE
    ├── architecture/     how the agent works        (01, 02, 07)
    ├── evaluation/       how we verify correctness   (03, 06)
    └── infrastructure/   how we run & ship           (04, 05)
```

Layering (brain-style): **L0** = the one-line abstract on each row below (scan to filter). **L1** = this routing table + each doc's "read it when". **L2** = the full research docs and their own `Sources` sections (the authoritative bibliography).

---

## Routing table — match the question, open the doc

Pick the row whose keywords best match the question, then open the target. If several match, the agent reads each. The synthesis (00) is the fallback when a question spans categories.

| If the question is about… (keywords) | Open |
|---|---|
| perception, how the agent "sees" a page, DOM vs accessibility tree, vision, screenshot, Set-of-Marks, action space, control loop, ReAct, hierarchical planner, comparing SOTA systems (browser-use / Stagehand / Skyvern / Agent-E / WebVoyager / computer-use) | `research/architecture/01-sota-browser-agents.md` |
| self-correction, a step/click failed, error recovery beyond retry, retry-vs-replan, verify-after-act, failure classification, observation alignment | `research/architecture/02-self-correction-and-healing.md` |
| self-maintenance, selector/locator broke, DOM changed, self-healing locators, ARIA/role locators, locator cascade, fingerprint matching | `research/architecture/02-self-correction-and-healing.md` |
| memory, skill reuse, workflow memory (AWM), Voyager, deliberate search, tree search, LATS, MCTS, milestone metric, key-node scoring, WebCanvas, REAL deterministic replicas, adopt/skip decisions | `research/architecture/07-memory-search-and-milestone-eval.md` |
| eval set design, benchmarks (WebArena / WebVoyager / Mind2Web / GAIA / AssistantBench / ST-WebAgentBench), silent-failure detection, dual-channel verification, trajectory anomaly, task diversity, held-out splits | `research/evaluation/03-evaluation-and-failure-detection.md` |
| eval methodology, verifying correctness without ground truth, LLM-as-judge reliability, self-preference bias, panel of judges, pass^k, calibration, abstention, statistical error bars / sample size, how many eval items / minimum sample size, Inspect AI / HAL harness | `research/evaluation/06-eval-methodology.md` |
| browser runtime / infrastructure, self-host Playwright vs Browserbase / Steel / Hyperbrowser, anti-bot, CAPTCHA, login/auth walls, MFA, captured-session/cookie *runtime* handling (cookie-jar, profile isolation, auth context), model choice & tiering, cost-per-task, $/task, scaling, concurrency | `research/infrastructure/04-browser-infra-and-models.md` |
| web frontend, live progress streaming, SSE vs WebSocket, AG-UI, inspectable-failure / trace view, observability, Langfuse / OpenTelemetry, deployment (Fly.io / Zeabur / Render), headless Chromium in containers, frontend secret/cookie/PII redaction | `research/infrastructure/05-frontend-and-deployment.md` |
| overall design, the convergent architecture, grading-axis → mechanism mapping, final readiness verdict, onboarding / overview / introduction, "where do I start" | `research/00-synthesis-and-design-implications.md` |

Cross-list notes: **milestone/deterministic eval** (WebCanvas key-node, REAL) lives in `architecture/07`, not `evaluation/`. **Security spans two docs by phase:** *redaction before output* — frontend exposure + cookie/auth-header/PII scrubbing in logs, streams, and stored traces — is in `infrastructure/05`; *runtime session handling* — cookie-jar, profile isolation, auth-wall context — is in `infrastructure/04`. A pure "don't leak secrets in the UI/logs" question is fully answered by `infrastructure/05` alone.

---

## Documents — read it when…

### Start here
- **`research/00-synthesis-and-design-implications.md`** — *L0:* one-stop design brief; convergent architecture diagram, grading-axis→mechanism table, adopt/skip decisions, readiness verdict. Read first; drill into a category doc for depth/citations.

### architecture/ — how the agent works
- **`01-sota-browser-agents.md`** — *L0:* 11 SOTA systems compared; perception philosophies, action spaces, control loops, memory. Read to choose perception/action/loop design.
- **`02-self-correction-and-healing.md`** — *L0:* the implementation-dense one; failure classification, verify-after-act, retry-vs-replan, and the semantic locator self-healing cascade. Read to build self-correction or self-maintenance.
- **`07-memory-search-and-milestone-eval.md`** — *L0:* adopt/skip for memory (Voyager, AWM), search (LATS/MCTS — skipped), and milestone/deterministic eval (WebCanvas, REAL).

### evaluation/ — how we verify correctness
- **`03-evaluation-and-failure-detection.md`** — *L0:* benchmark deep-dives + eval-set design + silent-failure (dual-channel verification, trajectory anomaly). Read to design the eval set.
- **`06-eval-methodology.md`** — *L0:* verifying correctness without ground truth; judge reliability, pass^k, calibration/abstention, statistical rigor, Inspect AI harness.

### infrastructure/ — how we run & ship
- **`04-browser-infra-and-models.md`** — *L0:* browser runtime choice, anti-bot/CAPTCHA/login reality, model tiering, cost-per-task & scaling.
- **`05-frontend-and-deployment.md`** — *L0:* SSE progress streaming, inspectable-failure trace view, Langfuse/OTel observability, headless-Chromium deployment, frontend secret/PII redaction.

---

**Conventions**
- Numeric prefixes (00–07) preserve research order and stable references after the re-org.
- Each doc opens with 研究日期 / 來源 / 信心程度 and ends with `Sources` + `Confidence/Gaps`.
- Unverified vendor numbers and future-dated (2025–2026) arXiv IDs are flagged inline — re-check before quoting externally.
- **Maintenance:** when a research doc is added/moved, add a routing row + an L0 line here. The `browser-agent-expert` skill depends on this file staying in sync.
