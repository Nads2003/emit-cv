import { useEffect, useMemo, useState } from "react";
import { Search, Eye, AlertCircle, UserX } from "lucide-react";
import ProfileModal from "@/components/admin/ProfileModal";
import { MENTIONS, NIVEAUX_ETUDE, AVAILABILITY } from "@/constants/academic";
import { getProfils } from "@/api/candidats.api";
import { useLanguage } from "@/hooks/useLanguage";

const INITIAL = { q: "", mention: "all", niveau: "all", dispo: "all" };

const selectClass =
  "rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand dark:border-night-line dark:bg-night-card";

export default function RechercheProfils() {
  const { t } = useLanguage();
  const [profils, setProfils] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(INITIAL);
  const [viewing, setViewing] = useState(null);

  useEffect(() => {
    let ignore = false;
    getProfils()
      .then((d) => !ignore && setProfils(d))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return profils.filter((c) => {
      if (filters.mention !== "all" && c.mention !== filters.mention) return false;
      if (filters.niveau !== "all" && c.niveau !== filters.niveau) return false;
      if (filters.dispo !== "all" && c.cv.profil.disponibilite !== filters.dispo) return false;
      if (!q) return true;
      return [c.cv.profil.nom, c.matricule, c.cv.profil.poste, ...c.cv.competences.map((s) => s.nom)]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [profils, filters]);

  const update = (key) => (e) => setFilters((f) => ({ ...f, [key]: e.target.value }));

  return (
    <section className="mx-auto max-w-[1200px] px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{t("admin.profiles.title")}</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("admin.profiles.subtitle")}</p>

      <div className="mt-8 space-y-3">
        <div className="relative">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={filters.q}
            onChange={update("q")}
            placeholder={t("admin.profiles.search")}
            className="w-full rounded-2xl border border-slate-300 bg-white py-4 pl-12 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:bg-night-card"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <select value={filters.mention} onChange={update("mention")} className={selectClass}>
            <option value="all">{t("admin.profiles.allMentions")}</option>
            {MENTIONS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <select value={filters.niveau} onChange={update("niveau")} className={selectClass}>
            <option value="all">{t("admin.profiles.allLevels")}</option>
            {NIVEAUX_ETUDE.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
          <select value={filters.dispo} onChange={update("dispo")} className={selectClass}>
            <option value="all">{t("admin.profiles.allAvailability")}</option>
            {AVAILABILITY.map((a) => (
              <option key={a} value={a}>{t(`cv.availability.${a}`)}</option>
            ))}
          </select>
          <button
            onClick={() => setFilters(INITIAL)}
            className="rounded-xl px-3 py-3 text-sm text-slate-500 transition hover:text-brand dark:text-slate-400"
          >
            {t("offers.filters.reset")}
          </button>
        </div>
      </div>

      <div className="mt-8">
        {loading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-52 animate-pulse rounded-3xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <AlertCircle size={36} className="text-red-500" />
            <p>{t("admin.profiles.error")}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <UserX size={36} />
            <p>{t("admin.profiles.empty")}</p>
          </div>
        ) : (
          <>
            <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-900 dark:text-white">{filtered.length}</span> {t("admin.profiles.results")}
            </p>
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {filtered.map((c) => (
                <article
                  key={c.id}
                  className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-brand/50 dark:border-night-line dark:bg-night-card"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand text-lg font-bold text-white">
                      {c.cv.profil.nom.charAt(0)}
                    </span>
                    <div className="min-w-0">
                      <h3 className="truncate font-semibold">{c.cv.profil.nom}</h3>
                      <p className="truncate text-xs text-slate-500 dark:text-slate-400">{c.cv.profil.poste}</p>
                    </div>
                  </div>

                  <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
                    {c.matricule} · {c.mention} · {c.niveau}
                  </p>
                  <span className="mt-2 inline-block w-fit rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-500">
                    {t(`cv.availability.${c.cv.profil.disponibilite}`)}
                  </span>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {c.cv.competences.slice(0, 4).map((s) => (
                      <span key={s.id} className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-night-line dark:text-slate-200">
                        {s.nom}
                      </span>
                    ))}
                    {c.cv.competences.length > 4 && (
                      <span className="px-1 py-1 text-xs text-slate-400">+{c.cv.competences.length - 4}</span>
                    )}
                  </div>

                  <button
                    onClick={() => setViewing(c)}
                    className="mt-auto inline-flex items-center gap-1.5 pt-6 text-sm font-semibold text-brand hover:underline"
                  >
                    <Eye size={15} /> {t("admin.profiles.view")}
                  </button>
                </article>
              ))}
            </div>
          </>
        )}
      </div>

      {viewing && <ProfileModal candidat={viewing} onClose={() => setViewing(null)} />}
    </section>
  );
}