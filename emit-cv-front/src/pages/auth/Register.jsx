import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { User, Mail, Hash, Lock, Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { getHomeRoute } from "@/utils/redirect";
import { registerRequest } from "@/api/auth.api";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";

const inputClass =
  "w-full rounded-xl border border-slate-300 bg-transparent py-3 pl-11 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:placeholder:text-slate-500";

const iconClass = "absolute left-4 top-1/2 -translate-y-1/2 text-slate-400";

export default function Register() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ nom: "", email: "", matricule: "", password: "", confirm: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (user) return <Navigate to={getHomeRoute(user)} replace />;

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) return setError(t("register.weak"));
    if (form.password !== form.confirm) return setError(t("register.mismatch"));

    setLoading(true);
    try {
      await registerRequest({
        nom: form.nom.trim(),
        email: form.email.trim(),
        matricule: form.matricule.trim(),
        password: form.password,
      });
      navigate(ROUTES.LOGIN, { state: { registered: true } });
    } catch (err) {
      const status = err.response?.status;
      if (status === 400 || status === 409) setError(t("register.exists"));
      else if (!err.response) setError(t("login.network"));
      else setError(t("login.generic"));
    } finally {
      setLoading(false);
    }
  };

  const textFields = [
    { name: "nom", type: "text", icon: User, label: t("register.name"), autoComplete: "name", placeholder: "Rakoto Jean" },
    { name: "email", type: "email", icon: Mail, label: t("register.email"), autoComplete: "email", placeholder: "nom@emit.mg" },
    { name: "matricule", type: "text", icon: Hash, label: t("register.matricule"), autoComplete: "off", placeholder: "EMIT-2024-001" },
  ];

  const passwordFields = [
    { name: "password", label: t("register.password") },
    { name: "confirm", label: t("register.confirm") },
  ];

  return (
    <section className="mx-auto max-w-xl px-5 py-12 lg:py-20">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 dark:border-night-line dark:bg-night-card sm:p-10">
        <h1 className="text-3xl font-semibold">{t("register.title")}</h1>
        <p className="mt-2 text-slate-500 dark:text-slate-400">{t("register.subtitle")}</p>

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

          {textFields.map(({ name, type, icon: Icon, label, autoComplete, placeholder }) => (
            <div key={name}>
              <label htmlFor={name} className="mb-2 block text-sm font-medium">
                {label}
              </label>
              <div className="relative">
                <Icon size={18} className={iconClass} />
                <input
                  id={name}
                  name={name}
                  type={type}
                  required
                  autoComplete={autoComplete}
                  value={form[name]}
                  onChange={handleChange}
                  placeholder={placeholder}
                  className={inputClass}
                />
              </div>
            </div>
          ))}

          {passwordFields.map(({ name, label }, i) => (
            <div key={name}>
              <label htmlFor={name} className="mb-2 block text-sm font-medium">
                {label}
              </label>
              <div className="relative">
                <Lock size={18} className={iconClass} />
                <input
                  id={name}
                  name={name}
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="new-password"
                  value={form[name]}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className={`${inputClass} pr-12`}
                />
                {i === 0 && (
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    aria-label={showPassword ? t("login.hidePassword") : t("login.showPassword")}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-brand"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                )}
              </div>
              {i === 0 && <p className="mt-1.5 text-xs text-slate-400">{t("register.hint")}</p>}
            </div>
          ))}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 py-3.5 font-semibold text-white shadow-[0_12px_40px_-8px_rgba(79,109,245,0.7)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                {t("register.loading")}
              </>
            ) : (
              t("register.submit")
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("register.haveAccount")}{" "}
          <Link to={ROUTES.LOGIN} className="font-semibold text-brand hover:underline">
            {t("register.login")}
          </Link>
        </p>
      </div>
    </section>
  );
}