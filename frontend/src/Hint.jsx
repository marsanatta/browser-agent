import { useCallback, useId, useState } from "react";
import { useTranslation } from "react-i18next";

export function Hint({ k }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const tipId = useId();

  const show = useCallback(() => setOpen(true), []);
  const hide = useCallback(() => setOpen(false), []);

  const onBlur = useCallback((e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
  }, []);

  const onKeyDown = useCallback((e) => {
    if (e.key === "Escape" && open) {
      e.stopPropagation();
      setOpen(false);
    }
  }, [open]);

  const text = t(`hint.${k}`);

  return (
    <span className="hintwrap" onMouseEnter={show} onMouseLeave={hide} onBlur={onBlur}>
      <button
        type="button"
        className="hintmark"
        aria-label={t("a11y.moreInfo")}
        aria-describedby={open ? tipId : undefined}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onFocus={show}
        onKeyDown={onKeyDown}
      >
        <span aria-hidden="true">ⓘ</span>
      </button>
      {open && (
        <span id={tipId} role="tooltip" className="hinttip">
          {text}
        </span>
      )}
    </span>
  );
}

const LANGS = [
  { code: "en", labelKey: "lang.en" },
  { code: "zh-Hant", labelKey: "lang.zhHant" },
];

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = i18n.resolvedLanguage ?? i18n.language;

  return (
    <div className="langswitch" role="group" aria-label={t("lang.groupLabel")}>
      {LANGS.map(({ code, labelKey }) => {
        const label = t(labelKey);
        const active = current === code;
        return (
          <button
            key={code}
            type="button"
            className={`langbtn ${active ? "active" : ""}`}
            aria-pressed={active}
            aria-label={t("lang.switchTo", { lang: label })}
            onClick={() => i18n.changeLanguage(code)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
