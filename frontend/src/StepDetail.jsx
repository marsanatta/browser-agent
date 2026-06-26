import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Hint } from "./Hint.jsx";

const STATUS_KEYS = ["pending", "running", "ok", "failed"];

export function StepDetail({ step, backend }) {
  const { t } = useTranslation();
  const shots = step.shots ?? [];
  const calls = step.calls ?? [];
  const recoveries = step.recoveries ?? [];

  return (
    <div className="stepdetail">
      <h2 className="break-words">{step.description ?? step.id}</h2>
      <div className="meta">
        <Tag
          label={t("step.statusLabel")}
          value={STATUS_KEYS.includes(step.status) ? t(`status.${step.status}`) : step.status}
          tone={step.status}
        />
        {step.tier != null && (
          <Tag
            label={t("step.locatorLabel")}
            value={t("step.locatorValue", { tier: step.tier, strategy: step.strategy })}
            hint="locatorTier"
          />
        )}
        {step.failureCategory && (
          <Tag label={t("step.failureLabel")} value={step.failureCategory} tone="failed" hint="failureCategory" />
        )}
      </div>

      {shots.length > 0 && (
        <section className="block">
          <h3>
            {t("step.screenshots")}
            <Hint k="screenshot" />
          </h3>
          <div className="shots">
            {shots.map((shot, i) => (
              <Shot key={i} shot={shot} backend={backend} />
            ))}
          </div>
        </section>
      )}

      {recoveries.length > 0 && (
        <section className="block">
          <h3>
            {t("step.recoveryChain")}
            <Hint k="recovery" />
          </h3>
          <ol className="chain">
            {recoveries.map((r, i) => (
              <li key={i}>
                <span className="attempt">{t("step.attempt", { n: r.attempt })}</span>
                <span className="fclass">{r.failure_class}</span>
                <span className="arrow">→</span>
                <span className="rec">{r.recovery}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      {calls.length > 0 && (
        <section className="block">
          <h3>{t("step.toolCalls")}</h3>
          {calls.map((c) => (
            <div key={c.call_id} className="call">
              <code className="tool">{c.tool}</code>
              {c.args && <code className="args">{JSON.stringify(c.args)}</code>}
              {c.result && <span className="result break-words">{c.result}</span>}
            </div>
          ))}
        </section>
      )}

      {step.askUser && (
        <p className="ask">
          {t("notices.askUser", { question: step.askUser })}
          <Hint k="askUser" />
        </p>
      )}
    </div>
  );
}

function Shot({ shot, backend }) {
  const { t } = useTranslation();
  const [box, setBox] = useState(null);
  const h = shot.highlight ?? {};
  const hasBox = h.width > 0 && h.height > 0;

  function onLoad(e) {
    const img = e.currentTarget;
    if (!img.naturalWidth) return;
    const scale = img.clientWidth / img.naturalWidth;
    setBox({
      left: h.x * scale,
      top: h.y * scale,
      width: h.width * scale,
      height: h.height * scale,
    });
  }

  return (
    <figure className="shot">
      <div className="shotframe">
        <img src={`${backend}${shot.screenshot_ref}`} alt={shot.caption ?? t("step.fallbackCaption")} onLoad={onLoad} loading="lazy" />
        {hasBox && box && (
          <span
            className="highlight"
            style={{ left: box.left, top: box.top, width: box.width, height: box.height }}
            aria-hidden="true"
          />
        )}
      </div>
      {shot.caption && <figcaption className="break-words">{shot.caption}</figcaption>}
    </figure>
  );
}

function Tag({ label, value, tone, hint }) {
  return (
    <span className={`tag ${tone ?? ""}`}>
      <span className="tlabel">
        {label}
        {hint && <Hint k={hint} />}
      </span>
      <span className="tval">{value}</span>
    </span>
  );
}
