import api from "./axiosInstance";
import { offresMock } from "@/data/offres.mock";

// Même variable que pour la connexion : true = données fictives
const MOCK = import.meta.env.VITE_AUTH_MOCK === "true";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** GET /api/offres/  → tableau d'offres (adapter si Django renvoie { results: [...] }) */
export const getOffres = async () => {
  if (MOCK) {
    await wait(500);
    return offresMock;
  }
  const { data } = await api.get("/offres/");
  return data;
};

/** POST /api/candidatures/  { offre: id } */
export const postulerOffre = async (offreId) => {
  if (MOCK) {
    await wait(500);
    return { ok: true };
  }
  const { data } = await api.post("/candidatures/", { offre: offreId });
  return data;
};