# 05 — Web Frontend & Deployment for a Browser-Automation Agent

**研究日期**: 2026-06-22  
**來源數量**: 35+ primary URLs fetched or searched  
**信心程度**: 82 / 100 (high on streaming patterns, UI tooling, observability; moderate on exact Fly.io/Railway timeout limits; low on Zeabur Chromium specifics)

---

## TL;DR

Build the UI on React + Vite, stream agent steps over Server-Sent Events (SSE) using the AG-UI event vocabulary, record per-step screenshots via Langfuse `LangfuseMedia` spans, deploy the FastAPI + Playwright backend on Fly.io (`performance-2x`, ≥2 GB RAM) behind a single Docker image. Redact secrets at the SSE serialization layer, never surface raw cookies or auth headers in the trace store.

---

## Research Plan

| # | Subquestion |
|---|------------|
| 1 | SSE vs WebSocket vs polling for multi-step agent progress streaming in Python/Node |
| 2 | What do browser-use, Skyvern, Stagehand, and Browserbase show in their "inspectable run" UIs? |
| 3 | What observability tooling (Langfuse, LangSmith, Phoenix, Laminar) supports browser-agent trace replay? |
| 4 | How to deploy headless Chromium + FastAPI backend to Fly.io / Render / Railway: constraints, Docker, memory |
| 5 | Frontend security: preventing API key / cookie / PII leakage in the trace UI |

---

## 1. Live Progress Streaming Patterns

### 1.1 Protocol Comparison

| Dimension | SSE | WebSocket | HTTP Long-Poll |
|-----------|-----|-----------|----------------|
| Direction | Server → client only | Full-duplex | Server → client only |
| Transport | Standard HTTP (1.1 keep-alive) | Upgraded TCP connection | HTTP, per-request |
| Browser API | `EventSource` (built-in) | `WebSocket` (built-in) | `fetch` polling |
| Auto-reconnect | Yes (browser handles it) | No (must implement) | No |
| Horizontal scale | Stateless; no sticky sessions | Needs socket broker / sticky sessions | Stateless |
| Binary (images) | No — text-only (`text/event-stream`) | Yes | No |
| HTTP/2 concern | Multiplexed; no 6-connection limit | Separate upgrade | Standard |
| Firewall friendliness | Excellent | Variable (some proxies block upgrade) | Excellent |

**Sources**: [websocket.org](https://websocket.org/guides/websockets-and-ai/), [buildmvpfast.com](https://www.buildmvpfast.com/blog/streaming-llm-responses-sse-vs-websockets-2026), [Medium — Anurag Chatterjee](https://tech-depth-and-breadth.medium.com/comparing-real-time-communication-options-http-streaming-sse-or-websockets-for-conversational-74c12f0bd7bc), [hivenet.com](https://www.hivenet.com/post/llm-streaming-sse-websockets)

### 1.2 Recommendation for a Browser-Automation Agent

**Use SSE for step progress**. Agent steps are server-initiated events (thought, navigate, click, screenshot_taken, error, done). No client pushes are needed during a run. SSE's automatic reconnect, HTTP/2 compatibility, and stateless horizontal scaling make it the right default.

**Add WebSocket only** when you implement human-in-the-loop approvals (agent pauses, user approves/rejects, agent resumes) — that bidirectional channel is where SSE breaks down. [(websocket.org)](https://websocket.org/guides/websockets-and-ai/)

**Images in SSE**: SSE is text-only. Transmit screenshots as base64-encoded strings within the JSON `data:` field of an SSE event, or transmit a signed URL pointing to an S3/R2 object. Do not embed large PNG bytes inline in the SSE stream — the overhead causes buffering artifacts in browsers.

### 1.3 FastAPI Implementation

```python
# backend: sse-starlette pattern
from sse_starlette.sse import EventSourceResponse
import asyncio, json

@app.post("/run/{task_id}/stream")
async def stream_task(task_id: str):
    async def event_gen():
        async for step in agent.run(task_id):
            yield {
                "event": step.type,            # "thought" | "action" | "screenshot" | "error" | "done"
                "data": json.dumps(step.payload)
            }
    return EventSourceResponse(event_gen())
```

```typescript
// frontend: fetch-based reader (avoids 6-connection limit of EventSource)
const resp = await fetch("/run/abc123/stream", { method: "POST", body: JSON.stringify(task) });
const reader = resp.body!.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  for (const line of new TextDecoder().decode(value).split("\n\n")) {
    if (line.startsWith("data:")) dispatch(JSON.parse(line.slice(5)));
  }
}
```

**Source**: [Burr + FastAPI + React (TDS)](https://towardsdatascience.com/how-to-build-a-streaming-agent-with-burr-fastapi-and-react-e2459ef527a8/), [Panaversity agent factory SSE](https://agentfactory.panaversity.org/docs/Building-Agent-Factories/fastapi-for-agents/streaming-with-sse)

### 1.4 AG-UI Protocol — the Standard Vocabulary

[AG-UI](https://www.datacamp.com/tutorial/ag-ui) (Agent-User Interaction Protocol, September 2025) is an open, event-based standard built on SSE that defines named event types:

- `RUN_STARTED` / `RUN_FINISHED`
- `STEP_STARTED` / `STEP_FINISHED` — marks sub-task boundaries
- `TEXT_MESSAGE_START` / `TEXT_MESSAGE_CONTENT` / `TEXT_MESSAGE_END` — token-level streaming of agent thought/narration
- `TOOL_CALL_START` / `TOOL_CALL_ARGS` / `TOOL_CALL_END` — streams tool invocation arguments
- `STATE_DELTA` — JSON-Patch diff for shared state
- `INTERRUPT` — pause for human approval

Compatible backends: LangGraph, CrewAI, Mastra, Pydantic AI, LlamaIndex. CopilotKit provides plug-in React components for the entire event vocabulary. **Using AG-UI rather than rolling a custom SSE schema gives a standard UI layer for free.**

**Sources**: [DataCamp AG-UI tutorial](https://www.datacamp.com/tutorial/ag-ui), [CopilotKit 17 event types](https://www.copilotkit.ai/blog/master-the-17-ag-ui-event-types-for-building-agents-the-right-way), [Microsoft DevBlogs AG-UI + Agent Framework](https://devblogs.microsoft.com/agent-framework/ag-ui-multi-agent-workflow-demo/)

### 1.5 Production Replay Recording

Record SSE streams to `.jsonl` for post-mortem replay. One pattern wraps the async generator:

```python
recorder = AgentStreamRecorder("streams/prod.jsonl")
async for event in recorder.record(agent.run(req)):
    yield event
```

Each line captures: session UUID, timestamp offset (relative, not wall-clock), event type, and data. Replay via CLI: `agent-stream replay prod.jsonl --speed 2`. **Source**: [DEV.to — Abhishek Chatterjee](https://dev.to/abhishek_chatterjee_33b9d/i-can-now-replay-any-ai-agent-stream-from-production-heres-how-4bg4)

---

## 2. How Existing Browser Agents Present Their UI

### 2.1 Skyvern — Most Complete Inspectable-Failure UI

Skyvern provides the most detailed built-in run viewer of any open-source browser agent. Key components:

- **Redesigned debugger UI** (shipped September 2025): integrated live browser preview, timeline modes, dynamic panel sizing. [(Skyvern changelog #3384)](https://github.com/Skyvern-AI/skyvern/issues/3384)
- **Step timeline**: per-step status, duration, and action type
- **Diagnostics tab** (per step):
  - Annotated screenshots (elements highlighted with AI decision overlay)
  - Action screenshots (before/after)
  - Element tree (`visible_elements_tree`) — which DOM nodes were detected
  - LLM prompt (`llm_response_parsed`) and raw request
  - Action list — what the model chose and why
  - Page HTML
  - Browser console output
- **Recording tab**: full WebM video of the entire run (start → end)
- **`failure_category` field**: added to tasks and workflow runs for programmatic failure classification
- **Artifact API** (`get_run_artifacts`): HAR files, Playwright traces, network traffic, formatted + raw execution logs
- **Troubleshooting workflow**: check status → find failed step → inspect artifacts → determine fix. Status codes communicate failure type: `completed` = prompt misinterpretation, `terminated` = auth/CAPTCHA block, `timed_out` = task too complex

**Sources**: [Skyvern visualizing results](https://www.skyvern.com/docs/running-tasks/visualizing-results/), [Skyvern troubleshooting guide](https://www.skyvern.com/docs/developers/debugging/troubleshooting-guide), [Skyvern changelog](https://github.com/Skyvern-AI/skyvern/issues/3384)

Frontend stack: TypeScript 23.6% of repo (React-based, in `skyvern-frontend/`). WebSocket/SSE implementation details are not publicly documented but live browser streaming is listed as a first-class feature. [(Skyvern GitHub)](https://github.com/Skyvern-AI/skyvern)

### 2.2 browser-use — Gradio UI with VNC Fallback

[browser-use/web-ui](https://github.com/browser-use/web-ui) is built entirely on **Gradio** (Python 98.9%), not React. It provides:

- LLM-agnostic task input (OpenAI, Anthropic, DeepSeek, Ollama, etc.)
- Persistent browser sessions with visible history
- VNC-based live browser view (`http://localhost:6080/vnc.html`) in Docker deployments
- High-definition screen recording

**Limitation** (acknowledged by maintainers in Issue #146): the Gradio layout cannot simultaneously show the live browser view and agent output stream; users must switch windows. This is the primary driver for replacing it with a custom React UI. There is a minimal `gradio_demo.py` in the core repo but no step-timeline or failure-inspection view.

**Sources**: [browser-use/web-ui GitHub](https://github.com/browser-use/web-ui), [Issue #146 custom UI discussion](https://github.com/browser-use/browser-use/issues/146)

### 2.3 Stagehand — No Built-In Run Viewer

Stagehand focuses on the SDK layer (act/extract/observe/agent primitives) with no native run viewer. Live debugging relies on Browserbase's hosted infrastructure when deployed there. **Source**: [Stagehand GitHub](https://github.com/browserbase/stagehand), [Stagehand docs](https://docs.stagehand.dev/v2/best-practices/build-agent)

### 2.4 Browserbase — CDP Screencast Session Recordings

Browserbase ships a production-grade session recording system (launched 2025):

- Underlying mechanism: CDP (`Page.startScreencast`) captures PNG frames when meaningful visual changes occur — not a fixed frame rate, minimizing browser load
- Frames are timestamped with **sub-second precision**
- **Multi-tab support**: up to 10 tabs recorded simultaneously with synchronized timeline
- HLS delivery for **instant seeking** (first 30 s encoded eagerly; remainder encoded on-demand)
- Viewer allows tab switching without altering timestamps
- Post-run (not real-time), though playback can begin within seconds via HLS

For real-time live streaming, Browserbase exposes a CDP endpoint accessible during the session.

**Sources**: [Browserbase session recordings blog](https://www.browserbase.com/blog/session-recordings), [Browserbase changelog](https://www.browserbase.com/changelog/session-recordings)

### 2.5 What a Good "Inspectable Failure" View Shows

Drawing from Skyvern's diagnostics tab and Browserbase's CDP recordings, a complete inspectable-failure view needs:

| Layer | Data | How to Capture |
|-------|------|----------------|
| Visual state | Per-step screenshot (annotated with chosen element) | Playwright `page.screenshot()` at each action |
| DOM snapshot | Element tree at decision time | CDP `DOMSnapshot.captureSnapshot` or Playwright ARIA snapshot |
| LLM trace | Full prompt + raw model response + parsed action | Log at agent step boundary |
| Locator | CSS/XPath selector used + confidence score | Instrument the locator resolution layer |
| Action outcome | Success/failure + HTTP status + JS errors | `page.on('console')`, response interceptors |
| Failure class | Timeout / element-not-found / auth-block / LLM-parse-error / CAPTCHA | Classify in the except handler, emit as SSE `error` event |
| Retry chain | Which retries were attempted, locator fallbacks used | Emit as `retry_attempt` SSE events |
| Network | HAR file or Playwright trace | `page.route()` + `browser.newContext({ recordHar })` |

---

## 3. Trace / Observability Tooling

### 3.1 Langfuse — Screenshot Attachments + Graph View

Langfuse supports attaching screenshots directly to spans via `LangfuseMedia`:

```python
from langfuse.media import LangfuseMedia

screenshot_bytes = await page.screenshot()
media = LangfuseMedia(content_bytes=screenshot_bytes, content_type="image/png")
span.update(input={"screenshot": media, "url": page.url, "action": chosen_action})
```

The Langfuse UI renders PNG/JPG/WebP inline in the trace viewer. Media is uploaded to object storage; the span holds a reference token. Auto-extraction handles base64 URIs embedded in multimodal LLM payloads.

**Agent graph view** (GA as of November 2025): visualizes the conceptual agent graph from span nesting and timing. Works with any framework or custom instrumentation. Also added: **Log View** — a single scrollable concatenation of all trace observations for linear step-by-step debugging.

**Limitation**: Langfuse has no built-in PII/secret redaction. Teams must sanitize before passing data to `span.update()`. Third-party libraries (LLM Guard, custom regex) handle this upstream.

**Sources**: [Langfuse multi-modality docs](https://langfuse.com/docs/tracing-features/multi-modality), [Langfuse for agents changelog](https://langfuse.com/changelog/2025-11-05-langfuse-for-agents), [Langfuse graph view](https://langfuse.com/changelog/2025-02-14-trace-graph-view)

### 3.2 Laminar — Browser-Agent Session Replay (Unique Differentiator)

Laminar is the only platform (as of mid-2026) that provides **synchronized browser session replay alongside trace spans** — you see what the agent saw while stepping through spans. It also provides an "agent rollout debugger" and supports replaying agents from mid-trace to test fixes.

Integration list includes Browser Use, Stagehand, and Playwright out-of-the-box.

**Sources**: [Laminar vs Langfuse vs LangSmith (2026)](https://laminar.sh/blog/2026-01-29-laminar-vs-langfuse-vs-langsmith-llm-observability-compared), [Laminar top 6 observability platforms](https://laminar.sh/article/2026-04-23-top-6-agent-observability-platforms), [Skyvern observability with Laminar](https://www.skyvern.com/docs/observability/overview)

### 3.3 Arize Phoenix — Self-Hosted, Open Source

[Arize Phoenix](https://arize.com/phoenix/) is self-hosted (ELv2 license, 9k+ GitHub stars), deployable via Docker or Kubernetes. Key features:

- Traces every step: LLM prompts, retrieval, tool calls, outputs
- **Span Replay**: re-execute past spans with new prompts/models to verify a fix
- Supports LangGraph, LlamaIndex, CrewAI, Claude Agent SDK, OpenAI Agents SDK
- Can be deployed on Railway (one-click template at [railway.com/deploy/phoenix](https://railway.com/deploy/phoenix))
- No native browser session replay; screenshot support requires custom span attachments

For teams that cannot send trace data to a SaaS platform (data residency, PII concerns), Phoenix is the self-hosted alternative to Langfuse.

**Sources**: [Arize Phoenix docs](https://arize.com/docs/phoenix), [Phoenix on Railway](https://railway.com/deploy/phoenix)

### 3.4 LangSmith

LangSmith added OpenTelemetry ingestion (March 2026). Best for LangChain/LangGraph-native teams. No browser session replay. Visualizes LangGraph execution graphs via LangGraph Studio.

**Source**: [LangSmith observability](https://www.langchain.com/langsmith/observability), [Agent observability comparison 2026](https://www.digitalapplied.com/blog/agent-observability-platforms-langsmith-langfuse-arize-2026)

### 3.5 OpenTelemetry GenAI Semantic Conventions

OTel GenAI semconv (v1.41.0, May 2026, **Development** status) defines:

| Span type | Key attributes |
|-----------|---------------|
| `invoke_agent` (CLIENT/INTERNAL) | `gen_ai.agent.name`, `gen_ai.provider.name` |
| `execute_tool` (INTERNAL) | `gen_ai.tool.name`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` |
| `invoke_workflow` (INTERNAL) | Predefined workflow execution |
| LLM call (CLIENT) | `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.response.finish_reasons` |

Content capture events: `gen_ai.client.inference.operation.details` captures full conversation (opt-in, privacy-gated).

Adopt with `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`. Backend support: Datadog, Honeycomb, New Relic, Langfuse, LangSmith, Phoenix all ingest these spans as of mid-2026.

**Instrument browser-automation agent tool calls** by wrapping each Playwright action (navigate, click, fill, screenshot) as an `execute_tool` span with `gen_ai.tool.name = "playwright.click"` and `gen_ai.tool.call.arguments = {"selector": "..."}`.

**Sources**: [OTel GenAI agent spans spec](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/), [Greptime OTel GenAI conventions deep-dive](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)

---

## 4. Deployment: Stateful Browser-Agent Backend + Frontend

### 4.1 Chromium in Docker — Non-Negotiable Requirements

These apply regardless of which platform is used:

1. **Base image**: Use official Playwright image (`mcr.microsoft.com/playwright:v1.40.0-jammy`) or `zenika/alpine-chrome:with-playwright`. Avoid Alpine for Playwright — musl/glibc incompatibility causes binary failures. **Do not use Alpine**.
2. **`/dev/shm`**: Docker defaults to 64 MB. Chromium uses it for rendering and crashes below ~128 MB. Either set `shm_size: '2gb'` in `docker-compose.yml` **or** pass `--disable-dev-shm-usage` in Playwright launch args.
3. **Launch flags**: `--disable-gpu --disable-dev-shm-usage --no-sandbox` (no-sandbox required only if running as root — avoid root).
4. **Non-root user**: Never run Chromium as root. Playwright must be installed by the non-privileged user to correctly cache to `/home/pwuser/.cache/ms-playwright`.
5. **Init process**: Add `init: true` (docker-compose) or install `tini` to prevent zombie subprocesses.
6. **Memory budget**: minimum 2 GB per machine; 4 GB+ for concurrent sessions. Per-session overhead: 200–500 MB per active tab depending on page complexity.

**Sources**: [Playwright + Chromium Docker guide](https://thomasbourimech.com/blog/en/playwright-chromium-docker-production/), [Fly.io Playwright community thread](https://community.fly.io/t/playwright-not-working/6784)

### 4.2 Fly.io

**Recommended for this project.**

- Deploy with `fly launch` from a Docker image.
- Default VM size is `micro-2x` (0.25 CPU, 512 MB RAM) — **insufficient for Chromium**. Scale to at least `performance-2x` (2 CPU, 4 GB RAM): `fly scale vm performance-2x --memory 4096`.
- Persistent state: Fly Volumes (block storage) attached per region.
- Long-running browser sessions: use `auto_stop_machines = false` in `fly.toml` for always-on, or configure `auto_stop_machines = "stop"` + warm-start for on-demand.
- Working Docker approach: use `zenika/alpine-chrome:with-playwright` or MCR Playwright as base; set `executablePath` to `/usr/bin/chromium-browser`; add `chromiumSandbox: false`.
- **No hard timeout limit on long-running HTTP responses** — SSE streams survive as long as the connection stays open and the machine is running.

**Sources**: [macarthur.me Puppeteer + Fly.io](https://macarthur.me/posts/puppeteer-with-docker/), [Fly.io community Playwright thread](https://community.fly.io/t/playwright-not-working/6784), [Fly.io FastAPI guide](https://fly.io/docs/python/frameworks/fastapi/)

### 4.3 Railway

- Steel Browser one-click template: deploys API (port 3000) + web UI dashboard (`/ui`) + CDP endpoint (port 9223, private network). Logs stored in DuckDB on a Railway volume. **Source**: [railway.com/deploy/steel-browser](https://railway.com/deploy/steel-browser)
- **Minimum 2 GB RAM; recommended 4 GB.** Chromium adds ~200–500 MB per active session.
- Volumes: available on Hobby ($5/mo) and Pro plans; live-resize supported on Pro.
- Arize Phoenix also has a Railway one-click deploy.
- Simpler UI/team workflow than Fly.io; less control over machine type.

**Source**: [Fly.io vs Railway 2026](https://www.kunalganglani.com/blog/fly-io-vs-railway), [Railway volumes docs](https://docs.railway.com/volumes/reference)

### 4.4 Render

- Official browser-use Render template ([render.com/templates/browser-use](https://render.com/templates/browser-use)) deploys a FastAPI `/run` POST endpoint built on the Playwright Python Docker image with Chromium pre-installed.
- **No frontend UI included** in the template — backend API only.
- `render.yaml` blueprint enables one-click deploy from a forked repo.
- Memory/CPU not specified in template; Render's starter instances (512 MB RAM) are insufficient; upgrade to at least the Standard plan (2 GB RAM).

**Source**: [Render browser-use template](https://render.com/templates/browser-use)

### 4.5 Zeabur

[UNVERIFIED] No Zeabur-specific Playwright/Chromium deployment documentation was found during research. Zeabur uses Docker-based deployment similar to Railway. Memory limits and Chromium compatibility are not publicly documented. Do not rely on Zeabur for this workload without direct testing.

### 4.6 Browserless / Steel as Managed Browser Infrastructure

An alternative to self-managing Chromium: offload browser orchestration to [Browserless](https://www.browserless.io/) (173M+ Docker pulls) or [Steel](https://railway.com/deploy/steel-browser) (open-source, self-hostable). Both expose a CDP or Playwright-compatible endpoint. The agent backend connects to the managed browser over CDP, eliminating the need to run Chromium inside the agent process itself.

This separates concerns: agent API (thin, stateless) + managed browser (stateful, memory-isolated).

### 4.7 Minimal Realistic Production Stack

```
┌──────────────────────────────────────────────┐
│  Fly.io Machine (performance-2x, 4 GB RAM)   │
│                                              │
│  [Docker image: mcr playwright jammy]        │
│                                              │
│  ┌────────────────┐   ┌───────────────────┐  │
│  │  FastAPI app   │   │  Playwright /     │  │
│  │  (uvicorn)     │──▶│  Chromium         │  │
│  │  :8080         │   │  (subprocess)     │  │
│  └────────────────┘   └───────────────────┘  │
│          │                                   │
│  ┌───────────────────────────────────────┐   │
│  │  Fly Volume: /data (trace JSONL logs) │   │
│  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
         │  SSE events
         ▼
┌──────────────────────────────────────────────┐
│  Vercel / Cloudflare Pages                   │
│  React + Vite + CopilotKit (AG-UI consumer)  │
└──────────────────────────────────────────────┘
         │  spans + screenshots
         ▼
┌──────────────────────────────────────────────┐
│  Langfuse (self-hosted on Railway) or        │
│  Arize Phoenix (self-hosted on Railway)      │
└──────────────────────────────────────────────┘
```

### 4.8 Real-Browser Escalation over CDP (`BROWSER_CDP_URL`) — Three Docker Topologies

The default `PlaywrightProvider` launches a headless Chromium inside the container —
fine for bot-wall-free sites, but a headless / fresh-profile browser trips anti-bot
interstitials on sites like Amazon (`UNSUPPORTED_SITES.md`). The swappable
`CDPProvider` (`backend/app/browser/provider.py`) instead connects Playwright over CDP
(`connect_over_cdp`) to an **externally-managed real browser**. Set `BROWSER_CDP_URL`
to switch; leave it unset for the default headless path (byte-identical to before). The
agent logic, SSE event stream, and per-step screenshots all work unchanged — the CDP
target is a real Playwright `Page` (verified: `page.screenshot()` returns valid PNG).

| Topology | `BROWSER_CDP_URL` | Bypasses anti-bot? | Docker networking |
|---|---|---|---|
| **A. Managed service (Steel/Browserbase)** ⭐ | `wss://connect.steel.dev?apiKey=…` / Browserbase `session.connectUrl` | **Yes** (residential IP + stealth) | none — container makes an outbound WSS |
| **B. Container → host's real Chrome** | `http://<HOST-IP>:9222` (an **IP**, never a hostname) | **Yes** (trusted real profile) | host-reachable + Chrome bound `0.0.0.0` |
| **C. Chrome inside the same image** | `http://127.0.0.1:9222` | **No** (datacenter IP + fresh profile → still walled) | none (same loopback) |

**A — Managed browser (recommended for cloud).** No Chromium in the image, no
host-networking: the container opens an outbound secure WebSocket to the provider, which
runs a stealth browser on a residential / anti-detect IP — that is the actual anti-bot
bypass (their product). Extends §4.6.

```yaml
# docker-compose.yml (excerpt) — nothing else needed; the browser is remote
services:
  agent:
    image: <your-image>
    environment:
      BROWSER_CDP_URL: "wss://connect.steel.dev?apiKey=${STEEL_API_KEY}"
```

**B — Host's real Chrome (fits the desktop self-host deployment).** When the backend
container runs on the same desktop as a real, trusted Chrome (e.g. one managed by
actionbook on CDP port 18800/9222), point the container at the host. Two gotchas:
- Chrome must bind beyond localhost: launch it with
  `--remote-debugging-address=0.0.0.0 --remote-debugging-port=9222`.
- **Use the host IP, not a hostname.** Chrome (66+) rejects the HTTP `/json` probe that
  Playwright sends first if the `Host` header is not an IP or `localhost` (DNS-rebinding
  protection), so `host.docker.internal` (a hostname) is rejected. Resolve it to the host
  IP and pass `http://<HOST-IP>:9222`, or front Chrome with a `socat`/proxy that rewrites
  `Host: localhost`.

```yaml
services:
  agent:
    extra_hosts: ["host.docker.internal:host-gateway"]   # Linux; resolve to IP at entrypoint
    environment:
      BROWSER_CDP_URL: "http://${HOST_IP}:9222"
```

**C — Chrome in the image (NOT for anti-bot).** Simplest networking (same loopback, no
Host-header issue), but a containerised Chrome has a datacenter IP and a fresh profile,
so anti-bot sites still block it — no gain over default headless. Only worth it if you
need a real (headed) Chrome window for non-anti-bot reasons; run it under Xvfb with the
§4.1 hardening (`--disable-dev-shm-usage`, non-root, `shm_size: 2gb`).

**Security:** topologies A/B drive a real, possibly logged-in profile, so screenshots may
capture that profile's PII — keep the screenshots dir a git-ignored secret and rely on
the §5 serialization-time redaction. `CDPProvider.close()` only closes the agent's own
tab, never the external browser or its other tabs.

**Sources**: [Chrome remote-debugging Host-header change (Chrome 66+)](https://developer.chrome.com/blog/remote-debugging-port), [Steel.dev — connect with Playwright (`connectOverCDP('wss://connect.steel.dev?apiKey=…')`)](https://docs.steel.dev/overview/guides/connect-with-playwright-node), [Browserbase — Playwright `connectOverCDP(session.connectUrl)`](https://docs.browserbase.com/introduction/playwright), [host.docker.internal + Chrome remote debugging in Docker](https://sahajamit.medium.com/can-selenium-chrome-dev-tools-recipe-works-inside-a-docker-container-afff92e9cce5)

---

## 5. Security in the Frontend

### 5.1 API Keys — Never in Code or Traces

- Load all LLM provider keys, browser auth credentials, and database URLs from environment variables at runtime (`process.env` / `os.getenv`). Never hardcode.
- When storing traces, **redact keys before the span is created** — not after. Apply regex at the SSE serialization layer:

```python
import re

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{32,}"),           # OpenAI keys
    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]{20,}"),  # Bearer tokens
    re.compile(r"(?i)(api[_-]?key|token)\s*[:=]\s*\S+"),
]

def redact_secrets(text: str) -> str:
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text
```

Apply `redact_secrets()` to every string before it enters any span attribute, log line, or SSE `data:` field.

**Source**: [Doppler advanced LLM security](https://www.doppler.com/blog/advanced-llm-security)

### 5.2 Captured Cookies / Auth Headers

Browser automation sessions capture cookies, `Authorization` headers, and session tokens in page context. These must never appear in:

- SSE event payloads (the `data:` field going to the browser frontend)
- Langfuse/Phoenix span attributes
- Recorded JSONL replay files
- Screenshots displayed in the UI (redact credential form fields before screenshot)

Pattern:

```python
# After each navigation, scrub auth state from the step record
step_record["request_headers"] = {
    k: "[REDACTED]" if k.lower() in ("authorization", "cookie", "x-auth-token") else v
    for k, v in step_record["request_headers"].items()
}
```

For HAR files stored in Playwright traces, use `recordHar({ omitContent: true })` to exclude response bodies. Store HAR files on a Fly Volume or S3 with IAM-restricted access — never serve them directly through the public-facing frontend.

**Sources**: [OWASP Agentic Applications Top 10 2026 (referenced in multiple LLM security articles)](https://www.oligo.security/academy/llm-security-in-2025-risks-examples-and-best-practices), [Doppler AI secret leakage](https://www.doppler.com/blog/ai-secret-leakage-llm-training-code-review)

### 5.3 PII in Page Content

Screenshots and DOM snapshots from logged-in sessions may contain user PII (names, emails, account numbers). Options:

1. **Client-side only**: never store screenshots containing PII; display them transiently in the SSE stream and discard server-side.
2. **Blur/mask before storage**: apply a server-side image processing step (e.g., OpenCV rectangle over known PII regions from the DOM).
3. **Store with access control**: write screenshots to S3/R2 with short-lived signed URLs; the frontend requests signed URLs per-step, not raw image bytes.

LiteLLM proxy has a built-in [Secret Detection guardrail](https://docs.litellm.ai/docs/proxy/guardrails/secret_detection) (Enterprise) that scans LLM inputs/outputs for secrets.

**Sources**: [Prediction Guard PII guide](https://predictionguard.com/blog/pii-detection-redaction-llm-pipelines-regulated-industries), [Kong PII sanitization](https://konghq.com/blog/enterprise/building-pii-sanitization-for-llms-and-agentic-ai), [LiteLLM secret detection](https://docs.litellm.ai/docs/proxy/guardrails/secret_detection)

### 5.4 Trace Store Access

Never make the observability backend (Langfuse, Phoenix) publicly accessible. Put it behind:
- Fly.io private network (`.internal` DNS) or
- Railway private network (CDP port 9223 is already private-only in the Steel template)

Only the agent backend reads/writes spans. The frontend queries the agent backend API for trace data (filtered, redacted); it never talks directly to the observability store.

---

## Data & Comparisons

### Observability Platform Matrix

| Platform | Open Source | Self-Host | Browser Session Replay | Screenshot Spans | Agent Graph View |
|----------|-------------|-----------|----------------------|------------------|-----------------|
| Langfuse | Yes (ELv2) | Yes | No | Yes (LangfuseMedia) | Yes (Nov 2025 GA) |
| Arize Phoenix | Yes (ELv2) | Yes | No | Via custom spans | Limited |
| Laminar | No | No (SaaS) | **Yes** (unique) | Yes | Yes |
| LangSmith | No | No (SaaS) | No | Limited | Via LangGraph Studio |

### Platform Deployment Matrix

| Platform | Docker Support | Min RAM for Chromium | Volumes | Auto-scale | Notes |
|----------|---------------|----------------------|---------|------------|-------|
| Fly.io | Yes | 2–4 GB (`performance-2x`) | Fly Volumes | Manual (`fly scale`) | Best control; preferred |
| Railway | Yes | 2–4 GB (Hobby plan) | Yes (Hobby+) | Auto | Simpler UX; Steel template |
| Render | Yes | 2 GB (Standard plan) | Yes | Yes | browser-use template; backend-only |
| Zeabur | Yes [UNVERIFIED] | Unknown | Unknown | Unknown | No confirmed Chromium docs |

---

## Risks & Gaps

1. **AG-UI maturity**: The protocol (September 2025) is young. CopilotKit React components handle the standard events, but `screenshot_taken` is not a named event in the current AG-UI spec — custom event types are needed for visual steps.
2. **Fly.io timeout for SSE**: No hard limit documented for persistent SSE connections, but Fly's HTTP proxy may impose idle-connection timeouts. Test with `fly proxy` and check whether heartbeat pings (`data: keep-alive\n\n`) are needed at intervals. [UNVERIFIED exact timeout]
3. **Zeabur Chromium**: No deployment guide found. Treat as unsupported until verified.
4. **Laminar pricing**: Laminar is SaaS-only; no self-hosted option. For data-residency requirements, use Langfuse or Phoenix.
5. **Binary images in SSE**: Base64-encoding a 1 MB screenshot adds ~33% overhead and may stall the SSE stream under slow connections. Use signed S3/R2 URLs instead, emitting only the URL in the SSE `data:` field.

---

## Conclusions

1. **SSE over WebSocket** for agent step streaming — simpler, stateless-scalable, browser-native reconnect. Use AG-UI event vocabulary (CopilotKit React) for standard step events.
2. **Langfuse + `LangfuseMedia`** for recording screenshots into spans — the clearest path to a trace viewer with per-step visual state, self-hostable.
3. **Skyvern's diagnostic schema** is the best reference implementation for what to show per step: annotated screenshot, element tree, LLM prompt, chosen action, failure_category.
4. **Fly.io `performance-2x` + 4 GB RAM** is the recommended deployment platform for Chromium + FastAPI in a single Docker image.
5. **Redact at SSE serialization** — not post-hoc — for secrets, auth headers, and PII. Never let raw cookies or API keys reach span attributes or replay files.

---

## Sources

1. [WebSockets and AI: Why LLMs Are Moving Beyond SSE — websocket.org](https://websocket.org/guides/websockets-and-ai/)
2. [SSE vs WebSockets for Streaming LLM Responses — buildmvpfast.com](https://www.buildmvpfast.com/blog/streaming-llm-responses-sse-vs-websockets-2026)
3. [HTTP Streaming, SSE, or WebSockets for Conversational LLM — Medium/Anurag Chatterjee](https://tech-depth-and-breadth.medium.com/comparing-real-time-communication-options-http-streaming-sse-or-websockets-for-conversational-74c12f0bd7bc)
4. [Streaming AI Agents Responses with SSE — Medium/Anurag Kumar](https://akanuragkumar.medium.com/streaming-ai-agents-responses-with-server-sent-events-sse-a-technical-case-study-f3ac855d0755)
5. [How to Build a Streaming Agent with Burr, FastAPI, and React — Towards Data Science](https://towardsdatascience.com/how-to-build-a-streaming-agent-with-burr-fastapi-and-react-e2459ef527a8/)
6. [Streaming with SSE — Panaversity Agent Factory](https://agentfactory.panaversity.org/docs/Building-Agent-Factories/fastapi-for-agents/streaming-with-sse)
7. [AG-UI Overview — DataCamp Tutorial](https://www.datacamp.com/tutorial/ag-ui)
8. [CopilotKit: Master the 17 AG-UI Event Types](https://www.copilotkit.ai/blog/master-the-17-ag-ui-event-types-for-building-agents-the-right-way)
9. [AG-UI + Microsoft Agent Framework Workflows — Microsoft DevBlogs](https://devblogs.microsoft.com/agent-framework/ag-ui-multi-agent-workflow-demo/)
10. [I Can Now Replay Any AI Agent Stream from Production — DEV.to](https://dev.to/abhishek_chatterjee_33b9d/i-can-now-replay-any-ai-agent-stream-from-production-heres-how-4bg4)
11. [Skyvern: Automate browser-based workflows — GitHub](https://github.com/Skyvern-AI/skyvern)
12. [Skyvern: Visualizing Results — docs](https://www.skyvern.com/docs/running-tasks/visualizing-results/)
13. [Skyvern: Troubleshooting Guide — docs](https://www.skyvern.com/docs/developers/debugging/troubleshooting-guide)
14. [Skyvern Changelog Week of September 1–7, 2025 — GitHub Issue #3384](https://github.com/Skyvern-AI/skyvern/issues/3384)
15. [Skyvern Observability with Laminar — docs](https://www.skyvern.com/docs/observability/overview)
16. [browser-use/web-ui — GitHub](https://github.com/browser-use/web-ui)
17. [browser-use Issue #146: Brand New WebUI Discussion](https://github.com/browser-use/browser-use/issues/146)
18. [Stagehand SDK — GitHub](https://github.com/browserbase/stagehand)
19. [Browserbase: This Week We Fixed the Worst Part — blog](https://www.browserbase.com/blog/session-recordings)
20. [Browserbase Session Recordings Changelog](https://www.browserbase.com/changelog/session-recordings)
21. [Langfuse Multi-Modality Documentation](https://langfuse.com/docs/tracing-features/multi-modality)
22. [Langfuse for Agents — November 2025 Changelog](https://langfuse.com/changelog/2025-11-05-langfuse-for-agents)
23. [Langfuse Graph View for LangGraph Traces — Changelog](https://langfuse.com/changelog/2025-02-14-trace-graph-view)
24. [Langfuse Security & Guardrails — docs](https://langfuse.com/docs/security-and-guardrails)
25. [Laminar vs Langfuse vs LangSmith (2026) — laminar.sh](https://laminar.sh/blog/2026-01-29-laminar-vs-langfuse-vs-langsmith-llm-observability-compared)
26. [Top 6 Agent Observability Platforms 2026 — laminar.sh](https://laminar.sh/article/2026-04-23-top-6-agent-observability-platforms)
27. [Agent Observability: LangSmith, Langfuse, Arize 2026 — digitalapplied.com](https://www.digitalapplied.com/blog/agent-observability-platforms-langsmith-langfuse-arize-2026)
28. [Arize Phoenix: AI Observability & Evaluation — GitHub](https://github.com/Arize-ai/phoenix)
29. [Arize Phoenix — docs](https://arize.com/docs/phoenix)
30. [Deploy Phoenix on Railway](https://railway.com/deploy/phoenix)
31. [OTel GenAI Agent Spans Spec — opentelemetry.io](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
32. [OpenTelemetry for AI Agents — Greptime blog](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)
33. [Playwright + Chromium Docker Production Guide — thomasbourimech.com](https://thomasbourimech.com/blog/en/playwright-chromium-docker-production/)
34. [Fly.io Playwright Community Thread](https://community.fly.io/t/playwright-not-working/6784)
35. [Run Puppeteer with Docker on Fly.io — macarthur.me](https://macarthur.me/posts/puppeteer-with-docker/)
36. [Steel Browser on Railway — railway.com](https://railway.com/deploy/steel-browser)
37. [Render browser-use template](https://render.com/templates/browser-use)
38. [Fly.io vs Railway 2026 — kunalganglani.com](https://www.kunalganglani.com/blog/fly-io-vs-railway)
39. [Doppler: Advanced LLM Security — Preventing Secret Leakage](https://www.doppler.com/blog/advanced-llm-security)
40. [LLM Guardrails Best Practices — Datadog](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
41. [PII Detection and Redaction for LLM Pipelines — Prediction Guard](https://predictionguard.com/blog/pii-detection-redaction-llm-pipelines-regulated-industries)
42. [LiteLLM: Secret Detection Guardrail](https://docs.litellm.ai/docs/proxy/guardrails/secret_detection)
43. [Kong PII Sanitization for LLMs and Agentic AI](https://konghq.com/blog/enterprise/building-pii-sanitization-for-llms-and-agentic-ai)
44. [Browserless: Deploy Headless Browsers in Docker — GitHub](https://github.com/browserless/browserless)
45. [Browser Tools: browser-use, Stagehand, Skyvern — DEV.to](https://dev.to/stevengonsalvez/browser-tools-for-ai-agents-part-2-the-framework-wars-browser-use-stagehand-skyvern-4gn)
