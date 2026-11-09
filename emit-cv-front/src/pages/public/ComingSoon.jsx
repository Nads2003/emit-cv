import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";

export default function ComingSoon({ titleKey }) {
  const { t } = useLanguage();
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-5 py-32 text-center">
      <h1 className="text-3xl font-semibold">{t(titleKey)}</h1>
      <p className="mt-3 text-slate-500 dark:text-slate-400">{t("pages.soon")}</p>
      <Link to={ROUTES.HOME} className="mt-8 text-brand hover:underline">
        {t("pages.back")}
      </Link>
    </div>
  );
}