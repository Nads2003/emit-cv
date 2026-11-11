import { useEffect, useMemo, useState } from "react";
import { SearchX, AlertCircle } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import OffreCard from "@/components/offers/OffreCard";
import OffreFilters from "@/components/offers/OffreFilters";
import OffreModal from "@/components/offers/OffreModal";
import { getOffres } from "@/api/offres.api";
import { useLanguage } from "@/hooks/useLanguage";

const INITIAL_FILTERS = { q: "", type: "all", mention: "all", niveau: "all" };

export default function Offres() {
  const { t } = useLanguage();
  const [offres, setOffres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let ignore = false;
    getOffres()
      .then((data) => !ignore && setOffres(data))
      .catch(() => !ignore && setError(true))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
  }, []);

  const mentions = useMemo(() => [...new Set(offres.map((o) => o.mention))], [offres]);

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return offres.filter((o) => {
      if (filters.type !== "all" && o.type !== filters.type) return false;
      if (filters.mention !== "all" && o.mention !== filters.mention) return false;
      if (filters.niveau !== "all" && o.niveau !== filters.niveau) return false;
      if (!q) return true;
      const text = [o.titre, o.description, o.entreprise, ...o.competences.map((c) => c.nom)]
        .join(" ")
        .toLowerCase();
      return text.includes(q);
    });
  }, [offres, filters]);

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-16 lg:px-12">
      <SectionTitle title1={t("offers.title1")} title2={t("offers.title2")}>
        <p className="mt-5 text-slate-500 dark:text-slate-400">{t("offers.subtitle")}</p>
      </SectionTitle>

      <div className="mt-12">
        <OffreFilters
          filters={filters}
          setFilters={setFilters}
          mentions={mentions}
          onReset={() => setFilters(INITIAL_FILTERS)}
        />
      </div>

      {/* Contenu */}
      <div className="mt-8">
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-72 animate-pulse rounded-3xl border border-slate-200 bg-white dark:border-night-line dark:bg-night-card"
              />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-20 text-center text-slate-500 dark:text-slate-400">
            <AlertCircle size={40} className="text-red-500" />
            <p>{t("offers.error")}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-20 text-center text-slate-500 dark:text-slate-400">
            <SearchX size={40} />
            <p>{t("offers.empty")}</p>
          </div>
        ) : (
          <>
            <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-900 dark:text-white">{filtered.length}</span>{" "}
              {t("offers.results")}
            </p>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {filtered.map((offre) => (
                <OffreCard key={offre.id} offre={offre} onOpen={setSelected} />
              ))}
            </div>
          </>
        )}
      </div>

      {selected && <OffreModal offre={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}