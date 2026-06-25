import { useMemo, useReducer, useRef, useState } from "react";
import { StepDetail } from "./StepDetail.jsx";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "";

const STREAM_EVENTS = [
  "RUN_STARTED",
  "RUN_FINISHED",
  "RUN_ERROR",
  "STEP_STARTED",
  "STEP_FINISHED",
  "TOOL_CALL_START",
  "TOOL_CALL_ARGS",
  "TOOL_CALL_END",
  "TEXT_MESSAGE",
  "SCREENSHOT_ANNOTATED",
  "LOCATOR_RESOLVED",
  "ASK_USER",
  "RECOVERY",
];

const TERMINAL = new Set(["RUN_FINISHED", "RUN_ERROR"]);

const initialState = { run: null, steps: [], order: [], notices: [] };

function reduce(state, ev) {
  const { type, payload } = ev;
  if (type === "RUN_STARTED") {
    return { run: { id: payload.run_id, task: payload.task, status: "running" }, steps: [], order: [], notices: [] };
  }
  if (type === "RUN_FINISHED") {
    return {
      ...state,
      run: {
        ...state.run,
        status: "finished",
        nominal: payload.nominal_completion,
        verified: payload.verified_completion,
        tokens: payload.tokens,
      },
    };
  }
  if (type === "RUN_ERROR") {
    return { ...state, run: { ...state.run, status: "error", error: payload.error } };
  }

  const stepId = payload.step_id ?? payload.call_id;
  if (type === "TEXT_MESSAGE") {
    return { ...state, notices: [...state.notices, { kind: "text", ...payload }] };
  }
  if (type === "ASK_USER") {
    const steps = upsert(state, payload.step_id, (s) => ({ ...s, askUser: payload.question }));
    return { ...steps, notices: [...state.notices, { kind: "ask", ...payload }] };
  }
  if (!stepId) return state;

  switch (type) {
    case "STEP_STARTED":
      return upsert(state, stepId, (s) => ({ ...s, description: payload.description, status: "running" }));
    case "STEP_FINISHED":
      return upsert(state, stepId, (s) => ({
        ...s,
        status: payload.status,
        failureCategory: payload.failure_category ?? s.failureCategory,
      }));
    case "LOCATOR_RESOLVED":
      return upsert(state, stepId, (s) => ({ ...s, tier: payload.tier, strategy: payload.strategy }));
    case "SCREENSHOT_ANNOTATED":
      return upsert(state, stepId, (s) => ({ ...s, shots: [...(s.shots ?? []), payload] }));
    case "RECOVERY":
      return upsert(state, stepId, (s) => ({ ...s, recoveries: [...(s.recoveries ?? []), payload] }));
    case "TOOL_CALL_START":
      return upsert(state, stepId, (s) => ({
        ...s,
        calls: [...(s.calls ?? []), { call_id: payload.call_id, tool: payload.tool }],
      }));
    case "TOOL_CALL_ARGS":
      return patchCall(state, payload.call_id, (c) => ({ ...c, args: payload.args }));
    case "TOOL_CALL_END":
      return patchCall(state, payload.call_id, (c) => ({ ...c, result: payload.result }));
    default:
      return state;
  }
}

function upsert(state, id, fn) {
  const exists = state.steps.some((s) => s.id === id);
  const steps = exists ? state.steps.map((s) => (s.id === id ? fn(s) : s)) : [...state.steps, fn({ id, status: "running" })];
  const order = exists ? state.order : [...state.order, id];
  return { ...state, steps, order };
}

function patchCall(state, callId, fn) {
  const steps = state.steps.map((s) =>
    (s.calls ?? []).some((c) => c.call_id === callId)
      ? { ...s, calls: s.calls.map((c) => (c.call_id === callId ? fn(c) : c)) }
      : s
  );
  return { ...state, steps };
}

const STATUS_LABEL = { running: "running", ok: "passed", failed: "failed" };

export default function App() {
  const [task, setTask] = useState("");
  const [url, setUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(null);
  const [authed, setAuthed] = useState(() => localStorage.getItem("ba_authed") === "1");
  const [state, dispatch] = useReducer(reduce, initialState);
  const sourceRef = useRef(null);

  const steps = state.steps;
  const selectedStep = useMemo(() => steps.find((s) => s.id === selected) ?? null, [steps, selected]);
  const run = state.run;

  async function unlock(token) {
    const res = await fetch(`${BACKEND}/auth`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ token }),
    });
    if (res.ok) {
      localStorage.setItem("ba_authed", "1");
      setAuthed(true);
      return null;
    }
    return res.status === 503 ? "Server has no access token configured." : "Invalid access token.";
  }

  if (!authed) return <AuthGate onUnlock={unlock} />;

  function start() {
    if (!task.trim() || running) return;
    sourceRef.current?.close();
    dispatch({ type: "RUN_STARTED", payload: { run_id: "—", task } });
    setSelected(null);
    setRunning(true);

    const params = new URLSearchParams({ task });
    if (url.trim()) params.set("url", url.trim());
    const es = new EventSource(`${BACKEND}/agent/run?${params.toString()}`, { withCredentials: true });
    sourceRef.current = es;

    const onAny = (e) => {
      const parsed = JSON.parse(e.data);
      dispatch(parsed);
      if (TERMINAL.has(parsed.type)) {
        es.close();
        setRunning(false);
      }
    };
    STREAM_EVENTS.forEach((name) => es.addEventListener(name, onAny));
    es.onerror = () => {
      es.close();
      setRunning(false);
    };
  }

  function stop() {
    sourceRef.current?.close();
    setRunning(false);
  }

  return (
    <main className="app">
      <header className="head">
        <h1>browser-agent</h1>
        <p className="disclosure">
          Supported: bot-wall-free public sites (search, browse, forms, extraction). Login / MFA / CAPTCHA /
          anti-bot walls are routed to “unsupported” — never evaded.
        </p>
      </header>

      <form
        className="runbar"
        onSubmit={(e) => {
          e.preventDefault();
          start();
        }}
      >
        <label className="field">
          <span>Task</span>
          <input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Describe a task in natural language"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="field url">
          <span>Start URL (optional)</span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
            autoComplete="off"
            spellCheck={false}
            inputMode="url"
          />
        </label>
        {running ? (
          <button type="button" className="btn ghost" onClick={stop}>
            Stop
          </button>
        ) : (
          <button type="submit" className="btn" disabled={!task.trim()}>
            Run
          </button>
        )}
      </form>

      {run && <RunVerdict run={run} />}

      <section className="board">
        <ol className="timeline" aria-live="polite" aria-label="Step timeline">
          {steps.length === 0 && <li className="empty">No steps yet. Submit a task to watch the agent work.</li>}
          {steps.map((s, i) => (
            <li key={s.id}>
              <button
                className={`steprow ${s.status} ${selected === s.id ? "active" : ""}`}
                onClick={() => setSelected(s.id)}
                aria-pressed={selected === s.id}
              >
                <span className="num">{i + 1}</span>
                <span className="desc">{s.description ?? s.id}</span>
                <span className={`badge ${s.status}`}>{STATUS_LABEL[s.status] ?? s.status}</span>
                {s.tier != null && <span className="tier">L{s.tier}</span>}
                {s.failureCategory && <span className="fcat">{s.failureCategory}</span>}
              </button>
            </li>
          ))}
        </ol>

        <aside className="detail">
          {selectedStep ? (
            <StepDetail step={selectedStep} backend={BACKEND} />
          ) : (
            <p className="hint">Select a step to inspect its diagnostics — locator tier, recovery chain, annotated screenshot, and verdict.</p>
          )}
        </aside>
      </section>

      {state.notices.length > 0 && (
        <section className="notices">
          {state.notices.map((n, i) => (
            <p key={i} className={`notice ${n.kind}`}>
              {n.kind === "ask" ? `Ask user: ${n.question}` : n.content}
            </p>
          ))}
        </section>
      )}
    </main>
  );
}

function AuthGate({ onUnlock }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!token.trim() || busy) return;
    setBusy(true);
    setError(null);
    const err = await onUnlock(token.trim()).catch(() => "Could not reach the server.");
    setBusy(false);
    if (err) setError(err);
  }

  return (
    <main className="app gate">
      <header className="head">
        <h1>browser-agent</h1>
        <p className="disclosure">This instance is access-controlled. Enter the access token your operator gave you.</p>
      </header>
      <form className="runbar" onSubmit={submit}>
        <label className="field">
          <span>Access token</span>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="access token"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button type="submit" className="btn" disabled={!token.trim() || busy}>
          {busy ? "Unlocking…" : "Unlock"}
        </button>
      </form>
      {error && <p className="notice ask">{error}</p>}
    </main>
  );
}

function RunVerdict({ run }) {
  if (run.status === "error") {
    return <div className="verdict error">Run error: {run.error}</div>;
  }
  if (run.status !== "finished") {
    return <div className="verdict running">Running…</div>;
  }
  const silent = run.nominal && !run.verified;
  return (
    <>
      <div className={`verdict ${silent ? "silent" : run.verified ? "ok" : "fail"}`}>
        <span>
          Nominal: <strong>{run.nominal ? "complete" : "incomplete"}</strong>
        </span>
        <span>
          Verified: <strong>{run.verified ? "complete" : "incomplete"}</strong>
        </span>
        {silent && <span className="flag">⚠ silent failure (nominal ≠ verified)</span>}
      </div>
      <TokenPanel tokens={run.tokens} />
    </>
  );
}

function _fmt(n) {
  if (n == null) return "—";
  if (n < 1000) return String(n);
  const k = n / 1000;
  return k >= 9.95 ? `${Math.round(k)}k` : `${k.toFixed(1)}k`; // round first: 9999 -> "10k", not "10.0k"
}

function TokenPanel({ tokens }) {
  const t = tokens || {};
  const known = ["output_tokens", "input_tokens", "reasoning_tokens", "total_nano_aiu"].some(
    (k) => t[k]
  );
  if (!known) {
    return <div className="tokens muted">tokens: n/a</div>;
  }
  const aiu = (t.total_nano_aiu ?? 0) / 1e9;
  return (
    <div className="tokens" title="Real LLM token usage for this run (cost transparency)">
      <span className="tlabel">tokens</span>
      <span><strong>{_fmt(t.output_tokens)}</strong> out</span>
      <span><strong>{_fmt(t.input_tokens)}</strong> in</span>
      <span><strong>{_fmt(t.reasoning_tokens)}</strong> reasoning</span>
      <span><strong>{aiu.toFixed(2)}</strong> AIU</span>
    </div>
  );
}
