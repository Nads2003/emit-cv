import { MapPin, Building2, CalendarDays, ArrowRight } from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";
import { formatDate } from "@/utils/formatDate";
import { typeTone, statusTone } from "./offreStyles";

export default function OffreCard({ offre, onOpen }) {
  const { t, lang } = useLanguage();
  const visibleSkills = offre.competences.slice(0, 3);
  const extra = offre.competences.length - visibleSkills.length;

  return (
    <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-brand/50 dark:border-night-line dark:bg-night-card">
      <div className="flex items-center justify-between gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${typeTone[offre.type]}`}>
          {t(`offers.types.${offre.type}`)}
        </span>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusTone[offre.statut]}`}>
          {t(`offers.status.${offre.statut}`)}
        </span>
      </div>

      <h3 className="mt-5 text-lg font-semibold leading-snug">{offre.titre}</h3>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500 dark:text-slate-400">
        <span className="inline-flex items-center gap-1.5">
          <Building2 size={14} /> {offre.entreprise}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MapPin size={14} /> {offre.lieu}
        </span>
      </div>

      <p className="mt-4 line-clamp-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
        {offre.description}
      </p>

      <div className="mt-5 flex flex-wrap gap-2">
        {visibleSkills.map((c) => (
          <span
            key={c.nom}
            className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-night-line dark:text-slate-200"
          >
            {c.nom}
          </span>
        ))}
        {extra > 0 && (
          <span className="rounded-lg px-2 py-1 text-xs text-slate-400">+{extra}</span>
        )}
      </div>

      <div className="mt-auto flex items-center justify-between pt-6">
        <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <CalendarDays size={14} />
          {formatDate(offre.datecreation, lang)}
        </span>
        <button
          onClick={() => onOpen(offre)}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand hover:underline"
        >
          {t("offers.view")} <ArrowRight size={15} />
        </button>
      </div>
    </article>
  );
}