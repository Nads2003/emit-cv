import { Link } from "react-router-dom";
import { Globe, MessageCircle, Users, AtSign, Shield } from "lucide-react";
import Logo from "@/components/common/Logo";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";

const socials = [Globe, MessageCircle, Users, AtSign];

export default function Footer() {
  const { t } = useLanguage();

  const columns = [
    {
      title: t("footer.product"),
      links: [
        { label: t("nav.offers"), to: ROUTES.OFFRES },
        { label: t("nav.cvAnalysis"), to: ROUTES.ANALYSE_CV },
        { label: t("nav.interview"), to: ROUTES.ENTRETIEN_IA },
      ],
    },
    {
      title: t("footer.company"),
      links: [
        { label: t("nav.contact"), to: ROUTES.CONTACT },
        { label: t("footer.about"), to: "#" },
        { label: t("footer.careers"), to: "#" },
        { label: t("footer.blog"), to: "#" },
      ],
    },
    {
      title: t("footer.legal"),
      links: [
        { label: t("footer.terms"), to: "#" },
        { label: t("footer.privacy"), to: "#" },
        { label: t("footer.cookies"), to: "#" },
        { label: t("footer.admin"), to: "#", icon: Shield },
      ],
    },
  ];

  return (
    <footer className="border-t border-slate-200 dark:border-night-line">
      <div className="mx-auto grid max-w-[1400px] gap-12 px-5 py-14 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-12">
        <div>
          <Logo />
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-slate-500 dark:text-slate-400">
            {t("footer.desc")}
          </p>
          <div className="mt-6 flex gap-3">
            {socials.map((Icon, i) => (
              <a
                key={i}
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 text-slate-600 transition hover:border-brand hover:text-brand dark:border-night-line dark:text-slate-300"
              >
                <Icon size={16} />
              </a>
            ))}
          </div>
        </div>

        {columns.map((col) => (
          <div key={col.title}>
            <h4 className="font-semibold">{col.title}</h4>
            <ul className="mt-5 space-y-3">
              {col.links.map(({ label, to, icon: Icon }) => (
                <li key={label}>
                  <Link
                    to={to}
                    className="inline-flex items-center gap-2 text-sm text-slate-600 transition hover:text-brand dark:text-slate-200"
                  >
                    {Icon && <Icon size={14} />}
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-slate-200 py-6 text-center text-sm text-slate-500 dark:border-night-line dark:text-slate-400">
        © {new Date().getFullYear()} EMIT-CV-IA. {t("footer.rights")}
      </div>
    </footer>
  );
}