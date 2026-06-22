# Browser Agent — Design (Task 1)

> Grounded in `docs/` (navigated via `/browser-agent-expert`). Each load-bearing decision cites a source doc.
> Citation keys: `[arch/01..03]` = `docs/architecture/*`, `[eval/01..02]` = `docs/evaluation/*`, `[infra/01..02]` = `docs/infrastructure/*`, `[00]` = `docs/00-synthesis-and-design-implications.md`.
> This design passed a 3-reviewer grounding gate (architecture / evaluation / infrastructure+compliance), each reviewer using `/browser-agent-expert`.

## 1. Goal & MVP scope

The assignment requires an agent that accepts **natural-language tasks**, executes them **reliably across different sites**, and demonstrates **self-correction** and **self-maintenance**, with a **self-built eval set**, a **public, operable web frontend** (live progress + inspectable failures), and an honest supported/unsupported listing. Graded on mechanism depth (not try/except), eval depth, silent-failure prevention, and concrete cost/latency/scalability/correctness analysis.

**Strategy: vertical slice → then deepen (aim for grade A).** First get one site working end-to-end through the full stack (NL → execute → verify → public frontend) so a public URL exists early; then deepen reliability and eval rigor along each grading axis. This de-risks the hard "must have a public frontend" requirement up front.

**MVP**: a single agent service — NL task → execution on bot-wall-free public sites → frontend shows live step progress and an inspectable failure trace → every run reports a nominal-vs-verified completion verdict. **Out of scope for MVP**: login/MFA sites, CAPTCHA solving, large-scale concurrency (designed-for, not built).

## 2. Tech stack (with rationale)

| Layer | Choice | Rationale (source) |
|---|---|---|
| Language | **Python** | Copilot SDK has a Python binding; keeps Playwright, Inspect AI, Langfuse SDK, `sse-starlette` all Python-native |
| **LLM (hard constraint)** | **GitHub Copilot SDK (Python)** — local `copilot --headless` server, used as a **model gateway** | All LLM calls must route through the Copilot SDK. Per-session model selection gives tiered routing; a different-family model serves as judge [eval/02]. See §LLM layer |
| Browser runtime | **Self-hosted Playwright/Chromium** (Windows-native) behind a `BrowserProvider` interface; Steel.dev reserved as escalation | Swappable, no lock-in [infra/01][00] |
| Perception | **Fused DOM + accessibility tree → indexed element list**; screenshot/SoM on demand | Convergent choice; **never feed raw DOM** (token blowup) [arch/01][00] |
| Backend | **FastAPI + `sse-starlette`** | SSE push for step progress; upgrade to WebSocket only if human-in-the-loop pause/resume is added [infra/02] |
| Frontend | **React + Vite (static)**, AG-UI event vocabulary (+ custom `screenshot_annotated`) | CopilotKit consumes AG-UI; AG-UI has no standard screenshot event so we add a custom one [infra/02] |
| Observability | **Langfuse (self-host) + OpenTelemetry GenAI spans** | Each Playwright action wrapped as a tool span; feeds frontend replay and the anomaly trip-wire [infra/02][00] |
| Eval harness | **Inspect AI + REAL** | Clean sandbox isolation; REAL = deterministic site replicas, state-diff for action tasks (judge only for retrieval tasks) [eval/02][arch/03] |
| Deployment | **Desktop self-host (Windows-native) + Cloudflare Tunnel** for the public URL | No container/Fly.io/Zeabur needed; Cloudflare Tunnel gives a stable public URL with TLS, no inbound port-forward |

### LLM layer — Copilot SDK details

GitHub Copilot SDK (GA 2026-06-02, Python binding). Run the agent runtime as a **local headless server** (`copilot --headless --port <PORT>`); backend connects via `CopilotClient` + `RuntimeConnection.for_uri("localhost:<PORT>")`. We use it **as a model gateway** — each step issues a tightly-scoped `session.sendAndWait()` with our own prompt and an explicit `model`, and we keep our deterministic perceive/locate/verify orchestration rather than delegating planning to the SDK's agent runtime. Tiered routing = choose a cheap model for triage/classification, a workhorse for acting, a stronger model for escalation; the **judge uses a different model family** from the Copilot menu [eval/02]. Auth: Copilot subscription (`COPILOT_GITHUB_TOKEN`) or BYOK. Because LLM usage is covered by the Copilot subscription, **per-task cost is effectively flat-rate, not per-token** — the binding constraint becomes Copilot premium-request quota / rate limits (see §11).

## 3. Architecture (components + data flow)

Layered pipeline extending the convergent architecture in `[00]`:

```
NL Task
  ▼ Planner (hierarchical): decompose → sub-tasks; replan = sub-goal fails N times
  ▼ per sub-task → stateless executor (fresh LLM context + clean page state) [arch/01][arch/03]
  ├─ OBSERVE-FIRST (prevention, not recovery) [A1]: merge co-labeled elements, render
  │                tables/lists as Markdown, selective history replay (pivotal nodes only).
  │                No extra LLM call — AgentOccam got WebArena 16.5%→43.1% from this alone [arch/02]
  ├─ PERCEIVE  fused DOM+AX → indexed elements; screenshot/SoM on demand; cache (no rebuild
  │            every step); Semantic Entropy Probe on extraction steps (zero-cost uncertainty) [eval/02]
  ├─ LOCATE    L1 deterministic 10-tier (zero LLM) [A2]: ARIA role+name → role → testid → id
  │            → aria-label(exact) → aria-label(contains) → href → CSS(exact) → CSS(contains)
  │            → visible text (arXiv:2603.20358). L2 only on L1 miss: fingerprint (LCS+attr)
  │            → LLM re-rank ≤5 → vision. 2-layer cache (hit = 0 token). No CSS/XPath as primary;
  │            `:near()` is deprecated — do not use [arch/02]
  ├─ PREDICT   expected effect (URL/DOM/network)
  ├─ ACT       batch where safe; confirm before write/submit
  ├─ VERIFY    diff actual vs predicted; NO_CHANGE → diagnose, re-ground (verify-after-act) [arch/02]
  └─ CLASSIFY  not-found→re-ground/heal | not-interactable→wait/scroll/dismiss | wrong-page→replan
        │      | stale/timing→state-wait then retry same action
        │ on exhaustion: local strategy-switch → global replan → ask_user
  ▼ VERIFY TASK (dual-channel): (a) programmatic state assertion where possible;
  │            (b) else screenshot-grounded judge scored twice (history-only vs +screenshot;
  │            divergence = fabrication flag) → report nominal vs verified completion [eval/01][eval/02]
  ▼ MEMORY     reflection: store failed trajectories (offline induct only, never online) [arch/03]
```

**Observability is first-class**: every step logs prompt, model, chosen locator + cascade level, screenshot, predicted-vs-actual diff, and failure class. **Redaction happens before the span is created and before SSE serialization** [C5][infra/02]. An SVDD trajectory trip-wire (trained on normal traces only) flags drift/cycles [00][eval/01].

## 4. Grading-axis coverage

| Grading axis (ASSIGNMENT) | Grounded mechanism | Source |
|---|---|---|
| Self-correction (not try/except) | Observe-first prevention + verify-after-act (predict→diff→re-ground) + per-class failure handling + retry→local-switch→replan | [arch/02][00] |
| Self-maintenance (selector adaptation) | Deterministic 10-tier cascade → fingerprint heal → LLM re-rank → vision; 2-layer cache | [arch/02] |
| Eval-set depth | Domain×task-type×difficulty tiers; ≥20% held-out unseen sites; block shortcuts; **key-node TCR/TSR** over binary | [eval/01][arch/03] |
| Silent-failure prevention | **nominal-vs-verified completion (CuP) is the headline metric**; dual-channel verification; pre-exec adversarial check; SEP + consistency + state check; trajectory anomaly; never trust verbalized confidence | [eval/01][eval/02][00] |
| Cost/latency/scalability | LLM-out-of-hot-path; cache/replay (0-token hits); batched actions; tiered model selection; stateless ephemeral browser per task; **cost bounded by Copilot quota, not per-token** | [infra/01][00] |
| Correctness verification | Independent ground truth (programmatic state / REAL state-diff), **never self-consistency**; the verify-after-act *mechanism* prevents silent failure, CuP *measures* it | [eval/01][eval/02] |

## 5. Self-correction & self-maintenance (depth)

- **Self-correction is not retry.** First prevent: observe-first alignment (no LLM) [A1]. Then per action: diff observation (DOM/URL/network) → branch by failure class (see diagram) → every retry must be justified by a **new observation** → on exhaustion, local strategy-switch (e.g. search-by-text instead of search-by-class) → global replan → `ask_user`. Write/submit retries require confirmation first. [arch/02]
- **Self-maintenance (locator healing).** Semantic-first, **zero-cost deterministic 10-tier first** (arXiv:2603.20358), LLM healing only on miss; ARIA role+name is most stable (a user-facing contract); healed locator written back to a 2-layer cache (hit = 0 token). Avoid CSS/XPath as primary; `:near()` is deprecated. [arch/02]
- **Honest limit.** Intent drift (a healed locator clicks a *plausible-but-wrong* element while CI stays green) is an **open research problem**. We mitigate with goal-level verify (predict→diff→re-ground) + CuP; we **do not claim to eliminate false success**. Concrete example: "click the red button" → healed to a different red button → nominal success, verified failure. [00][arch/02]

## 6. Silent-failure & verification layer (the differentiator)

- **Per-step**: verify-after-act, with the correction signal grounded in observable browser state, never the LLM's self-assessment. [arch/02][00]
- **Per-task dual-channel**: (a) programmatic state assertion where inspectable (DOM/API/extracted field); (b) else a screenshot-grounded judge **scored twice** (action-history-only vs +screenshot) — divergence flags fabrication. [eval/01]
- **Headline metric = nominal vs verified completion (CuP-style)**; the delta is the silent-failure rate. [eval/02][00]
- **LLM judge guardrails** (only when unavoidable): different model family from the agent, explicit "Unknown" escape hatch, one dimension per call. **Panels do not fix correlated error** — ~9 judges ≈ 2 effective votes; panel accuracy falls 8–22pp short of true independence; the best single judge ≈ the full panel. Spend extra judges on independent axes. [eval/02]
- **Three stacked silent-failure signals**: Semantic Entropy Probe on extraction steps + repeat-and-compare consistency sampling + independent post-action state check; plus an SVDD trajectory trip-wire (needs only normal traces). [eval/02][eval/01]
- **Never accept verbalized confidence as a success signal** (LLMs are systematically overconfident). [eval/02]

## 7. Eval set & harness

- **Diversity**: domain (e-commerce / forms / information retrieval / multi-tab / stateful) × task-type × difficulty (single-step / same-domain multi-step / cross-domain multi-step); **≥20% held-out** on sites never seen in development; block shortcut paths. [eval/01]
- **Scoring**: **WebCanvas key-node (TCR/TSR)** instead of binary (binary scores partial progress as 0; the 23.1% TSR vs 48.8% TCR gap shows how much signal that discards); **pass^k (k≥3)** for side-effecting tasks. [arch/03][eval/02]
- **Harness**: Inspect AI (clean sandbox per run) + **REAL** as the primary offline harness — action tasks use deterministic **state-diff**, retrieval tasks use a rubric judge (still low-variance because data is locked). [eval/02][arch/03]
- **Statistical rigor**: target n≈1,000 items; report SE/CI (clustered SE when tasks share a site); measure calibration and discrimination separately. [eval/02]
- **Eval-driven development**: start from 20–50 *real* failure cases with two-reviewer pass/fail agreement; saturation means the set needs harder tasks. [eval/02]
- **Non-negotiable ablation rule**: every "memory/skill improves performance" claim must report total token usage **and** a budget-matched vanilla-actor baseline. **Cautionary precedent**: AWM reports +51% on WebArena, but a budget-matched baseline refutes it — Vanilla-IB 50.74% vs AWM 44.98% (−5.76pp) using 29% fewer tokens (arXiv:2606.15017). [arch/03]

## 8. Frontend & observability

- **Input**: NL task box + optional target URL.
- **Live progress**: SSE (`sse-starlette`) emitting AG-UI events (`STEP_STARTED` / `TOOL_CALL_*` / `INTERRUPT`) plus a **custom `screenshot_annotated`** event (AG-UI has no standard screenshot event) [C6][infra/02].
- **Inspectable-failure view (Skyvern-style)**, per step: annotated screenshot (highlighted element) · element tree · LLM prompt + raw response + parsed action · chosen locator + cascade level · `failure_category` · retry chain · HAR. [infra/02]
- **Observability**: Langfuse (inline screenshot spans via `LangfuseMedia`) + OTel GenAI spans. **Langfuse has no built-in redaction — we sanitize before `span.update()`.** [infra/02]
- **Implementation aid**: reuse existing skills rather than hand-rolling — `minimax-fullstack-dev` (frontend↔backend integration, SSE streaming), `vercel-react-best-practices`, `vercel-web-design-guidelines`, `minimax-frontend-dev` (polish the failure trace view).

## 9. Deployment

- **Desktop self-host** (Windows-native): `uvicorn` (FastAPI) + Playwright Chromium running directly on the machine — no container required. Static React frontend served alongside or from a static host.
- **Public URL via Cloudflare Tunnel**: free, stable named URL, TLS, no inbound port-forward (does not expose the home IP). Evaluators reach the desktop service through it.
- **Caveat**: uptime depends on the desktop being on during evaluation.

## 10. Supported / unsupported scope (honest disclosure — must be prominent in README/frontend) [C4]

- **Supported**: bot-wall-free public sites (search, browse, forms, extraction, multi-step navigation). MVP seed set: `the-internet.herokuapp.com`, `automationexercise.com`, `books.toscrape.com`, `Wikipedia` (kept separate from the REAL eval replicas to preserve held-out).
- **Unsupported (routed to "needs-auth / unsupported", never evaded)**: Cloudflare Turnstile / DataDome / PerimeterX walls, CAPTCHA, login walls / MFA, banking / SSO / healthcare. This list IS the honest unsupported disclosure the assignment requires; **concrete tested domains are recorded in `UNSUPPORTED_SITES.md` (populated by real testing in M5)** [C1]. [infra/01]
- **Security**: ephemeral profile per task; OAuth delegated scopes preferred over raw cookie injection; captured session state treated as a secret; **redact before serialization** (`sk-*`/Bearer/`Authorization`/`Cookie`/PII never reach a span, SSE `data:`, or replay file). [infra/01][infra/02][CLAUDE.md]

## 11. Cost & scalability analysis (planned)

- **LLM cost is flat-rate via the Copilot subscription, not per-token.** The binding constraint is **Copilot premium-request quota / rate limits**; we will measure **LLM requests per task** (the real scaling cost), not $/token.
- **Caveat (prominent)**: any $/task figures carried over from research are **editorial estimates, from early-2025 HAL models, and require in-house measurement** on our task distribution before being quoted. Not fixed values. [infra/01]
- **Latency**: dominated by the LLM loop (planning/verify/judge), not the browser. Levers: keep the LLM out of the hot path (deterministic cascade + cache → 0-token hits), batch actions, prune-to-last-N screenshots, on-demand perception. [infra/01][00]
- **Scalability**: stateless ephemeral browser per task (~300–500 MB each); recycle to bound memory creep. MVP is single-desktop; the queue + autoscale shape is designed-for, not built. The new ceiling is Copilot rate limits, not browser RAM.

## 12. Milestones

| M | Content | Verification |
|---|---|---|
| M0 | Scaffold: `BrowserProvider`, Copilot SDK wiring (headless server + client), SSE skeleton, frontend skeleton, redact wrapper, OTel/Langfuse | starts up; SSE connects; redaction unit tests; `screenshot_annotated` payload schema defined |
| M1 | Core loop (observe-first→perceive→locate→act) on 2–3 seed sites; NL→plan→happy path | seed tasks 100% on deterministic state check + nominal verification |
| M2 | Self-correction (verify-after-act + classify + retry/replan) + self-maintenance (10-tier→heal→re-rank + cache) | injected selector change/failure self-heals; "duplicate red button" variant makes nominal vs verified diverge (intent-drift caught by goal-verify) |
| M3 | Verification layer (dual-channel + nominal-vs-verified + SEP + SVDD) + eval set v1 (key-node) + Inspect AI + REAL + pass^k | harness emits TCR/TSR + pass^k + SE/CI; every ablation carries a budget-matched baseline |
| M4 | Frontend (SSE progress + inspectable failure view) + Langfuse/OTel + desktop self-host + Cloudflare Tunnel; reuse frontend skills | public URL operable; failures inspectable; screenshot events render |
| M5 | Hardening: anti-bot routing, `UNSUPPORTED_SITES.md` (concrete sites), README (prominent intent-drift disclosure), ANALYSIS (cost = Copilot quota/rate-limit, with unverified caveats) | held-out task suite + disclosures complete |

## 13. Risks & open problems

- **Intent drift** has no detector (open problem); mitigated by goal-level verify, not solved. [00][arch/02]
- **Vendor self-healing numbers are unverified** (Functionize 99.97%, etc.) — directional only. [00]
- **Cost figures require in-house measurement**; under Copilot SDK the relevant metric is requests-per-task vs Copilot rate limits, which we must measure. [infra/01]
- **Copilot SDK is an agent runtime, not a bare completion API** — we use it as a model gateway; if its session overhead is significant, that is a latency factor to measure in M1.
- **Single-source / future-dated arXiv IDs**: re-check before external citation. [00]
- **Desktop uptime + Cloudflare Tunnel** must be running during evaluation.
