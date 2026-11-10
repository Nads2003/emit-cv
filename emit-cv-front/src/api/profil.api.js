import api from "./axiosInstance";
import { tokenStorage } from "@/utils/token";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * PATCH /api/auth/me/   (multipart/form-data)
 * data  : champs texte modifiés (nom, telephone, adresse, mention, niveau, poste)
 * photo : undefined = inchangée | null = supprimer | { blob, preview } = nouvelle photo
 * Réponse : l'utilisateur mis à jour { id, nom, email, role, telephone, adresse, photo, ... }
 */
export const updateProfil = async ({ data, photo }) => {
  if (MOCK) {
    await wait(600);
    const merged = { ...tokenStorage.getUser(), ...data };
    if (photo === null) merged.photo = null;
    else if (photo) merged.photo = photo.preview;
    return merged;
  }

  const formData = new FormData();
  Object.entries(data).forEach(([key, value]) => formData.append(key, value));
  if (photo === null) formData.append("supprimer_photo", "true");
  else if (photo) formData.append("photo", photo.blob, "photo.jpg");

  const { data: user } = await api.patch("/auth/me/", formData);
  return user;
};

/**
 * POST /api/auth/change-password/  { ancien_mot_de_passe, nouveau_mot_de_passe }
 * Réponse : 200, ou 400 si l'ancien mot de passe est incorrect
 */
export const changePassword = async (current, next) => {
  if (MOCK) {
    await wait(600);
    if (current.length < 4) {
      const err = new Error("wrong");
      err.response = { status: 400 };
      throw err;
    }
    return { ok: true };
  }
  const { data } = await api.post("/auth/change-password/", {
    ancien_mot_de_passe: current,
    nouveau_mot_de_passe: next,
  });
  return data;
};