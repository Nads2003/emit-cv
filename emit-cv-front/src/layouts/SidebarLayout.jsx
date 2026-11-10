import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu, X, Sun, Moon } from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";
import { useTheme } from "@/hooks/useTheme";
import { useLanguage } from "@/hooks/useLanguage";
import NotificationBell from "@/components/layout/NotificationBell";

const roundBtn =
  "flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 text-slate-700 transition hover:border-brand hover:text-brand dark:border-night-line dark:text-white";

export default function SidebarLayout({ links }) {
  const { t, lang, toggleLang } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen lg:flex">
      {/* Menu latéral - desktop */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-slate-200 bg-white dark:border-night-line dark:bg-night-card lg:block">
        <Sidebar links={links} />
      </aside>

      {/* Menu latéral - mobile */}
      {open && (
        <div className="fixed inset-0 z-[60] lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-72 bg-white dark:bg-night-card">
            <Sidebar links={links} onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-5 backdrop-blur-md dark:border-night-line dark:bg-night/80 lg:justify-end lg:px-12">
          <button onClick={() => setOpen(true)} className={`${roundBtn} lg:hidden`} aria-label={t("nav.menu")}>
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>

          <div className="flex items-center gap-3">
            <NotificationBell btnClass={roundBtn} />
            <button onClick={toggleTheme} className={roundBtn} aria-label={t("nav.toggleTheme")}></button>
            <button onClick={toggleTheme} className={roundBtn} aria-label={t("nav.toggleTheme")}>
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              onClick={toggleLang}
              className={`${roundBtn} text-xs font-bold uppercase`}
              aria-label={t("nav.toggleLang")}
            >
              {lang}
            </button>
          </div>
        </header>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}