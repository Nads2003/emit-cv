import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, GraduationCap, MessageSquareText, Users } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";
import Features from "@/components/home/Features";
import HowItWorks from "@/components/home/HowItWorks";
import WhyChoose from "@/components/home/WhyChoose";
import Services from "@/components/home/Services";
import ContactSection from "@/components/home/ContactSection";

function FeatureCard({ icon, tone, text }) {
  const tones = {
    blue: "bg-brand/15 text-brand",
    amber: "bg-amber-400/15 text-amber-400",
  };
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
      <span className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-brand/10" />
      <span className={`relative mb-6 flex h-14 w-14 items-center justify-center rounded-2xl ${tones[tone]}`}>
        {icon}
      </span>
      <p className="relative text-[15px] leading-relaxed text-slate-600 dark:text-slate-200">{text}</p>
    </div>
  );
}

function FloatingBadge({ icon, tone, title, sub, className }) {
  const tones = {
    blue: "bg-brand/15 text-brand",
    green: "bg-emerald-400/15 text-emerald-400",
  };
  return (
    <div
      className={`absolute flex items-center gap-4 rounded-2xl border border-slate-200 bg-white/95 px-5 py-4 shadow-xl backdrop-blur dark:border-night-line dark:bg-night-card/95 ${className}`}
    >
      <span className={`flex h-12 w-12 items-center justify-center rounded-xl ${tones[tone]}`}>{icon}</span>
      <div>
        <p className="text-sm font-bold text-slate-900 dark:text-white">{title}</p>
        <p className="text-sm text-slate-500 dark:text-slate-400">{sub}</p>
      </div>
    </div>
  );
}

// Placez votre photo dans public/images/hero.jpg
function HeroVisual({ t }) {
  const [failed, setFailed] = useState(false);

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[580px]">
      <div className="absolute inset-0 rounded-full bg-brand/20 blur-3xl" />
      <div
        className="absolute inset-6 overflow-hidden border-4 border-slate-200 shadow-[0_0_80px_rgba(79,109,245,0.25)] dark:border-night-line"
        style={{ borderRadius: "50% 50% 50% 50% / 45% 45% 55% 55%" }}
      >
        {failed ? (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand/40 to-night-card">
            <GraduationCap size={96} className="text-white/80" />
          </div>
        ) : (
          <img
            src="/images/EMITPHOTO.jpg"
            alt="Étudiants de l'EMIT"
            onError={() => setFailed(true)}
            className="h-full w-full object-cover"
          />
        )}
      </div>

      <FloatingBadge
        className="right-0 top-2"
        tone="blue"
        icon={<Users size={22} />}
        title={t("hero.badgeTop.title")}
        sub={t("hero.badgeTop.sub")}
      />
      <FloatingBadge
        className="-left-2 bottom-6 sm:-left-8"
        tone="green"
        icon={<CheckCircle2 size={22} />}
        title={t("hero.badgeBottom.title")}
        sub={t("hero.badgeBottom.sub")}
      />
    </div>
  );
}

export default function Accueil() {
  const { t } = useLanguage();

  return (
    <>
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -left-40 top-20 h-96 w-96 rounded-full bg-brand/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-[1400px] items-center gap-14 px-5 py-14 lg:grid-cols-2 lg:px-12 lg:py-20">
          {/* Texte */}
          <div>
            <h1 className="text-4xl font-semibold leading-[1.15] tracking-tight sm:text-5xl xl:text-4xl">
              {t("hero.title1")} <span className="text-brand">{t("hero.title2")}</span>
            </h1>

            <div className="mt-8 flex gap-2.5" aria-hidden="true">
              <span className="h-3 w-3 rounded-full bg-brand" />
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              <span className="h-3 w-3 rounded-full bg-emerald-500" />
            </div>

            <div className="mt-10 grid max-w-xl gap-5 sm:grid-cols-2">
              <FeatureCard tone="blue" icon={<MessageSquareText size={24} />} text={t("hero.card1")} />
              <FeatureCard tone="amber" icon={<GraduationCap size={24} />} text={t("hero.card2")} />
            </div>

            <Link
              to={ROUTES.REGISTER}
              className="mt-10 inline-flex items-center gap-3 rounded-full bg-brand px-8 py-4 text-lg font-semibold text-white shadow-[0_12px_40px_-8px_rgba(79,109,245,0.7)] transition hover:-translate-y-0.5 hover:brightness-110"
            >
              {t("hero.cta")}
              <ArrowRight size={20} />
            </Link>
          </div>

          {/* Visuel */}
          <HeroVisual t={t} />
        </div>
      </section>

      <Features />
      <HowItWorks />
      <WhyChoose />
      <Services />
      <ContactSection />
    </>
  );
}