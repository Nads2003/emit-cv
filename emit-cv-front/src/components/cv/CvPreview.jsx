import { Mail, Phone, MapPin } from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";

const LEVEL_PCT = { debutant: 25, intermediaire: 50, avance: 75, expert: 100 };

export default function CvPreview({ cv }) {
  const { t, lang } = useLanguage();
  const p = cv.profil;
  const model = cv.modele;

  const name = p.nom || t("cv.preview.name");
  const job = p.poste || t("cv.preview.job");
  const fmt = (v) =>
    v
      ? new Date(`${v}-01`).toLocaleDateString(lang === "fr" ? "fr-FR" : "en-GB", {
          month: "short",
          year: "numeric",
        })
      : "";
  const period = (e) =>
    e.dateDebut ? `${fmt(e.dateDebut)} – ${e.dateFin ? fmt(e.dateFin) : t("cv.preview.present")}` : "";

  const skills = cv.competences.filter((c) => c.nom.trim());
  const formations = cv.formations.filter((f) => f.diplome.trim() || f.etablissement.trim());
  const experiences = cv.experiences.filter((e) => e.poste.trim() || e.entreprise.trim());
  const contacts = [
    { icon: Mail, value: p.email },
    { icon: Phone, value: p.telephone },
    { icon: MapPin, value: p.adresse },
  ].filter((c) => c.value);
  const availability = p.disponibilite ? t(`cv.availability.${p.disponibilite}`) : "";

  const heading = {
    classique: "mb-2 border-b border-slate-300 pb-1 text-xs font-bold uppercase tracking-widest text-slate-800",
    moderne: "mb-2 text-xs font-bold uppercase tracking-widest text-brand",
    minimal: "mb-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-400",
  }[model];

  // Blocs communs
  const mainBlocks = (
    <>
      {p.resume && (
        <section>
          <h3 className={heading}>{t("cv.preview.profile")}</h3>
          <p className="text-[13px] leading-relaxed">{p.resume}</p>
        </section>
      )}
      {experiences.length > 0 && (
        <section>
          <h3 className={heading}>{t("cv.preview.experience")}</h3>
          <div className="space-y-3">
            {experiences.map((e) => (
              <div key={e.id}>
                <div className="flex justify-between gap-3">
                  <p className="text-sm font-semibold">{e.poste}</p>
                  <span className="shrink-0 text-xs text-slate-500">{period(e)}</span>
                </div>
                <p className="text-xs text-slate-600">{e.entreprise}</p>
                {e.description && <p className="mt-1 text-[13px] leading-relaxed">{e.description}</p>}
              </div>
            ))}
          </div>
        </section>
      )}
      {formations.length > 0 && (
        <section>
          <h3 className={heading}>{t("cv.preview.education")}</h3>
          <div className="space-y-2">
            {formations.map((f) => (
              <div key={f.id}>
                <div className="flex justify-between gap-3">
                  <p className="text-sm font-semibold">{f.diplome}</p>
                  <span className="shrink-0 text-xs text-slate-500">{f.annee}</span>
                </div>
                <p className="text-xs text-slate-600">{f.etablissement}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );

  const skillsList =
    model === "classique" ? (
      <p className="text-[13px]">{skills.map((s) => s.nom).join("  •  ")}</p>
    ) : (
      <div className="flex flex-wrap gap-1.5">
        {skills.map((s) => (
          <span key={s.id} className="rounded-full border border-slate-300 px-2.5 py-0.5 text-xs">
            {s.nom}
          </span>
        ))}
      </div>
    );

  const extraBlocks = (
    <>
      {skills.length > 0 && (
        <section>
          <h3 className={heading}>{t("cv.preview.skills")}</h3>
          {skillsList}
        </section>
      )}
      {availability && (
        <section>
          <h3 className={heading}>{t("cv.preview.availability")}</h3>
          <p className="text-[13px]">{availability}</p>
        </section>
      )}
    </>
  );

  const contactLine = (
    <>
      {contacts.map(({ icon: Icon, value }) => (
        <span key={value} className="inline-flex items-center gap-1.5">
          <Icon size={12} /> {value}
        </span>
      ))}
    </>
  );

  return (
    <div id="cv-print" className="min-h-[640px] overflow-hidden rounded-lg bg-white text-slate-900 shadow-2xl">
      {model === "moderne" && (
        <div className="grid min-h-[720px] grid-cols-[34%_66%]">
          <aside className="space-y-6 bg-brand p-6 text-white">
            {contacts.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-bold uppercase tracking-widest text-white/70">
                  {t("cv.preview.contact")}
                </h3>
                <div className="flex flex-col gap-2 break-words text-xs">{contactLine}</div>
              </section>
            )}
            {skills.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-bold uppercase tracking-widest text-white/70">
                  {t("cv.preview.skills")}
                </h3>
                <ul className="space-y-2.5">
                  {skills.map((s) => (
                    <li key={s.id}>
                      <p className="text-xs">{s.nom}</p>
                      <div className="mt-1 h-1 rounded bg-white/25">
                        <div className="h-1 rounded bg-white" style={{ width: `${LEVEL_PCT[s.niveau] ?? 50}%` }} />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {availability && (
              <section>
                <h3 className="mb-2 text-xs font-bold uppercase tracking-widest text-white/70">
                  {t("cv.preview.availability")}
                </h3>
                <p className="text-xs">{availability}</p>
              </section>
            )}
          </aside>
          <div className="space-y-5 p-6">
            <header>
              <h2 className="text-2xl font-bold leading-tight">{name}</h2>
              <p className="text-sm font-medium text-brand">{job}</p>
            </header>
            {mainBlocks}
          </div>
        </div>
      )}

      {model === "classique" && (
        <div className="space-y-5 p-8">
          <header className="border-b-2 border-slate-800 pb-4 text-center">
            <h2 className="font-serif text-3xl font-bold uppercase tracking-wide">{name}</h2>
            <p className="mt-1 text-sm">{job}</p>
            <div className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-slate-600">
              {contactLine}
            </div>
          </header>
          {mainBlocks}
          {extraBlocks}
        </div>
      )}

      {model === "minimal" && (
        <div className="space-y-6 p-8">
          <header>
            <h2 className="text-3xl font-light tracking-tight">{name}</h2>
            <p className="mt-1 text-sm text-slate-500">{job}</p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">{contactLine}</div>
          </header>
          {mainBlocks}
          {extraBlocks}
        </div>
      )}
    </div>
  );
}