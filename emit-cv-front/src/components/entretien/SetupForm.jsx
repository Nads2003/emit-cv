import { useState } from "react";
import { Briefcase, Loader2, Sparkles, AlertCircle } from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";

const TYPES = ["rh", "technique", "mixte"];
const COUNTS = [3, 5, 8];

export default function SetupForm({ defaultPoste = "", loading, error, onStart }) {
  const { t } = useLanguage();
  const [poste, setPoste] = useState(defaultPoste);
  const [type, setType] = useState("mixte");
  const [count, setCount] = useState(5);

  const submit = (e) => {
    e.preventDefault();
    if (poste.trim()) onStart({ poste: poste.trim(), type, count });
  };

  const choice = (active) =>
    `rounded-2xl border p-4 text-left transition ${
      active
        ? "border-brand bg-brand/10"
        : "border-slate-200 hover:border-brand/50 dark:border-night-line"
    }`;

  return (
    <form
      onSubmit={submit}
      className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-8"
    >
      {error && (
        <div
          role="alert"
          className="mb-6 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500"
        >
          <AlertCircle size={18} className="shrink-0" />
          {t("interview.error")}
        </div>
      )}

      {/* Poste visé */}
      <label htmlFor="poste" className="mb-2 block text-sm font-medium">
        {t("interview.setup.job")}
      </label>
      <div className="relative">
        <Briefcase size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          id="poste"
          value={poste}
          onChange={(e) => setPoste(e.target.value)}
          placeholder={t("interview.setup.jobPh")}
          required
          className="w-full rounded-xl border border-slate-300 bg-transparent py-3 pl-11 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:placeholder:text-slate-500"
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {[0, 1, 2, 3].map((i) => (
          <button
            key={i}
            type="button"
            onClick={() => setPoste(t(`interview.setup.suggestions.${i}`))}
            className="rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-600 transition hover:text-brand dark:bg-night-line dark:text-slate-200"
          >
            {t(`interview.setup.suggestions.${i}`)}
          </button>
        ))}
      </div>

      {/* Type */}
      <p className="mb-2 mt-8 text-sm font-medium">{t("interview.setup.type")}</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {TYPES.map((k) => (
          <button key={k} type="button" onClick={() => setType(k)} className={choice(type === k)}>
            <p className="font-semibold">{t(`interview.setup.types.${k}`)}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t(`interview.setup.typeDesc.${k}`)}</p>
          </button>
        ))}
      </div>

      {/* Nombre de questions */}
      <p className="mb-2 mt-8 text-sm font-medium">{t("interview.setup.count")}</p>
      <div className="flex flex-wrap gap-3">
        {COUNTS.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setCount(n)}
            className={`rounded-full px-6 py-2.5 text-sm font-medium transition ${
              count === n
                ? "bg-brand text-white"
                : "bg-slate-100 text-slate-600 hover:text-brand dark:bg-night-line dark:text-slate-200"
            }`}
          >
            {n} {t("interview.setup.questions")}
          </button>
        ))}
      </div>

      <button
        type="submit"
        disabled={loading || !poste.trim()}
        className="mt-10 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 px-8 py-3.5 font-semibold text-white shadow-[0_12px_40px_-8px_rgba(79,109,245,0.7)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
        {loading ? t("interview.setup.loading") : t("interview.setup.start")}
      </button>
    </form>
  );
}