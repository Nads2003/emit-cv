import { useEffect } from "react";
import { X } from "lucide-react";
import CvPreview from "@/components/cv/CvPreview";
import { useLanguage } from "@/hooks/useLanguage";

export default function ProfileModal({ candidat, onClose }) {
  const { t } = useLanguage();

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-slate-200 bg-white p-5 dark:border-night-line dark:bg-night-card sm:p-6"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold">{candidat.cv.profil.nom}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {candidat.matricule} · {candidat.mention} · {candidat.niveau}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label={t("offers.close")}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-300 text-slate-500 transition hover:border-brand hover:text-brand dark:border-night-line"
          >
            <X size={18} />
          </button>
        </div>
        <CvPreview cv={candidat.cv} />
      </div>
    </div>
  );
}