import { User, Wrench, GraduationCap, Briefcase, CalendarCheck, Plus, Trash2 } from "lucide-react";
import Field from "./Field";
import EditorSection from "./EditorSection";
import { useLanguage } from "@/hooks/useLanguage";

const LEVELS = ["debutant", "intermediaire", "avance", "expert"];
const AVAILABILITY = ["immediate", "oneMonth", "threeMonths", "notAvailable"];

function RemoveButton({ onClick, label, className = "" }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`flex h-10 w-10 items-center justify-center rounded-xl text-slate-400 transition hover:bg-red-500/10 hover:text-red-500 ${className}`}
    >
      <Trash2 size={16} />
    </button>
  );
}

function AddButton({ onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-full border border-dashed border-brand/60 px-4 py-2 text-sm font-medium text-brand transition hover:bg-brand/10"
    >
      <Plus size={16} /> {children}
    </button>
  );
}

function ItemCard({ children, onRemove, label }) {
  return (
    <div className="relative rounded-2xl border border-slate-200 p-4 pr-14 dark:border-night-line">
      <RemoveButton onClick={onRemove} label={label} className="absolute right-2 top-2" />
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </div>
  );
}

export default function CvEditor({ cv, setField, setProfil, addItem, updateItem, removeItem }) {
  const { t } = useLanguage();
  const p = cv.profil;
  const upd = (section, id, field) => (e) => updateItem(section, id, field, e.target.value);

  return (
    <div className="space-y-6">
      {/* Informations générales */}
      <EditorSection icon={User} title={t("cv.sections.general")}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            className="sm:col-span-2"
            label={t("cv.fields.title")}
            value={cv.titre}
            onChange={(e) => setField("titre", e.target.value)}
            placeholder={t("cv.fields.titlePh")}
          />
          <Field label={t("cv.fields.name")} value={p.nom} onChange={(e) => setProfil("nom", e.target.value)} />
          <Field label={t("cv.fields.job")} value={p.poste} onChange={(e) => setProfil("poste", e.target.value)} />
          <Field
            type="email"
            label={t("cv.fields.email")}
            value={p.email}
            onChange={(e) => setProfil("email", e.target.value)}
          />
          <Field
            type="tel"
            label={t("cv.fields.phone")}
            value={p.telephone}
            onChange={(e) => setProfil("telephone", e.target.value)}
          />
          <Field
            className="sm:col-span-2"
            label={t("cv.fields.address")}
            value={p.adresse}
            onChange={(e) => setProfil("adresse", e.target.value)}
          />
          <Field
            as="textarea"
            rows={4}
            className="sm:col-span-2"
            label={t("cv.fields.summary")}
            value={p.resume}
            onChange={(e) => setProfil("resume", e.target.value)}
          />
        </div>
      </EditorSection>

      {/* Disponibilité */}
      <EditorSection icon={CalendarCheck} title={t("cv.sections.availability")}>
        <Field
          as="select"
          label={t("cv.fields.availability")}
          value={p.disponibilite}
          onChange={(e) => setProfil("disponibilite", e.target.value)}
        >
          <option value="">{t("cv.fields.choose")}</option>
          {AVAILABILITY.map((a) => (
            <option key={a} value={a}>
              {t(`cv.availability.${a}`)}
            </option>
          ))}
        </Field>
      </EditorSection>

      {/* Compétences */}
      <EditorSection icon={Wrench} title={t("cv.sections.skills")}>
        {cv.competences.map((c) => (
          <div key={c.id} className="grid items-end gap-3 sm:grid-cols-[1fr_170px_auto]">
            <Field
              label={t("cv.fields.skill")}
              value={c.nom}
              onChange={upd("competences", c.id, "nom")}
              placeholder="React"
            />
            <Field
              as="select"
              label={t("cv.fields.level")}
              value={c.niveau}
              onChange={upd("competences", c.id, "niveau")}
            >
              {LEVELS.map((l) => (
                <option key={l} value={l}>
                  {t(`cv.levels.${l}`)}
                </option>
              ))}
            </Field>
            <RemoveButton onClick={() => removeItem("competences", c.id)} label={t("cv.remove")} />
          </div>
        ))}
        <AddButton onClick={() => addItem("competences")}>{t("cv.add.skill")}</AddButton>
      </EditorSection>

      {/* Formations */}
      <EditorSection icon={GraduationCap} title={t("cv.sections.education")}>
        {cv.formations.map((f) => (
          <ItemCard key={f.id} onRemove={() => removeItem("formations", f.id)} label={t("cv.remove")}>
            <Field
              className="sm:col-span-2"
              label={t("cv.fields.degree")}
              value={f.diplome}
              onChange={upd("formations", f.id, "diplome")}
            />
            <Field
              label={t("cv.fields.school")}
              value={f.etablissement}
              onChange={upd("formations", f.id, "etablissement")}
            />
            <Field
              type="number"
              min="1980"
              max="2100"
              label={t("cv.fields.year")}
              value={f.annee}
              onChange={upd("formations", f.id, "annee")}
            />
          </ItemCard>
        ))}
        <AddButton onClick={() => addItem("formations")}>{t("cv.add.education")}</AddButton>
      </EditorSection>

      {/* Expériences */}
      <EditorSection icon={Briefcase} title={t("cv.sections.experience")}>
        {cv.experiences.map((x) => (
          <ItemCard key={x.id} onRemove={() => removeItem("experiences", x.id)} label={t("cv.remove")}>
            <Field label={t("cv.fields.position")} value={x.poste} onChange={upd("experiences", x.id, "poste")} />
            <Field
              label={t("cv.fields.company")}
              value={x.entreprise}
              onChange={upd("experiences", x.id, "entreprise")}
            />
            <Field
              type="month"
              label={t("cv.fields.start")}
              value={x.dateDebut}
              onChange={upd("experiences", x.id, "dateDebut")}
            />
            <Field
              type="month"
              label={t("cv.fields.end")}
              value={x.dateFin}
              onChange={upd("experiences", x.id, "dateFin")}
            />
            <Field
              as="textarea"
              rows={3}
              className="sm:col-span-2"
              label={t("cv.fields.description")}
              value={x.description}
              onChange={upd("experiences", x.id, "description")}
            />
          </ItemCard>
        ))}
        <AddButton onClick={() => addItem("experiences")}>{t("cv.add.experience")}</AddButton>
      </EditorSection>
    </div>
  );
}