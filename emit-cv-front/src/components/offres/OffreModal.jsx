import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { X, MapPin, Building2, CalendarDays, GraduationCap, Layers, Check, Loader2 } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { ROLES } from "@/constants/roles";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";
import { formatDate } from "@/utils/formatDate";
import { postulerOffre } from "@/api/offres.api";
import { typeTone, statusTone } from "./offreStyles";

export default function OffreModal({ offre, onClose }) {
  const { t, lang } = useLanguage();
  const { user } = useAuth();
  const [state, setState] = useState("idle"); // idle | loading | done | error

  // Fermeture avec la touche Échap
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const isOpen = offre.statut === "ouverte";
  const isAdmin = user?.role === ROLES.ADMIN;

  const handleApply = async () => {
    setState("loading");
    try {
      await postulerOffre(offre.id);
      setState("done");
    } catch {
      setState("error");
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${typeTone[offre.type]}`}>
              {t(`offers.types.${offre.type}`)}
            </span>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusTone[offre.statut]}`}>
              {t(`offers.status.${offre.statut}`)}
            </span>
          </div>
          <button
            onClick={onClose}
            aria-label={t("offers.close")}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-300 text-slate-500 transition hover:border-brand hover:text-brand dark:border-night-line"
          >
            <X size={18} />
          </button>
        </div>

        <h2 className="mt-5 text-2xl font-bold leading-snug">{offre.titre}</h2>

        <div className="mt-4 grid gap-3 text-sm text-slate-500 dark:text-slate-400 sm:grid-cols-2">
          <span className="inline-flex items-center gap-2"><Building2 size={16} /> {offre.entreprise}</span>
          <span className="inline-flex items-center gap-2"><MapPin size={16} /> {offre.lieu}</span>
          <span className="inline-flex items-center gap-2">
            <Layers size={16} /> {t("offers.mention")} : {offre.mention}
          </span>
          <span className="inline-flex items-center gap-2">
            <GraduationCap size={16} /> {t("offers.level")} : {offre.niveau}
          </span>
          <span className="inline-flex items-center gap-2">
            <CalendarDays size={16} /> {t("offers.publishedOn")} {formatDate(offre.datecreation, lang)}
          </span>
        </div>

        <h3 className="mt-7 font-semibold">{t("offers.description")}</h3>
        <p className="mt-2 leading-relaxed text-slate-500 dark:text-slate-400">{offre.description}</p>

        <h3 className="mt-7 font-semibold">{t("offers.skills")}</h3>
        <ul className="mt-3 flex flex-wrap gap-2">
          {offre.competences.map((c) => (
            <li
              key={c.nom}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${
                c.obligatoire
                  ? "bg-brand/15 font-medium text-brand"
                  : "bg-slate-100 text-slate-600 dark:bg-night-line dark:text-slate-200"
              }`}
            >
              {c.obligatoire && <Check size={14} />}
              {c.nom}
              {c.obligatoire && <span className="text-xs opacity-70">· {t("offers.required")}</span>}
            </li>
          ))}
        </ul>

        {/* Action */}
        {!isAdmin && (
          <div className="mt-8 border-t border-slate-200 pt-6 dark:border-night-line">
            {!isOpen ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">{t("offers.notOpen")}</p>
            ) : !user ? (
              <Link
                to={ROUTES.LOGIN}
                className="inline-flex rounded-full bg-brand px-7 py-3 text-sm font-semibold text-white transition hover:brightness-110"
              >
                {t("offers.loginToApply")}
              </Link>
            ) : state === "done" ? (
              <p className="inline-flex items-center gap-2 text-sm font-medium text-emerald-500">
                <Check size={18} /> {t("offers.applied")}
              </p>
            ) : (
              <>
                <button
                  onClick={handleApply}
                  disabled={state === "loading"}
                  className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 px-7 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-70"
                >
                  {state === "loading" && <Loader2 size={16} className="animate-spin" />}
                  {state === "loading" ? t("offers.applying") : t("offers.apply")}
                </button>
                {state === "error" && <p className="mt-3 text-sm text-red-500">{t("offers.applyError")}</p>}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}