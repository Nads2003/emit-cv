import { Routes, Route } from "react-router-dom";
import PublicLayout from "@/layouts/PublicLayout";
import Accueil from "@/pages/public/Accueil";
import Contact from "@/pages/public/Contact";
import ComingSoon from "@/pages/public/ComingSoon";
import NotFound from "@/pages/public/NotFound";
import Login from "@/pages/auth/Login";
import Offres from "@/pages/public/Offres";
import { ROUTES } from "@/constants/routes";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path={ROUTES.HOME} element={<Accueil />} />
        <Route path={ROUTES.OFFRES} element={<Offres />} />
        <Route path={ROUTES.ANALYSE_CV} element={<ComingSoon titleKey="nav.cvAnalysis" />} />
        <Route path={ROUTES.ENTRETIEN_IA} element={<ComingSoon titleKey="nav.interview" />} />
        <Route path={ROUTES.CONTACT} element={<Contact />} />
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.REGISTER} element={<ComingSoon titleKey="hero.cta" />} />

        {/* Espaces connectés (provisoires, protégés à l'étape suivante) */}
        <Route path={ROUTES.ADMIN_DASHBOARD} element={<ComingSoon titleKey="pages.dashboard" />} />
        <Route path={ROUTES.ETUDIANT_DASHBOARD} element={<ComingSoon titleKey="pages.dashboard" />} />

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}