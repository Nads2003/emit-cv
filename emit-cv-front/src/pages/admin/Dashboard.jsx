import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, ClipboardList, Users, UserCheck, Plus, ArrowRight, AlertCircle } from "lucide-react";
import { statusTone } from "@/components/offers/offreStyles";
import { ROUTES } from "@/constants/routes";
import { getAdminOverview } from "@/api/candidats.api";
import { useAuth } from "@/hooks/useAuth";
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

export default function AdminDashboard() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let ignore = false;
    getAdminOverview()
      .then((d) => !ignore && setData(d))
      .catch(() => !ignore && setError(true));
    return () => {
      ignore = true;
    };
  }, []);

  const s = data?.stats;
  const v = (value) => (s ? value : "…");

  return (
    <section className="mx-auto max-w-[1200px] px-5 py-10 lg:px-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">
            {t("admin.dashboard.hello")}, <span className="text-brand">{user?.nom}</span>
          </h1>
          <p className="mt-2 text-slate-500 dark:text-slate-400">{t("admin.dashboard.subtitle")}</p>
        </div>
        <Link
          to={ROUTES.ADMIN_OFFRE_NEW}
          className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:brightness-110"
        >
          <Plus size={16} /> {t("admin.dashboard.newOffer")}
        </Link>
      </div>

      {error && (
        <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          <AlertCircle size={18} /> {t("admin.dashboard.error")}
        </div>
      )}

      <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <Stat icon={Briefcase} tone="bg-brand/15 text-brand" label={t("admin.dashboard.stats.openOffers")} value={v(s?.offresOuvertes)} />
        <Stat icon={ClipboardList} tone="bg-violet-500/15 text-violet-400" label={t("admin.dashboard.stats.totalOffers")} value={v(s?.offresTotal)} />
        <Stat icon={Users} tone="bg-amber-400/15 text-amber-500" label={t("admin.dashboard.stats.publishedCvs")} value={v(s?.cvPublies)} />
        <Stat icon={UserCheck} tone="bg-emerald-500/15 text-emerald-500" label={t("admin.dashboard.stats.selected")} value={v(s?.selectionnes)} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* Dernières offres */}
        <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">{t("admin.dashboard.latest")}</h2>
            <Link to={ROUTES.ADMIN_OFFRES} className="text-sm font-semibold text-brand hover:underline">
              {t("admin.dashboard.seeAll")}
            </Link>
          </div>
          <ul className="mt-4 divide-y divide-slate-200 dark:divide-night-line">
            {(data?.dernieresOffres ?? []).map((o) => (
              <li key={o.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{o.titre}</p>
                  <span className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-xs ${statusTone[o.statut]}`}>
                    {t(`offers.status.${o.statut}`)}
                  </span>
                </div>
                <Link
                  to={`${ROUTES.ADMIN_CANDIDATS}?offre=${o.id}`}
                  className="shrink-0 text-xs font-semibold text-brand hover:underline"
                >
                  {t("admin.dashboard.seeRanking")}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Meilleurs candidats */}
        <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
          <h2 className="font-semibold">
            {t("admin.dashboard.top")}
            {data?.topOffre && <span className="text-brand"> « {data.topOffre.titre} »</span>}
          </h2>
          {data && !data.topOffre ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">{t("admin.dashboard.noOffer")}</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {(data?.top ?? []).map((c, i) => (
                <li key={c.id} className="flex items-center gap-3 rounded-2xl bg-slate-100 p-3 dark:bg-night-line/50">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">{c.cv.profil.nom}</p>
                    <p className="truncate text-xs text-slate-500 dark:text-slate-400">
                      {c.mention} · {c.niveau}
                    </p>
                  </div>
                  <span className="rounded-full bg-brand/15 px-3 py-1 text-sm font-bold text-brand">{c.score}%</span>
                </li>
              ))}
            </ul>
          )}
          {data?.topOffre && (
            <Link
              to={`${ROUTES.ADMIN_CANDIDATS}?offre=${data.topOffre.id}`}
              className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
            >
              {t("admin.dashboard.seeRanking")} <ArrowRight size={15} />
            </Link>
          )}
        </div>
      </div>
    </section>
  );
}