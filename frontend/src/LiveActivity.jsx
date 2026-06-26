import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const PHASE_KEYS = new Set(["planning", "launching", "running"]);

function fmtElapsed(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function LiveActivity({ startedAt, phase, activeStepDescription }) {
  const { t } = useTranslation();
  const [now, setNow] = useState(() => Date.now());

  const tick = useCallback(() => setNow(Date.now()), []);
  useEffect(() => {
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [tick]);

  const phaseLabel = PHASE_KEYS.has(phase) ? t(`phase.${phase}`) : t("phase.running");
  const activity = activeStepDescription ?? phaseLabel;
  const elapsed = fmtElapsed((startedAt ? now - startedAt : 0));

  return (
    <div className="live" role="status">
      <span className="live-icon" aria-hidden="true">
        <span className="live-spinner" />
      </span>
      <span className="live-text" aria-live="polite" aria-atomic="true">
        <span className="live-working">{t("live.working")}</span>
        <span className="live-activity">{activity}</span>
        <span className="live-cursor" aria-hidden="true" />
      </span>
      <span className="live-elapsed" aria-label={t("live.elapsed", { time: elapsed })}>
        <span aria-hidden="true">{elapsed}</span>
      </span>
    </div>
  );
}
