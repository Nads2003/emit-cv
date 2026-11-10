import api from "./axiosInstance";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// Données d'exemple renvoyées par l'import simulé
const sample = {
  titre: "CV Développeur web",
  profil: {
    nom: "Rakoto Jean",
    poste: "Développeur web Full Stack",
    email: "jean.rakoto@emit.mg",
    telephone: "+261 34 12 345 67",
    adresse: "Antananarivo, Madagascar",
    resume:
      "Étudiant en licence professionnelle en informatique, passionné par le développement web et l'intelligence artificielle. À la recherche d'un stage pour mettre en pratique mes compétences.",
    disponibilite: "immediate",
  },
  competences: [
    { id: "c1", nom: "React", niveau: "avance" },
    { id: "c2", nom: "Django", niveau: "intermediaire" },
    { id: "c3", nom: "PostgreSQL", niveau: "intermediaire" },
    { id: "c4", nom: "Tailwind CSS", niveau: "avance" },
  ],
  formations: [
    {
      id: "f1",
      diplome: "Licence professionnelle en Informatique",
      etablissement: "EMIT",
      annee: "2026",
    },
  ],
  experiences: [
    {
      id: "e1",
      poste: "Stagiaire développeur",
      entreprise: "Startup Mada Tech",
      dateDebut: "2025-07",
      dateFin: "2025-09",
      description: "Développement de modules React et d'une API Django REST.",
    },
  ],
};

/**
 * POST /api/cv/import/  (multipart, champ "file")
 * Réponse : le CV extrait par le module IA (même structure que `sample`)
 */
export const importCv = async (file) => {
  if (MOCK) {
    await wait(1500);
    return structuredClone(sample);
  }
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/cv/import/", formData);
  return data;
};