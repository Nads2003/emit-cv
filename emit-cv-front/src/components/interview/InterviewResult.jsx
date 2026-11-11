import { Check, Lightbulb, RotateCcw, Settings2 } from "lucide-react";
import ScoreBadge from "@/components/common/ScoreBadge";
import { useLanguage } from "@/hooks/useLanguage";

// Les 3 clés les plus fréquentes
const top = (answers, field) => {
  const count = {};
  answers.forEach((a) => a[field].forEach((k) => (count[k] = (count[k] ?? 0) + 1)));
  return Object.entries(count)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([k]) => k);
};

export default function InterviewResult({ answers, onRetry, onNew }) {
  const { t } = useLanguage();
  const avg = Math.round(answers.reduce((s, a) => s + a.score, 0) / answers.length);
  const level = avg >= 80 ? "excellent" : avg >= 60 ? "good" : "work";
  const strengths = top(answers, "good");
  const tips = top(answers, "improve");

  return (
    <div className="space-y-6">
      {/* Score global */}
      <div className="flex flex-col items-center gap-5 rounded-3xl bg-gradient-to-br from-brand to-indigo-700 p-8 text-center text-white sm:flex-row sm:text-left">
        <div className="shrink-0 rounded-full bg-white/10 p-2">
          <ScoreBadge score={avg} />
        </div>
        <div>
          <p className="text-sm text-white/80">{t("interview.result.overall")}</p>
          <h2 className="text-2xl font-bold">{t(`interview.result.levels.${level}`)}</h2>
          <p className="mt-2 text-white/90">{t(`interview.result.messages.${level}`)}</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
          <h3 className="font-semibold">{t("interview.result.strengths")}</h3>
          <ul className="mt-4 space-y-2">
            {strengths.length === 0 && <li className="text-sm text-slate-400">—</li>}
            {strengths.map((k) => (
              <li key={k} className="flex items-start gap-2 text-sm text-emerald-500">
                <Check size={16} className="mt-0.5 shrink-0" /> {t(`interview.fb.${k}`)}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
          <h3 className="font-semibold">{t("interview.result.tips")}</h3>
          <ul className="mt-4 space-y-2">
            {tips.length === 0 && <li className="text-sm text-slate-400">—</li>}
            {tips.map((k) => (
              <li key={k} className="flex items-start gap-2 text-sm text-amber-500">
                <Lightbulb size={16} className="mt-0.5 shrink-0" /> {t(`interview.fb.${k}`)}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Détail */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
        <h3 className="font-semibold">{t("interview.result.details")}</h3>
        <ul className="mt-4 divide-y divide-slate-200 dark:divide-night-line">
          {answers.map((a, i) => (
            <li key={i} className="flex items-center justify-between gap-4 py-3 text-sm">
              <span className="text-slate-600 dark:text-slate-300">
                {i + 1}. {a.question}
              </span>
              <span className="shrink-0 rounded-full bg-brand/15 px-3 py-1 font-bold text-brand">{a.score}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-full bg-brand px-7 py-3 text-sm font-semibold text-white transition hover:brightness-110"
        >
          <RotateCcw size={16} /> {t("interview.result.retry")}
        </button>
        <button
          onClick={onNew}
          className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-7 py-3 text-sm font-medium transition hover:border-brand hover:text-brand dark:border-night-line"
        >
          <Settings2 size={16} /> {t("interview.result.new")}
        </button>
      </div>
    </div>
  );
}