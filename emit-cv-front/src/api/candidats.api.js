import api from "./axiosInstance";
import { candidatsMock } from "@/data/candidats.mock";
import { offresStore } from "@/data/offresStore";
import { calculerScore } from "@/utils/scoring";
import { notifStore } from "@/data/notifStore";
import { historiqueStore } from "@/data/historiqueStore";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const KEY = "emit_decisions_demo"; // { "offreId:candidatId": "selectionne" | "refuse" }
const readDecisions = () => {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? {};
  } catch {
    return {};
  }
};
const writeDecisions = (d) => {
  try {
    localStorage.setItem(KEY, JSON.stringify(d));
  } catch {
    /* stockage indisponible */
  }
};

const published = () => candidatsMock.filter((c) => c.cvPublie);

/** GET /api/profils/ : étudiants dont le CV est publié */
export const getProfils = async () => {
  if (MOCK) {
    await wait(400);
    return published();
  }
  const { data } = await api.get("/profils/");
  return data;
};

/**
 * GET /api/offres/{id}/candidats-recommandes/
 * Réponse : tableau trié par score décroissant,
 * chaque élément = { ...candidat, score, communes, manquantes, decision }
 */
export const getClassement = async (offreId) => {
  if (MOCK) {
    await wait(700);
    const offre = offresStore.get(offreId);
    if (!offre) throw new Error("not found");
    const decisions = readDecisions();
    return published()
      .map((c) => ({
        ...c,
        ...calculerScore(c, offre),
        decision: decisions[`${offreId}:${c.id}`] ?? "attente",
      }))
      .sort((a, b) => b.score - a.score);
  }
  const { data } = await api.get(`/offres/${offreId}/candidats-recommandes/`);
  return data;
};

/** POST /api/offres/{id}/candidats/{candidatId}/decision/  { decision } */
/** POST /api/offres/{id}/candidats/{candidatId}/decision/  { decision } */
export const setDecision = async (offreId, candidatId, decision) => {
  if (MOCK) {
    await wait(250);
    const all = readDecisions();
    const key = `${offreId}:${candidatId}`;
    if (decision === "attente") delete all[key];
    else all[key] = decision;
    writeDecisions(all);

    const offre = offresStore.get(offreId);
    const candidat = candidatsMock.find((c) => c.id === Number(candidatId));
    const params = { nom: candidat?.cv.profil.nom ?? "", titre: offre?.titre ?? "" };
    historiqueStore.log(
      decision === "selectionne" ? "histo.selected" : decision === "refuse" ? "histo.rejected" : "histo.reset",
      params,
    );
    if (decision === "selectionne") notifStore.push("etudiant", "notif.selected", { titre: params.titre });
    return { ok: true };
  }
  const { data } = await api.post(`/offres/${offreId}/candidats/${candidatId}/decision/`, { decision });
  return data;
};

/** GET /api/admin/overview/ */
export const getAdminOverview = async () => {
  if (MOCK) {
    await wait(500);
    const offres = offresStore.all();
    const open = offres.filter((o) => o.statut === "ouverte");
    const profils = published();
    const topOffre = open[0] ?? null;
    const top = topOffre
      ? profils
          .map((c) => ({ ...c, ...calculerScore(c, topOffre) }))
          .sort((a, b) => b.score - a.score)
          .slice(0, 3)
      : [];
    return {
      stats: {
        offresOuvertes: open.length,
        offresTotal: offres.length,
        cvPublies: profils.length,
        selectionnes: Object.values(readDecisions()).filter((d) => d === "selectionne").length,
      },
      dernieresOffres: offres.slice(0, 4),
      topOffre,
      top,
    };
  }
  const { data } = await api.get("/admin/overview/");
  return data;
};