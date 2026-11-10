import { SKILL_LEVELS } from "@/constants/academic";

const rank = (level) => Math.max(0, SKILL_LEVELS.indexOf(level));
const norm = (s) => s.trim().toLowerCase();

// Critères normalisés (les anciennes offres n'ont pas de poids ni de niveau)
export const criteresOf = (offre) =>
  offre.competences
    .filter((c) => c.nom.trim())
    .map((c) => ({
      nom: c.nom,
      obligatoire: !!c.obligatoire,
      poids: c.poids ?? (c.obligatoire ? 4 : 2),
      niveauRequis: c.niveauRequis ?? "intermediaire",
    }));

/**
 * Équivalent de calculerScore(cv, offre) du diagramme de classes.
 * Simulation côté front : sera remplacée par le module IA de Django.
 */
export const calculerScore = (candidat, offre) => {
  const criteres = criteresOf(offre);
  if (criteres.length === 0) return { score: 0, communes: [], manquantes: [] };

  const mine = new Map(candidat.cv.competences.map((c) => [norm(c.nom), c.niveau]));
  const communes = [];
  const manquantes = [];
  let total = 0;
  let obtenu = 0;
  let obligatoireManquant = false;

  criteres.forEach((c) => {
    total += c.poids;
    const level = mine.get(norm(c.nom));
    if (level === undefined) {
      manquantes.push(c.nom);
      if (c.obligatoire) obligatoireManquant = true;
      return;
    }
    communes.push(c.nom);
    obtenu += c.poids * (rank(level) >= rank(c.niveauRequis) ? 1 : 0.6);
  });

  let score = (obtenu / total) * 100;
  if (communes.length > 0 && candidat.mention === offre.mention) score += 5;
  if (obligatoireManquant) score *= 0.6;

  return { score: Math.max(0, Math.min(100, Math.round(score))), communes, manquantes };
};