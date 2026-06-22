import { useRef, useState } from "react";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const STEP_EVENTS = [
  "RUN_STARTED",
  "STEP_STARTED",
  "STEP_FINISHED",
  "TOOL_CALL_START",
  "TOOL_CALL_ARGS",
  "TOOL_CALL_END",
  "TEXT_MESSAGE",
  "SCREENSHOT_ANNOTATED",
  "RUN_FINISHED",
  "RUN_ERROR",
];

export default function App() {
  const [task, setTask] = useState("");
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const sourceRef = useRef(null);

  function start() {
    if (!task.trim()) return;
    sourceRef.current?.close();
    setEvents([]);
    setRunning(true);

    const url = `${BACKEND}/sse/stream?task=${encodeURIComponent(task)}`;
    const es = new EventSource(url);
    sourceRef.current = es;

    const onAny = (e) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [...prev, parsed]);
      if (parsed.type === "RUN_FINISHED" || parsed.type === "RUN_ERROR") {
        es.close();
        setRunning(false);
      }
    };
    STEP_EVENTS.forEach((name) => es.addEventListener(name, onAny));
    es.onerror = () => {
      es.close();
      setRunning(false);
    };
  }

  return (
    <main style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>browser-agent</h1>
      <p style={{ color: "#666" }}>
        Supported: bot-wall-free public sites. Login / CAPTCHA / MFA walls are routed to
        "unsupported", never evaded.
      </p>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Describe a task in natural language"
          style={{ flex: 1, padding: 8 }}
          onKeyDown={(e) => e.key === "Enter" && !running && start()}
        />
        <button onClick={start} disabled={running} style={{ padding: "8px 16px" }}>
          {running ? "Running…" : "Run"}
        </button>
      </div>

      <ol style={{ marginTop: 24 }}>
        {events.map((ev, i) => (
          <li key={i} style={{ marginBottom: 6 }}>
            <code style={{ color: "#0a58ca" }}>{ev.type}</code>{" "}
            <span style={{ color: "#444" }}>{JSON.stringify(ev.payload)}</span>
          </li>
        ))}
      </ol>
    </main>
  );
}
