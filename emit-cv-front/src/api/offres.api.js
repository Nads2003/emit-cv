import api from "./axiosInstance";
import { offresStore } from "@/data/offresStore";
import { notifStore } from "@/data/notifStore";
import { historiqueStore } from "@/data/historiqueStore";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** GET /api/offres/ */
export const getOffres = async () => {
  if (MOCK) {
    await wait(500);
    return offresStore.all();
  }
  const { data } = await api.get("/offres/");
  return data;
};

/** GET /api/offres/{id}/ */
export const getOffre = async (id) => {
  if (MOCK) {
    await wait(250);
    const offre = offresStore.get(id);
    if (!offre) throw new Error("not found");
    return offre;
  }
  const { data } = await api.get(`/offres/${id}/`);
  return data;
};

/** POST /api/offres/ (création) ou PUT /api/offres/{id}/ (modification) */
export const saveOffre = async (offre) => {
  if (MOCK) {
    await wait(500);
    const isNew = !offre.id;
    const saved = offresStore.save(offre);
    historiqueStore.log(isNew ? "histo.offerCreated" : "histo.offerUpdated", { titre: saved.titre });
    if (isNew && saved.statut === "ouverte") notifStore.push("etudiant", "notif.newOffer", { titre: saved.titre });
    return saved;
  }
  const { data } = offre.id ? await api.put(`/offres/${offre.id}/`, offre) : await api.post("/offres/", offre);
  return data;
};

/** PATCH /api/offres/{id}/  { statut } : clôturer / republier */
export const changerStatutOffre = async (offre, statut) => {
  if (MOCK) {
    await wait(300);
    const saved = offresStore.save({ ...offre, statut });
    historiqueStore.log(statut === "ouverte" ? "histo.offerRepublished" : "histo.offerClosed", { titre: saved.titre });
    if (statut === "ouverte") notifStore.push("etudiant", "notif.newOffer", { titre: saved.titre });
    return saved;
  }
  const { data } = await api.patch(`/offres/${offre.id}/`, { statut });
  return data;
};

/** DELETE /api/offres/{id}/ */
export const supprimerOffre = async (id) => {
  if (MOCK) {
    await wait(300);
    const offre = offresStore.get(id);
    offresStore.remove(id);
    if (offre) historiqueStore.log("histo.offerDeleted", { titre: offre.titre });
    return;
  }
  await api.delete(`/offres/${id}/`);
};

/** POST /api/candidatures/  { offre: id } */
export const postulerOffre = async (offreId) => {
  if (MOCK) {
    await wait(500);
    const offre = offresStore.get(offreId);
    notifStore.push("admin", "notif.newApplication", { titre: offre?.titre ?? "" });
    return { ok: true };
  }
  const { data } = await api.post("/candidatures/", { offre: offreId });
  return data;
};