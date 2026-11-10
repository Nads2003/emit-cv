import { ROLES } from "@/constants/roles";
import { ROUTES } from "@/constants/routes";

// Page d'accueil de l'espace selon le rôle
export const getHomeRoute = (user) =>
  user?.role === ROLES.ADMIN ? ROUTES.ADMIN_DASHBOARD : ROUTES.ETUDIANT_DASHBOARD;

// Page de profil selon le rôle
export const getProfileRoute = (user) =>
  user?.role === ROLES.ADMIN ? ROUTES.ADMIN_PROFIL : ROUTES.ETUDIANT_PROFIL;