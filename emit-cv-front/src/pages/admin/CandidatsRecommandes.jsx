import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Check, X, Eye, AlertCircle, Star, UserX } from "lucide-react";
import ScoreBadge from "@/components/common/ScoreBadge";
import ProfileModal from "@/components/admin/ProfileModal";
import { getOffres } from "@/api/offres.api";
import { getClassement, setDecision } from "@/api/candidats.api";
import { criteresOf } from "@/utils/scoring";
import { useLanguage } from "@/hooks/useLanguage";

const DECISION_TONE = {
  attente: "bg-slate-500/15 text-slate-400",
  selectionne: "bg-emerald-500/15 text-emerald-500",
  refuse: "bg-red-500/15 text-red-500",
};

const selectClass =
  "rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand dark:border-night-line dark:bg-night-card";

export default function CandidatsRecommandes() {
  const { t } = useLanguage();
  const [params, setParams] = useSearchParams();
  const [offres, setOffres] = useState([]);
  const [candidats, setCandidats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState({ q: "", min: 0, decision: "all" });
  const [viewing, setViewing] = useState(null);

  const offreId = Number(params.get("offre")) || null;
  const offre = offres.find((o) => o.id === offreId);

  // Chargement des offres + sélection par défaut
  useEffect(() => {
    let ignore = false;
    getOffres()
      .then((list) => {
        if (ignore) return;
        setOffres(list);
        if (!params.get("offre") && list.length > 0) {
          const first = list.find((o) => o.statut === "ouverte") ?? list[0];
          setParams({ offre: String(first.id) }, { replace: true });
        }
      })
      .catch(() => !ignore && setError(true));
    return () => {
      ignore = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Classement de l'offre choisie
  useEffect(() => {
    if (!offreId) return;
    let ignore = false;
    setLoading(true);
    setError(false);
    getClassement(offreId)
      .then((d) => !ignore && setCandidats(d))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, [offreId]);

  const ranks = useMemo(() => new Map(candidats.map((c, i) => [c.id, i + 1])), [candidats]);

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return candidats.filter((c) => {
      if (c.score < filters.min) return false;
      if (filters.decision !== "all" && c.decision !== filters.decision) return false;
      if (!q) return true;
      return [c.cv.profil.nom, c.matricule, ...c.cv.competences.map((s) => s.nom)].join(" ").toLowerCase().includes(q);
    });
  }, [candidats, filters]);

  const selectedCount = candidats.filter((c) => c.decision === "selectionne").length;

  // Cliquer deux fois sur la même décision l'annule
  const decide = async (cand, decision) => {
    const next = cand.decision === decision ? "attente" : decision;
    const apply = (value) =>
      setCandidats((list) => list.map((c) => (c.id === cand.id ? { ...c, decision: value } : c)));
    apply(next);
    try {
      await setDecision(offreId, cand.id, next);
    } catch {
      apply(cand.decision);
    }
  };

  const update = (key) => (e) => setFilters((f) => ({ ...f, [key]: key === "min" ? Number(e.target.value) : e.target.value }));

  return (
    <section className="mx-auto max-w-[1200px] px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{t("admin.ranking.title")}</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("admin.ranking.subtitle")}</p>

      {/* Choix de l'offre */}
      <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-5 dark:border-night-line dark:bg-night-card sm:p-6">
        <label className="block text-sm font-medium">
          {t("admin.ranking.offer")}
          <select
            value={offreId ?? ""}
            onChange={(e) => setParams({ offre: e.target.value })}
            className={`${selectClass} mt-2 w-full`}
          >
            {offres.length === 0 && <option value="">{t("admin.ranking.noOffers")}</option>}
            {offres.map((o) => (
              <option key={o.id} value={o.id}>
                {o.titre} ({t(`offers.status.${o.statut}`)})
              </option>
            ))}
          </select>
        </label>

        {offre && (
          <div className="mt-4">
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{t("admin.ranking.criteria")}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {criteresOf(offre).map((c) => (
                <span
                  key={c.nom}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs ${
                    c.obligatoire ? "bg-brand/15 font-medium text-brand" : "bg-slate-100 text-slate-600 dark:bg-night-line dark:text-slate-200"
                  }`}
                >
                  {c.obligatoire && <Star size={12} fill="currentColor" />}
                  {c.nom} · {t(`cv.levels.${c.niveauRequis}`)} · ×{c.poids}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Filtres */}
      <div className="mt-6 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={filters.q}
            onChange={update("q")}
            placeholder={t("admin.ranking.search")}
            className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:bg-night-card"
          />
        </div>
        <select value={filters.min} onChange={update("min")} className={selectClass} aria-label={t("admin.ranking.minScore")}>
          {[0, 50, 70, 80].map((m) => (
            <option key={m} value={m}>
              {m === 0 ? t("admin.ranking.anyScore") : `${t("admin.ranking.minScore")} ${m}%`}
            </option>
          ))}
        </select>
        <select value={filters.decision} onChange={update("decision")} className={selectClass}>
          <option value="all">{t("admin.ranking.allDecisions")}</option>
          {["attente", "selectionne", "refuse"].map((d) => (
            <option key={d} value={d}>
              {t(`admin.ranking.decisions.${d}`)}
            </option>
          ))}
        </select>
      </div>

      {!loading && candidats.length > 0 && (
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
          <span className="font-semibold text-slate-900 dark:text-white">{filtered.length}</span> {t("admin.ranking.total")} ·{" "}
          <span className="font-semibold text-emerald-500">{selectedCount}</span> {t("admin.ranking.selectedCount")}
        </p>
      )}

      {/* Classement */}
      <div className="mt-5 space-y-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-36 animate-pulse rounded-3xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card" />
          ))
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <AlertCircle size={36} className="text-red-500" />
            <p>{t("admin.ranking.error")}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-slate-500 dark:text-slate-400">
            <UserX size={36} />
            <p>{t("admin.ranking.empty")}</p>
          </div>
        ) : (
          filtered.map((c) => {
            const rank = ranks.get(c.id);
            return (
              <article
                key={c.id}
                className={`rounded-3xl border bg-white p-5 transition dark:bg-night-card sm:p-6 ${
                  c.decision === "selectionne" ? "border-emerald-500/60" : "border-slate-200 dark:border-night-line"
                } ${c.decision === "refuse" ? "opacity-60" : ""}`}
              >
                <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
                  <div className="flex items-center gap-4">
                    <span
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                        rank === 1 ? "bg-amber-400 text-slate-900" : "bg-slate-100 text-slate-600 dark:bg-night-line dark:text-slate-200"
                      }`}
                      title={t("admin.ranking.rank")}
                    >
                      #{rank}
                    </span>
                    <ScoreBadge score={c.score} />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{c.cv.profil.nom}</h3>
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${DECISION_TONE[c.decision]}`}>
                        {t(`admin.ranking.decisions.${c.decision}`)}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {c.matricule} · {c.mention} · {c.niveau} · {t(`cv.availability.${c.cv.profil.disponibilite}`)}
                    </p>

                    {c.communes.length > 0 && (
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <span className="text-xs text-slate-400">{t("admin.ranking.common")}</span>
                        {c.communes.map((s) => (
                          <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-500">
                            <Check size={12} /> {s}
                          </span>
                        ))}
                      </div>
                    )}
                    {c.manquantes.length > 0 && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className="text-xs text-slate-400">{t("admin.ranking.missing")}</span>
                        {c.manquantes.map((s) => (
                          <span key={s} className="rounded-lg bg-amber-400/15 px-2.5 py-1 text-xs font-medium text-amber-500">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 lg:w-44 lg:flex-col">
                    <button
                      onClick={() => decide(c, "selectionne")}
                      className={`inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition ${
                        c.decision === "selectionne"
                          ? "bg-emerald-500 text-white"
                          : "border border-emerald-500/50 text-emerald-500 hover:bg-emerald-500/10"
                      }`}
                    >
                      <Check size={14} />
                      {c.decision === "selectionne" ? t("admin.ranking.selectedBtn") : t("admin.ranking.select")}
                    </button>
                    <button
                      onClick={() => decide(c, "refuse")}
                      className={`inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition ${
                        c.decision === "refuse"
                          ? "bg-red-500 text-white"
                          : "border border-red-500/40 text-red-500 hover:bg-red-500/10"
                      }`}
                    >
                      <X size={14} />
                      {c.decision === "refuse" ? t("admin.ranking.refusedBtn") : t("admin.ranking.refuse")}
                    </button>
                    <button
                      onClick={() => setViewing(c)}
                      className="inline-flex items-center justify-center gap-1.5 rounded-full border border-slate-300 px-4 py-2 text-xs font-medium transition hover:border-brand hover:text-brand dark:border-night-line"
                    >
                      <Eye size={14} /> {t("admin.ranking.viewCv")}
                    </button>
                  </div>
                </div>
              </article>
            );
          })
        )}
      </div>

      {viewing && <ProfileModal candidat={viewing} onClose={() => setViewing(null)} />}
    </section>
  );
}