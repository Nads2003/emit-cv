import api from "./axiosInstance";
import { offresMock } from "@/data/offres.mock";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// Scores fictifs (calculés par le module IA une fois le back-end branché)
const mockScores = {
  1: { score: 92, communes: ["React", "Django", "PostgreSQL"], manquantes: ["Git"] },
  3: { score: 71, communes: ["API REST"], manquantes: ["React Native", "UI / UX"] },
  2: { score: 58, communes: ["SQL"], manquantes: ["Python", "Power BI"] },
};

/**
 * GET /api/recommandations/
 * Réponse attendue : tableau trié par score décroissant, chaque élément =
 * { ...offre, score, communes: [noms], manquantes: [noms] }
 */
export const getRecommandations = async () => {
  if (MOCK) {
    await wait(600);
    return Object.entries(mockScores)
      .map(([id, s]) => ({ ...offresMock.find((o) => o.id === Number(id)), ...s }))
      .sort((a, b) => b.score - a.score);
  }
  const { data } = await api.get("/recommandations/");
  return data;
};