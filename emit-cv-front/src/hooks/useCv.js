import { useCallback, useEffect, useMemo, useState } from "react";

const KEY = "emit_cv_demo";
const uid = () => Math.random().toString(36).slice(2, 9);

export const emptyCv = {
  titre: "",
  statut: "brouillon", // brouillon | publie
  source: "cree", // cree | importe
  modele: "moderne", // classique | moderne | minimal
  profil: { nom: "", poste: "", email: "", telephone: "", adresse: "", resume: "", disponibilite: "" },
  competences: [],
  formations: [],
  experiences: [],
};

const newItem = {
  competences: () => ({ id: uid(), nom: "", niveau: "intermediaire" }),
  formations: () => ({ id: uid(), diplome: "", etablissement: "", annee: "" }),
  experiences: () => ({ id: uid(), poste: "", entreprise: "", dateDebut: "", dateFin: "", description: "" }),
};

const normalize = (data) => ({ ...emptyCv, ...data, profil: { ...emptyCv.profil, ...data?.profil } });

const load = () => {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? normalize(JSON.parse(raw)) : emptyCv;
  } catch {
    return emptyCv;
  }
};

// Équivalent de calculerCompletude() du diagramme de classes
export const calculerCompletude = (cv) => {
  const p = cv.profil;
  const checks = [
    p.nom.trim(),
    p.email.trim(),
    p.telephone.trim(),
    p.resume.trim(),
    p.disponibilite,
    cv.formations.some((f) => f.diplome.trim()),
    cv.competences.filter((c) => c.nom.trim()).length >= 3,
    cv.experiences.some((e) => e.poste.trim()),
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
};

export function useCv() {
  const [cv, setCv] = useState(load);

  // Enregistrement automatique (démo : navigateur uniquement)
  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(cv));
    } catch {
      /* stockage indisponible */
    }
  }, [cv]);

  const completude = useMemo(() => calculerCompletude(cv), [cv]);

  const setField = useCallback((key, value) => setCv((c) => ({ ...c, [key]: value })), []);

  const setProfil = useCallback(
    (field, value) => setCv((c) => ({ ...c, profil: { ...c.profil, [field]: value } })),
    [],
  );

  const addItem = useCallback(
    (section) => setCv((c) => ({ ...c, [section]: [...c[section], newItem[section]()] })),
    [],
  );

  const updateItem = useCallback(
    (section, id, field, value) =>
      setCv((c) => ({
        ...c,
        [section]: c[section].map((it) => (it.id === id ? { ...it, [field]: value } : it)),
      })),
    [],
  );

  const removeItem = useCallback(
    (section, id) => setCv((c) => ({ ...c, [section]: c[section].filter((it) => it.id !== id) })),
    [],
  );

  // Remplace le contenu (import) en gardant le modèle choisi
  const replace = useCallback(
    (data) => setCv((c) => ({ ...normalize(data), modele: c.modele, statut: "brouillon" })),
    [],
  );

  const reset = useCallback(() => setCv(emptyCv), []);

  return { cv, completude, setField, setProfil, addItem, updateItem, removeItem, replace, reset };
}