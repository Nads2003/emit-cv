import { LayoutDashboard, FileText, Briefcase, Mic, User } from "lucide-react";
import SidebarLayout from "@/layouts/SidebarLayout";
import { ROUTES } from "@/constants/routes";
import { useLanguage } from "@/hooks/useLanguage";


export default function EtudiantLayout() {
  const { t } = useLanguage();

  const links = [
    { to: ROUTES.ETUDIANT_DASHBOARD, icon: LayoutDashboard, label: t("side.dashboard"), end: true },
    { to: ROUTES.ETUDIANT_CV, icon: FileText, label: t("side.cv") },
    { to: ROUTES.ENTRETIEN_IA, icon: Mic, label: t("side.interview") },
    { to: ROUTES.OFFRES, icon: Briefcase, label: t("side.offers") },
        { to: ROUTES.ETUDIANT_PROFIL, icon: User, label: t("side.profile") },
  ];

  return <SidebarLayout links={links} />;
}