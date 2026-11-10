import { useEffect, useState } from "react";
import { History, Plus, Pencil, Lock, RotateCcw, Trash2, Check, X, AlertCircle } from "lucide-react";
import { getHistorique } from "@/api/historique.api";
import { useLanguage } from "@/hooks/useLanguage";

const META = {
  "histo.offerCreated": [Plus, "bg-brand/15 text-brand"],
  "histo.offerUpdated": [Pencil, "bg-violet-500/15 text-violet-400"],
  "histo.offerClosed": [Lock, "bg-amber-400/15 text-amber-500"],
  "histo.offerRepublished": [RotateCcw, "bg-emerald-500/15 text-emerald-500"],
  "histo.offerDeleted": [Trash2, "bg-red-500/15 text-red-500"],
  "histo.selected": [Check, "bg-emerald-500/15 text-emerald-500"],
  "histo.rejected": [X, "bg-red-500/15 text-red-500"],
  "histo.reset": [RotateCcw, "bg-slate-500/15 text-slate-400"],
};

export default function Historique() {
  const { t, lang } = useLanguage();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let ignore = false;
    getHistorique()
      .then((d) => !ignore && setItems(d))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, []);

  const formatDate = (d) =>
    new Date(d).toLocaleString(lang === "fr" ? "fr-FR" : "en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <section className="mx-auto max-w-3xl px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{t("admin.history.title")}</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("admin.history.subtitle")}</p>

      <div className="mt-8">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <AlertCircle size={36} className="text-red-500" />
            <p>{t("admin.history.error")}</p>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <History size={36} />
            <p>{t("admin.history.empty")}</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {items.map((h) => {
              const [Icon, tone] = META[h.key] ?? [History, "bg-slate-500/15 text-slate-400"];
              return (
                <li
                  key={h.id}
                  className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-night-line dark:bg-night-card"
                >
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone}`}>
                    <Icon size={18} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{h.key ? t(h.key, h.params) : h.action}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{formatDate(h.date)}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}