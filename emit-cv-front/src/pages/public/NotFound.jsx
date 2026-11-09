import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";

export default function NotFound() {
  const { t } = useLanguage();
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-5 py-32 text-center">
      <p className="text-7xl font-bold text-brand">404</p>
      <h1 className="mt-4 text-2xl font-semibold">{t("pages.notFound")}</h1>
      <Link to={ROUTES.HOME} className="mt-8 text-brand hover:underline">
        {t("pages.back")}
      </Link>
    </div>
  );
}