import { FileSearch, MessagesSquare, Users, Wrench } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import { useLanguage } from "@/hooks/useLanguage";

const items = [
  { icon: FileSearch, tone: "bg-brand/15 text-brand" },
  { icon: MessagesSquare, tone: "bg-amber-400/15 text-amber-400" },
  { icon: Users, tone: "bg-emerald-500/15 text-emerald-400" },
  { icon: Wrench, tone: "bg-violet-500/15 text-violet-400" },
];

export default function Features() {
  const { t } = useLanguage();

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-20 lg:px-12">
      <SectionTitle title1={t("features.title1")} title2={t("features.title2")}>
        <h3 className="mt-8 text-lg font-semibold">{t("features.subtitle")}</h3>
        <p className="mt-4 text-slate-500 dark:text-slate-400">{t("features.desc")}</p>
      </SectionTitle>

      <div className="mt-14 grid gap-6 md:grid-cols-2">
        {items.map(({ icon: Icon, tone }, i) => (
          <article
            key={i}
            className="rounded-3xl border border-slate-200 bg-white p-8 dark:border-night-line dark:bg-night-card"
          >
            <span className={`mb-6 flex h-14 w-14 items-center justify-center rounded-2xl ${tone}`}>
              <Icon size={24} />
            </span>
            <h4 className="text-lg font-semibold">{t(`features.items.${i}.title`)}</h4>
            <p className="mt-3 text-[15px] leading-relaxed text-slate-500 dark:text-slate-400">
              {t(`features.items.${i}.desc`)}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}