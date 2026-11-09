import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { getHomeRoute } from "@/utils/redirect";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";

const inputClass =
  "w-full rounded-xl border border-slate-300 bg-transparent py-3 pl-11 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:placeholder:text-slate-500";

export default function Login() {
  const { t } = useLanguage();
  const { user, login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Déjà connecté (ou connexion réussie) → redirection selon le rôle
  if (user) return <Navigate to={getHomeRoute(user)} replace />;

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.email.trim(), form.password);
    } catch (err) {
      const status = err.response?.status;
      if (status === 400 || status === 401) setError(t("login.invalid"));
      else if (!err.response) setError(t("login.network"));
      else setError(t("login.generic"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto grid max-w-[1200px] items-stretch gap-8 px-5 py-12 lg:grid-cols-2 lg:px-12 lg:py-20">
      {/* Panneau de présentation */}
      <div className="relative hidden overflow-hidden rounded-3xl bg-gradient-to-br from-brand to-indigo-700 p-10 text-white lg:flex lg:flex-col lg:justify-center">
        <span className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10" />
        <span className="absolute -bottom-20 -left-10 h-60 w-60 rounded-full bg-white/10" />
        <h2 className="relative text-3xl font-bold leading-tight">{t("login.panelTitle")}</h2>
        <ul className="relative mt-8 space-y-4">
          {[0, 1, 2].map((i) => (
            <li key={i} className="flex items-start gap-3 text-white/90">
              <CheckCircle2 size={20} className="mt-0.5 shrink-0" />
              {t(`login.panelPoints.${i}`)}
            </li>
          ))}
        </ul>
      </div>

      {/* Formulaire */}
      <div className="rounded-3xl border border-slate-200 bg-white p-8 dark:border-night-line dark:bg-night-card sm:p-10">
        <h1 className="text-3xl font-semibold">{t("login.title")}</h1>
        <p className="mt-2 text-slate-500 dark:text-slate-400">{t("login.subtitle")}</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {error && (
            <div
              role="alert"
              className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500"
            >
              <AlertCircle size={18} className="shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium">
              {t("login.email")}
            </label>
            <div className="relative">
              <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={form.email}
                onChange={handleChange}
                placeholder="nom@emit.mg"
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor="password" className="text-sm font-medium">
                {t("login.password")}
              </label>
              <Link to="#" className="text-sm text-brand hover:underline">
                {t("login.forgot")}
              </Link>
            </div>
            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={form.password}
                onChange={handleChange}
                placeholder="••••••••"
                className={`${inputClass} pr-12`}
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? t("login.hidePassword") : t("login.showPassword")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-brand"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 py-3.5 font-semibold text-white shadow-[0_12px_40px_-8px_rgba(79,109,245,0.7)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                {t("login.loading")}
              </>
            ) : (
              t("login.submit")
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("login.noAccount")}{" "}
          <Link to={ROUTES.REGISTER} className="font-semibold text-brand hover:underline">
            {t("login.register")}
          </Link>
        </p>
      </div>
    </section>
  );
}