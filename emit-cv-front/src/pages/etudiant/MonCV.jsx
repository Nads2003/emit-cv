import { useRef, useState } from "react";
import {
  Info,
  Upload,
  Printer,
  RotateCcw,
  Loader2,
  Globe,
  FileEdit,
  CheckCircle2,
  AlertCircle,
  Eye,
  Pencil,
} from "lucide-react";
import CvEditor from "@/components/cv/CvEditor";
import CvPreview from "@/components/cv/CvPreview";
import { useCv } from "@/hooks/useCv";
import { useLanguage } from "@/hooks/useLanguage";
import { importCv } from "@/api/cv.api";

const MODELS = ["moderne", "classique", "minimal"];
const MAX_SIZE = 5 * 1024 * 1024;

const toolBtn =
  "inline-flex items-center gap-2 rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium transition hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-50 dark:border-night-line";

export default function MonCV() {
  const { t } = useLanguage();
  const { cv, completude, setField, setProfil, addItem, updateItem, removeItem, replace, reset } = useCv();
  const fileRef = useRef(null);
  const [view, setView] = useState("edit"); // mobile : edit | preview
  const [importing, setImporting] = useState(false);
  const [notice, setNotice] = useState(null); // { type: "ok" | "error", key }

  const isPublished = cv.statut === "publie";
  // Règle de gestion : un CV doit avoir un nom et au moins une formation pour être publié
  const canPublish = cv.profil.nom.trim() && cv.formations.some((f) => f.diplome.trim());

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setNotice(null);

    if (!/\.(pdf|docx?)$/i.test(file.name)) return setNotice({ type: "error", key: "cv.import.badType" });
    if (file.size > MAX_SIZE) return setNotice({ type: "error", key: "cv.import.tooBig" });

    setImporting(true);
    try {
      const data = await importCv(file);
      replace({ ...data, source: "importe" });
      setNotice({ type: "ok", key: "cv.import.ok" });
    } catch {
      setNotice({ type: "error", key: "cv.import.error" });
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    if (window.confirm(t("cv.actions.resetConfirm"))) {
      reset();
      setNotice(null);
    }
  };

  const handlePrint = () => {
    setView("preview"); // l'aperçu doit être affiché pour être imprimé
    setTimeout(() => window.print(), 150);
  };

  return (
    <section className="mx-auto max-w-[1400px] px-5 py-12 lg:px-12">
      {/* En-tête */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">{t("cv.title")}</h1>
          <p className="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">{t("cv.subtitle")}</p>
        </div>
        <span
          className={`rounded-full px-4 py-1.5 text-sm font-medium ${
            isPublished ? "bg-emerald-500/15 text-emerald-500" : "bg-amber-400/15 text-amber-500"
          }`}
        >
          {t(`cv.status.${cv.statut}`)}
        </span>
      </div>

      {/* Bandeau démo */}
      <div className="mt-6 flex items-center gap-3 rounded-2xl border border-brand/30 bg-brand/10 px-5 py-3 text-sm text-brand">
        <Info size={18} className="shrink-0" />
        {t("cv.demo")}
      </div>

      {/* Barre d'outils */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input ref={fileRef} type="file" accept=".pdf,.doc,.docx" onChange={handleFile} className="hidden" />
        <button onClick={() => fileRef.current?.click()} disabled={importing} className={toolBtn}>
          {importing ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
          {importing ? t("cv.actions.importing") : t("cv.actions.import")}
        </button>

        <button
          onClick={() => setField("statut", isPublished ? "brouillon" : "publie")}
          disabled={!isPublished && !canPublish}
          title={!isPublished && !canPublish ? t("cv.publishHint") : undefined}
          className={
            isPublished
              ? toolBtn
              : "inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          }
        >
          {isPublished ? <FileEdit size={16} /> : <Globe size={16} />}
          {isPublished ? t("cv.actions.unpublish") : t("cv.actions.publish")}
        </button>

        <button onClick={handlePrint} className={toolBtn}>
          <Printer size={16} /> {t("cv.actions.download")}
        </button>

        <button onClick={handleReset} className={`${toolBtn} sm:ml-auto`}>
          <RotateCcw size={16} /> {t("cv.actions.reset")}
        </button>
      </div>

      {!isPublished && !canPublish && (
        <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{t("cv.publishHint")}</p>
      )}

      {notice && (
        <div
          role="status"
          className={`mt-4 flex items-center gap-2 rounded-xl border px-4 py-3 text-sm ${
            notice.type === "ok"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
              : "border-red-500/30 bg-red-500/10 text-red-500"
          }`}
        >
          {notice.type === "ok" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          {t(notice.key)}
        </div>
      )}

      {/* Complétude */}
      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-night-line dark:bg-night-card">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{t("cv.completeness")}</span>
          <span className="font-bold text-brand">{completude}%</span>
        </div>
        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-night-line">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-emerald-400 transition-all duration-500"
            style={{ width: `${completude}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-slate-400">{t("cv.autosave")}</p>
      </div>

      {/* Onglets mobile */}
      <div className="mt-6 flex gap-2 lg:hidden">
        {[
          { key: "edit", icon: Pencil },
          { key: "preview", icon: Eye },
        ].map(({ key, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`inline-flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition ${
              view === key ? "bg-brand text-white" : "bg-white dark:bg-night-card"
            }`}
          >
            <Icon size={16} /> {t(`cv.tabs.${key}`)}
          </button>
        ))}
      </div>

      {/* Éditeur + aperçu */}
      <div className="mt-6 grid gap-8 lg:grid-cols-2">
        <div className={view === "edit" ? "" : "hidden lg:block"}>
          <CvEditor
            cv={cv}
            setField={setField}
            setProfil={setProfil}
            addItem={addItem}
            updateItem={updateItem}
            removeItem={removeItem}
          />
        </div>

        <div
          className={`${view === "preview" ? "" : "hidden lg:block"} lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:self-start lg:overflow-y-auto`}
        >
          <div className="mb-4 flex flex-wrap gap-2">
            {MODELS.map((m) => (
              <button
                key={m}
                onClick={() => setField("modele", m)}
                className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                  cv.modele === m
                    ? "bg-brand text-white"
                    : "bg-white text-slate-600 hover:text-brand dark:bg-night-card dark:text-slate-200"
                }`}
              >
                {t(`cv.templates.${m}`)}
              </button>
            ))}
          </div>
          <CvPreview cv={cv} />
        </div>
      </div>
    </section>
  );
}