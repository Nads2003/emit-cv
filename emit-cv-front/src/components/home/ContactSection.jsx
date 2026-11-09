import { useState } from "react";
import { Mail, Phone, MapPin, Send } from "lucide-react";
import SectionTitle from "@/components/common/SectionTitle";
import { useLanguage } from "@/hooks/useLanguage";

const inputClass =
  "w-full rounded-xl border border-slate-300 bg-transparent px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:placeholder:text-slate-500";

export default function ContactSection() {
  const { t } = useLanguage();
  const [sent, setSent] = useState(false);

  const infos = [
    { icon: Mail, label: t("contact.email"), value: "contact@emit-cv-ia.com" },
    { icon: Phone, label: t("contact.phone"), value: "+261 34 00 000 00" },
    { icon: MapPin, label: t("contact.address"), value: t("contact.addressValue") },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO : envoyer vers l'API Django plus tard
    setSent(true);
    e.target.reset();
  };

  return (
    <section id="contact" className="py-20">
      <div className="mx-auto max-w-[1400px] px-5 lg:px-12">
        <SectionTitle title1={t("contact.title1")} title2={t("contact.title2")}>
          <p className="mt-5 text-slate-500 dark:text-slate-400">{t("contact.subtitle")}</p>
        </SectionTitle>
      </div>

      <div className="mt-12 bg-slate-100 py-12 dark:bg-night-card/60">
        <div className="mx-auto grid max-w-[1400px] gap-8 px-5 lg:grid-cols-[1fr_2fr] lg:px-12">
          {/* Infos */}
          <div className="space-y-5">
            {infos.map(({ icon: Icon, label, value }) => (
              <div
                key={label}
                className="flex items-center gap-4 rounded-2xl bg-white p-5 dark:bg-night-card"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/15 text-brand">
                  <Icon size={20} />
                </span>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
                  <p className="text-sm font-semibold">{value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Formulaire */}
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl bg-white p-6 dark:bg-night-card sm:p-8"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <input type="text" required placeholder={t("contact.name")} className={inputClass} />
              <input type="email" required placeholder={t("contact.emailField")} className={inputClass} />
            </div>
            <textarea
              required
              rows={5}
              placeholder={t("contact.message")}
              className={`${inputClass} mt-4 resize-y`}
            />
            <button
              type="submit"
              className="mt-5 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 px-7 py-3 text-sm font-semibold text-white transition hover:brightness-110"
            >
              <Send size={16} />
              {t("contact.send")}
            </button>
            {sent && <p className="mt-4 text-sm text-emerald-500">{t("contact.sent")}</p>}
          </form>
        </div>
      </div>
    </section>
  );
}