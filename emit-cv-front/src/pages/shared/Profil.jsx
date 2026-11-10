import { useRef, useState } from "react";
import { Camera, Trash2, Loader2, CheckCircle2, AlertCircle, Eye, EyeOff } from "lucide-react";
import Avatar from "@/components/common/Avatar";
import Field from "@/components/cv/Field";
import { MENTIONS, NIVEAUX_ETUDE } from "@/constants/academic";
import { ROLES } from "@/constants/roles";
import { updateProfil, changePassword } from "@/api/profil.api";
import { resizeImage } from "@/utils/image";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";

const MAX_PHOTO = 2 * 1024 * 1024;
const PHONE_RE = /^[+\d][\d\s().-]{5,}$/;
const DEFAULTS = { telephone: "", adresse: "", matricule: "", mention: MENTIONS[0], niveau: "L3", poste: "" };
const EMPTY_PWD = { current: "", next: "", confirm: "" };

const card = "rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-8";

function Notice({ notice }) {
  if (!notice) return null;
  const ok = notice.type === "ok";
  return (
    <div
      role={ok ? "status" : "alert"}
      className={`flex items-center gap-2 rounded-xl border px-4 py-3 text-sm ${
        ok
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
          : "border-red-500/30 bg-red-500/10 text-red-500"
      }`}
    >
      {ok ? <CheckCircle2 size={18} className="shrink-0" /> : <AlertCircle size={18} className="shrink-0" />}
      {notice.text}
    </div>
  );
}

function SubmitButton({ loading, disabled, children }) {
  return (
    <button
      type="submit"
      disabled={loading || disabled}
      className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 px-8 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  );
}

export default function Profil() {
  const { t } = useLanguage();
  const { user, updateUser } = useAuth();
  const fileRef = useRef(null);
  const isStudent = user.role === ROLES.ETUDIANT;

  const base = { ...DEFAULTS, ...user };
  const [form, setForm] = useState(base);
  const [photo, setPhoto] = useState(undefined); // undefined = inchangée | null = supprimée | { blob, preview }
  const [saving, setSaving] = useState(false);
  const [infoNotice, setInfoNotice] = useState(null);

  const [pwd, setPwd] = useState(EMPTY_PWD);
  const [showPwd, setShowPwd] = useState(false);
  const [pwdSaving, setPwdSaving] = useState(false);
  const [pwdNotice, setPwdNotice] = useState(null);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const setP = (key) => (e) => setPwd((p) => ({ ...p, [key]: e.target.value }));

  const shownPhoto = photo === null ? null : photo ? photo.preview : user.photo;
  const editable = isStudent ? ["nom", "telephone", "adresse", "mention", "niveau"] : ["nom", "telephone", "adresse", "poste"];
  const dirty = photo !== undefined || editable.some((k) => (form[k] ?? "") !== (base[k] ?? ""));

  const pickPhoto = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setInfoNotice(null);

    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return setInfoNotice({ type: "error", text: t("profile.photo.badType") });
    if (file.size > MAX_PHOTO) return setInfoNotice({ type: "error", text: t("profile.photo.tooBig") });

    try {
      setPhoto(await resizeImage(file));
    } catch {
      setInfoNotice({ type: "error", text: t("profile.photo.error") });
    }
  };

  const saveInfo = async (e) => {
    e.preventDefault();
    setInfoNotice(null);

    if (!form.nom.trim()) return setInfoNotice({ type: "error", text: t("profile.info.errors.name") });
    if (form.telephone.trim() && !PHONE_RE.test(form.telephone.trim()))
      return setInfoNotice({ type: "error", text: t("profile.info.errors.phone") });

    setSaving(true);
    try {
      const data = {
        nom: form.nom.trim(),
        telephone: form.telephone.trim(),
        adresse: form.adresse.trim(),
        ...(isStudent ? { mention: form.mention, niveau: form.niveau } : { poste: form.poste.trim() }),
      };
      const updated = await updateProfil({ data, photo });
      updateUser(updated);
      setPhoto(undefined);
      setInfoNotice({ type: "ok", text: t("profile.info.saved") });
    } catch {
      setInfoNotice({ type: "error", text: t("profile.info.errors.save") });
    } finally {
      setSaving(false);
    }
  };

  const savePassword = async (e) => {
    e.preventDefault();
    setPwdNotice(null);

    const fail = (key) => setPwdNotice({ type: "error", text: t(`profile.password.errors.${key}`) });
    if (pwd.next.length < 8) return fail("short");
    if (pwd.next !== pwd.confirm) return fail("mismatch");
    if (pwd.next === pwd.current) return fail("same");

    setPwdSaving(true);
    try {
      await changePassword(pwd.current, pwd.next);
      setPwd(EMPTY_PWD);
      setPwdNotice({ type: "ok", text: t("profile.password.saved") });
    } catch (err) {
      const status = err.response?.status;
      fail(status === 400 || status === 401 || status === 403 ? "wrong" : "generic");
    } finally {
      setPwdSaving(false);
    }
  };

  return (
    <section className="mx-auto max-w-3xl px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{t("profile.title")}</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("profile.subtitle")}</p>

      <div className="mt-8 space-y-6">
        {/* Photo + identité */}
        <div className={`${card} flex flex-col items-center gap-6 text-center sm:flex-row sm:text-left`}>
          <Avatar user={{ ...user, photo: shownPhoto }} size={96} />
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-xl font-bold">{form.nom || user.nom}</h2>
            <p className="truncate text-sm text-slate-500 dark:text-slate-400">{user.email}</p>
            <span className="mt-2 inline-block rounded-full bg-brand/15 px-3 py-1 text-xs font-semibold text-brand">
              {t(`profile.roles.${user.role}`)}
            </span>
          </div>
          <div className="flex flex-col items-center gap-2 sm:items-end">
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={pickPhoto} className="hidden" />
            <div className="flex flex-wrap justify-center gap-2">
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-4 py-2 text-sm font-medium transition hover:border-brand hover:text-brand dark:border-night-line"
              >
                <Camera size={16} /> {t("profile.photo.change")}
              </button>
              {shownPhoto && (
                <button
                  type="button"
                  onClick={() => setPhoto(null)}
                  className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm text-red-500 transition hover:bg-red-500/10"
                >
                  <Trash2 size={16} /> {t("profile.photo.remove")}
                </button>
              )}
            </div>
            <p className="text-xs text-slate-400">{t("profile.photo.hint")}</p>
          </div>
        </div>

        {/* Informations personnelles */}
        <form onSubmit={saveInfo} className={`${card} space-y-5`}>
          <h2 className="text-lg font-semibold">{t("profile.info.title")}</h2>
          <Notice notice={infoNotice} />

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("profile.info.name")} value={form.nom} onChange={set("nom")} required />
            <div>
              <Field label={t("profile.info.email")} value={user.email} disabled readOnly className="opacity-70" />
              <p className="mt-1.5 text-xs text-slate-400">{t("profile.info.emailHint")}</p>
            </div>

            <Field type="tel" label={t("profile.info.phone")} value={form.telephone} onChange={set("telephone")} placeholder="+261 34 00 000 00" />
            <Field label={t("profile.info.address")} value={form.adresse} onChange={set("adresse")} placeholder="Antananarivo, Madagascar" />

            {isStudent ? (
              <>
                <Field label={t("profile.info.matricule")} value={form.matricule || "—"} disabled readOnly className="opacity-70" />
                <Field as="select" label={t("profile.info.mention")} value={form.mention} onChange={set("mention")}>
                  {MENTIONS.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </Field>
                <Field as="select" label={t("profile.info.level")} value={form.niveau} onChange={set("niveau")}>
                  {NIVEAUX_ETUDE.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </Field>
              </>
            ) : (
              <Field
                className="sm:col-span-2"
                label={t("profile.info.position")}
                value={form.poste}
                onChange={set("poste")}
                placeholder="Responsable des stages"
              />
            )}
          </div>

          <SubmitButton loading={saving} disabled={!dirty}>
            {saving ? t("profile.info.saving") : t("profile.info.save")}
          </SubmitButton>
        </form>

        {/* Mot de passe */}
        <form onSubmit={savePassword} className={`${card} space-y-5`}>
          <div>
            <h2 className="text-lg font-semibold">{t("profile.password.title")}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t("profile.password.subtitle")}</p>
          </div>
          <Notice notice={pwdNotice} />

          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              className="sm:col-span-2"
              type={showPwd ? "text" : "password"}
              label={t("profile.password.current")}
              value={pwd.current}
              onChange={setP("current")}
              autoComplete="current-password"
              required
            />
            <Field
              type={showPwd ? "text" : "password"}
              label={t("profile.password.new")}
              value={pwd.next}
              onChange={setP("next")}
              autoComplete="new-password"
              required
            />
            <Field
              type={showPwd ? "text" : "password"}
              label={t("profile.password.confirm")}
              value={pwd.confirm}
              onChange={setP("confirm")}
              autoComplete="new-password"
              required
            />
          </div>
          <p className="text-xs text-slate-400">{t("profile.password.hint")}</p>

          <div className="flex flex-wrap items-center gap-4">
            <SubmitButton loading={pwdSaving} disabled={!pwd.current || !pwd.next || !pwd.confirm}>
              {pwdSaving ? t("profile.password.saving") : t("profile.password.submit")}
            </SubmitButton>
            <button
              type="button"
              onClick={() => setShowPwd((s) => !s)}
              className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-brand dark:text-slate-400"
            >
              {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              {showPwd ? t("login.hidePassword") : t("login.showPassword")}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}