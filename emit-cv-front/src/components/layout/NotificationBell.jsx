import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "@/api/notifications.api";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";

export default function NotificationBell({ btnClass = "" }) {
  const { t, lang } = useLanguage();
  const { user } = useAuth();
  const role = user?.role;
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const load = useCallback(() => {
    if (!role) return;
    getNotifications(role)
      .then(setItems)
      .catch(() => {});
  }, [role]);

  // Chargement + mise à jour (événement local et vérification toutes les 30 s)
  useEffect(() => {
    load();
    window.addEventListener("emit:notifs", load);
    const timer = setInterval(load, 30000);
    return () => {
      window.removeEventListener("emit:notifs", load);
      clearInterval(timer);
    };
  }, [load]);

  // Fermeture : clic à l'extérieur ou touche Échap
  useEffect(() => {
    if (!open) return;
    const onClick = (e) => !ref.current?.contains(e.target) && setOpen(false);
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  const unread = items.filter((n) => !n.lu).length;

  const read = (n) => {
    if (n.lu) return;
    setItems((list) => list.map((x) => (x.id === n.id ? { ...x, lu: true } : x)));
    markNotificationRead(role, n.id);
  };

  const readAll = () => {
    setItems((list) => list.map((x) => ({ ...x, lu: true })));
    markAllNotificationsRead(role);
  };

  const formatDate = (d) =>
    new Date(d).toLocaleString(lang === "fr" ? "fr-FR" : "en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`relative ${btnClass}`}
        aria-label={t("bell.title")}
        aria-expanded={open}
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-3 w-[min(22rem,calc(100vw-2.5rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-night-line dark:bg-night-card">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-night-line">
            <p className="font-semibold">{t("bell.title")}</p>
            {unread > 0 && (
              <button onClick={readAll} className="inline-flex items-center gap-1.5 text-xs font-medium text-brand hover:underline">
                <CheckCheck size={14} /> {t("bell.markAll")}
              </button>
            )}
          </div>

          <ul className="max-h-96 overflow-y-auto">
            {items.length === 0 ? (
              <li className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">{t("bell.empty")}</li>
            ) : (
              items.map((n) => (
                <li key={n.id}>
                  <button
                    onClick={() => read(n)}
                    className={`flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-slate-100 dark:hover:bg-night-line/50 ${
                      n.lu ? "" : "bg-brand/5"
                    }`}
                  >
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${n.lu ? "bg-transparent" : "bg-brand"}`} />
                    <span className="min-w-0">
                      <span className={`block text-sm ${n.lu ? "text-slate-500 dark:text-slate-400" : "font-medium"}`}>
                        {n.key ? t(n.key, n.params) : n.message}
                      </span>
                      <span className="mt-1 block text-xs text-slate-400">{formatDate(n.date)}</span>
                    </span>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}