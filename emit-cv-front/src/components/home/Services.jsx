import { useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, FileSearch, Mic, Check, ArrowRight } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import ImageWithFallback from "@/components/common/ImageWithFallback";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";

// Placez vos images dans public/images/ (services-offres.jpg, services-cv.jpg, services-entretien.jpg)
const tabs = [
  { icon: Briefcase, to: ROUTES.OFFRES, image: "/images/services-offres.jpg" },
  { icon: FileSearch, to: ROUTES.ANALYSE_CV, image: "/images/services-cv.jpg" },
  { icon: Mic, to: ROUTES.ENTRETIEN_IA, image: "/images/services-entretien.jpg" },
];

export default function Services() {
  const { t } = useLanguage();
  const [active, setActive] = useState(0);
  const { icon: Icon, to, image } = tabs[active];

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-20 lg:px-12">
      <SectionTitle title1={t("services.title1")} title2={t("services.title2")}>
        <p className="mt-5 text-slate-500 dark:text-slate-400">{t("services.subtitle")}</p>
      </SectionTitle>

      {/* Onglets */}
      <div className="mt-10 flex flex-wrap justify-center gap-3">
        {tabs.map(({ icon: TabIcon }, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition ${
              active === i
                ? "bg-brand text-white shadow-[0_10px_30px_-8px_rgba(79,109,245,0.8)]"
                : "bg-white text-slate-600 hover:text-brand dark:bg-night-card dark:text-slate-200"
            }`}
          >
            <TabIcon size={18} />
            {t(`services.tabs.${i}.label`)}
          </button>
        ))}
      </div>

      {/* Contenu de l'onglet actif */}
      <div className="mt-10 grid items-center gap-10 rounded-[2rem] border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-10 lg:grid-cols-2">
        <div className="lg:px-4">
          <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand to-indigo-600 text-white">
            <Icon size={26} />
          </span>
          <h3 className="mt-8 text-2xl font-bold sm:text-3xl">{t(`services.tabs.${active}.title`)}</h3>
          <p className="mt-4 leading-relaxed text-slate-500 dark:text-slate-400">
            {t(`services.tabs.${active}.desc`)}
          </p>

          <ul className="mt-6 flex flex-wrap gap-x-8 gap-y-2 text-sm">
            {[0, 1].map((p) => (
              <li key={p} className="flex items-center gap-2">
                <Check size={16} className="text-emerald-500" />
                {t(`services.tabs.${active}.points.${p}`)}
              </li>
            ))}
          </ul>

          <Link
            to={to}
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:brightness-110"
          >
            {t(`services.tabs.${active}.cta`)}
            <ArrowRight size={16} />
          </Link>
        </div>

        <ImageWithFallback
          key={image}
          src={image}
          alt={t(`services.tabs.${active}.title`)}
          className="h-72 w-full rounded-3xl sm:h-96"
          fallback={<Icon size={72} className="text-white/80" />}
        />
      </div>
    </section>
  );
}