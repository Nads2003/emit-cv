import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Globe, Briefcase, Trophy, Check, ArrowRight, AlertCircle, Inbox } from "lucide-react";
import ScoreBadge from "@/components/common/ScoreBadge";
import OffreModal from "@/components/offres/OffreModal";
import { typeTone } from "@/components/offres/offreStyles";
import { ROUTES } from "@/constants/routes";
import { getRecommandations } from "@/api/recommandations.api";
import { useAuth } from "@/hooks/useAuth";
import { useCv } from "@/hooks/useCv";
import { useLanguage } from "@/hooks/useLanguage";

function Stat({ icon: Icon, tone, label, value }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
      <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${tone}`}>
        <Icon size={20} />
      </span>
      <p className="mt-5 text-2xl font-bold">{value}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</p>
    </div>
  );
}

export default function Dashboard() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const { cv, completude } = useCv();
  const [recos, setRecos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let ignore = false;
    getRecommandations()
      .then((data) => !ignore && setRecos(data))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, []);

  const isPublished = cv.statut === "publie";
  const best = recos[0]?.score;

  return (
    <section className="mx-auto max-w-[1200px] px-5 py-10 lg:px-12">
      {/* Bienvenue */}
      <h1 className="text-3xl font-semibold">
        {t("dash.hello")}, <span className="text-brand">{user?.nom}</span> 👋
      </h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("dash.subtitle")}</p>

      {/* Statistiques */}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <Stat icon={FileText} tone="bg-brand/15 text-brand" label={t("dash.stats.completeness")} value={`${completude}%`} />
        <Stat
          icon={Globe}
          tone={isPublished ? "bg-emerald-500/15 text-emerald-500" : "bg-amber-400/15 text-amber-500"}
          label={t("dash.stats.cvStatus")}
          value={t(`cv.status.${cv.statut}`)}
        />
        <Stat
          icon={Briefcase}
          tone="bg-violet-500/15 text-violet-400"
          label={t("dash.stats.recommended")}
          value={loading ? "…" : recos.length}
        />
        <Stat
          icon={Trophy}
          tone="bg-emerald-500/15 text-emerald-500"
          label={t("dash.stats.bestScore")}
          value={loading || best == null ? "—" : `${best}%`}
        />
      </div>

      {/* Carte CV */}
      <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">{t("dash.cvCard.title")}</h2>
          <Link
            to={ROUTES.ETUDIANT_CV}
            className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            {t("dash.cvCard.edit")} <ArrowRight size={16} />
          </Link>
        </div>

        <div className="mt-5 h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-night-line">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-emerald-400 transition-all duration-500"
            style={{ width: `${completude}%` }}
          />
        </div>
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          {completude < 100 ? t("dash.cvCard.incomplete") : t("dash.cvCard.complete")}
          {!isPublished && ` ${t("dash.cvCard.draftHint")}`}
        </p>
      </div>

      {/* Offres recommandées */}
      <div className="mt-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">{t("dash.reco.title")}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t("dash.reco.subtitle")}</p>
          </div>
          <Link to={ROUTES.OFFRES} className="text-sm font-semibold text-brand hover:underline">
            {t("dash.reco.seeAll")}
          </Link>
        </div>

        <div className="mt-6 space-y-5">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-36 animate-pulse rounded-3xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card"
              />
            ))
          ) : error ? (
            <div className="flex flex-col items-center gap-3 py-14 text-center text-slate-500 dark:text-slate-400">
              <AlertCircle size={36} className="text-red-500" />
              <p>{t("dash.reco.error")}</p>
            </div>
          ) : recos.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-14 text-center text-slate-500 dark:text-slate-400">
              <Inbox size={36} />
              <p>{t("dash.reco.none")}</p>
            </div>
          ) : (
            recos.map((r) => (
              <article
                key={r.id}
                className="flex flex-col gap-5 rounded-3xl border border-slate-200 bg-white p-6 transition hover:border-brand/50 dark:border-night-line dark:bg-night-card sm:flex-row sm:items-center"
              >
                <div className="flex items-center gap-3 sm:flex-col sm:gap-1">
                  <ScoreBadge score={r.score} />
                  <span className="text-xs text-slate-500 dark:text-slate-400">{t("dash.reco.match")}</span>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${typeTone[r.type]}`}>
                      {t(`offers.types.${r.type}`)}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {r.entreprise} · {r.lieu}
                    </span>
                  </div>
                  <h3 className="mt-2 font-semibold">{r.titre}</h3>

                  {r.communes.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-400">{t("dash.reco.common")}</span>
                      {r.communes.map((c) => (
                        <span
                          key={c}
                          className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-500"
                        >
                          <Check size={12} /> {c}
                        </span>
                      ))}
                    </div>
                  )}
                  {r.manquantes.length > 0 && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-400">{t("dash.reco.missing")}</span>
                      {r.manquantes.map((c) => (
                        <span key={c} className="rounded-lg bg-amber-400/15 px-2.5 py-1 text-xs font-medium text-amber-500">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setSelected(r)}
                  className="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-brand hover:underline"
                >
                  {t("offers.view")} <ArrowRight size={15} />
                </button>
              </article>
            ))
          )}
        </div>
      </div>

      {selected && <OffreModal offre={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}