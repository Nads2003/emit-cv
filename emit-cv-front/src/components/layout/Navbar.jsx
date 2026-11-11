import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, X, Sun, Moon, LogOut } from "lucide-react";
import Logo from "@/components/common/Logo";
import { ROUTES } from "@/constants/routes";
import { getHomeRoute } from "@/utils/redirect";
import { useTheme } from "@/hooks/useTheme";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import NotificationBell from "@/components/layout/NotificationBell";

const links = [
  { to: ROUTES.HOME, key: "nav.home", end: true },
  { to: ROUTES.OFFRES, key: "nav.offers" },
  { to: ROUTES.CONTACT, key: "nav.contact" },
];

const linkClass = ({ isActive }) =>
  `text-[16px] transition-colors hover:text-brand ${
    isActive ? "text-brand" : "text-slate-600 dark:text-slate-200"
  }`;

const roundBtn =
  "flex h-12 w-12  items-center justify-center rounded-full border border-slate-400 text-slate-700 transition hover:border-brand hover:text-brand dark:border-night-line dark:text-white";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLang, t } = useLanguage();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md dark:border-night-line dark:bg-night/80">
      <div className="mx-auto flex h-[84px] max-w-[1400px] items-center justify-between px-5 lg:px-12">
        <Logo />

        {/* Liens - desktop */}
        <nav className="hidden items-center gap-6 xl:gap-10 lg:flex">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              {t(l.key)}
            </NavLink>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button onClick={toggleTheme} className={roundBtn} aria-label={t("nav.toggleTheme")}>
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          <button
            onClick={toggleLang}
            className={`${roundBtn} text-sm font-bold uppercase`}
            aria-label={t("nav.toggleLang")}
          >
            {lang}
          </button>

          {user ? (
            <>
            <NotificationBell btnClass={roundBtn} />
              <Link
                to={getHomeRoute(user)}
                className="hidden rounded-full bg-brand px-5 py-2.5 text-[15px] font-semibold text-white transition hover:brightness-110 sm:inline"
              >
                {t("nav.mySpace")}
              </Link>
              <button onClick={logout} className={roundBtn} aria-label={t("nav.logout")} title={t("nav.logout")}>
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <Link
              to={ROUTES.LOGIN}
              className="hidden px-2 text-[17px] text-slate-700 transition hover:text-brand dark:text-white sm:inline"
            >
              {t("nav.login")}
            </Link>
          )}

          <button
            onClick={() => setOpen((o) => !o)}
            className={`${roundBtn} lg:hidden`}
            aria-label={t("nav.menu")}
            aria-expanded={open}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Menu - mobile */}
      {open && (
        <nav className="flex flex-col gap-4 border-t border-slate-200 px-5 py-5 dark:border-night-line lg:hidden">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass} onClick={() => setOpen(false)}>
              {t(l.key)}
            </NavLink>
          ))}
          <Link
            to={user ? getHomeRoute(user) : ROUTES.LOGIN}
            onClick={() => setOpen(false)}
            className="text-[17px] font-semibold text-brand sm:hidden"
          >
            {user ? t("nav.mySpace") : t("nav.login")}
          </Link>
        </nav>
      )}
    </header>
  );
}