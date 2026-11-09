import { UserPlus, ScanSearch, Route, Rocket } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import { useLanguage } from "@/hooks/useLanguage";

const icons = [UserPlus, ScanSearch, Route, Rocket];

export default function HowItWorks() {
  const { t } = useLanguage();

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-20 lg:px-12">
      <SectionTitle title1={t("how.title1")} title2={t("how.title2")}>
        <p className="mt-5 text-slate-500 dark:text-slate-400">{t("how.subtitle")}</p>
      </SectionTitle>

      <div className="relative mt-16 grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
        {/* Ligne reliant les étapes */}
        <span className="absolute left-[12.5%] right-[12.5%] top-8 hidden h-px bg-brand/30 lg:block" />

        {icons.map((Icon, i) => (
          <div key={i} className="relative flex flex-col items-center text-center">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-brand to-indigo-600 text-xl font-bold text-white shadow-[0_0_30px_rgba(79,109,245,0.5)]">
              {i + 1}
            </span>
            <span className="mt-6 flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand dark:bg-night-card">
              <Icon size={20} />
            </span>
            <h3 className="mt-5 font-semibold">{t(`how.steps.${i}.title`)}</h3>
            <p className="mt-2 max-w-[240px] text-sm leading-relaxed text-slate-500 dark:text-slate-400">
              {t(`how.steps.${i}.desc`)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}