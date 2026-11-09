import { Search, RotateCcw } from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";

const TYPES = ["all", "stage", "emploi", "projet"];
const LEVELS = ["L1", "L2", "L3", "M1", "M2"];

const selectClass =
  "rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand dark:border-night-line dark:bg-night-card";

export default function OffreFilters({ filters, setFilters, mentions, onReset }) {
  const { t } = useLanguage();
  const update = (key, value) => setFilters((f) => ({ ...f, [key]: value }));

  return (
    <div className="space-y-5">
      {/* Recherche */}
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          value={filters.q}
          onChange={(e) => update("q", e.target.value)}
          placeholder={t("offers.search")}
          className="w-full rounded-2xl border border-slate-300 bg-white py-4 pl-12 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:bg-night-card dark:placeholder:text-slate-500"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* Type */}
        <div className="flex flex-wrap gap-2">
          {TYPES.map((type) => (
            <button
              key={type}
              onClick={() => update("type", type)}
              className={`rounded-full px-5 py-2.5 text-sm font-medium transition ${
                filters.type === type
                  ? "bg-brand text-white shadow-[0_8px_24px_-8px_rgba(79,109,245,0.8)]"
                  : "bg-white text-slate-600 hover:text-brand dark:bg-night-card dark:text-slate-200"
              }`}
            >
              {type === "all" ? t("offers.filters.all") : t(`offers.types.${type}`)}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:ml-auto">
          <select
            value={filters.mention}
            onChange={(e) => update("mention", e.target.value)}
            className={selectClass}
            aria-label={t("offers.mention")}
          >
            <option value="all">{t("offers.filters.allMentions")}</option>
            {mentions.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          <select
            value={filters.niveau}
            onChange={(e) => update("niveau", e.target.value)}
            className={selectClass}
            aria-label={t("offers.level")}
          >
            <option value="all">{t("offers.filters.allLevels")}</option>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>

          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 rounded-xl px-3 py-3 text-sm text-slate-500 transition hover:text-brand dark:text-slate-400"
          >
            <RotateCcw size={15} />
            {t("offers.filters.reset")}
          </button>
        </div>
      </div>
    </div>
  );
}