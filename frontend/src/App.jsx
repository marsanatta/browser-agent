import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { StepDetail } from "./StepDetail.jsx";
import { LiveActivity } from "./LiveActivity.jsx";
import { Hint, LanguageSwitcher } from "./Hint.jsx";

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
  "PLAN_READY",
  "PHASE",
];

const TERMINAL = new Set(["RUN_FINISHED", "RUN_ERROR"]);

const initialState = { run: null, steps: [], order: [], notices: [] };

function reduce(state, ev) {
  const { type, payload } = ev;
  if (type === "RUN_STARTED") {
    return {
      run: { id: payload.run_id, task: payload.task, status: "running", phase: "planning", startedAt: Date.now() },
      steps: [],
      order: [],
      notices: [],
    };
  }
  if (type === "PLAN_READY") {
    return seedPlan(state, payload.run_id, payload.plan ?? []);
  }
  if (type === "PHASE") {
    return { ...state, run: { ...state.run, phase: payload.phase } };
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

function describePlanned(a) {
  if (a.action === "navigate") return `navigate to ${a.url ?? ""}`;
  return `${a.action} '${a.target ?? ""}'`;
}

function seedPlan(state, runId, plan) {
  const known = new Set(state.steps.map((s) => s.id));
  const steps = [...state.steps];
  const order = [...state.order];
  plan.forEach((a, i) => {
    const id = `${runId}-s${i + 1}`;
    if (known.has(id)) return; // a STEP_STARTED already arrived for this id
    steps.push({ id, description: describePlanned(a), status: "pending" });
    order.push(id);
  });
  return { ...state, steps, order };
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

const STATUS_KEY = { pending: "pending", running: "running", ok: "ok", failed: "failed" };

export default function App() {
  const { t } = useTranslation();
  const [task, setTask] = useState("");
  const [url, setUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(null);
  const [authed, setAuthed] = useState(() => localStorage.getItem("ba_authed") === "1");
  const [sessionExpired, setSessionExpired] = useState(false);
  const [state, dispatch] = useReducer(reduce, initialState);
  const sourceRef = useRef(null);

  const steps = state.steps;
  const selectedStep = useMemo(() => steps.find((s) => s.id === selected) ?? null, [steps, selected]);
  const run = state.run;
  const activeStep = useMemo(() => steps.find((s) => s.status === "running") ?? null, [steps]);

  const tailRef = useRef(null);
  const stepCount = steps.length;
  useEffect(() => {
    if (running) tailRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [stepCount, running]);

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
    return res.status === 503 ? t("gate.noTokenConfigured") : t("gate.invalidToken");
  }

  if (!authed) return <AuthGate onUnlock={unlock} expired={sessionExpired} />;

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

    let opened = false;
    let terminated = false;
    es.onopen = () => { opened = true; };
    const onAny = (e) => {
      const parsed = JSON.parse(e.data);
      dispatch(parsed);
      if (TERMINAL.has(parsed.type)) {
        terminated = true;
        es.close();
        setRunning(false);
      }
    };
    STREAM_EVENTS.forEach((name) => es.addEventListener(name, onAny));
    es.onerror = () => {
      if (terminated) return; // clean end: server closed the stream after a terminal event
      es.close();
      setRunning(false);
      // surface the failure instead of freezing the UI on "executing"
      dispatch({ type: "RUN_ERROR", payload: { error: t("verdict.connectionLost") } });
      if (!opened) {
        // never connected -> almost always an expired/invalid access cookie; re-show the gate
        localStorage.removeItem("ba_authed");
        setSessionExpired(true);
        setAuthed(false);
      }
    };
  }

  function stop() {
    sourceRef.current?.close();
    setRunning(false);
  }

  return (
    <main className="app">
      <header className="head">
        <div className="headrow">
          <h1 translate="no">{t("brand")}</h1>
          <LanguageSwitcher />
        </div>
        <p className="disclosure">
          {t("header.disclosure")}
          <Hint k="unsupported" />
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
          <span>
            {t("runbar.task")}
            <Hint k="task" />
          </span>
          <input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder={t("runbar.taskPlaceholder")}
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="field url">
          <span>
            {t("runbar.startUrl")}
            <Hint k="startUrl" />
          </span>
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
          <span className="btnwrap">
            <button type="button" className="btn ghost" onClick={stop}>
              {t("runbar.stop")}
            </button>
            <Hint k="stop" />
          </span>
        ) : (
          <span className="btnwrap">
            <button type="submit" className="btn" disabled={!task.trim()}>
              {t("runbar.run")}
            </button>
            <Hint k="run" />
          </span>
        )}
      </form>

      {run?.status === "running" && (
        <LiveActivity startedAt={run.startedAt} phase={run.phase} activeStepDescription={activeStep?.description} />
      )}
      {run && run.status !== "running" ? <RunVerdict run={run} /> : null}

      <section className="board">
        <ol className="timeline" aria-live="polite" aria-label={t("timeline.label")}>
          {steps.length === 0 && <li className="empty">{t("timeline.empty")}</li>}
          {steps.map((s, i) => (
            <li key={s.id} className={`fade-in ${s.status === "running" ? "is-active" : ""}`}>
              <button
                className={`steprow ${s.status} ${selected === s.id ? "active" : ""}`}
                onClick={() => setSelected(s.id)}
                aria-pressed={selected === s.id}
                aria-current={s.status === "running" ? "step" : undefined}
              >
                <span className="num">{i + 1}</span>
                <span className="desc">{s.description ?? s.id}</span>
                <span className={`badge ${s.status}`}>
                  {STATUS_KEY[s.status] ? t(`status.${STATUS_KEY[s.status]}`) : s.status}
                </span>
                {s.tier != null && <span className="tier">L{s.tier}</span>}
                {s.failureCategory && <span className="fcat">{s.failureCategory}</span>}
              </button>
            </li>
          ))}
          <li ref={tailRef} aria-hidden="true" className="tail" />
        </ol>

        <aside className="detail">
          {selectedStep ? (
            <StepDetail step={selectedStep} backend={BACKEND} />
          ) : (
            <p className="hint">{t("timeline.detailHint")}</p>
          )}
        </aside>
      </section>

      {state.notices.length > 0 && (
        <section className="notices">
          {state.notices.map((n, i) => (
            <p key={i} className={`notice ${n.kind}`}>
              {n.kind === "ask" ? t("notices.askUser", { question: n.question }) : n.content}
            </p>
          ))}
        </section>
      )}
    </main>
  );
}

function AuthGate({ onUnlock, expired }) {
  const { t } = useTranslation();
  const [token, setToken] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!token.trim() || busy) return;
    setBusy(true);
    setError(null);
    const err = await onUnlock(token.trim()).catch(() => t("gate.unreachable"));
    setBusy(false);
    if (err) setError(err);
  }

  return (
    <main className="app gate">
      <header className="head">
        <div className="headrow">
          <h1 translate="no">{t("brand")}</h1>
          <LanguageSwitcher />
        </div>
        <p className="disclosure">{t("gate.disclosure")}</p>
      </header>
      {expired && <p className="notice ask">{t("gate.sessionExpired")}</p>}
      <form className="runbar" onSubmit={submit}>
        <label className="field">
          <span>{t("gate.token")}</span>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder={t("gate.tokenPlaceholder")}
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button type="submit" className="btn" disabled={!token.trim() || busy}>
          {busy ? t("gate.unlocking") : t("gate.unlock")}
        </button>
      </form>
      {error && <p className="notice ask">{error}</p>}
    </main>
  );
}

function RunVerdict({ run }) {
  const { t } = useTranslation();
  if (run.status === "error") {
    return <div className="verdict error">{t("verdict.runError", { error: run.error })}</div>;
  }
  if (run.status !== "finished") {
    return <div className="verdict running">{t("verdict.running")}</div>;
  }
  const silent = run.nominal && !run.verified;
  return (
    <>
      <div className={`verdict ${silent ? "silent" : run.verified ? "ok" : "fail"}`}>
        <span>
          {t("verdict.nominal")}
          <Hint k="nominal" />: <strong>{run.nominal ? t("verdict.complete") : t("verdict.incomplete")}</strong>
        </span>
        <span>
          {t("verdict.verified")}
          <Hint k="verified" />: <strong>{run.verified ? t("verdict.complete") : t("verdict.incomplete")}</strong>
        </span>
        {silent && (
          <span className="flag">
            {t("verdict.silentFlag")}
            <Hint k="silent" />
          </span>
        )}
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
  const { t } = useTranslation();
  const tok = tokens || {};
  const known = ["output_tokens", "input_tokens", "reasoning_tokens", "total_nano_aiu"].some(
    (k) => tok[k]
  );
  if (!known) {
    return <div className="tokens muted">{t("tokens.na")}</div>;
  }
  const aiu = (tok.total_nano_aiu ?? 0) / 1e9;
  return (
    <div className="tokens" title={t("tokens.title")}>
      <span className="tlabel">{t("tokens.label")}</span>
      <Hint k="tokens" />
      <span><strong>{_fmt(tok.output_tokens)}</strong> {t("tokens.out")}</span>
      <span><strong>{_fmt(tok.input_tokens)}</strong> {t("tokens.in")}</span>
      <span><strong>{_fmt(tok.reasoning_tokens)}</strong> {t("tokens.reasoning")}</span>
      <span>
        <strong>{aiu.toFixed(2)}</strong> {t("tokens.aiu")}
        <Hint k="aiu" />
      </span>
    </div>
  );
}
