import { Routes, Route } from "react-router-dom";
import PublicLayout from "@/layouts/PublicLayout";
import EtudiantLayout from "@/layouts/EtudiantLayout";
import AdminLayout from "@/layouts/AdminLayout";
import ProtectedRoute from "@/routes/ProtectedRoute";
import Accueil from "@/pages/public/Accueil";
import Contact from "@/pages/public/Contact";
import Offres from "@/pages/public/Offres";
import ComingSoon from "@/pages/public/ComingSoon";
import NotFound from "@/pages/public/NotFound";
import Login from "@/pages/auth/Login";
import Register from "@/pages/auth/Register";
import MonCV from "@/pages/etudiant/MonCV";
import EtudiantDashboard from "@/pages/etudiant/Dashboard";
import Entretien from "@/pages/etudiant/Entretien";
import AdminDashboard from "@/pages/admin/Dashboard";
import GestionOffres from "@/pages/admin/GestionOffres";
import OffreForm from "@/pages/admin/OffreForm";
import CandidatsRecommandes from "@/pages/admin/CandidatsRecommandes";
import RechercheProfils from "@/pages/admin/RechercheProfils";
import { ROUTES } from "@/constants/routes";
import { ROLES } from "@/constants/roles";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Pages publiques */}
      <Route element={<PublicLayout />}>
        <Route path={ROUTES.HOME} element={<Accueil />} />
        <Route path={ROUTES.OFFRES} element={<Offres />} />
        <Route path={ROUTES.ANALYSE_CV} element={<ComingSoon titleKey="nav.cvAnalysis" />} />
        <Route path={ROUTES.CONTACT} element={<Contact />} />
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.REGISTER} element={<Register />} />
        <Route path="*" element={<NotFound />} />
      </Route>

      {/* Espace étudiant */}
      <Route element={<EtudiantLayout />}>
        {/* Mon CV : volontairement ouvert pour la démo */}
        <Route path={ROUTES.ETUDIANT_CV} element={<MonCV />} />

        <Route element={<ProtectedRoute roles={[ROLES.ETUDIANT]} />}>
          <Route path={ROUTES.ETUDIANT_DASHBOARD} element={<EtudiantDashboard />} />
          <Route path={ROUTES.ENTRETIEN_IA} element={<Entretien />} />
        </Route>
      </Route>

      {/* Espace administrateur */}
      <Route element={<ProtectedRoute roles={[ROLES.ADMIN]} />}>
        <Route element={<AdminLayout />}>
          <Route path={ROUTES.ADMIN_DASHBOARD} element={<AdminDashboard />} />
          <Route path={ROUTES.ADMIN_OFFRES} element={<GestionOffres />} />
          <Route path={ROUTES.ADMIN_OFFRE_NEW} element={<OffreForm />} />
          <Route path={ROUTES.ADMIN_OFFRE_EDIT} element={<OffreForm />} />
          <Route path={ROUTES.ADMIN_CANDIDATS} element={<CandidatsRecommandes />} />
          <Route path={ROUTES.ADMIN_PROFILS} element={<RechercheProfils />} />
        </Route>
      </Route>
    </Routes>
  );
}