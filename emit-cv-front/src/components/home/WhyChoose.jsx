import { Sparkles, ShieldCheck, UserCog, Star } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import { useLanguage } from "@/hooks/useLanguage";

const items = [
  { icon: Sparkles, tone: "text-brand" },
  { icon: ShieldCheck, tone: "text-violet-400" },
  { icon: UserCog, tone: "text-brand" },
];

const stats = ["1200+", "300+", "95%"];

export default function WhyChoose() {
  const { t } = useLanguage();

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-20 lg:px-12">
      <SectionTitle title1={t("why.title1")} title2={t("why.title2")} />

      <div className="mt-14 grid items-center gap-10 lg:grid-cols-2">
        {/* Liste des atouts avec fond organique */}
        <div
          className="space-y-8 bg-slate-100 p-8 dark:bg-night-card sm:p-12"
          style={{ borderRadius: "45% 55% 50% 50% / 40% 40% 60% 60%" }}
        >
          {items.map(({ icon: Icon, tone }, i) => (
            <div key={i} className="flex gap-4">
              <span
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white dark:bg-night-line ${tone}`}
              >
                <Icon size={20} />
              </span>
              <div>
                <h3 className="font-semibold">{t(`why.items.${i}.title`)}</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                  {t(`why.items.${i}.desc`)}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Carte statistiques */}
        <div className="rounded-3xl bg-gradient-to-br from-brand to-indigo-700 p-8 text-white shadow-[0_20px_60px_-15px_rgba(79,109,245,0.6)] sm:p-10">
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20">
            <Star size={28} fill="currentColor" />
          </span>
          <h3 className="mt-8 text-2xl font-bold">{t("why.cardTitle")}</h3>
          <p className="mt-4 leading-relaxed text-white/90">{t("why.cardDesc")}</p>

          <div className="mt-8 grid grid-cols-3 gap-4">
            {stats.map((value, i) => (
              <div key={i}>
                <p className="text-2xl font-bold">{value}</p>
                <p className="mt-1 text-xs text-white/80 sm:text-sm">{t(`why.stats.${i}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}