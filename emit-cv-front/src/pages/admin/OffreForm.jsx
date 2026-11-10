import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Plus, Trash2, Loader2, AlertCircle } from "lucide-react";
import Field from "@/components/cv/Field";
import { MENTIONS, NIVEAUX_ETUDE, SKILL_LEVELS, OFFER_TYPES, OFFER_STATUS } from "@/constants/academic";
import { ROUTES } from "@/constants/routes";
import { getOffre, saveOffre } from "@/api/offres.api";
import { useLanguage } from "@/hooks/useLanguage";

const uid = () => Math.random().toString(36).slice(2, 9);
const newCritere = () => ({ id: uid(), nom: "", niveauRequis: "intermediaire", poids: 3, obligatoire: false });

const emptyForm = {
  titre: "",
  type: "stage",
  entreprise: "EMIT",
  lieu: "Antananarivo",
  description: "",
  mention: MENTIONS[0],
  niveau: "L3",
  statut: "ouverte",
  competences: [newCritere()],
};

const card = "rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card sm:p-8";

export default function OffreForm() {
  const { t } = useLanguage();
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEdit) return;
    let ignore = false;
    getOffre(id)
      .then((o) => {
        if (ignore) return;
        setForm({
          ...emptyForm,
          ...o,
          competences: o.competences.map((c) => ({
            id: uid(),
            nom: c.nom,
            niveauRequis: c.niveauRequis ?? "intermediaire",
            poids: c.poids ?? (c.obligatoire ? 4 : 2),
            obligatoire: !!c.obligatoire,
          })),
        });
      })
      .catch(() => !ignore && setError(t("admin.form.errors.load")))
      .finally(() => !ignore && setLoading(false));
    return () => {
      ignore = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const updateCritere = (cid, field, value) =>
    setForm((f) => ({
      ...f,
      competences: f.competences.map((c) => (c.id === cid ? { ...c, [field]: value } : c)),
    }));

  const addCritere = () => setForm((f) => ({ ...f, competences: [...f.competences, newCritere()] }));
  const removeCritere = (cid) =>
    setForm((f) => ({ ...f, competences: f.competences.filter((c) => c.id !== cid) }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    const criteres = form.competences.filter((c) => c.nom.trim());
    if (!form.titre.trim() || !form.description.trim()) return setError(t("admin.form.errors.missing"));
    if (criteres.length === 0) return setError(t("admin.form.errors.noCriteria"));

    setSaving(true);
    try {
      await saveOffre({
        ...form,
        titre: form.titre.trim(),
        description: form.description.trim(),
        competences: criteres.map((c) => ({
          nom: c.nom.trim(),
          niveauRequis: c.niveauRequis,
          poids: Number(c.poids),
          obligatoire: c.obligatoire,
        })),
      });
      navigate(ROUTES.ADMIN_OFFRES, { state: { saved: true } });
    } catch {
      setError(t("admin.form.errors.save"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="mx-auto max-w-3xl px-5 py-20 text-center text-slate-500">…</div>;
  }

  return (
    <section className="mx-auto max-w-3xl px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{isEdit ? t("admin.form.titleEdit") : t("admin.form.titleNew")}</h1>

      <form onSubmit={submit} className="mt-8 space-y-6">
        {error && (
          <div role="alert" className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
            <AlertCircle size={18} className="shrink-0" /> {error}
          </div>
        )}

        {/* Informations générales */}
        <div className={card}>
          <h2 className="mb-5 text-lg font-semibold">{t("admin.form.general")}</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field className="sm:col-span-2" label={t("admin.form.fields.title")} value={form.titre} onChange={set("titre")} required />

            <Field as="select" label={t("admin.form.fields.type")} value={form.type} onChange={set("type")}>
              {OFFER_TYPES.map((x) => (
                <option key={x} value={x}>{t(`offers.types.${x}`)}</option>
              ))}
            </Field>
            <Field as="select" label={t("admin.form.fields.status")} value={form.statut} onChange={set("statut")}>
              {OFFER_STATUS.map((x) => (
                <option key={x} value={x}>{t(`offers.status.${x}`)}</option>
              ))}
            </Field>

            <Field label={t("admin.form.fields.company")} value={form.entreprise} onChange={set("entreprise")} />
            <Field label={t("admin.form.fields.place")} value={form.lieu} onChange={set("lieu")} />

            <Field as="select" label={t("admin.form.fields.mention")} value={form.mention} onChange={set("mention")}>
              {MENTIONS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </Field>
            <Field as="select" label={t("admin.form.fields.level")} value={form.niveau} onChange={set("niveau")}>
              {NIVEAUX_ETUDE.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </Field>

            <Field
              as="textarea"
              rows={5}
              className="sm:col-span-2"
              label={t("admin.form.fields.description")}
              value={form.description}
              onChange={set("description")}
              required
            />
          </div>
        </div>

        {/* Critères */}
        <div className={card}>
          <h2 className="text-lg font-semibold">{t("admin.form.criteria")}</h2>
          <p className="mb-5 mt-1 text-sm text-slate-500 dark:text-slate-400">{t("admin.form.criteriaHint")}</p>

          <div className="space-y-4">
            {form.competences.map((c) => (
              <div key={c.id} className="rounded-2xl border border-slate-200 p-4 dark:border-night-line">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label={t("admin.form.fields.skill")}
                    value={c.nom}
                    onChange={(e) => updateCritere(c.id, "nom", e.target.value)}
                    placeholder="React"
                  />
                  <Field
                    as="select"
                    label={t("admin.form.fields.requiredLevel")}
                    value={c.niveauRequis}
                    onChange={(e) => updateCritere(c.id, "niveauRequis", e.target.value)}
                  >
                    {SKILL_LEVELS.map((l) => (
                      <option key={l} value={l}>{t(`cv.levels.${l}`)}</option>
                    ))}
                  </Field>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
                  <label className="flex items-center gap-3 text-sm">
                    <span className="text-slate-500 dark:text-slate-400">{t("admin.form.fields.weight")}</span>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={c.poids}
                      onChange={(e) => updateCritere(c.id, "poids", e.target.value)}
                      className="accent-brand"
                    />
                    <span className="w-4 font-bold text-brand">{c.poids}</span>
                  </label>

                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={c.obligatoire}
                      onChange={(e) => updateCritere(c.id, "obligatoire", e.target.checked)}
                      className="h-4 w-4 accent-brand"
                    />
                    {t("admin.form.fields.mandatory")}
                  </label>

                  <button
                    type="button"
                    onClick={() => removeCritere(c.id)}
                    className="ml-auto inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs text-red-500 transition hover:bg-red-500/10"
                  >
                    <Trash2 size={14} /> {t("admin.form.remove")}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={addCritere}
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-dashed border-brand/60 px-4 py-2 text-sm font-medium text-brand transition hover:bg-brand/10"
          >
            <Plus size={16} /> {t("admin.form.addCriterion")}
          </button>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-indigo-600 px-8 py-3 font-semibold text-white transition hover:brightness-110 disabled:opacity-70"
          >
            {saving && <Loader2 size={18} className="animate-spin" />}
            {saving ? t("admin.form.saving") : t("admin.form.save")}
          </button>
          <Link
            to={ROUTES.ADMIN_OFFRES}
            className="inline-flex items-center rounded-full border border-slate-300 px-8 py-3 text-sm font-medium transition hover:border-brand hover:text-brand dark:border-night-line"
          >
            {t("admin.form.cancel")}
          </Link>
        </div>
      </form>
    </section>
  );
}