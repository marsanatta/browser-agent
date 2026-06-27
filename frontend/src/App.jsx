import { Fragment, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { StepDetail } from "./StepDetail.jsx";
import { LiveActivity } from "./LiveActivity.jsx";
import { Hint, LanguageSwitcher } from "./Hint.jsx";
import { maskArgs, MASK } from "./mask.js";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "";

const TERMINAL = new Set(["RUN_FINISHED", "RUN_ERROR"]);

const initialState = { run: null, steps: [], order: [], notices: [], plan: null, planVersions: [] };

function reduce(state, ev) {
  const { type, payload } = ev;
  if (type === "RUN_STARTED") {
    return {
      run: { id: payload.run_id, task: payload.task, status: "running", phase: "planning", startedAt: Date.now() },
      steps: [],
      order: [],
      notices: [],
      plan: null,
      planVersions: [],
    };
  }
  if (type === "PLAN_READY") {
    // Seed the execution timeline off the FULL reconciled plan (unchanged), and
    // ACCUMULATE this version into the history (never overwrite a prior plan/replan).
    const seeded = seedPlan(state, payload.run_id, payload.plan ?? []);
    const version = {
      version: payload.version ?? state.planVersions.length + 1,
      kind: payload.kind ?? "plan",
      reasoning: payload.reasoning ?? "",
      failures: payload.failures ?? null,
      steps: payload.steps ?? payload.plan ?? [],
    };
    return { ...seeded, planVersions: [...state.planVersions, version] };
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
        goalChecked: payload.goal_checked,
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

function maskRawPlan(raw) {
  // Show the planner LLM's verbatim output, but never render a `fill` value — it can be
  // a secret the user asked the agent to type (same precaution maskArgs applies to the
  // step view). Real tokens/keys/emails are already masked server-side by redact().
  if (!raw) return "";
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return JSON.stringify(parsed.map((a) => maskArgs(a)), null, 2);
  } catch {
    // not clean JSON (model added prose / malformed) — fall back to a regex mask
  }
  // Defensive fallback (can't parse structure to tell actions apart): mask EVERY
  // "value" field, order-independent, so a `fill` value can never leak. Over-masking
  // a non-secret value (e.g. a press key) is acceptable for raw observability.
  return raw.replace(/("value"\s*:\s*)"(?:[^"\\]|\\.)*"/g, `$1"${MASK}"`);
}

function buildCriterion(type, value, css) {
  // Assemble the optional success criterion into the state_check shape the backend
  // allows (url_contains / h1_equals / selector_text_equals — never loose text).
  if (!type || !value.trim()) return null;
  if (type === "selector_text_equals") {
    if (!css.trim()) return null;
    return { selector_text_equals: { css: css.trim(), value } };
  }
  return { [type]: value };
}

function describePlanned(a) {
  if (a.action === "navigate") return `navigate to ${a.url ?? ""}`;
  return `${a.action} '${a.target ?? ""}'`;
}

function seedPlan(state, runId, plan) {
  const isReplan = state.plan != null;
  const planIds = plan.map((_, i) => `${runId}-s${i + 1}`);
  const byId = new Map(state.steps.map((s) => [s.id, s]));

  // First plain (non-replan) plan: seed any not-yet-known id as pending.
  if (!isReplan) {
    const steps = [...state.steps];
    const order = [...state.order];
    plan.forEach((a, i) => {
      const id = planIds[i];
      if (byId.has(id)) return; // a STEP_STARTED already arrived for this id
      steps.push({ id, description: describePlanned(a), status: "pending" });
      order.push(id);
    });
    return { ...state, steps, order, plan: { steps: plan, count: plan.length, replanFrom: -1 } };
  }

  // Replan: the backend emits the FULL reconciled plan (already-done prefix +
  // new tail). The divergence point is the first index whose existing row is not
  // an "ok" completion — from there on the rows are the replan's new sub-tasks.
  const replanFrom = plan.findIndex((_, i) => (byId.get(planIds[i])?.status ?? "pending") !== "ok");

  const steps = [];
  const order = [];
  plan.forEach((a, i) => {
    const id = planIds[i];
    const prev = byId.get(id);
    if (replanFrom >= 0 && i >= replanFrom) {
      // Replaced by the replan: a brand-new sub-task reusing this id. Start a fresh
      // row — do NOT carry over the prior sub-task's recoveries/calls/shots/locator,
      // or stale diagnostics from the old action show under the new one.
      steps.push({ id, description: describePlanned(a), status: "pending", replanned: true });
    } else {
      steps.push(prev ?? { id, description: describePlanned(a), status: "pending" });
    }
    order.push(id);
  });
  // Orphan rows from a longer original plan that the new plan no longer covers are
  // dropped by virtue of rebuilding steps/order from the new plan above — but never
  // a row that already ran (the prefix is all "ok", always within the new plan).

  return { ...state, steps, order, plan: { steps: plan, count: plan.length, replanFrom } };
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
  const [models, setModels] = useState(null); // { menu, defaults, thinking_levels, thinking_defaults }
  const [modelSel, setModelSel] = useState(null); // current per-role model selection
  const [effortSel, setEffortSel] = useState(null); // current per-role thinking level
  const [maxReplans, setMaxReplans] = useState(10); // bounded global replans before abstain
  const [critType, setCritType] = useState(""); // optional success criterion (independent goal check)
  const [critValue, setCritValue] = useState("");
  const [critCss, setCritCss] = useState("");
  const [state, dispatch] = useReducer(reduce, initialState);
  const sourceRef = useRef(null);

  useEffect(() => () => sourceRef.current?.close(), []); // abort an in-flight run stream on unmount

  useEffect(() => {
    let alive = true;
    fetch(`${BACKEND}/models`)
      .then((r) => (r.ok ? r.json() : null))
      .then((m) => {
        if (alive && m?.menu?.length) {
          setModels(m);
          setModelSel(m.defaults);
          setEffortSel(m.thinking_defaults);
        }
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

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
    if (modelSel) {
      params.set("model_plan", modelSel.plan);
      params.set("model_exec", modelSel.exec);
      params.set("model_replanner", modelSel.replanner);
    }
    if (effortSel) {
      params.set("think_plan", effortSel.plan);
      params.set("think_exec", effortSel.exec);
      params.set("think_replanner", effortSel.replanner);
    }
    params.set("max_replans", String(maxReplans));
    const criterion = buildCriterion(critType, critValue, critCss);
    if (criterion) params.set("criterion", JSON.stringify(criterion));
    // Stream over POST instead of EventSource(GET): Cloudflare quick tunnels
    // buffer SSE-over-GET and flush only at connection close (cloudflared#1449);
    // POST streams live. We parse the text/event-stream frames by hand.
    const controller = new AbortController();
    let terminated = false;
    sourceRef.current = { close: () => { terminated = true; controller.abort(); } };

    const fail = (gate) => {
      if (terminated) return; // clean end or user-initiated stop
      terminated = true;
      controller.abort();
      setRunning(false);
      dispatch({ type: "RUN_ERROR", payload: { error: t("verdict.connectionLost") } });
      if (gate) {
        // never connected -> almost always an expired/invalid access cookie
        localStorage.removeItem("ba_authed");
        setSessionExpired(true);
        setAuthed(false);
      }
    };

    (async () => {
      let res;
      try {
        res = await fetch(`${BACKEND}/agent/run?${params.toString()}`, {
          method: "POST",
          credentials: "include",
          signal: controller.signal,
        });
      } catch {
        fail(true);
        return;
      }
      if (!res.ok || !res.body) {
        fail(res.status === 401 || res.status === 503);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true }).replace(/\r/g, "");
          let i;
          while ((i = buf.indexOf("\n\n")) >= 0) {
            const frame = buf.slice(0, i);
            buf = buf.slice(i + 2);
            const data = frame
              .split("\n")
              .filter((l) => l.startsWith("data:"))
              .map((l) => l.slice(5).replace(/^ /, ""))
              .join("\n");
            if (!data) continue; // heartbeat / comment frame
            const parsed = JSON.parse(data);
            dispatch(parsed);
            if (TERMINAL.has(parsed.type)) {
              terminated = true;
              controller.abort();
              setRunning(false);
              return;
            }
          }
        }
        fail(false); // stream ended without a terminal event
      } catch {
        fail(false); // mid-stream network drop (no-op if user stopped)
      }
    })();
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
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={(e) => {
              // textarea Enter inserts a newline; keep a keyboard submit path
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                e.preventDefault();
                start();
              }
            }}
            placeholder={t("runbar.taskPlaceholder")}
            rows={3}
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

      <details className="criterion">
        <summary>
          {t("criterion.heading")}
          <Hint k="criterion" />
        </summary>
        <div className="criterion-grid">
          <label className="field">
            <span>{t("criterion.check")}</span>
            <select value={critType} onChange={(e) => setCritType(e.target.value)}>
              <option value="">{t("criterion.none")}</option>
              <option value="url_contains">{t("criterion.urlContains")}</option>
              <option value="h1_equals">{t("criterion.h1Equals")}</option>
              <option value="selector_text_equals">{t("criterion.selectorTextEquals")}</option>
            </select>
          </label>
          {critType === "selector_text_equals" && (
            <label className="field">
              <span>{t("criterion.css")}</span>
              <input
                value={critCss}
                onChange={(e) => setCritCss(e.target.value)}
                placeholder={t("criterion.cssPlaceholder")}
                autoComplete="off"
                spellCheck={false}
              />
            </label>
          )}
          {critType && (
            <label className="field">
              <span>{t("criterion.value")}</span>
              <input
                value={critValue}
                onChange={(e) => setCritValue(e.target.value)}
                placeholder={t("criterion.valuePlaceholder")}
                autoComplete="off"
                spellCheck={false}
              />
            </label>
          )}
        </div>
      </details>

      {models && modelSel && effortSel && (
        <details className="models">
          <summary>{t("models.heading")}</summary>
          <div className="models-grid">
            {["plan", "exec", "replanner"].map((role) => (
              <div key={role} className="model-row">
                <span className="model-role">{t(`models.${role}`)}</span>
                <label className="field">
                  <span>{t("models.model")}</span>
                  <select
                    value={modelSel[role]}
                    onChange={(e) => setModelSel((s) => ({ ...s, [role]: e.target.value }))}
                  >
                    {models.menu.map((id) => (
                      <option key={id} value={id} translate="no">
                        {id}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>{t("models.thinking")}</span>
                  <select
                    value={effortSel[role]}
                    onChange={(e) => setEffortSel((s) => ({ ...s, [role]: e.target.value }))}
                  >
                    {models.thinking_levels.map((lv) => (
                      <option key={lv} value={lv} translate="no">
                        {lv}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            ))}
            <label className="field model-replans">
              <span>{t("models.maxReplans")}</span>
              <input
                type="number"
                min={0}
                max={10}
                value={maxReplans}
                onChange={(e) =>
                  setMaxReplans(Math.max(0, Math.min(10, Number(e.target.value) || 0)))
                }
              />
            </label>
          </div>
        </details>
      )}

      {run?.status === "running" && (
        <LiveActivity startedAt={run.startedAt} phase={run.phase} activeStepDescription={activeStep?.description} />
      )}
      {run && run.status !== "running" ? <RunVerdict run={run} /> : null}

      {state.planVersions.length > 0 && <PlanHistory versions={state.planVersions} />}

      <section className="board">
        <ol className="timeline" aria-live="polite" aria-label={t("timeline.label")}>
          {steps.length === 0 && <li className="empty">{t("timeline.empty")}</li>}
          {steps.map((s, i) => (
            <Fragment key={s.id}>
              {s.replanned && (steps[i - 1] == null || !steps[i - 1].replanned) && (
                <li className="replan-divider" aria-label={t("plan.replanned")}>
                  <span>{t("plan.replanned")}</span>
                </li>
              )}
            <li className={`fade-in ${s.status === "running" ? "is-active" : ""}`}>
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
            </Fragment>
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

function PlanSteps({ steps }) {
  return (
    <ol className="plan-steps">
      {steps.map((a, i) => (
        <li key={i}>
          <span className="num">{i + 1}</span>
          <code className="plan-action">{a.action}</code>
          <span className="plan-target break-words">
            {a.action === "navigate" ? a.url ?? "" : a.target ?? ""}
            {a.value != null && a.action !== "navigate" ? ` = ${maskArgs(a).value}` : ""}
          </span>
        </li>
      ))}
    </ol>
  );
}

function PlanHistory({ versions }) {
  // Preserve the full plan -> replan history: every version is kept and shown in full
  // (vertical, all expanded), each with the planner LLM's verbatim output and, for a
  // replan, the failure log that was fed to the LLM (the "why").
  const { t } = useTranslation();
  return (
    <section className="plan-history" aria-label={t("planHistory.heading")}>
      <h2 className="plan-heading">{t("planHistory.heading")}</h2>
      {versions.map((v, idx) => (
        <article key={idx} className={`plan-version ${v.kind}`}>
          <h3 className="plan-version-head">
            {v.kind === "replan"
              ? t("planHistory.replan", { v: v.version, n: v.failures?.length ?? 0 })
              : t("planHistory.initial", { v: v.version })}
          </h3>
          {v.kind === "replan" && (v.failures?.length ?? 0) > 0 && (
            <div className="plan-why">
              <span className="plan-why-label">{t("planHistory.why")}</span>
              <ul className="plan-failures">
                {v.failures.map((f, i) => (
                  <li key={i}>
                    <code>{f.step}</code> → <span className="fcat">{f.class}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <PlanSteps steps={v.steps ?? []} />
          {v.reasoning && (
            <details className="plan-raw" open>
              <summary>{t("planHistory.rawOutput")}</summary>
              <pre className="plan-raw-pre">{maskRawPlan(v.reasoning)}</pre>
            </details>
          )}
        </article>
      ))}
    </section>
  );
}

const VERDICT_CLASS = { verified: "ok", unverified: "unverified", silent: "silent", failed: "fail" };

function runVerdictState(run) {
  // Three honest states. The word "verified" is earned ONLY when an independent
  // goal check actually ran (run.goalChecked). Without one, a nominal pass is
  // self-report only — never shown as verified.
  if (!run.goalChecked) return run.nominal ? "unverified" : "failed";
  if (run.verified) return "verified";
  return run.nominal ? "silent" : "failed"; // claimed success, goal check disagreed
}

function RunVerdict({ run }) {
  const { t } = useTranslation();
  if (run.status === "error") {
    return <div className="verdict error">{t("verdict.runError", { error: run.error })}</div>;
  }
  if (run.status !== "finished") {
    return <div className="verdict running">{t("verdict.running")}</div>;
  }
  const verdict = runVerdictState(run);
  return (
    <>
      <div className={`verdict ${VERDICT_CLASS[verdict]}`}>
        <span className="verdict-headline">{t(`verdict.state.${verdict}`)}</span>
        <span>
          {t("verdict.nominal")}
          <Hint k="nominal" />: <strong>{run.nominal ? t("verdict.complete") : t("verdict.incomplete")}</strong>
        </span>
        {run.goalChecked ? (
          <span>
            {t("verdict.verified")}
            <Hint k="verified" />: <strong>{run.verified ? t("verdict.complete") : t("verdict.incomplete")}</strong>
          </span>
        ) : (
          <span className="muted">
            {t("verdict.goalCheck")}
            <Hint k="goalCheck" />: <strong>{t("verdict.notProvided")}</strong>
          </span>
        )}
        {verdict === "silent" && (
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
