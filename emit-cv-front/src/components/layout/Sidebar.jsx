import { NavLink, Link, useNavigate } from "react-router-dom";
import { Home, LogOut, LogIn } from "lucide-react";
import Logo from "@/components/common/Logo";
import { ROUTES } from "@/constants/routes";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";

const itemClass = ({ isActive }) =>
  `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
    isActive
      ? "bg-brand/15 text-brand"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-line/60"
  }`;

export default function Sidebar({ links, onNavigate }) {
  const { t } = useLanguage();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    onNavigate?.();
    navigate(ROUTES.HOME);
  };

  return (
    <div className="flex h-full flex-col p-5">
      <Logo />

      {/* Utilisateur */}
      <div className="mt-8 flex items-center gap-3 rounded-2xl bg-slate-100 p-3 dark:bg-night-line/50">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand text-lg font-bold text-white">
          {(user?.nom ?? "D").charAt(0).toUpperCase()}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{user?.nom ?? t("side.demo")}</p>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email ?? t("side.student")}</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-6 flex flex-col gap-1.5">
        {links.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end} className={itemClass} onClick={onNavigate}>
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bas de menu */}
      <div className="mt-auto flex flex-col gap-1.5 border-t border-slate-200 pt-4 dark:border-night-line">
        <Link
          to={ROUTES.HOME}
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-line/60"
        >
          <Home size={18} />
          {t("side.home")}
        </Link>

        {user ? (
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-red-500 transition hover:bg-red-500/10"
          >
            <LogOut size={18} />
            {t("nav.logout")}
          </button>
        ) : (
          <Link
            to={ROUTES.LOGIN}
            onClick={onNavigate}
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-brand transition hover:bg-brand/10"
          >
            <LogIn size={18} />
            {t("nav.login")}
          </Link>
        )}
      </div>
    </div>
  );
}