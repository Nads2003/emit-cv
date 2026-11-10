import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { useAuth } from "@/hooks/useAuth";
import { getHomeRoute } from "@/utils/redirect";

/**
 * Protège un groupe de routes.
 * - non connecté      → /login (on mémorise la page demandée)
 * - mauvais rôle      → renvoyé vers son propre espace
 * Usage : <Route element={<ProtectedRoute roles={[ROLES.ETUDIANT]} />}> ... </Route>
 */
export default function ProtectedRoute({ roles }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return <Navigate to={ROUTES.LOGIN} replace state={{ from: location }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to={getHomeRoute(user)} replace />;

  return <Outlet />;
}