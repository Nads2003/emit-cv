import api from "./axiosInstance";
import { offresStore } from "@/data/offresStore";

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
    return offresStore.save(offre);
  }
  const { data } = offre.id ? await api.put(`/offres/${offre.id}/`, offre) : await api.post("/offres/", offre);
  return data;
};

/** PATCH /api/offres/{id}/  { statut } : clôturer / republier */
export const changerStatutOffre = async (offre, statut) => {
  if (MOCK) {
    await wait(300);
    return offresStore.save({ ...offre, statut });
  }
  const { data } = await api.patch(`/offres/${offre.id}/`, { statut });
  return data;
};

/** DELETE /api/offres/{id}/ */
export const supprimerOffre = async (id) => {
  if (MOCK) {
    await wait(300);
    offresStore.remove(id);
    return;
  }
  await api.delete(`/offres/${id}/`);
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