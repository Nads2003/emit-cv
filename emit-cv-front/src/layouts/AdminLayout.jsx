import { LayoutDashboard, Briefcase, UserCheck, Search } from "lucide-react";
import SidebarLayout from "@/layouts/SidebarLayout";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";

export default function AdminLayout() {
  const { t } = useLanguage();

  const links = [
    { to: ROUTES.ADMIN_DASHBOARD, icon: LayoutDashboard, label: t("side.dashboard"), end: true },
    { to: ROUTES.ADMIN_OFFRES, icon: Briefcase, label: t("side.offers") },
    { to: ROUTES.ADMIN_CANDIDATS, icon: UserCheck, label: t("side.candidates") },
    { to: ROUTES.ADMIN_PROFILS, icon: Search, label: t("side.profiles") },
  ];

  return <SidebarLayout links={links} />;
}