import { ROLES } from "@/constants/roles";
import { ROUTES } from "@/constants/routes";

// Page d'accueil de l'espace selon le rôle
export const getHomeRoute = (user) =>
  user?.role === ROLES.ADMIN ? ROUTES.ADMIN_DASHBOARD : ROUTES.ETUDIANT_DASHBOARD;