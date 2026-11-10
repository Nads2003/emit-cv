import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Plus, Search, Pencil, Users, Lock, RotateCcw, Trash2, CheckCircle2, AlertCircle, CalendarDays } from "lucide-react";
import { typeTone, statusTone } from "@/components/offres/offreStyles";
import { OFFER_STATUS } from "@/constants/academic";
import { ROUTES } from "@/constants/routes";
import { getOffres, changerStatutOffre, supprimerOffre } from "@/api/offres.api";
import { useLanguage } from "@/hooks/useLanguage";
import { formatDate } from "@/utils/formatDate";

const actionBtn =
  "inline-flex items-center gap-1.5 rounded-full border border-slate-300 px-3.5 py-2 text-xs font-medium transition hover:border-brand hover:text-brand dark:border-night-line";

export default function GestionOffres() {
  const { t, lang } = useLanguage();
  const location = useLocation();
  const [offres, setOffres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");

  useEffect(() => {
    let ignore = false;
    getOffres()
      .then((d) => !ignore && setOffres(d))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    return offres.filter(
      (o) => (status === "all" || o.statut === status) && o.titre.toLowerCase().includes(term),
    );
  }, [offres, q, status]);

  const toggleStatus = async (offre) => {
    setError(false);
    try {
      const saved = await changerStatutOffre(offre, offre.statut === "ouverte" ? "fermee" : "ouverte");
      setOffres((list) => list.map((o) => (o.id === offre.id ? saved : o)));
    } catch {
      setError(true);
    }
  };

  const remove = async (offre) => {
    if (!window.confirm(t("admin.offers.confirmDelete"))) return;
    setError(false);
    try {
      await supprimerOffre(offre.id);
      setOffres((list) => list.filter((o) => o.id !== offre.id));
    } catch {
      setError(true);
    }
  };

  return (
    <section className="mx-auto max-w-[1200px] px-5 py-10 lg:px-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">{t("admin.offers.title")}</h1>
          <p className="mt-2 text-slate-500 dark:text-slate-400">{t("admin.offers.subtitle")}</p>
        </div>
        <Link
          to={ROUTES.ADMIN_OFFRE_NEW}
          className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:brightness-110"
        >
          <Plus size={16} /> {t("admin.offers.new")}
        </Link>
      </div>

      {location.state?.saved && (
        <div className="mt-6 flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-500">
          <CheckCircle2 size={18} /> {t("admin.offers.saved")}
        </div>
      )}
      {error && (
        <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          <AlertCircle size={18} /> {t("admin.offers.error")}
        </div>
      )}

      {/* Filtres */}
      <div className="mt-8 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("admin.offers.search")}
            className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:bg-night-card"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-brand dark:border-night-line dark:bg-night-card"
        >
          <option value="all">{t("admin.offers.allStatus")}</option>
          {OFFER_STATUS.map((s) => (
            <option key={s} value={s}>
              {t(`offers.status.${s}`)}
            </option>
          ))}
        </select>
      </div>

      {/* Liste */}
      <div className="mt-6 space-y-4">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-3xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card" />
          ))
        ) : filtered.length === 0 ? (
          <p className="py-16 text-center text-slate-500 dark:text-slate-400">{t("admin.offers.empty")}</p>
        ) : (
          filtered.map((o) => (
            <article
              key={o.id}
              className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-night-line dark:bg-night-card sm:p-6"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${typeTone[o.type]}`}>
                  {t(`offers.types.${o.type}`)}
                </span>
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusTone[o.statut]}`}>
                  {t(`offers.status.${o.statut}`)}
                </span>
                <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                  <CalendarDays size={13} /> {formatDate(o.datecreation, lang)}
                </span>
              </div>

              <h2 className="mt-3 text-lg font-semibold">{o.titre}</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {o.entreprise} · {o.mention} · {o.niveau} · {o.competences.length} {t("admin.offers.criteria")}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                <Link to={`${ROUTES.ADMIN_CANDIDATS}?offre=${o.id}`} className={actionBtn}>
                  <Users size={14} /> {t("admin.offers.candidates")}
                </Link>
                <Link to={ROUTES.ADMIN_OFFRE_EDIT.replace(":id", o.id)} className={actionBtn}>
                  <Pencil size={14} /> {t("admin.offers.edit")}
                </Link>
                <button onClick={() => toggleStatus(o)} className={actionBtn}>
                  {o.statut === "ouverte" ? <Lock size={14} /> : <RotateCcw size={14} />}
                  {o.statut === "ouverte" ? t("admin.offers.close") : t("admin.offers.republish")}
                </button>
                <button
                  onClick={() => remove(o)}
                  className="inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-medium text-red-500 transition hover:bg-red-500/10"
                >
                  <Trash2 size={14} /> {t("admin.offers.delete")}
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}