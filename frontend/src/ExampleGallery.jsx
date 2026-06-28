import { useState } from "react";
import { useTranslation } from "react-i18next";

const GROUP_ORDER = ["good", "limitation"];

const GROUP_TITLE = {
  good: "gallery.groupGood",
  limitation: "gallery.groupLimitation",
};

export function ExampleGallery({ examples, running, onPick }) {
  const { t } = useTranslation();
  const [group, setGroup] = useState("good");
  const entries = examples.filter((ex) => ex.group === group);

  return (
    <div className="example-gallery">
      <div className="gallery-head">
        <span className="gallery-title">{t("gallery.title")}</span>
        <span className="gallery-hint">{t("gallery.hint")}</span>
      </div>
      <div className="gallery-seg" role="tablist" aria-label={t("gallery.title")}>
        {GROUP_ORDER.map((g) => {
          const count = examples.filter((ex) => ex.group === g).length;
          return (
            <button
              key={g}
              type="button"
              role="tab"
              aria-selected={group === g}
              className={`gallery-seg-btn gallery-seg-${g}${group === g ? " on" : ""}`}
              onClick={() => setGroup(g)}
            >
              {t(GROUP_TITLE[g])}
              {count > 0 && <span className="gallery-seg-count">{count}</span>}
            </button>
          );
        })}
      </div>
      <ul className={`gallery-cards gallery-${group}`}>
        {entries.map((ex) => (
          <li key={ex.id}>
            <button
              type="button"
              className="gallery-card"
              disabled={running}
              onClick={() => onPick(ex)}
            >
              <span className={`gallery-badge badge-${ex.group}`} data-badge={ex.badge}>
                {t(`gallery.badge.${ex.badge}`)}
              </span>
              <span className="gallery-card-label">{t(`gallery.items.${ex.id}.label`)}</span>
              <span className="gallery-card-why">{t(`gallery.items.${ex.id}.why`)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
